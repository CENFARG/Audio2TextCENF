import os
import json
import soundfile as sf
import numpy as np
import shutil
from datetime import datetime

class FileManager:
    """Gestor de archivos de audio y transcripciones usaando soundfile"""

    def __init__(self, config_manager):
        self.config = config_manager
        self.audio_path = self.config.get("audio_path")
        self.transcriptions_path = self.config.get("transcriptions_path")

        # Crear directorios si no existen
        os.makedirs(self.audio_path, exist_ok=True)
        os.makedirs(self.transcriptions_path, exist_ok=True)

    def save_audio_file(self, audio_data, sample_rate=16000):
        if not self.config.get("save_audio", True): return None
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"audio_{timestamp}.wav"
            filepath = os.path.join(self.audio_path, filename)
            
            # Ensure audio_data is a numpy array
            if isinstance(audio_data, list):
                if len(audio_data) > 0:
                     audio_data = np.concatenate(audio_data, axis=0)
                else:
                     return None
            
            sf.write(filepath, audio_data, sample_rate)
            return filepath
        except Exception as e:
            print(f"Error al guardar audio: {e}")
            return None

    def save_audio_file_from_temp(self, temp_path):
        """Guarda el archivo de audio desde una ruta temporal a la carpeta de audios."""
        if not self.config.get("save_audio", True):
            return None
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"audio_{timestamp}.wav"
            filepath = os.path.join(self.audio_path, filename)
            shutil.copy(temp_path, filepath)
            return filepath
        except Exception as e:
            print(f"Error al guardar audio desde temporal: {e}")
            return None

    def save_transcription_entry(self, transcription_data):
        if not self.config.get("save_logs", True): return
        try:
            log_file = os.path.join(self.transcriptions_path, "transcriptions_log.jsonl")
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "duration": transcription_data.get("duration", 0),
                "language": transcription_data.get("language", "es"),
                "text_length": len(transcription_data.get("text", "")),
                "audio_file": transcription_data.get("audio_file", ""),
                "transcription": transcription_data.get("text", "")
            }
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            self.maintain_log_size()
        except Exception as e:
            print(f"Error al guardar transcripción: {e}")

    def maintain_log_size(self):
        max_entries = self.config.get("max_log_entries", 1000)
        log_file = os.path.join(self.transcriptions_path, "transcriptions_log.jsonl")
        if not os.path.exists(log_file): return
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            if len(lines) > max_entries:
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines[-max_entries:])
        except Exception as e:
            print(f"Error al mantener tamaño del log: {e}")

    def get_audio_files_size(self):
        try:
            total_size = sum(os.path.getsize(os.path.join(self.audio_path, f)) for f in os.listdir(self.audio_path) if f.endswith('.wav'))
            return total_size
        except Exception as e:
            print(f"Error al calcular tamaño de audio: {e}")
            return 0

    def get_transcriptions_size(self):
        try:
            log_file = os.path.join(self.transcriptions_path, "transcriptions_log.jsonl")
            return os.path.getsize(log_file) if os.path.exists(log_file) else 0
        except Exception as e:
            print(f"Error al obtener tamaño de transcripciones: {e}")
            return 0

    def clear_audio_files(self):
        try:
            for filename in os.listdir(self.audio_path):
                if filename.endswith('.wav'): os.remove(os.path.join(self.audio_path, filename))
            return True
        except Exception as e:
            print(f"Error al eliminar archivos de audio: {e}")
            return False

    def clear_transcriptions(self):
        try:
            log_file = os.path.join(self.transcriptions_path, "transcriptions_log.jsonl")
            if os.path.exists(log_file): os.remove(log_file)
            return True
        except Exception as e:
            print(f"Error al eliminar transcripciones: {e}")
            return False
