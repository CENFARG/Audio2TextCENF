# C:\Users\gonza\Dropbox\DOC. RECA\06-Software\Audio2Text\audio2text_v0.8.1\backend\config_manager.py
import os
import json
import logging
from .localization_manager import LocalizationManager

class ConfigManager:
    """Gestor de configuración de la aplicación para la v0.8.0"""

    def __init__(self, config_file="config.json"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_file = config_file
        self.default_config = {
            "app_version": "0.8.1",
            "audio_path": "./audio",
            "transcriptions_path": "./transcriptions",
            "save_audio": True,
            "save_logs": True,
            "hotkey": "f12",
            "record_mode": "toggle", # Opciones: "hold" o "toggle" - CAMBIO AQUI
            "default_language": "es",
            "max_audio_files": 100,
            "max_log_entries": 1000,
            "max_recording_time": 300,
            "groq_api_key": "", # Default empty, user must provide it
            "openrouter_api_key": "", # Only for PRO
            "audio_priority_apps": ["zoom.exe", "teams.exe", "meet.exe", "skype.exe"],
            "show_transcription_panel": False,
            "auto_paste_text": False,
            "client_logo_path": ""
        }
        self.config = self.load_config()
        self.localization_manager = LocalizationManager(lang_code=self.config.get("default_language"))

    def load_config(self):
        """Cargar configuración desde archivo."""
        config = self.default_config.copy()
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Exclude groq_api_key from loaded_config if it exists, as it's now from env
                    # if "groq_api_key" in loaded_config: del loaded_config["groq_api_key"]
                    config.update(loaded_config)
                self.logger.info(f"Configuración cargada desde {self.config_file}")
            else:
                self.logger.info(f"Archivo de configuración {self.config_file} no encontrado. Usando configuración por defecto.")
        except Exception as e:
            self.logger.error(f"Error al cargar configuración desde {self.config_file}: {e}, usando configuración por defecto.")
        
        return config

    def save_config(self):
        """Guardar configuración en archivo."""
        try:
            config_to_save = self.config.copy()
            # Ensure groq_api_key is persisted to replace default gift key
            # if "groq_api_key" in config_to_save: del config_to_save["groq_api_key"]

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Configuración guardada en {self.config_file}")
        except Exception as e:
            self.logger.error(f"Error al guardar configuración en {self.config_file}: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

    def set_multiple(self, new_settings: dict):
        self.config.update(new_settings)
        self.save_config()

    def get_localized_string(self, key, **kwargs):
        return self.localization_manager.get_string(key, **kwargs)

    def set_language(self, lang_code):
        old_lang = self.config.get("default_language")
        self.config["default_language"] = lang_code
        self.localization_manager.set_language(lang_code)
        self.save_config()
        self.logger.info(f"Idioma cambiado de '{old_lang}' a '{lang_code}'")

    def get_groq_api_key_from_env(self):
        # 1. Check Env Var
        api_key = os.getenv("GROQ_API_KEY")
        if api_key: return api_key

        # 2. Check internal config (runtime setting)
        api_key = self.config.get("groq_api_key")
        if api_key: return api_key
        
        self.logger.warning("GROQ_API_KEY no encontrada en variables de entorno ni en configuración.")
        return None
