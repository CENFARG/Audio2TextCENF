import os
import tempfile
import sounddevice as sd
import soundfile as sf
import numpy as np
import keyboard
import time
import psutil
import threading
from groq import Groq
import logging
from .localization_manager import LocalizationManager
from .utf8_validator import UTF8Validator
from .custom_vocabulary import CustomVocabulary
from .blocks import BlockManager, ProcessingStage
from .blocks.task_extractor_block import TaskExtractorBlock
from .blocks.summary_block import SummaryBlock
from .blocks.keyword_extractor_block import KeywordExtractorBlock
from .nvidia_asr import NvidiaASR
from .faster_whisper_asr import FasterWhisperASR
from .transcription_metadata import TranscriptionMetadata
from .transcription_metadata_generator import TranscriptionMetadataGenerator

MIN_AUDIO_DURATION = 0.5

class Transcriber:
    def __init__(self, config_manager, sound_manager, file_manager, update_status_callback, transcription_callback, localization_manager, overlay_callback=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_manager = config_manager
        self.sound_manager = sound_manager
        self.file_manager = file_manager
        self.update_status = update_status_callback
        self.transcription_callback = transcription_callback
        self.localization_manager = localization_manager
        self.overlay_callback = overlay_callback  # Callback para actualizar overlay

        self.logger.info(f"Transcriber inicializado con hotkey: {self.config_manager.get('hotkey')}, modo de grabación: {self.config_manager.get('record_mode')}")

        self.is_recording = False
        self.recording_lock = threading.Lock()
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
        self.faster_whisper_client = self._init_faster_whisper_client()

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
        self.metadata_generator = TranscriptionMetadataGenerator(use_llm=True)
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
            client = Groq(api_key=api_key)
            self.logger.info("Cliente Groq inicializado exitosamente.")
            return client
        except Exception as e:
            self.update_status(self.localization_manager.get_string("groq_init_error", error=e), "red")
            self.logger.error(f"Error al inicializar Groq: {e}")
            return None

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
        """Inicializar cliente faster-whisper (transcripción local sin Docker)."""
        faster_whisper_enabled = self.config_manager.get("faster_whisper_enabled", False)

        if not faster_whisper_enabled:
            self.logger.info("faster-whisper deshabilitado en configuración.")
            return None

        try:
            # Obtener configuración del modelo
            model_size = self.config_manager.get("faster_whisper_model", "base")
            device = self.config_manager.get("faster_whisper_device", "auto")

            client = FasterWhisperASR(model_size=model_size, device=device)
            if client.is_available():
                model_info = client.get_model_info()
                self.logger.info(f"Cliente faster-whisper inicializado (modelo={model_size}, device={model_info['device']})")
                return client
            else:
                self.logger.warning("faster-whisper: no se pudo inicializar el modelo")
                return None
        except Exception as e:
            self.logger.warning(f"Error al inicializar faster-whisper: {e}")
            return None

    def get_transcription_service(self):
        """
        Obtener el servicio de transcripción activo.

        Returns:
            'nvidia', 'groq', 'faster_whisper' o None si no hay ninguno disponible.
        """
        asr_provider = self.config_manager.get("asr_provider", "groq")  # "groq", "nvidia" o "faster_whisper"

        if asr_provider == "nvidia" and self.nvidia_client:
            return "nvidia"
        elif asr_provider == "faster_whisper" and self.faster_whisper_client:
            return "faster_whisper"
        elif self.cliente:
            return "groq"
        else:
            return None

    def reload_client(self):
        """Reinicializa los clientes de transcripción (Groq, NVIDIA y faster-whisper)."""
        self.logger.info("Recargando clientes de transcripción...")
        self.cliente = self._init_groq_client()
        self.nvidia_client = self._init_nvidia_client()
        self.faster_whisper_client = self._init_faster_whisper_client()

        service = self.get_transcription_service()
        if service:
            service_names = {
                "nvidia": "NVIDIA Riva",
                "groq": "Groq",
                "faster_whisper": "faster-whisper"
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
            keyboard.unhook_all()
            keyboard.on_press_key(self.hotkey, self.handle_key_event, suppress=True)
            keyboard.on_release_key(self.hotkey, self.handle_key_event, suppress=True)
            self.logger.info(f"Hotkey enganchado: {self.hotkey}")
        except Exception as e:
            self.logger.error(f"Error enganchando hotkey: {e}")

    def update_hotkey(self, new_hotkey):
        self.logger.info(f"Actualizando hotkey a: {new_hotkey}")
        self.hotkey = new_hotkey
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

    def start_recording(self):
        if self.is_recording: return
        if any(p.info['name'].lower() in self.audio_priority_apps for p in psutil.process_iter(['pid', 'name'])):
            self.update_status(self.localization_manager.get_string("priority_app_in_use"), "orange")
            return

        self.is_recording = True
        self.audio_data = []
        self.stop_event.clear()
        self.sound_manager.sound_start_recording()
        self.update_status(self.localization_manager.get_string("status_recording"), "green")
        self.logger.info("Grabación iniciada.")
        
        # Actualizar overlay
        if self.overlay_callback:
            self.overlay_callback("recording", 0, 0)
        
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
        start_time = time.time()
        max_time = self.config_manager.get("max_recording_time", 300)
        
        while not self.stop_event.is_set():
            try:
                # Read from stream
                if self.input_stream.active:
                    data, overflowed = self.input_stream.read(1024)
                    if overflowed:
                        self.logger.warning("Audio buffer overflow")
                    self.audio_data.append(data)
                
                elapsed_time = time.time() - start_time
                if elapsed_time > max_time:
                    self.stop_recording(); break
                minutes, seconds = divmod(int(elapsed_time), 60)
                self.update_status(f'{self.localization_manager.get_string("status_recording")} {minutes:02d}:{seconds:02d}', "green")
                
                # Actualizar overlay si existe
                if self.overlay_callback:
                    self.overlay_callback("recording", minutes, seconds)
                    
            except Exception as e:
                self.logger.error(f"Error en bucle de grabación: {e}")
                self.stop_recording()
                break

    def stop_recording(self):
        if not self.is_recording: return
        
        self.stop_event.set()
        self.is_recording = False
        self.sound_manager.sound_stop_recording()
        self.update_status(self.localization_manager.get_string("status_processing"), "yellow")
        self.logger.info("Grabación detenida. Iniciando procesamiento.")
        
        # Actualizar overlay
        if self.overlay_callback:
            self.overlay_callback("processing", 0, 0)

        time.sleep(0.1)

        if self.input_stream:
            self.input_stream.stop()
            self.input_stream.close()
            self.input_stream = None

        if not self.audio_data:
            self.update_status(self.localization_manager.get_string("no_audio_captured"), "red")
            return
        
        threading.Thread(target=self.process_recording, daemon=True).start()

    def process_recording(self):
        self.logger.info("Iniciando procesamiento de grabación.")
        temp_path = None
        try:
            # Combine audio data chunks
            full_audio = np.concatenate(self.audio_data, axis=0)
            duration = len(full_audio) / self.freq
            
            if duration < MIN_AUDIO_DURATION:
                self.update_status(self.localization_manager.get_string("audio_too_short", min_duration=1.5), "red")
                self.logger.warning("Audio demasiado corto (< 1.5s).")
                self.overlay_callback("ready") # Ocultar overlay si es corto
                return
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
                "faster_whisper": "faster-whisper"
            }
            service_name = service_names.get(service, service)
            self.logger.info(f"Iniciando transcripción con {service_name}.")
            transcription = self.transcribe(temp_path)
            
            if transcription:
                self.transcription_callback(transcription)
                self.file_manager.save_transcription_entry({
                    "text": transcription, "duration": duration,
                    "language": self.config_manager.get("default_language"), "audio_file": audio_file_path or ""
                })
                self.sound_manager.sound_success()
                self.update_status(self.localization_manager.get_string("transcription_completed"), "green")
                # Actualizar overlay
                if self.overlay_callback:
                    self.overlay_callback("ready", 0, 0)
            else:
                self.update_status(self.localization_manager.get_string("transcription_failed"), "red")
                # Actualizar overlay
                if self.overlay_callback:
                    self.overlay_callback("error", 0, 0)
            
            if os.path.exists(temp_path): os.unlink(temp_path)
            
        except Exception as e:
            self.update_status(f'{self.localization_manager.get_string("processing_error")} {e}', "red")
            self.logger.critical(f"Error crítico durante el procesamiento: {e}", exc_info=True)
        finally:
            if temp_path and os.path.exists(temp_path): os.unlink(temp_path)

    def transcribe_with_groq(self, audio_path):
        if not self.cliente:
            self.update_status(self.localization_manager.get_string("groq_client_not_initialized"), "red")
            return None
        try:
            self.logger.debug(f"Enviando audio {audio_path} a la API de Groq.")
            with open(audio_path, "rb") as audio_file:
                response = self.cliente.audio.transcriptions.create(
                    file=(os.path.basename(audio_path), audio_file.read()), model="whisper-large-v3",
                    response_format="text", language=self.config_manager.get("default_language", "es")
                )

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
            response = self.nvidia_client.transcribe(
                audio_path=audio_path,
                language_code=self.config_manager.get("default_language", "es-US")
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

    def transcribe_with_faster_whisper(self, audio_path):
        """Transcribir audio usando faster-whisper (local sin Docker)."""
        if not self.faster_whisper_client:
            self.update_status("Cliente faster-whisper no inicializado", "red")
            return None
        try:
            self.logger.debug(f"Transcribiendo audio {audio_path} con faster-whisper.")
            response = self.faster_whisper_client.transcribe(
                audio_path=audio_path,
                language_code=self.config_manager.get("default_language", "es")
            )

            if not response:
                self.logger.error("faster-whisper: No se pudo transcribir el audio")
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
            self.update_status(f'Error de faster-whisper: {e}', "red")
            self.logger.error(f"Error de faster-whisper: {e}")
            return None

    def transcribe(self, audio_path):
        """
        Transcribir audio usando el servicio configurado (Groq, NVIDIA o faster-whisper).

        Elige automáticamente según la configuración 'asr_provider'.
        """
        service = self.get_transcription_service()

        if service == "nvidia":
            return self.transcribe_with_nvidia(audio_path)
        elif service == "faster_whisper":
            return self.transcribe_with_faster_whisper(audio_path)
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