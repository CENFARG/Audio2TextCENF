# C:\Users\gonza\Dropbox\DOC. RECA\06-Software\Audio2Text\audio2text_v0.8.0\backend\localization_manager.py
import json
import os

class LocalizationManager:
    SUPPORTED_LANGUAGES = {"es", "en"}

    def __init__(self, lang_code="es", lang_dir="lang"):
        self.lang_code = self._normalize_language(lang_code)
        # Ajustar la ruta para que sea relativa al directorio del script
        self.lang_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", lang_dir)
        self.translations = {}
        self.load_translations()

    def load_translations(self):
        lang_file = os.path.join(self.lang_dir, f"{self.lang_code}.json")
        if not os.path.exists(lang_file):
            print(f"Warning: Language file not found for {self.lang_code}. Falling back to 'es'.")
            self.lang_code = "es"
            lang_file = os.path.join(self.lang_dir, f"{self.lang_code}.json")
            if not os.path.exists(lang_file):
                print(f"Error: Default language file 'es.json' not found at {lang_file}.")
                self.translations = {}
                return

        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except Exception as e:
            print(f"Error loading translations for {self.lang_code}: {e}")
            self.translations = {}

    def get_string(self, key, **kwargs):
        text = self.translations.get(key, f"MISSING_TRANSLATION_{key}")
        return text.format(**kwargs)
    
    def set_language(self, lang_code):
        lang_code = self._normalize_language(lang_code)
        if self.lang_code != lang_code:
            self.lang_code = lang_code
            self.load_translations()
        return self.lang_code

    @classmethod
    def _normalize_language(cls, lang_code):
        return lang_code if lang_code in cls.SUPPORTED_LANGUAGES else "es"
