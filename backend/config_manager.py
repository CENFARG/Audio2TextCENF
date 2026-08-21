# C:\Users\gonza\Dropbox\DOC. RECA\06-Software\Audio2Text\audio2text_v0.8.1\backend\config_manager.py
import os
import json
import re
import logging
from .localization_manager import LocalizationManager

# Optional keyring support — graceful fallback if not installed
try:
    import keyring as _keyring
    _KEYRING_AVAILABLE = True
except ImportError:
    _keyring = None
    _KEYRING_AVAILABLE = False

_KEYRING_SERVICE = "audio2text-cenf"
_KEYRING_USER = "groq_api_key"


class ConfigManager:
    """Gestor de configuración de la aplicación para la v0.15.7"""

    def __init__(self, config_file="config.json"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_file = config_file
        if not _KEYRING_AVAILABLE:
            self.logger.warning(
                "python-keyring no instalado — usando env GROQ_API_KEY / config.json. "
                "Instalá con: pip install keyring"
            )
        self.default_config = {
            "app_version": "0.15.7",
            "audio_path": "./audio",
            "transcriptions_path": "./transcriptions",
            "save_audio": True,
            "save_logs": True,
            "hotkey": "f9",  # FIX: default F9 (estaba f12) — pedido del usuario
            "hotkey_modifier": "",  # DEPRECATED: Usar formato "ctrl+f9" en hotkey
            "record_mode": "toggle", # Opciones: "hold" o "toggle"
            "default_language": "es",  # Idioma de INTERFAZ (siempre es)
            "transcription_language": "es",  # Idioma de TRANSCRIPCIÓN (es/en, configurable por el usuario)
            "max_audio_files": 100,
            "max_log_entries": 1000,
            "max_recording_time": 1200,  # FIX: default 20 min (antes 5 min)
            "max_transcription_age_days": 30,  # Días antes de limpiar transcripciones antiguas
            "auto_cleanup_enabled": True,      # Limpieza automática de archivos antiguos
            # HC-01 FIX: placeholder vacío — key real via GROQ_API_KEY env o keyring, nunca hardcodeada
            "groq_api_key": "",
            "gift_key_encoded": "",  # DEPRECATED: removido por seguridad, mantener clave vacía para compat
            "audio_priority_apps": ["zoom.exe", "teams.exe", "meet.exe", "skype.exe"],
            "show_transcription_panel": True,  # FIX: panel visible por defecto
            "auto_paste_text": True,  # FIX: auto-pegar habilitado por defecto (pedido del usuario)
            "autostart_windows": False,  # FIX: desactivado por defecto
            "client_logo_path": "",
            "utf8_validation": True,  # Validación y corrección UTF-8 para caracteres españoles
            "asr_provider": "groq",   # Servicio de transcripción: "groq" o "nvidia"
            "nvidia_enabled": False,  # Habilitar NVIDIA Riva ASR
            "nvidia_api_key": "",     # API key de NVIDIA (se ofuscará al guardar)
            "nvidia_mode": "cloud",   # Modo NVIDIA: "cloud" (API) o "local" (Docker)
            "window_geometry": "590x590+200+100",  # FIX v0.15.7: default cuadrado — pisa config vieja si no existe
            # FIX v0.15.0: faster-whisper ERRADICADO (modelo local) — solo API cloud
        }
        # Cargar configuración ANTES de inicializar localization_manager
        self.config = self.load_config()
        self.localization_manager = LocalizationManager(lang_code=self.config.get("default_language"))

    def load_config(self):
        """Cargar configuración desde archivo."""
        config = self.default_config.copy()
        loaded_config = {}
        needs_save = False
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
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
        
        # Migración: si el archivo no tenía transcription_language, copiar desde su default_language
        if "transcription_language" not in loaded_config:
            # Si el archivo tenía default_language (ej: "en"), respetarlo para transcripción
            if "default_language" in loaded_config:
                config["transcription_language"] = loaded_config.get("default_language", "es")
            # Si no, ya tiene el default "es"
            needs_save = True

        # Forzar interfaz siempre en español (requisito v0.15.1)
        config["default_language"] = "es"

        # Ensure we don't overwrite the hardcoded version in memory
        config["app_version"] = self.default_config["app_version"]

        # QA: geometry validation + migration — robust 590x590 cuadrado
        # Fresh install: si no hay config_file, default 590x590+200+100 ya está en config (default_config).
        # Validación: window_geometry debe matchear ^\d+x\d+(\+\d+\+\d+)?$ sino se resetea a default.
        # Migración one-shot para usuarios existentes: si el valor guardado es legacy conocido
        # (650x550*, 1536x793*, 160x160*, 800x600*, etc.) y aún no está marcado como migrado,
        # se actualiza a 590x590+200+100 y se marca _geometry_migrated=True para no repetir.
        # Esto NO pisa custom resize válido del usuario (ej: 700x800+100+100) porque solo migra
        # prefijos legacy conocidos, no cualquier valor distinto de 590x590. Tras la primera
        # migración, el flag evita re-migrar aunque el usuario luego customice.
        _GEOMETRY_DEFAULT = self.default_config["window_geometry"]
        _GEOMETRY_PATTERN = re.compile(r"^\d+x\d+(\+\d+\+\d+)?$")
        _LEGACY_PREFIXES = ("650x550", "1536x793", "160x160", "800x600", "1024x768", "1280x720")
        saved_geo = loaded_config.get("window_geometry") if isinstance(loaded_config, dict) else None
        current_geo = config.get("window_geometry", "")
        # 1) Validación de formato — si no matchea regex, reset a default
        if not isinstance(current_geo, str) or not current_geo.strip() or not _GEOMETRY_PATTERN.match(current_geo.strip()):
            self.logger.warning(f"window_geometry inválida '{current_geo}' — reseteando a default {_GEOMETRY_DEFAULT}")
            config["window_geometry"] = _GEOMETRY_DEFAULT
            needs_save = True
        else:
            current_geo = current_geo.strip()
            config["window_geometry"] = current_geo
            # 2) Migración legacy one-shot: solo si el valor original en disco era legacy
            #    y el flag _geometry_migrated no existe. Usamos saved_geo (lo que vino del archivo)
            #    para decidir, no current_geo normalizado, para respetar custom del usuario.
            if isinstance(loaded_config, dict):
                already_migrated = config.get("_geometry_migrated") is True or loaded_config.get("_geometry_migrated") is True
            else:
                already_migrated = config.get("_geometry_migrated") is True
            is_legacy = any(str(saved_geo).strip().startswith(p) for p in _LEGACY_PREFIXES) if isinstance(saved_geo, str) and saved_geo.strip() else False
            # Para no pisar custom, NO usamos "not startswith 590x590" genérico — solo legacy list.
            if is_legacy and not already_migrated:
                self.logger.info(f"QA migration: window_geometry legacy '{saved_geo}' -> {_GEOMETRY_DEFAULT} (one-shot)")
                config["window_geometry"] = _GEOMETRY_DEFAULT
                config["_geometry_migrated"] = True
                needs_save = True
            elif current_geo.startswith("590x590") and not already_migrated and os.path.exists(self.config_file):
                # Ya está en 590x590 pero sin flag — sellar migración para que futuros customs no se re-migren
                config["_geometry_migrated"] = True
                needs_save = True
            # Si el archivo tenía geometry vacía/missing y ya validamos arriba, marcamos migrado para no re-evaluar
            elif not saved_geo and not already_migrated:
                # Archivo existente sin key — normalizar a default y sellar
                if os.path.exists(self.config_file):
                    config["_geometry_migrated"] = True
                    needs_save = True
        
        # Decode sensitive keys (Always do this, even for defaults) — compat con configs viejas obfuscadas
        for key in ["groq_api_key", "nvidia_api_key"]:
            if config.get(key):
                original_value = config[key]
                decoded_value = self._decode_gift_key(config[key])
                # Si decodificación produjo valor válido, usarlo; si no, mantener original (ya podría ser plain)
                # _decode_gift_key ya maneja el caso plain retornando original
                config[key] = decoded_value
                self.logger.debug(f"Decoded {key}: {original_value[:20]}... -> {decoded_value[:20]}...")
        
        # También decodificar gift_key_encoded si existe (compatibilidad con instalaciones viejas)
        if config.get("gift_key_encoded"):
            try:
                decoded_gift = self._decode_gift_key(config["gift_key_encoded"])
                if decoded_gift and decoded_gift.startswith("gsk_"):
                    # Migrar gift key a groq_api_key si este está vacío
                    if not config.get("groq_api_key"):
                        config["groq_api_key"] = decoded_gift
                        needs_save = True
                    self.logger.warning("gift_key_encoded está DEPRECATED — migrando a groq_api_key y limpiar gift_key_encoded")
                # Limpiar gift_key_encoded en memoria para no exponerla
                # No guardar gift_key_encoded en config salva (ver save_config)
            except Exception:
                pass

        self.config = config
        
        # Force save if it was plain text to obfuscate it immediately
        if needs_save:
            self.logger.info("Detectada clave en texto plano. Ofuscando automáticamente...")
            self.save_config()
            
        return config

    def save_config(self):
        """Guardar configuración en archivo."""
        try:
            config_to_save = self.config.copy()
            # HC-01: nunca persistir gift_key_encoded con valor real — limpiar
            if config_to_save.get("gift_key_encoded"):
                config_to_save["gift_key_encoded"] = ""
            
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
        return self.localization_manager.get_string(key, **kwargs)

    def set_language(self, lang_code):
        old_lang = self.config.get("default_language")
        self.config["default_language"] = lang_code
        self.localization_manager.set_language(lang_code)
        self.save_config()
        self.logger.info(f"Idioma cambiado de '{old_lang}' a '{lang_code}'")

    # ── HC-01: keyring helpers ──────────────────────────────────────────
    def _get_keyring_api_key(self):
        """Intentar leer GROQ_API_KEY desde OS keyring. Retorna None si no disponible."""
        if not _KEYRING_AVAILABLE or _keyring is None:
            return None
        try:
            val = _keyring.get_password(_KEYRING_SERVICE, _KEYRING_USER)
            if val:
                self.logger.debug("GROQ_API_KEY leída desde keyring")
            return val
        except Exception as e:
            self.logger.warning(f"Error leyendo keyring: {e}")
            return None

    def _set_keyring_api_key(self, api_key: str) -> bool:
        """Guardar GROQ_API_KEY en OS keyring. Retorna True si éxito."""
        if not _KEYRING_AVAILABLE or _keyring is None:
            self.logger.warning("keyring no disponible — no se guardó en vault OS")
            return False
        try:
            _keyring.set_password(_KEYRING_SERVICE, _KEYRING_USER, api_key)
            self.logger.info("GROQ_API_KEY guardada en keyring OS vault")
            return True
        except Exception as e:
            self.logger.warning(f"Error guardando en keyring: {e}")
            return False

    def _delete_keyring_api_key(self) -> bool:
        if not _KEYRING_AVAILABLE or _keyring is None:
            return False
        try:
            _keyring.delete_password(_KEYRING_SERVICE, _KEYRING_USER)
            return True
        except Exception:
            return False

    def get_groq_api_key(self):
        """
        Fuente primaria de GROQ_API_KEY con prioridad:
        1. GROQ_API_KEY env var
        2. OS keyring (si python-keyring instalado)
        3. config.json groq_api_key (runtime, decoded)
        4. gift_key_encoded decoded (deprecated, compat)
        """
        # 1. Env var — prioridad máxima, ideal para CI/docker
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            return api_key.strip()

        # 2. OS keyring vault
        rk = self._get_keyring_api_key()
        if rk:
            return rk.strip()

        # 3. Config runtime (decoded en load_config)
        api_key = self.config.get("groq_api_key")
        if api_key:
            return api_key.strip()

        # 4. Gift key deprecated (compat)
        encoded_gift = self.config.get("gift_key_encoded")
        if encoded_gift:
            try:
                decoded = self._decode_gift_key(encoded_gift)
                if decoded and decoded.startswith("gsk_"):
                    return decoded.strip()
            except Exception:
                pass

        self.logger.warning("GROQ_API_KEY no encontrada en env / keyring / config. Configurala en Configuración o via GROQ_API_KEY.")
        return None

    def get_groq_api_key_from_env(self):
        """Compat: alias a get_groq_api_key() para código existente."""
        return self.get_groq_api_key()

    def set_groq_api_key(self, api_key: str, use_keyring: bool = True):
        """
        Guardar GROQ_API_KEY. Si use_keyring y keyring disponible, guarda en vault;
        siempre guarda en config como fallback (ofuscada al persistir).
        """
        api_key = (api_key or "").strip()
        if use_keyring and api_key:
            if self._set_keyring_api_key(api_key):
                # También guardar en config para fallback si keyring falla luego
                self.config["groq_api_key"] = api_key
                self.save_config()
                return True
        # Fallback: solo config
        self.config["groq_api_key"] = api_key
        self.save_config()
        return True

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
