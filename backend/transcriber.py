import os
import tempfile
import sounddevice as sd
import soundfile as sf
import numpy as np
import keyboard
import time
import uuid
import hashlib
import psutil
import threading
import random
import logging
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from groq import Groq
from .logger import ensure_transcription_debug_handler, get_transcription_logger, log_transcription_event
# CAP TRANSITORIO A - reevaluar post B: hardening Groq (ver _call_groq_api)
try:
    from groq import APIStatusError as _GroqAPIStatusError, APITimeoutError as _GroqTimeoutError, RateLimitError as _GroqRateLimitError
except Exception:  # compat si groq no expone
    _GroqAPIStatusError = Exception
    _GroqTimeoutError = Exception
    _GroqRateLimitError = Exception
from .localization_manager import LocalizationManager
from .utf8_validator import UTF8Validator
from .custom_vocabulary import CustomVocabulary
from .blocks import BlockManager, ProcessingStage
from .blocks.task_extractor_block import TaskExtractorBlock
from .blocks.summary_block import SummaryBlock
from .blocks.keyword_extractor_block import KeywordExtractorBlock
from .nvidia_asr import NvidiaASR
from .transcription_metadata import TranscriptionMetadata
from .transcription_metadata_generator import TranscriptionMetadataGenerator
from .audio_chunker import transcribe_chunks

MIN_AUDIO_DURATION = 0.5
CHUNK_THRESHOLD_S = 28.0  # Audio >= 28s se troza para evitar pérdida en costuras de Groq

# ── Slice A Hardening constants ──────────────────────────────────────────
GROQ_TIMEOUT_S = 30  # timeout por chunk (CAP TRANSITORIO A - reevaluar post B)
GROQ_MAX_RETRIES_429 = 3
GROQ_BACKOFF_BASE_S = 1.0
GROQ_MAX_FILE_MB = 25  # Groq 413 threshold aprox 25MB
GROQ_CIRCUIT_THRESHOLD = 3  # fallos 429 consecutivos que abren circuito
GROQ_CIRCUIT_OPEN_S = 60  # segundos que permanece abierto
# CAP TRANSITORIO A - reevaluar post B
TRANSIENT_CAP_S = 720  # 12 min
_groq_circuit_failures = 0
_groq_circuit_open_until = 0.0
_groq_circuit_lock = threading.Lock()

# ── Slice B: paralelización Groq ──────────────────────────────────────────
# ThreadPoolExecutor 3 workers (2-4 configurable) — NO multiprocessing
GROQ_PARALLEL_WORKERS_DEFAULT = 3
GROQ_PARALLEL_WORKERS_MIN = 2
GROQ_PARALLEL_WORKERS_MAX = 4
GROQ_PARALLEL_TIMEOUT_S = 30  # timeout por future

class Transcriber:
    def __init__(self, config_manager, sound_manager, file_manager, update_status_callback, transcription_callback, localization_manager, overlay_callback=None):
        import queue as _queue
        # Ensure deterministic debug log file handler exists (flush per record)
        try:
            ensure_transcription_debug_handler()
        except Exception:
            pass
        self.logger = logging.getLogger(self.__class__.__name__)
        self.tlogger = get_transcription_logger()
        self.config_manager = config_manager
        self.sound_manager = sound_manager
        self.file_manager = file_manager
        self.update_status = update_status_callback
        self.transcription_callback = transcription_callback
        self.localization_manager = localization_manager
        # FIX v0.15.0: overlay_callback (si existe) se canaliza por la cola de eventos
        # para que el thread de grabación/transcripción NUNCA toque la UI directamente.
        self.overlay_callback = overlay_callback  # se llama vía _push_overlay_event
        # Slice A: cola ampliada a 64 para no descartar eventos críticos (progress Chunk X/48)
        # CAP TRANSITORIO A - reevaluar post B (antes 8, insuficiente para 48 chunks)
        self.timer_queue = _queue.Queue(maxsize=64)  # cola de eventos (timer/overlay/progress) para polling

        self.logger.info(f"Transcriber inicializado con hotkey: {self.config_manager.get('hotkey')}, modo de grabación: {self.config_manager.get('record_mode')}")

        self.is_recording = False
        self.recording_lock = threading.Lock()
        # FIX Bug F: lock dedicado para audio_data (compartido entre _record_loop y process_recording)
        self.audio_lock = threading.Lock()
        # v0.15.8 blindaje anti-duplicación: single-owner
        self.process_lock = threading.Lock()
        self.current_recording_id = None
        self.last_audio_hash = None
        self.last_process_time = 0.0
        self.stop_event = threading.Event()
        self.last_key_event_time = 0
        self.debounce_time = 0.2

        self.ejecutando = True
        self.audio_data = [] # List to store numpy arrays
        self.freq = 16000
        self.hotkey = self.config_manager.get("hotkey", "f12")
        self.record_mode = self.config_manager.get("record_mode", "toggle")
        self.audio_priority_apps = self.config_manager.get("audio_priority_apps", [])

        self.input_stream = None # sounddevice InputStream
        self.cliente = self._init_groq_client()
        self.nvidia_client = self._init_nvidia_client()

        self.hotkey_thread = threading.Thread(target=self.hotkey_listener, daemon=True)
        self.hotkey_thread.start()
        self.logger.info("Hilo de escucha de hotkey iniciado.")

        # Inicializar validador UTF-8 para corrección de caracteres españoles
        self.utf8_validator = UTF8Validator(logger=self.logger)
        utf8_validation = self.config_manager.get("utf8_validation", True)
        self.utf8_validation_enabled = utf8_validation if isinstance(utf8_validation, bool) else True
        self.logger.info(f"Validación UTF-8: {'activada' if self.utf8_validation_enabled else 'desactivada'}")

        # Inicializar BlockManager para procesamiento POST-transcripción
        self.block_manager = BlockManager()
        self._setup_blocks()
        self.logger.info("BlockManager inicializado con bloques POST-transcripción")

        # Inicializar CustomVocabulary para correcciones de palabras
        self.custom_vocab = CustomVocabulary()
        vocab_stats = self.custom_vocab.get_stats()
        self.logger.info(f"CustomVocabulary inicializado con {vocab_stats['total_corrections']} correcciones")

        # Inicializar TranscriptionMetadata para guardar metadatos
        self.metadata_manager = TranscriptionMetadata()
        self.logger.info("TranscriptionMetadata inicializado")

        # Inicializar generador de metadatos automáticos con LLM
        # FIX Bug H: use_llm=False — evitar SEGUNDA llamada a la API por cada transcripción
        # (duplicaba costo y latencia). Con False usa reglas simples, sin llamada extra.
        self.metadata_generator = TranscriptionMetadataGenerator(use_llm=False)
        self.logger.info("TranscriptionMetadataGenerator inicializado (LLM enabled)")

    def _setup_blocks(self):
        """
        Configurar e inicializar bloques POST-transcripción según config.

        Lee la configuración y registra los bloques habilitados.
        """
        # Configuración de bloques
        blocks_config = self.config_manager.get("blocks", {})

        # Task Extractor Block
        if blocks_config.get("task_extractor_enabled", True):
            task_config = {
                'min_priority': blocks_config.get("task_min_priority", 3),
                'max_tasks': blocks_config.get("task_max_tasks", 10),
                'extract_due_dates': blocks_config.get("task_extract_dates", True),
                'extract_assignees': blocks_config.get("task_extract_assignees", True)
            }
            self.block_manager.register_block(TaskExtractorBlock(config=task_config))
            self.logger.info(f"TaskExtractorBlock registrado (min_priority={task_config['min_priority']})")

        # Summary Block
        if blocks_config.get("summary_enabled", True):
            summary_config = {
                'max_sentences': blocks_config.get("summary_max_sentences", 3),
                'max_length': blocks_config.get("summary_max_length", 300),
                'include_keywords': blocks_config.get("summary_include_keywords", True)
            }
            self.block_manager.register_block(SummaryBlock(config=summary_config))
            self.logger.info(f"SummaryBlock registrado (max_sentences={summary_config['max_sentences']})")

        # Keyword Extractor Block
        if blocks_config.get("keyword_extractor_enabled", True):
            keyword_config = {
                'max_keywords': blocks_config.get("keyword_max_keywords", 10),
                'min_length': blocks_config.get("keyword_min_length", 4),
                'include_entities': blocks_config.get("keyword_include_entities", True),
                'use_vocabulary': blocks_config.get("keyword_use_vocabulary", True)
            }
            self.block_manager.register_block(KeywordExtractorBlock(config=keyword_config))
            self.logger.info(f"KeywordExtractorBlock registrado (max_keywords={keyword_config['max_keywords']})")

    def _init_groq_client(self):
        # Updated to use the new method in config_manager
        api_key = self.config_manager.get_groq_api_key_from_env()
        if not api_key:
            self.logger.warning("GROQ_API_KEY no configurada. El cliente Groq no se inicializará.")
            return None
        try:
            client = Groq(api_key=api_key, timeout=GROQ_TIMEOUT_S)
            self.logger.info(f"Cliente Groq inicializado exitosamente (timeout={GROQ_TIMEOUT_S}s).")
            return client
        except Exception as e:
            self.update_status(self.localization_manager.get_string("groq_init_error", error=e), "red")
            self.logger.error(f"Error al inicializar Groq: {e}")
            return None

    # ── Slice A helpers: circuit-breaker + error classification ─────────
    def _is_circuit_open(self) -> bool:
        with _groq_circuit_lock:
            return time.time() < _groq_circuit_open_until

    def _record_groq_success(self):
        global _groq_circuit_failures
        with _groq_circuit_lock:
            _groq_circuit_failures = 0

    def _record_groq_failure_429(self):
        global _groq_circuit_failures, _groq_circuit_open_until
        with _groq_circuit_lock:
            _groq_circuit_failures += 1
            if _groq_circuit_failures >= GROQ_CIRCUIT_THRESHOLD:
                _groq_circuit_open_until = time.time() + GROQ_CIRCUIT_OPEN_S
                self.logger.warning(f"Circuit-breaker GROQ abierto {_groq_circuit_open_until - time.time():.0f}s (429 x{_groq_circuit_failures})")

    def _classify_groq_error(self, e: Exception) -> str:
        """Clasifica error Groq: '413' | '429' | 'timeout' | 'other'."""
        # status_code directo (groq SDK)
        sc = getattr(e, "status_code", None)
        msg = str(e).lower()
        if sc == 413 or "413" in msg or "too large" in msg or "payload" in msg:
            return "413"
        if sc == 429 or isinstance(e, _GroqRateLimitError) or "429" in msg or "rate limit" in msg:
            return "429"
        if isinstance(e, _GroqTimeoutError) or "timeout" in msg or "timed out" in msg:
            return "timeout"
        # httpx timeouts
        if "httpx" in msg and "timeout" in msg:
            return "timeout"
        return "other"

    # ── Slice B helper: workers configurables ────────────────────────────
    def _get_parallel_workers(self) -> int:
        """Retorna workers Groq clamp [2,4], default 3."""
        try:
            w = int(self.config_manager.get("groq_parallel_workers", GROQ_PARALLEL_WORKERS_DEFAULT))
        except Exception:
            w = GROQ_PARALLEL_WORKERS_DEFAULT
        return max(GROQ_PARALLEL_WORKERS_MIN, min(GROQ_PARALLEL_WORKERS_MAX, w))

    def _init_nvidia_client(self):
        """Inicializar cliente NVIDIA Riva ASR si está configurado."""
        nvidia_api_key = self.config_manager.get("nvidia_api_key") or os.environ.get("NVIDIA_API_KEY")
        nvidia_mode = self.config_manager.get("nvidia_mode", "cloud")  # "cloud" o "local"
        nvidia_enabled = self.config_manager.get("nvidia_enabled", False)

        if not nvidia_enabled:
            self.logger.info("NVIDIA Riva ASR deshabilitado en configuración.")
            return None

        try:
            client = NvidiaASR(api_key=nvidia_api_key, mode=nvidia_mode)
            if client.is_available():
                self.logger.info(f"Cliente NVIDIA Riva ASR inicializado (modo: {nvidia_mode})")
                return client
            else:
                self.logger.warning("NVIDIA Riva ASR: nvidia-riva-client no está instalado")
                return None
        except Exception as e:
            self.logger.warning(f"Error al inicializar NVIDIA Riva ASR: {e}")
            return None

    def _init_faster_whisper_client(self):
        """FIX: faster-whisper (modelo local) ERRADICADO — la app usa API cloud (Groq)."""
        return None

    def get_transcription_service(self):
        """
        Obtener el servicio de transcripción activo.

        Returns:
            'nvidia' o 'groq', o None si no hay ninguno disponible.
        """
        asr_provider = self.config_manager.get("asr_provider", "groq")  # "groq" o "nvidia"

        if asr_provider == "nvidia":
            return "nvidia" if self.nvidia_client else None
        else:
            return "groq" if self.cliente else None

    def reload_client(self):
        """Reinicializa los clientes de transcripción (Groq y NVIDIA)."""
        self.logger.info("Recargando clientes de transcripción...")
        self.cliente = self._init_groq_client()
        self.nvidia_client = self._init_nvidia_client()

        service = self.get_transcription_service()
        if service:
            service_names = {
                "nvidia": "NVIDIA Riva",
                "groq": "Groq",
            }
            service_name = service_names.get(service, service)
            self.update_status(f"Cliente {service_name} listo", "white")
        else:
            self.update_status("API Key inválida o faltante", "red")

    def update_utf8_validation(self, enabled: bool):
        """
        Actualizar la configuración de validación UTF-8.

        Args:
            enabled: True para activar, False para desactivar
        """
        self.utf8_validation_enabled = enabled
        self.logger.info(f"Validación UTF-8: {'activada' if enabled else 'desactivada'}")
        return enabled

    def reload_blocks(self):
        """
        Recargar bloques según configuración actual.

        Útil cuando cambia la configuración de bloques.
        """
        self.logger.info("Recargando bloques...")
        self.block_manager = BlockManager()
        self._setup_blocks()
        self.logger.info("Bloques recargados exitosamente")

    def get_block_results(self) -> list:
        """
        Obtener resultados del procesamiento de bloques de la última transcripción.

        Returns:
            Lista de BlockResult o lista vacía si no hay resultados
        """
        return getattr(self, 'last_block_results', [])

    def get_block_stats(self) -> dict:
        """
        Obtener estadísticas de los bloques.

        Returns:
            Diccionario con estadísticas de cada bloque
        """
        return self.block_manager.get_stats()

    def enable_block(self, block_name: str) -> bool:
        """Activar un bloque específico."""
        return self.block_manager.enable_block(block_name)

    def disable_block(self, block_name: str) -> bool:
        """Desactivar un bloque específico."""
        return self.block_manager.disable_block(block_name)

    def validate_text(self, text: str) -> tuple:
        """
        Validar un texto específico y retornar estado de validación.

        Args:
            text: Texto a validar

        Returns:
            Tuple con (es_válido, lista de problemas)
        """
        return self.utf8_validator.validate_transcription(text)

    def hotkey_listener(self):
        self.logger.info(f"Escuchando hotkey: {self.hotkey}")
        # Initial hook
        self._hook_hotkey()
        
        while self.ejecutando:
             time.sleep(1) # Keep thread alive, hotkey hooked
        
        keyboard.unhook_all()
        self.logger.info("Hilo de escucha de hotkey finalizado.")
    
    def _hook_hotkey(self):
        try:
            # v0.15.8: no desenganchar durante grabación — evita race que duplica hotkey events
            if getattr(self, 'is_recording', False):
                self.logger.info("_hook_hotkey deferido: grabación en curso, no se hace unhook")
                return
            keyboard.unhook_all()

            # Detectar si el hotkey tiene modificadores (contiene "+")
            if "+" in self.hotkey:
                # Hotkey con modificadores: usar add_hotkey()
                # Nota: add_hotkey solo dispara en KEY_DOWN, ideal para modo toggle
                # Para modo hold con modificadores, necesitamos un enfoque diferente
                if self.record_mode == "toggle":
                    keyboard.add_hotkey(self.hotkey, self._handle_toggle_hotkey, suppress=True)
                    self.logger.info(f"Hotkey enganchado (toggle): {self.hotkey}")
                else:
                    # Modo hold con modificadores: usar hook personalizado
                    keyboard.hook(self._handle_modifier_hotkey)
                    self.logger.info(f"Hotkey enganchado (hold con modificadores): {self.hotkey}")
            else:
                # Hotkey simple sin modificadores: usar métodos antiguos
                keyboard.on_press_key(self.hotkey, self.handle_key_event, suppress=True)
                keyboard.on_release_key(self.hotkey, self.handle_key_event, suppress=True)
                self.logger.info(f"Hotkey enganchado: {self.hotkey}")
        except Exception as e:
            self.logger.error(f"Error enganchando hotkey: {e}")

    def update_hotkey(self, new_hotkey):
        self.logger.info(f"Actualizando hotkey a: {new_hotkey}")
        self.hotkey = new_hotkey
        # v0.15.8: diferir re-hook si hay grabación activa
        if getattr(self, 'is_recording', False):
            self.logger.info("update_hotkey deferido: grabación en curso")
            return
        self._hook_hotkey()

    def handle_key_event(self, event):
        with self.recording_lock:
            # En modo hold, no aplicar debounce al KEY_UP para que responda inmediatamente
            if self.record_mode == "hold" and event.event_type == keyboard.KEY_UP:
                if self.is_recording:
                    self.stop_recording()
                return
            
            # Debounce solo para KEY_DOWN
            current_time = time.time()
            if (current_time - self.last_key_event_time) < self.debounce_time:
                return
            self.last_key_event_time = current_time

            if self.record_mode == "toggle":
                if event.event_type == keyboard.KEY_DOWN:
                    if not self.is_recording:
                        self.start_recording()
                    else:
                        self.stop_recording()
            
            elif self.record_mode == "hold":
                if event.event_type == keyboard.KEY_DOWN and not self.is_recording:
                    self.start_recording()

    def _handle_toggle_hotkey(self):
        """Handler para hotkeys con modificadores en modo toggle."""
        with self.recording_lock:
            current_time = time.time()
            if (current_time - self.last_key_event_time) < self.debounce_time:
                return
            self.last_key_event_time = current_time

            if not self.is_recording:
                self.start_recording()
            else:
                self.stop_recording()

    def _handle_modifier_hotkey(self, event):
        """
        Handler para hotkeys con modificadores en modo hold.
        Usa keyboard.hook() para detectar KEY_DOWN y KEY_UP de modificadores.
        """
        # v0.15.8: debounce unificado — también para path add_hotkey/hook (antes solo toggle)
        # Debounce en KEY_DOWN; KEY_UP no se debouncea para hold responsivo
        if event.event_type == keyboard.KEY_DOWN:
            _now = time.time()
            if (_now - self.last_key_event_time) < self.debounce_time:
                return
            # actualizamos last_key_event_time dentro del lock más abajo para ser precisos,
            # pero hacemos check temprano para no parsear innecesario
        # Verificar si este evento corresponde a nuestro hotkey
        try:
            # Parsear el hotkey actual
            hotkey_obj = self.hotkey_manager.parse_hotkey_string(self.hotkey)

            # Obtener el estado actual de los modificadores
            current_modifiers = []
            if keyboard.is_pressed('ctrl'):
                current_modifiers.append('ctrl')
            if keyboard.is_pressed('alt'):
                current_modifiers.append('alt')
            if keyboard.is_pressed('shift'):
                current_modifiers.append('shift')

            # Obtener la tecla presionada
            key_name = event.name.lower().replace(' ', '_')

            # Verificar si coincide con nuestro hotkey
            modifiers_match = set(current_modifiers) == set(hotkey_obj.modifiers)
            key_match = key_name == hotkey_obj.key

            if modifiers_match and key_match:
                with self.recording_lock:
                    if event.event_type == keyboard.KEY_DOWN:
                        # v0.15.8: debounce unificado — registrar timestamp al consumir KEY_DOWN
                        _now2 = time.time()
                        if (_now2 - self.last_key_event_time) < self.debounce_time:
                            return
                        self.last_key_event_time = _now2
                        if not self.is_recording:
                            self.start_recording()
                    elif event.event_type == keyboard.KEY_UP:
                        if self.is_recording:
                            self.stop_recording()
        except Exception as e:
            self.logger.debug(f"Error en _handle_modifier_hotkey: {e}")

    def start_recording(self):
        if self.is_recording: return
        if any(p.info['name'].lower() in self.audio_priority_apps for p in psutil.process_iter(['pid', 'name'])):
            self.update_status(self.localization_manager.get_string("priority_app_in_use"), "orange")
            return

        # v0.15.8 single-owner: asignar recording_id al inicio (owner)
        self.current_recording_id = str(uuid.uuid4())
        self.is_recording = True
        # FIX Bug F: reset de audio_data bajo lock (evita correr contra process_recording)
        with self.audio_lock:
            self.audio_data = []
        self.stop_event.clear()
        self.sound_manager.sound_start_recording()
        self.update_status(self.localization_manager.get_string("status_recording"), "green")
        self.logger.info("Grabación iniciada.")
        
        # Actualizar overlay (vía cola, nunca directo desde el thread)
        self._push_overlay_event("recording", 0, 0)
        
        try:
            # Initialize SoundDevice Stream
            self.input_stream = sd.InputStream(samplerate=self.freq, channels=1, dtype='float32')
            self.input_stream.start()
            
            self.recording_thread = threading.Thread(target=self._record_loop, daemon=True)
            self.recording_thread.start()
        except Exception as e:
            self.update_status(self.localization_manager.get_string("audio_error_mic_in_use"), "red")
            self.is_recording = False
            self.logger.error(f"Error al iniciar el stream de audio: {e}")

    def _record_loop(self):
        """Bucle de grabación — HOT LOOP de SOLO lectura de audio.

        FIX v0.15.0 (Kaizen Nodal / sdd-explore): el bug de grabaciones largas era
        la UI dentro del bucle: update_status/overlay_callback hacen after() cross-
        thread que se traban con el lock de Tcl cuando el main thread está ocupado,
        estancando el read() de audio → frames perdidos SILENCIOSAMENTE → audio
        comprimido/cortado → Groq devuelve texto con palabras cortadas y tildes
        faltantes en esos puntos ("funciona por momentos y por momentos no").

        Propiedad ESTRUCTURAL: la captura de audio es un hot-loop que NUNCA debe
        bloquearse. La UI se actualiza por POLLING desde el main thread vía cola.
        """
        import queue
        if not hasattr(self, 'timer_queue'):
            # CAP TRANSITORIO A - reevaluar post B: maxsize 64 para progress 48 chunks
            self.timer_queue = queue.Queue(maxsize=64)  # cola acotada, put_nowait no bloquea

        start_time = time.time()
        max_time = self.config_manager.get("max_recording_time", 300)
        last_ui_push = 0.0
        ui_interval = 0.25  # 250ms — push de timer a la cola, NUNCA bloquea lectura

        while not self.stop_event.is_set():
            try:
                # 1) ÚNICA prioridad: leer audio, inmediato y sin bloqueos
                if self.input_stream.active:
                    data, overflowed = self.input_stream.read(1024)
                    if overflowed:
                        self.logger.warning("Audio buffer overflow")
                    with self.audio_lock:
                        self.audio_data.append(data)

                # 2) Push de timer a la cola (no bloquea: put_nowait + cola acotada)
                now = time.time()
                elapsed_time = now - start_time
                if elapsed_time > max_time:
                    # FIX: drenar el buffer antes de cortar (última lectura parcial)
                    self._drain_remaining_audio()
                    # Avisar que se cortó por límite (vía cola, sin bloquear)
                    try:
                        qd = self.timer_queue.qsize()
                    except Exception:
                        qd = -1
                    try:
                        self.tlogger.info(f"record_loop AUTO-CUT dur={elapsed_time:.1f}s cap={max_time}s queue_depth={qd}")
                    except Exception:
                        pass
                    try:
                        self._queue_put(("limit", int(max_time)), critical=True)
                    except Exception:
                        pass
                    # stop_recording ahora es seguro desde recording_thread (skip join)
                    try:
                        self.stop_recording()
                    except Exception as _stop_e:
                        try:
                            self.tlogger.error(f"record_loop stop_recording error: {_stop_e}")
                        except Exception:
                            pass
                        self.logger.error(f"record_loop stop_recording error: {_stop_e}")
                    break
                if now - last_ui_push >= ui_interval:
                    last_ui_push = now
                    minutes, seconds = divmod(int(elapsed_time), 60)
                    try:
                        self.timer_queue.put_nowait(("timer", minutes, seconds))
                    except Exception:
                        pass  # cola llena → se saltea un tick, nunca bloquea la captura

            except Exception as e:
                self.logger.error(f"Error en bucle de grabación: {e}")
                try:
                    self.tlogger.error(f"record_loop exception: {e} queue_depth={self.timer_queue.qsize()}")
                except Exception:
                    pass
                # Evitar doble stop si ya se detuvo (el fix de join ya evitó RuntimeError, pero este except era el que causaba second call con is_recording False → no process)
                # Solo intentar stop si aún está grabando
                if getattr(self, "is_recording", False):
                    try:
                        self.stop_recording()
                    except Exception:
                        pass
                break

    def _drain_remaining_audio(self):
        """FIX: leer lo que quede en el buffer de PortAudio antes de cerrar.

        Cuando se corta por max_recording_time o por stop, el stream puede tener
        frames pendientes que de otro modo se pierden (la race que descartaba el
        bloque final). Se lee hasta vaciar o timeout corto (sin bloquear mucho).
        """
        try:
            if not self.input_stream or not self.input_stream.active:
                return
            import time as _t
            deadline = _t.time() + 0.15  # máx 150ms de drenado
            while _t.time() < deadline and self.input_stream.active:
                try:
                    data, _ = self.input_stream.read(1024)
                    with self.audio_lock:
                        self.audio_data.append(data)
                except Exception:
                    break
        except Exception as e:
            self.logger.warning(f"Error drenando audio: {e}")

    def get_timer_event(self):
        """Consumir un evento de timer de la cola (usado por el polling de la UI).

        Returns:
            Tupla ("timer", minutes, seconds), ("limit", seconds),
            ("overlay", state, minutes, seconds), ("progress", cur, total, eta_s)
            o None si vacía.
        """
        import queue
        q = getattr(self, 'timer_queue', None)
        if q is None:
            return None
        try:
            return q.get_nowait()
        except queue.Empty:
            return None

    def _queue_put(self, item, critical=False):
        """Encolar sin perder eventos críticos. CAP TRANSITORIO A - reevaluar post B"""
        import queue
        q = getattr(self, 'timer_queue', None)
        if q is None:
            return False
        try:
            q.put_nowait(item)
            # log queue depth at DEBUG for transcription_debug
            try:
                if critical or item[0] == "progress":
                    self.tlogger.debug(f"queue_put OK {item[0]} q={q.qsize()}/{q.maxsize} critical={critical}")
            except Exception:
                pass
            return True
        except queue.Full:
            try:
                qd = q.qsize()
            except Exception:
                qd = -1
            if critical:
                # eventos críticos: intentar con timeout corto, si aún lleno descartar el más viejo y reintentar
                try:
                    self.tlogger.debug(f"queue_put FULL critical={item[0]} q={qd}/{q.maxsize} trying timeout 0.15s")
                except Exception:
                    pass
                try:
                    q.put(item, timeout=0.15)
                    try:
                        self.tlogger.debug(f"queue_put RETRY OK {item[0]} q={q.qsize()}/{q.maxsize}")
                    except Exception:
                        pass
                    return True
                except queue.Full:
                    try:
                        # hacer espacio descartando un timer no crítico si existe
                        discarded = q.get_nowait()
                        q.put_nowait(item)
                        try:
                            self.tlogger.warning(f"queue_put DISCARDED oldest={discarded[0]} to make room for critical={item[0]} q={q.qsize()}/{q.maxsize}")
                        except Exception:
                            pass
                        return True
                    except Exception:
                        self.logger.debug(f"timer_queue llena, evento crítico descartado: {item[0]}")
                        try:
                            self.tlogger.warning(f"queue_put CRITICAL DISCARD {item[0]} q={qd}/{q.maxsize}")
                        except Exception:
                            pass
                        return False
            else:
                self.logger.debug(f"timer_queue llena, evento no crítico descartado: {item[0]}")
                try:
                    self.tlogger.debug(f"queue_put DISCARD non-critical {item[0]} q={qd}/{q.maxsize}")
                except Exception:
                    pass
                return False
        except Exception:
            return False

    def _push_progress_event(self, current: int, total: int, eta_s: float):
        """Progress Chunk X/Y ETA Zs — evento crítico, no debe perderse."""
        try:
            self.tlogger.debug(f"progress push Chunk {current}/{total} ETA {eta_s:.1f}s q={self.timer_queue.qsize()}/{self.timer_queue.maxsize}")
        except Exception:
            pass
        self._queue_put(("progress", int(current), int(total), float(eta_s)), critical=True)

    def _push_overlay_event(self, state, minutes=0, seconds=0):
        """FIX: canalizar actualizaciones de overlay por la cola (nunca bloquear).

        El thread de grabación/transcripción NO debe tocar la UI directamente
        (eso trababa la captura en grabaciones largas). Este método encola el
        evento; la UI lo consume por polling.
        """
        # overlay es crítico para UX pero puede ser lossy si hay burst; lo marcamos critical
        if not self._queue_put(("overlay", state, minutes, seconds), critical=True):
            # Fallback directo si no hay cola (compatibilidad)
            if getattr(self, 'overlay_callback', None):
                try:
                    self.overlay_callback(state, minutes, seconds)
                except Exception:
                    pass

    def stop_recording(self):
        if not self.is_recording: return
        
        self.stop_event.set()
        self.is_recording = False
        self.sound_manager.sound_stop_recording()
        self.update_status(self.localization_manager.get_string("status_processing"), "yellow")
        self.logger.info("Grabación detenida. Iniciando procesamiento.")
        
        # Actualizar overlay (vía cola) — crítico, no descartar
        self._push_overlay_event("processing", 0, 0)

        # Slice A: join ampliado para no descartar audio/timer crítico (CAP TRANSITORIO A - reevaluar post B)
        # FIX CRÍTICO 12m smoke (cannot join current thread): si stop_recording se llama
        # desde el propio recording_thread (auto-cut por max_recording_time en _record_loop),
        # join al current thread lanza RuntimeError y aborta antes de spawnear process_recording.
        if getattr(self, 'recording_thread', None) and self.recording_thread.is_alive():
            if threading.current_thread() is self.recording_thread:
                # auto-cut path — no hacer join a sí mismo, solo log y continuar a process_recording
                try:
                    self.tlogger.debug("stop_recording: llamado desde recording_thread (auto-cut) — skip join, queue_depth=%s" % self.timer_queue.qsize())
                except Exception:
                    pass
                self.logger.debug("stop_recording: auto-cut desde recording_thread — skip join (evita RuntimeError)")
            else:
                try:
                    self.recording_thread.join(timeout=1.0)
                except RuntimeError as _join_err:
                    self.logger.warning(f"join recording_thread falló (RuntimeError): {_join_err} — continuando a process_recording")
                    try:
                        self.tlogger.warning(f"join RuntimeError skip: {_join_err} queue_depth={self.timer_queue.qsize()}")
                    except Exception:
                        pass
                if self.recording_thread.is_alive():
                    self.logger.warning("recording_thread aún vivo tras join 1.0s — posible pérdida de último bloque, drenando")
                    try:
                        self.tlogger.warning(f"recording_thread aún vivo tras 1.0s queue_depth={self.timer_queue.qsize()}")
                    except Exception:
                        pass
                    # intentar drenar una vez más aunque el thread siga
                    try:
                        self._drain_remaining_audio()
                    except Exception:
                        pass

        if self.input_stream:
            try:
                self.input_stream.stop()
                self.input_stream.close()
            except Exception as e:
                self.logger.warning(f"Error cerrando stream: {e}")
            self.input_stream = None

        if not self.audio_data:
            self.update_status(self.localization_manager.get_string("no_audio_captured"), "red")
            return

        # v0.15.8 single-owner: snapshot + recording_id ANTES de spawnear thread (sin tocar _record_loop)
        recording_id = self.current_recording_id
        with self.audio_lock:
            audio_snapshot = list(self.audio_data)
        if not audio_snapshot:
            self.update_status(self.localization_manager.get_string("no_audio_captured"), "red")
            return
        threading.Thread(target=self.process_recording, args=(recording_id, audio_snapshot), daemon=True).start()

    def process_recording(self, recording_id=None, audio_snapshot=None):
        # v0.15.8 single-owner + hash dedup + process_lock
        # Discard stale recording_id (ya no es el current owner)
        if recording_id is not None and self.current_recording_id is not None and recording_id != self.current_recording_id:
            self.logger.warning(f"process_recording descartado: stale recording_id {recording_id} != current {self.current_recording_id}")
            return
        # process_lock: solo uno a la vez; si ya hay uno en curso, descarta duplicado
        if not self.process_lock.acquire(blocking=False):
            self.logger.warning("process_recording ya en curso, descartando duplicado (process_lock)")
            return
        # hash dedup: si mismo audio <2s, descarta
        _snapshot_for_hash = audio_snapshot
        if _snapshot_for_hash is None:
            with self.audio_lock:
                _snapshot_for_hash = list(self.audio_data)
        _audio_hash = None
        try:
            if _snapshot_for_hash:
                _concat = np.concatenate(_snapshot_for_hash, axis=0) if len(_snapshot_for_hash) > 0 else None
                if _concat is not None and len(_concat) > 0:
                    _audio_hash = hashlib.sha1(_concat.tobytes()).hexdigest()
                    _now = time.time()
                    if _audio_hash == self.last_audio_hash and (_now - self.last_process_time) < 2.0:
                        self.logger.warning(f"process_recording descartado por hash duplicado { _audio_hash[:8]} <2s")
                        self.process_lock.release()
                        return
        except Exception as _e:
            self.logger.debug(f"hash dedup error (non-blocking): {_e}")

        self.logger.info(f"Iniciando procesamiento de grabación (id={recording_id}).")
        temp_path = None
        transcription = None
        try:
            # Usar snapshot pasado o tomar uno nuevo
            if audio_snapshot is not None:
                _snap = audio_snapshot
            else:
                with self.audio_lock:
                    _snap = list(self.audio_data)
            if not _snap:
                self.update_status(self.localization_manager.get_string("no_audio_captured"), "red")
                return
            # guarda hash/tiempo para dedup futuro (solo si no fue descartado)
            if _audio_hash is not None:
                self.last_audio_hash = _audio_hash
                self.last_process_time = time.time()
            # Combine audio data chunks
            full_audio = np.concatenate(_snap, axis=0)
            duration = len(full_audio) / self.freq
            
            if duration < MIN_AUDIO_DURATION:
                self.update_status(self.localization_manager.get_string("audio_too_short", min_duration=1.5), "red")
                self.logger.warning("Audio demasiado corto (< 1.5s).")
                self._push_overlay_event("ready")  # Ocultar overlay si es corto
                return
            # CAP TRANSITORIO A - reevaluar post B: clamp validación (grabación ya corta a 720s)
            if duration > TRANSIENT_CAP_S:
                self.logger.warning(f"Duración {duration:.1f}s excede CAP TRANSITORIO A {TRANSIENT_CAP_S}s — se transcribe igual por chunks")
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
                temp_path = temp_audio_file.name
            
            # Write using soundfile
            sf.write(temp_path, full_audio, self.freq)
            self.logger.debug(f"Audio temporal guardado en: {temp_path}")

            audio_file_path = None
            if self.config_manager.get("save_audio"):
                # Pass numpy array directly to file_manager (or just path since we saved it?)
                # FileManager's save_audio_file takes audio_data now
                audio_file_path = self.file_manager.save_audio_file(full_audio, self.freq)
                self.logger.info(f"Audio guardado permanentemente en: {audio_file_path}")

            service = self.get_transcription_service()
            service_names = {
                "nvidia": "NVIDIA Riva",
                "groq": "Groq",
            }
            service_name = service_names.get(service, service)
            self.logger.info(f"Iniciando transcripción con {service_name}.")
            transcription = self.transcribe(temp_path)

            # Checkpoint parcial: si transcribe creó .partial.txt y transcription es None/falla, recuperar parcial
            partial_path = (str(temp_path) + ".partial.txt") if temp_path else None
            has_partial = bool(partial_path and os.path.exists(partial_path))
            if transcription:
                # Éxito (full o parcial con texto) — verificar si fue parcial incompleto
                is_partial = has_partial
                if is_partial:
                    self.logger.warning("Transcripción parcial detectada — WAV temporal se conserva para reintento")
                    try:
                        # guardar parcial también como entrada marcada
                        self.file_manager.save_transcription_entry({
                            "text": transcription, "duration": duration,
                            "language": self.config_manager.get("transcription_language", self.config_manager.get("default_language", "es")), "audio_file": audio_file_path or "",
                            "partial": True
                        })
                    except Exception:
                        pass
                    self.update_status("⚠️ Transcripción parcial guardada — WAV conservado", "orange")
                    self._push_overlay_event("error", 0, 0)
                    # NO borrar temp ni parcial — conservar para reintento manual
                else:
                    self.transcription_callback(transcription)
                    self.file_manager.save_transcription_entry({
                        "text": transcription, "duration": duration,
                        "language": self.config_manager.get("transcription_language", self.config_manager.get("default_language", "es")), "audio_file": audio_file_path or ""
                    })
                    self.sound_manager.sound_success()
                    self.update_status(self.localization_manager.get_string("transcription_completed"), "green")
                    self._push_overlay_event("ready", 0, 0)
                    # Éxito completo — borrar temporales
                    try:
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                            temp_path = None
                    except Exception:
                        pass
                    try:
                        if partial_path and os.path.exists(partial_path):
                            os.unlink(partial_path)
                    except Exception:
                        pass
            else:
                # Falla total — intentar recuperar parcial del checkpoint
                if has_partial:
                    try:
                        with open(partial_path, "r", encoding="utf-8") as pf:
                            partial_text = pf.read().strip()
                    except Exception:
                        partial_text = ""
                    if partial_text:
                        self.logger.warning(f"Recuperando transcripción parcial {len(partial_text)} chars tras fallo")
                        self.transcription_callback(partial_text)
                        try:
                            self.file_manager.save_transcription_entry({
                                "text": partial_text, "duration": duration,
                                "language": self.config_manager.get("transcription_language", self.config_manager.get("default_language", "es")), "audio_file": audio_file_path or "",
                                "partial": True
                            })
                        except Exception:
                            pass
                        self.update_status("⚠️ Transcripción parcial guardada — WAV conservado", "orange")
                        self._push_overlay_event("error", 0, 0)
                        # conservar WAV y parcial
                    else:
                        self.update_status(self.localization_manager.get_string("transcription_failed"), "red")
                        self._push_overlay_event("error", 0, 0)
                        self.logger.warning(f"Transcripción fallida — WAV temporal conservado en {temp_path} para reintento")
                else:
                    self.update_status(self.localization_manager.get_string("transcription_failed"), "red")
                    self._push_overlay_event("error", 0, 0)
                    self.logger.warning(f"Transcripción fallida — WAV temporal conservado en {temp_path} para reintento")
                # No borrar temp en caso de fallo
            
        except Exception as e:
            self.update_status(f'{self.localization_manager.get_string("processing_error")} {e}', "red")
            self.logger.critical(f"Error crítico durante el procesamiento: {e}", exc_info=True)
            # conservar WAV en caso de excepción
            if temp_path and os.path.exists(temp_path):
                self.logger.warning(f"WAV temporal conservado tras excepción: {temp_path}")
        finally:
            # Solo borrar si hubo éxito completo (transcription truthy y sin parcial pendiente)
            # Si temp_path aún existe, verificar si corresponde borrar + log determinístico
            partial_path_final = (str(temp_path) + ".partial.txt") if temp_path else None
            has_partial_final = bool(partial_path_final and os.path.exists(partial_path_final))
            if temp_path and os.path.exists(temp_path):
                if transcription and not has_partial_final:
                    try:
                        os.unlink(temp_path)
                        try:
                            self.tlogger.info(f"temp DELETE success transcription={len(transcription) if transcription else 0} path={temp_path}")
                        except Exception:
                            pass
                    except Exception as _del_e:
                        try:
                            self.tlogger.warning(f"temp DELETE fail {_del_e} path={temp_path}")
                        except Exception:
                            pass
                else:
                    # conservar — log ya emitido
                    try:
                        self.tlogger.info(f"temp CONSERVED partial={has_partial_final} transcription={'yes' if transcription else 'no'} path={temp_path} log_path=logs/transcription_debug.log")
                    except Exception:
                        pass
                    # Asegurar mensaje UI con ruta de log si hubo fallo
                    if not transcription or has_partial_final:
                        try:
                            self.update_status(f"⚠️ Ver logs/transcription_debug.log — WAV conservado {temp_path}", "orange")
                        except Exception:
                            pass
            # v0.15.8: liberar process_lock si fue adquirido
            try:
                if self.process_lock.locked():
                    self.process_lock.release()
            except Exception:
                pass

    def _call_groq_api(self, wav_path, prompt=None):
        """Llamar a la API de Groq con un único archivo WAV — con hardening Slice A.

        - timeout=30s (Groq client)
        - 413 no reintenta (fail fast)
        - 429 retry backoff + jitter + circuit-breaker
        - timeout retry 2x sin bloquear para siempre
        CAP TRANSITORIO A - reevaluar post B
        Instrumentado: logs/transcription_debug.log con file_size, attempt, latency, err, circuit, queue_depth.
        """
        # circuit-breaker check
        if self._is_circuit_open():
            with _groq_circuit_lock:
                remaining = max(0.0, _groq_circuit_open_until - time.time())
            self.logger.warning(f"Groq circuit-breaker abierto ({remaining:.0f}s restantes) — fail fast")
            try:
                self.tlogger.warning(f"Groq circuit OPEN skip {wav_path} remaining={remaining:.0f}s queue_depth={getattr(self, 'timer_queue', None).qsize() if getattr(self, 'timer_queue', None) else -1}")
            except Exception:
                pass
            raise RuntimeError(f"Groq circuit-breaker abierto, reintente en {remaining:.0f}s")

        # 413 pre-check por tamaño (evita subir 38MB y recibir 413)
        try:
            sz = os.path.getsize(wav_path)
            sz_mb = sz / (1024 * 1024)
            try:
                self.tlogger.debug(f"Groq pre-check {os.path.basename(wav_path)} size={sz_mb:.2f}MB prompt={'yes' if prompt else 'no'}")
            except Exception:
                pass
            if sz > GROQ_MAX_FILE_MB * 1024 * 1024:
                self.logger.error(f"Groq 413 pre-check: {wav_path} {sz/(1024*1024):.1f}MB > {GROQ_MAX_FILE_MB}MB")
                try:
                    self.tlogger.error(f"Groq 413 pre-check FAIL {wav_path} size={sz_mb:.2f}MB >{GROQ_MAX_FILE_MB}MB")
                except Exception:
                    pass
                self.update_status(f"❌ Audio {sz/(1024*1024):.1f}MB excede límite Groq {GROQ_MAX_FILE_MB}MB (413)", "red")
                raise RuntimeError(f"413 Payload Too Large {sz} bytes > {GROQ_MAX_FILE_MB}MB")
        except RuntimeError:
            raise
        except Exception:
            pass  # si no se puede stat, seguir

        last_exc = None
        max_attempts = GROQ_MAX_RETRIES_429 + 1  # 1 intento inicial + retries
        for attempt in range(max_attempts):
            t_api0 = time.perf_counter()
            try:
                with open(wav_path, "rb") as f:
                    file_bytes = f.read()
                    file_mb = len(file_bytes) / (1024 * 1024)
                    kwargs = dict(
                        file=(os.path.basename(wav_path), file_bytes),
                        model="whisper-large-v3",
                        response_format="text",
                        language=self.config_manager.get("transcription_language", self.config_manager.get("default_language", "es")),
                    )
                    if prompt:
                        kwargs["prompt"] = prompt
                    try:
                        qd = self.timer_queue.qsize() if getattr(self, "timer_queue", None) else -1
                    except Exception:
                        qd = -1
                    try:
                        self.tlogger.debug(f"Groq call START wav={os.path.basename(wav_path)} size={file_mb:.2f}MB attempt={attempt+1}/{max_attempts} q={qd}")
                    except Exception:
                        pass
                    result = self.cliente.audio.transcriptions.create(**kwargs)
                    latency = time.perf_counter() - t_api0
                    self._record_groq_success()
                    try:
                        self.tlogger.info(f"Groq call OK wav={os.path.basename(wav_path)} latency={latency:.3f}s attempt={attempt+1} size={file_mb:.2f}MB")
                    except Exception:
                        pass
                    return result
            except Exception as e:
                latency = time.perf_counter() - t_api0
                last_exc = e
                kind = self._classify_groq_error(e)
                try:
                    qd = self.timer_queue.qsize() if getattr(self, "timer_queue", None) else -1
                except Exception:
                    qd = -1
                try:
                    self.tlogger.warning(f"Groq call FAIL wav={os.path.basename(wav_path)} err={kind} latency={latency:.3f}s attempt={attempt+1}/{max_attempts} q={qd} exc={e}")
                except Exception:
                    pass
                if kind == "413":
                    self.logger.error(f"Groq 413 Payload Too Large: {e} — no reintenta")
                    self.update_status("❌ Groq 413: archivo muy grande", "red")
                    raise
                elif kind == "429":
                    self._record_groq_failure_429()
                    if attempt < GROQ_MAX_RETRIES_429:
                        # backoff exponencial + jitter
                        base = GROQ_BACKOFF_BASE_S * (2 ** attempt)
                        jitter = random.uniform(0, 1.0)
                        # respetar Retry-After si viene en headers
                        retry_after = None
                        try:
                            resp = getattr(e, "response", None)
                            if resp is not None and hasattr(resp, "headers"):
                                ra = resp.headers.get("retry-after") or resp.headers.get("Retry-After")
                                if ra:
                                    retry_after = float(ra)
                        except Exception:
                            pass
                        wait = retry_after if retry_after is not None else base + jitter
                        wait = min(wait, 8.0)  # cap 8s
                        self.logger.warning(f"Groq 429 intento {attempt+1}/{max_attempts} backoff {wait:.1f}s")
                        try:
                            self.tlogger.info(f"Groq 429 backoff {wait:.1f}s attempt={attempt+1}")
                        except Exception:
                            pass
                        # informar progreso si es chunk
                        try:
                            self.update_status(f"⏳ Groq 429, reintento {attempt+1}/{GROQ_MAX_RETRIES_429} en {wait:.1f}s...", "orange")
                        except Exception:
                            pass
                        time.sleep(wait)
                        continue
                    else:
                        self.logger.error(f"Groq 429 agotados {max_attempts} intentos — circuit-breaker")
                        raise
                elif kind == "timeout":
                    # timeout: reintentar máximo 2 veces con backoff corto
                    if attempt < 2:
                        wait = GROQ_BACKOFF_BASE_S * (attempt + 1) + random.uniform(0, 0.5)
                        wait = min(wait, 4.0)
                        self.logger.warning(f"Groq timeout intento {attempt+1} backoff {wait:.1f}s — {e}")
                        try:
                            self.tlogger.info(f"Groq timeout backoff {wait:.1f}s attempt={attempt+1}")
                        except Exception:
                            pass
                        time.sleep(wait)
                        continue
                    else:
                        self.logger.error(f"Groq timeout definitivo tras {attempt+1} intentos: {e}")
                        raise
                else:
                    # other errors: no retry
                    self.logger.error(f"Groq error no reintentable ({kind}): {e}")
                    raise
        if last_exc:
            raise last_exc
        raise RuntimeError("Groq _call_groq_api falló sin excepción capturada")

    def _groq_chunk_callback(self, chunk, sr, prompt=None):
        """Callback para transcribe_chunks: escribe chunk a WAV temporal y llama Groq (con timeout 30s)."""
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            sf.write(tmp_path, chunk, sr)
            res = self._call_groq_api(tmp_path, prompt=prompt)
            return res or ""
        except Exception as e:
            # 413/429/timeout ya logueado en _call_groq_api; propagar para que caller marque parcial (no confundir con silencio)
            self.logger.warning(f"Error transcribiendo chunk: {e}")
            kind = self._classify_groq_error(e)
            if kind in ("413", "429", "timeout") or "circuit-breaker" in str(e).lower():
                raise
            return ""
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def transcribe_with_groq(self, audio_path, progress_callback=None):
        if not self.cliente:
            self.update_status(self.localization_manager.get_string("groq_client_not_initialized"), "red")
            return None
        try:
            data, sr = sf.read(audio_path)
            duration = len(data) / sr

            # CAP TRANSITORIO A - reevaluar post B: validar duración
            if duration > TRANSIENT_CAP_S:
                self.logger.warning(f"Audio {duration:.1f}s excede CAP TRANSITORIO A {TRANSIENT_CAP_S}s (12 min) — se intentará transcribir igual por chunks (no se pierde).")
                # No rechazamos de plano para no perder datos si el cap se saltea; el record ya corta a 720s.
                # Si se quiere rechazar estricto, descomentar:
                # self.update_status(f"❌ Audio {duration/60:.1f}min excede límite transitorio 12 min", "red")
                # return None

            if duration >= CHUNK_THRESHOLD_S:
                self.logger.info(
                    f"Audio largo ({duration:.1f}s): trozando en ventanas <30s "
                    f"para evitar pérdida en costuras de Groq."
                )
                # Slice B: paralelización Groq — ThreadPoolExecutor 3 workers (2-4 configurable)
                from .audio_chunker import split_audio_on_silence
                chunks = split_audio_on_silence(data, sr, target_s=25.0, max_s=29.0)
                total = len(chunks)
                workers = self._get_parallel_workers()
                self.logger.info(f"Groq chunking: {total} chunks (target 25s, max 29s) workers={workers} parallel=SliceB")
                # checkpoint parcial: archivo .partial junto al wav si está en temp
                partial_path = str(audio_path) + ".partial.txt"
                # limpiar parcial previo si existe
                try:
                    if os.path.exists(partial_path):
                        os.unlink(partial_path)
                except Exception:
                    pass

                # Global timeout safety para 28 chunks *30s=840s
                _global_deadline = time.time() + 700  # 700s < 12m cap + margen
                try:
                    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
                except Exception:
                    file_size_mb = len(data) * 2 / (1024 * 1024)  # estimado PCM16
                try:
                    self.tlogger.info(f"transcribe START dur={duration:.1f}s file={file_size_mb:.2f}MB chunks={total} sr={sr} workers={workers} queue_depth={self.timer_queue.qsize() if getattr(self,'timer_queue',None) else -1}")
                except Exception:
                    pass

                # Slice B structures — thread-safe
                texts_ordered: list = [None] * total
                chunk_times: list = []
                completed = 0
                all_ok = True
                start_wall = time.perf_counter()
                checkpoint_lock = threading.Lock()
                times_lock = threading.Lock()
                completed_lock = threading.Lock()
                # global timeout flag
                _global_timed_out = False

                def _parallel_chunk_task(idx0: int, chunk: np.ndarray) -> str:
                    """Task por chunk: START/END con worker_id, latency, pool queue. 413/429 no bloquea pool."""
                    worker_id = threading.current_thread().name  # groq-w_0 etc
                    # pool queue depth (executor._work_queue.qsize si existe)
                    try:
                        qsz = getattr(_parallel_chunk_task, "_executor", None)
                        if qsz is not None and hasattr(qsz, "_work_queue"):
                            q_depth = qsz._work_queue.qsize()
                        else:
                            q_depth = -1
                    except Exception:
                        q_depth = -1
                    try:
                        chunk_dur = len(chunk) / sr
                        chunk_mb = len(chunk) * 2 / (1024 * 1024)
                    except Exception:
                        chunk_dur = 0
                        chunk_mb = 0
                    try:
                        self.tlogger.debug(f"Chunk START {idx0+1}/{total} worker={worker_id} dur={chunk_dur:.1f}s size={chunk_mb:.2f}MB q={q_depth}")
                    except Exception:
                        pass
                    t0 = time.perf_counter()
                    part = ""
                    try:
                        # Slice B: prompt=None en paralelo para evitar dependencia secuencial (tradeoff speedup >2.5x)
                        # circuit-breaker + 429 backoff ya manejado en _call_groq_api por chunk
                        part = self._groq_chunk_callback(chunk, sr, prompt=None) or ""
                    except Exception as ce:
                        kind = self._classify_groq_error(ce)
                        latency_fail = time.perf_counter() - t0
                        try:
                            # outer q depth
                            qd2 = -1
                            try:
                                ex = getattr(_parallel_chunk_task, "_executor", None)
                                if ex is not None and hasattr(ex, "_work_queue"):
                                    qd2 = ex._work_queue.qsize()
                            except Exception:
                                pass
                            self.tlogger.error(f"Chunk FAIL {idx0+1}/{total} worker={worker_id} err={kind} latency={latency_fail:.3f}s exc={ce} q={qd2}")
                        except Exception:
                            pass
                        if kind == "413":
                            # 413 no reintenta, retornar vacío sin bloquear pool
                            return ""
                        # 429/timeout/circuit: ya hizo retry/backoff interno, retornar vacío para no cancelar otros
                        return ""
                    latency = max(0.01, time.perf_counter() - t0)
                    try:
                        qd_end = -1
                        try:
                            ex = getattr(_parallel_chunk_task, "_executor", None)
                            if ex is not None and hasattr(ex, "_work_queue"):
                                qd_end = ex._work_queue.qsize()
                        except Exception:
                            pass
                        kind2 = "ok" if part and part.strip() else "empty"
                        self.tlogger.debug(f"Chunk END {idx0+1}/{total} worker={worker_id} latency={latency:.3f}s result={kind2} len={len(part) if part else 0} q={qd_end}")
                    except Exception:
                        pass
                    return part.strip() if part else ""

                # ——— submit all ———
                futures_map = {}
                # throughput ETA: completed/elapsed
                with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="groq-w") as executor:
                    # attach executor for queue logging inside task
                    _parallel_chunk_task._executor = executor
                    for idx0, ch in enumerate(chunks):
                        # global deadline pre-check: si ya pasó, no submitear resto
                        if time.time() > _global_deadline:
                            _global_timed_out = True
                            break
                        fut = executor.submit(_parallel_chunk_task, idx0, ch)
                        futures_map[fut] = idx0
                    # as_completed — orden de llegada desordenado, reordena antes de join
                    for fut in as_completed(futures_map):
                        idx0 = futures_map[fut]
                        # timeout 30s por future (GROQ_PARALLEL_TIMEOUT_S)
                        try:
                            part = fut.result(timeout=GROQ_PARALLEL_TIMEOUT_S)
                        except concurrent.futures.TimeoutError:
                            try:
                                self.tlogger.error(f"Chunk TIMEOUT {idx0+1}/{total} worker=timeout latency={GROQ_PARALLEL_TIMEOUT_S}s q={executor._work_queue.qsize() if hasattr(executor,'_work_queue') else -1}")
                            except Exception:
                                pass
                            part = ""
                            all_ok = False
                        except Exception as ce:
                            part = ""
                            all_ok = False
                        # guardar en posición ordenada
                        texts_ordered[idx0] = part or ""
                        if not part:
                            all_ok = False
                        else:
                            # latency approx via wall? ya logueada en task; para ETA usamos wall elapsed
                            pass
                        # thread-safe checkpoint: reordena antes de join
                        with checkpoint_lock:
                            # escribir join ordenado de los completados (None → no incluido aún)
                            ordered_partial = " ".join([t for t in texts_ordered if t])
                            if ordered_partial:
                                try:
                                    with open(partial_path, "w", encoding="utf-8") as pf:
                                        pf.write(ordered_partial)
                                        pf.flush()
                                        os.fsync(pf.fileno())
                                    try:
                                        self.tlogger.info(f"checkpoint WRITE completed chunk {idx0+1}/{total} total_len={len(ordered_partial)} path={partial_path} q={executor._work_queue.qsize() if hasattr(executor,'_work_queue') else -1}")
                                    except Exception:
                                        pass
                                except Exception as ce:
                                    try:
                                        self.tlogger.warning(f"checkpoint FAIL Chunk {idx0+1} err={ce}")
                                    except Exception:
                                        pass
                        # thread-safe ETA por throughput real
                        with completed_lock:
                            completed += 1
                            elapsed = time.perf_counter() - start_wall
                            avg = elapsed / completed if completed else 0
                            eta = avg * (total - completed)
                            # track latency for avg display
                            with times_lock:
                                # aproximar latency como avg
                                chunk_times.append(avg if avg else 0.01)
                            try:
                                self._push_progress_event(completed, total, float(eta))
                            except Exception:
                                pass
                            if progress_callback:
                                try:
                                    progress_callback(completed, total, float(eta))
                                except Exception:
                                    pass
                            try:
                                self.update_status(f"⏳ Chunk {completed}/{total} ETA {int(eta)}s...", "yellow")
                            except Exception:
                                pass
                            # global timeout post-check
                            if time.time() > _global_deadline:
                                _global_timed_out = True
                    # cleanup attach
                    try:
                        _parallel_chunk_task._executor = None
                    except Exception:
                        pass

                if _global_timed_out:
                    self.logger.error(f"transcribe GLOBAL TIMEOUT tras {time.time() - (_global_deadline-700):.0f}s — abort parcial")
                    try:
                        self.tlogger.error(f"GLOBAL TIMEOUT aborted completed={completed}/{total}")
                    except Exception:
                        pass
                    try:
                        self.update_status("❌ Timeout global — parcial guardado, ver logs/transcription_debug.log", "red")
                    except Exception:
                        pass
                    all_ok = False

                # reordena antes de join — orden preservado por índice
                texts = [t for t in texts_ordered if t]
                response = " ".join(texts)
                # si hubo algún chunk fallido pero tenemos texto parcial, lo consideramos éxito parcial
                if not response and not all_ok:
                    self.logger.warning("Transcripción chunked sin texto y con fallos — retornando None para que caller preserve WAV")
                    return None
                # push final progress 100%
                try:
                    self._push_progress_event(total, total, 0.0)
                except Exception:
                    pass
                # checkpoint: si todo OK, borrar parcial; si no, mantener
                if all_ok and response:
                    try:
                        if os.path.exists(partial_path):
                            os.unlink(partial_path)
                    except Exception:
                        pass
                else:
                    self.logger.warning(f"Transcripción parcial {len(texts)}/{total} chunks OK — WAV no se borrará, parcial en {partial_path}")
            else:
                self.logger.debug(f"Enviando audio {audio_path} a la API de Groq.")
                try:
                    sz = os.path.getsize(audio_path) / (1024*1024)
                    self.tlogger.info(f"transcribe SINGLE dur={duration:.1f}s size={sz:.2f}MB path={audio_path}")
                except Exception:
                    pass
                # progress single chunk
                try:
                    self._push_progress_event(1, 1, 0.0)
                except Exception:
                    pass
                response = self._call_groq_api(audio_path)

            # Aplicar validación UTF-8 si está habilitada
            if self.utf8_validation_enabled and response:
                response = self.validate_transcription_utf8(response)

            # Aplicar correcciones de vocabulario personalizado
            if response:
                response = self.custom_vocab.apply_corrections(response)

            # Procesar con bloques POST-transcripción
            if response:
                response = self._process_with_blocks(response)

            # Generar metadatos automáticos con LLM
            if response:
                try:
                    filename = os.path.basename(audio_path)
                    auto_metadata = self.metadata_generator.generate_metadata(
                        transcription=response,
                        filename=filename
                    )
                    self.metadata_manager.set_auto_metadata(filename, auto_metadata)
                    self.logger.info(f"Metadatos automáticos generados para {filename}")
                except Exception as e:
                    self.logger.warning(f"Error generando metadatos automáticos: {e}")

            return response
        except Exception as e:
            self.update_status(f'{self.localization_manager.get_string("groq_api_error")} {e}', "red")
            self.logger.error(f"Error de API Groq: {e}")
            return None

    def transcribe_with_nvidia(self, audio_path):
        """Transcribir audio usando NVIDIA Riva ASR."""
        if not self.nvidia_client:
            self.update_status("Cliente NVIDIA no inicializado", "red")
            return None
        try:
            self.logger.debug(f"Enviando audio {audio_path} a NVIDIA Riva ASR.")
            _tlang = self.config_manager.get("transcription_language", self.config_manager.get("default_language", "es"))
            # NVIDIA espera formato es-ES/en-US
            _nvidia_lang = "en-US" if _tlang.startswith("en") else "es-ES"
            response = self.nvidia_client.transcribe(
                audio_path=audio_path,
                language_code=_nvidia_lang
            )

            if not response:
                self.logger.error("NVIDIA Riva ASR: No se pudo transcribir el audio")
                return None

            # Aplicar validación UTF-8 si está habilitada
            if self.utf8_validation_enabled and response:
                response = self.validate_transcription_utf8(response)

            # Aplicar correcciones de vocabulario personalizado
            if response:
                response = self.custom_vocab.apply_corrections(response)

            # Procesar con bloques POST-transcripción
            if response:
                response = self._process_with_blocks(response)

            # Generar metadatos automáticos con LLM
            if response:
                try:
                    filename = os.path.basename(audio_path)
                    auto_metadata = self.metadata_generator.generate_metadata(
                        transcription=response,
                        filename=filename
                    )
                    # Guardar metadatos automáticos
                    self.metadata_manager.set_auto_metadata(filename, auto_metadata)
                    self.logger.info(f"Metadatos automáticos generados para {filename}")
                except Exception as e:
                    self.logger.warning(f"Error generando metadatos automáticos: {e}")

            return response
        except Exception as e:
            self.update_status(f'Error de NVIDIA Riva: {e}', "red")
            self.logger.error(f"Error de NVIDIA Riva: {e}")
            return None

    def transcribe(self, audio_path):
        """
        Transcribir audio usando el servicio configurado (Groq o NVIDIA).

        Elige automáticamente según la configuración 'asr_provider'.
        """
        service = self.get_transcription_service()

        if service == "nvidia":
            return self.transcribe_with_nvidia(audio_path)
        else:
            return self.transcribe_with_groq(audio_path)

    def _process_with_blocks(self, text: str) -> str:
        """
        Procesar texto transcrito con los bloques POST-transcripción.

        Args:
            text: Texto transcrito y validado

        Returns:
            Texto procesado por los bloques (o original si falla)
        """
        if not text or not text.strip():
            return text

        try:
            # Ejecutar bloques en etapa TRANSCRIBED_TEXT
            block_results = self.block_manager.process(
                data=text,
                stage=ProcessingStage.TRANSCRIBED_TEXT
            )

            # Si hay resultados de bloques, procesarlos
            if block_results:
                self.logger.info(f"Procesando {len(block_results)} resultados de bloques")

                # Buscar resumen si está disponible
                for result in block_results:
                    if result.success and result.metadata:
                        block_name = result.metadata.get('block_name', '')

                        # Si es un resumen, loguearlo
                        if 'summary' in block_name.lower() and result.data:
                            self.logger.debug(f"Resumen generado: {result.data[:100]}...")

                        # Guardar resultados para UI
                        if hasattr(self, 'last_block_results'):
                            self.last_block_results.append(result)
                        else:
                            self.last_block_results = [result]

            # Retornar texto original (los bloques generan metadatos adicionales)
            return text

        except Exception as e:
            self.logger.error(f"Error procesando con bloques: {e}")
            return text

    def validate_transcription_utf8(self, text: str) -> str:
        """
        Validar y corregir la transcripción para problemas de encoding UTF-8.

        Args:
            text: Texto de transcripción a validar

        Returns:
            Texto validado y corregido
        """
        if not text or not text.strip():
            return text

        try:
            # Validar la transcripción
            is_valid, problems = self.utf8_validator.validate_transcription(text)

            if not is_valid:
                self.logger.warning(f"Problemas de encoding detectados: {problems}")
                # Aplicar corrección
                corrected = self.utf8_validator.normalize_transcription(text, normalize=True)

                # Verificar que la corrección mejoró el texto
                if corrected != text:
                    self.logger.info(f"Texto corregido: '{text[:50]}...' -> '{corrected[:50]}...'")
                    return corrected
                else:
                    self.logger.debug("No se aplicaron correcciones de encoding")
                    return text
            else:
                self.logger.debug("Transcripción válida sin problemas de encoding")
                return text

        except Exception as e:
            self.logger.error(f"Error validando transcripción UTF-8: {e}")
            # En caso de error, retornar el texto original
            return text

    def stop(self):
        self.logger.info("Deteniendo Transcriber.")
        self.ejecutando = False
        keyboard.unhook_all()
        self.stop_event.set()
        if self.input_stream:
             self.input_stream.stop()
             self.input_stream.close()
        self.logger.info("Transcriber detenido.")