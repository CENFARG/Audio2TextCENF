# C:\Users\gonza\Dropbox\DOC. RECA\06-Software\Audio2Text\audio2text_v0.8.1\backend\config_manager.py
import os
import json
import logging
import copy
from .localization_manager import LocalizationManager

class ConfigManager:
    """Gestor de configuración de la aplicación para la v0.8.0"""

    def __init__(self, config_file="config.json"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_file = config_file
        self.default_config = {
            "app_version": "0.15.0",  # FIX: versión real (estaba hardcodeada 0.13.0)
            "audio_path": "./audio",
            "transcriptions_path": "./transcriptions",
            "save_audio": True,
            "save_logs": True,
            "hotkey": "f9",  # FIX: default F9 (estaba f12) — pedido del usuario
            "hotkey_modifier": "",  # DEPRECATED: Usar formato "ctrl+f9" en hotkey
            "record_mode": "toggle", # Opciones: "hold" o "toggle"
            "default_language": "es",  # Legacy compatibility input only
            "ui_language": "es",
            "transcription_output_language": "es",
            "max_audio_files": 100,
            "max_log_entries": 1000,
            "max_recording_time": 300,
            "max_transcription_age_days": 30,  # Días antes de limpiar transcripciones antiguas
            "auto_cleanup_enabled": True,      # Limpieza automática de archivos antiguos
            "groq_api_key": "",
            "gift_key_encoded": "",
            "audio_priority_apps": ["zoom.exe", "teams.exe", "meet.exe", "skype.exe"],
            "show_transcription_panel": False,
            "auto_paste_text": True,  # FIX: auto-pegar habilitado por defecto (pedido del usuario)
            "client_logo_path": "",
            "utf8_validation": True,  # Validación y corrección UTF-8 para caracteres españoles
            "asr_provider": "groq",   # Servicio de transcripción: "groq" o "nvidia"
            "nvidia_enabled": False,  # Habilitar NVIDIA Riva ASR
            "nvidia_api_key": "",     # API key de NVIDIA (se ofuscará al guardar)
            "nvidia_mode": "cloud"    # Modo NVIDIA: "cloud" (API) o "local" (Docker)
            # FIX v0.15.0: faster-whisper ERRADICADO (modelo local) — solo API cloud
        }
        # Cargar configuración ANTES de inicializar localization_manager
        self.config = self.load_config()
        self.localization_manager = LocalizationManager(lang_code=self.config.get("ui_language", "es"))

    def load_config(self):
        """Cargar configuración desde archivo."""
        config = copy.deepcopy(self.default_config)
        needs_save = False
        config_exists = os.path.exists(self.config_file)
        loaded_keys = set()
        try:
            if config_exists:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    loaded_keys = set(loaded_config)
                    config.update(loaded_config)
                
                # Check if keys are already obfuscated by trying to decode them
                # If they are NOT obfuscated (plain 'gsk_', 'nvapi-', 'sk-'), we force a save after loading
                needs_save = False
                for key in ["groq_api_key", "nvidia_api_key"]:
                    val = config.get(key, "")
                    if val and (val.startswith("gsk_") or val.startswith("nvapi-") or val.startswith("sk-")):
                        needs_save = True
                        break
                
        except Exception as e:
            self.logger.error(f"Error al cargar configuración desde {self.config_file}: {e}, usando configuración por defecto.")
        
        needs_save = self._normalize_language_settings(config, loaded_keys) or needs_save

        # Ensure we don't overwrite the hardcoded version in memory
        config["app_version"] = self.default_config["app_version"]
        
        # Decode sensitive keys (Always do this, even for defaults)
        for key in ["groq_api_key", "nvidia_api_key"]:
            if config.get(key):
                decoded_value = self._decode_gift_key(config[key])
                config[key] = decoded_value
                self.logger.debug("Decoded sensitive configuration value for %s", key)
        
        self.config = config
        
        # Force save if it was plain text to obfuscate it immediately
        if needs_save and config_exists:
            self.logger.info("Detectada clave en texto plano. Ofuscando automáticamente...")
            self.save_config()
            
        return config

    def _normalize_language_settings(self, config, loaded_keys=None):
        """Normalize independent language settings and migrate legacy input."""
        valid_languages = {"es", "en"}
        legacy_language = config.get("default_language")
        legacy_language = legacy_language if legacy_language in valid_languages else "es"
        loaded_keys = loaded_keys or set()
        changed = False

        for key in ("ui_language", "transcription_output_language"):
            if "default_language" in loaded_keys and key not in loaded_keys:
                normalized = legacy_language
            elif config[key] not in valid_languages:
                normalized = "es"
            else:
                normalized = config[key]

            if config.get(key) != normalized:
                config[key] = normalized
                changed = True

        return changed

    def save_config(self):
        """Guardar configuración en archivo."""
        try:
            config_to_save = self.config.copy()
            
            # Encode sensitive keys before saving
            for key in ["groq_api_key", "nvidia_api_key"]:
                if config_to_save.get(key):
                    config_to_save[key] = self._encode_key(config_to_save[key])
            
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
        getter = getattr(self.localization_manager, "get", None)
        if callable(getter):
            return getter(key, **kwargs)
        return self.localization_manager.get_string(key, **kwargs)

    def set_language(self, lang_code):
        old_lang = self.config.get("ui_language")
        if lang_code not in {"es", "en"}:
            lang_code = "es"
        self.config["ui_language"] = lang_code
        # Keep the legacy field writable for old consumers, but do not read it
        # as the runtime source of truth.
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
        if api_key:
             return api_key

        # 3. Check for Encoded Gift Key (Optional)
        encoded_gift = self.config.get("gift_key_encoded")
        if encoded_gift:
            return self._decode_gift_key(encoded_gift)
        
        self.logger.warning("GROQ_API_KEY no encontrada en variables de entorno ni en configuración.")
        return None

    def _encode_key(self, key):
        """Ofusca una clave (Base64 + XOR simple)."""
        import base64
        xor_key = "CENF_SECRET"
        xor_result = bytes([ord(c) ^ ord(xor_key[i % len(xor_key)]) for i, c in enumerate(key)])
        return base64.b64encode(xor_result).decode('utf-8')

    def _decode_gift_key(self, encoded_key):
        """Decodifica una clave obfuscada (Base64 + XOR simple)."""
        if not encoded_key: return ""

        # SI YA ESTÁ DECODIFICADA (Empieza con gsk_, sk- o nvapi_), NO HACER NADA
        if encoded_key.startswith("gsk_") or encoded_key.startswith("sk-") or encoded_key.startswith("nvapi-"):
            return encoded_key

        import base64
        try:
            # Check if it looks like base64
            decoded_bytes = base64.b64decode(encoded_key)
            # Simple XOR con una clave fija 'CENF_SECRET'
            xor_key = "CENF_SECRET"
            result = "".join(chr(b ^ ord(xor_key[i % len(xor_key)])) for i, b in enumerate(decoded_bytes))

            # Si el resultado no empieza con los prefijos esperados, es probable que no fuera base64
            if not (result.startswith("gsk_") or result.startswith("sk-") or result.startswith("nvapi-")):
                 self.logger.debug("La clave decodificada no tiene el formato esperado, devolviendo original.")
                 return encoded_key
            return result
        except Exception as e:
            # If fails, maybe it's not encoded or corrupted
            self.logger.debug(f"Error decodificando key (podría no estar codificada): {e}")
            return encoded_key
