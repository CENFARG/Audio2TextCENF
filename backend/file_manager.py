import os
import json
import soundfile as sf
import numpy as np
import shutil
from datetime import datetime
import sys

class FileManager:
    """Gestor de archivos de audio y transcripciones usaando soundfile"""

    def __init__(self, config_manager):
        self.config = config_manager

        # Obtener directorio base del ejecutable/script
        # Si está compilado con PyInstaller, usar el directorio del .exe
        # Si es desarrollo, usar el directorio del script
        if getattr(sys, 'frozen', False):
            # Ejecutándose como .exe compilado
            self.base_dir = os.path.dirname(sys.executable)
        else:
            # Ejecutándose como script Python
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
            # Ir al directorio raíz del proyecto (desde backend/ hasta raíz)
            self.base_dir = os.path.dirname(self.base_dir)

        # Convertir paths relativos a absolutos
        audio_path_rel = self.config.get("audio_path")
        transcriptions_path_rel = self.config.get("transcriptions_path")

        if os.path.isabs(audio_path_rel):
            self.audio_path = audio_path_rel
        else:
            # Unir y normalizar para eliminar ./ o ../
            self.audio_path = os.path.normpath(os.path.join(self.base_dir, audio_path_rel))

        if os.path.isabs(transcriptions_path_rel):
            self.transcriptions_path = transcriptions_path_rel
        else:
            # Unir y normalizar para eliminar ./ o ../
            self.transcriptions_path = os.path.normpath(os.path.join(self.base_dir, transcriptions_path_rel))

        # Log para debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"FileManager inicializado:")
        logger.info(f"  Base dir: {self.base_dir}")
        logger.info(f"  Audio path: {self.audio_path}")
        logger.info(f"  Transcriptions path: {self.transcriptions_path}")

        # Crear directorios si no existen
        os.makedirs(self.audio_path, exist_ok=True)
        os.makedirs(self.transcriptions_path, exist_ok=True)

        # Límites de archivos
        self.max_audio_files = self.config.get("max_audio_files", 100)
        self.max_transcription_age_days = self.config.get("max_transcription_age_days", 30)

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

            # Mantener límite de archivos después de guardar
            self.maintain_audio_file_limit()

            # Limpiar archivos antiguos si está activado
            if self.config.get("auto_cleanup_enabled", True):
                self.clean_old_audio_files()

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

    def clean_old_audio_files(self, days_old=None):
        """
        Limpiar archivos de audio más antiguos que X días.

        Args:
            days_old: Número de días para considerar un archivo como antiguo
                      (default: usa configuración max_transcription_age_days)

        Returns:
            int: Número de archivos eliminados
        """
        if days_old is None:
            days_old = self.max_transcription_age_days

        if days_old <= 0:
            return 0

        try:
            import time
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            deleted_count = 0

            for filename in os.listdir(self.audio_path):
                if filename.endswith('.wav'):
                    filepath = os.path.join(self.audio_path, filename)
                    file_mtime = os.path.getmtime(filepath)

                    if file_mtime < cutoff_time:
                        os.remove(filepath)
                        deleted_count += 1
                        print(f"Archivo antiguo eliminado: {filename}")

            return deleted_count
        except Exception as e:
            print(f"Error al limpiar archivos antiguos: {e}")
            return 0

    def maintain_audio_file_limit(self):
        """
        Mantener el límite de archivos de audio eliminando los más antiguos.

        Returns:
            int: Número de archivos eliminados
        """
        try:
            audio_files = [f for f in os.listdir(self.audio_path) if f.endswith('.wav')]

            if len(audio_files) <= self.max_audio_files:
                return 0

            # Ordenar por fecha de modificación (más antiguos primero)
            audio_files_with_mtime = [
                (f, os.path.getmtime(os.path.join(self.audio_path, f)))
                for f in audio_files
            ]
            audio_files_with_mtime.sort(key=lambda x: x[1])  # Ascendente (antiguos primero)

            # Eliminar archivos excedentes (empezando por los más antiguos)
            files_to_delete = len(audio_files) - self.max_audio_files
            deleted_count = 0

            for filename, _ in audio_files_with_mtime[:files_to_delete]:
                filepath = os.path.join(self.audio_path, filename)
                os.remove(filepath)
                deleted_count += 1
                print(f"Archivo excedente eliminado: {filename}")

            return deleted_count
        except Exception as e:
            print(f"Error al mantener límite de archivos: {e}")
            return 0

    def get_audio_files_list(self, limit=None, offset=0):
        """
        Obtener lista de archivos de audio con paginación.

        Args:
            limit: Número máximo de archivos a retornar (None = sin límite)
            offset: Número de archivos a saltar (para paginación)

        Returns:
            list: Lista de archivos (nombre, filepath, mtime)
        """
        try:
            audio_files = [f for f in os.listdir(self.audio_path) if f.endswith('.wav')]

            # Agregar metadatos
            files_with_metadata = []
            for filename in audio_files:
                filepath = os.path.join(self.audio_path, filename)
                files_with_metadata.append({
                    "name": filename,
                    "path": filepath,
                    "mtime": os.path.getmtime(filepath)
                })

            # Ordenar por fecha de modificación (más recientes primero)
            files_with_metadata.sort(key=lambda x: x["mtime"], reverse=True)

            # Aplicar offset y límite
            if offset > 0:
                files_with_metadata = files_with_metadata[offset:]

            if limit is not None:
                files_with_metadata = files_with_metadata[:limit]

            return files_with_metadata
        except Exception as e:
            print(f"Error al obtener lista de archivos: {e}")
            return []
