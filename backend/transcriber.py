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

        self.hotkey_thread = threading.Thread(target=self.hotkey_listener, daemon=True)
        self.hotkey_thread.start()
        self.logger.info("Hilo de escucha de hotkey iniciado.")

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

    def reload_client(self):
        """Reinicializa el cliente Groq (útil cuando cambia la API Key)."""
        self.logger.info("Recargando cliente Groq...")
        self.cliente = self._init_groq_client()
        if self.cliente:
             self.update_status(self.localization_manager.get_string("status_ready"), "white")
        else:
             self.update_status("API Key inválida o faltante", "red")

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

            self.logger.info("Iniciando transcripción con Groq.")
            transcription = self.transcribe_with_groq(temp_path)
            
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
            return response
        except Exception as e:
            self.update_status(f'{self.localization_manager.get_string("groq_api_error")} {e}', "red")
            self.logger.error(f"Error de API Groq: {e}")
            return None

    def stop(self):
        self.logger.info("Deteniendo Transcriber.")
        self.ejecutando = False
        keyboard.unhook_all()
        self.stop_event.set()
        if self.input_stream:
             self.input_stream.stop()
             self.input_stream.close()
        self.logger.info("Transcriber detenido.")