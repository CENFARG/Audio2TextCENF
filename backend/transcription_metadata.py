"""
Transcription Metadata Manager - Gestión de metadata de transcripciones.

Guarda información adicional sobre transcripciones como:
- Emoji personalizado
- Título personalizado
- Etiquetas
- Notas
"""

import json
import os
from typing import Dict, Optional, Any
from datetime import datetime


class TranscriptionMetadata:
    """Gestor de metadata de transcripciones."""

    def __init__(self, metadata_file: str = "transcription_metadata.json"):
        """
        Inicializar gestor de metadata.

        Args:
            metadata_file: Archivo JSON para guardar metadata
        """
        self.metadata_file = metadata_file
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self._load_metadata()

    def _load_metadata(self):
        """Cargar metadata desde archivo."""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                print(f"Error cargando metadata: {e}")
                self.metadata = {}
        else:
            self.metadata = {}

    def _save_metadata(self):
        """Guardar metadata a archivo."""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando metadata: {e}")

    def get_emoji(self, filename: str, default: str = "🎤") -> str:
        """
        Obtener emoji personalizado para una transcripción.

        Args:
            filename: Nombre del archivo de audio
            default: Emoji por defecto si no hay custom

        Returns:
            Emoji a mostrar
        """
        if filename in self.metadata:
            return self.metadata[filename].get("emoji", default)
        return default

    def set_emoji(self, filename: str, emoji: str):
        """
        Establecer emoji personalizado para una transcripción.

        Args:
            filename: Nombre del archivo de audio
            emoji: Emoji a asignar
        """
        if filename not in self.metadata:
            self.metadata[filename] = {}

        self.metadata[filename]["emoji"] = emoji
        self.metadata[filename]["updated_at"] = datetime.now().isoformat()
        self._save_metadata()

    def get_title(self, filename: str, default: Optional[str] = None) -> Optional[str]:
        """
        Obtener título personalizado para una transcripción.

        Args:
            filename: Nombre del archivo de audio
            default: Título por defecto si no hay custom

        Returns:
            Título personalizado o default
        """
        if filename in self.metadata:
            return self.metadata[filename].get("title", default)
        return default

    def set_title(self, filename: str, title: str):
        """
        Establecer título personalizado para una transcripción.

        Args:
            filename: Nombre del archivo de audio
            title: Título a asignar
        """
        if filename not in self.metadata:
            self.metadata[filename] = {}

        self.metadata[filename]["title"] = title
        self.metadata[filename]["updated_at"] = datetime.now().isoformat()
        self._save_metadata()

    def get_tags(self, filename: str) -> list:
        """
        Obtener etiquetas de una transcripción.

        Args:
            filename: Nombre del archivo de audio

        Returns:
            Lista de etiquetas
        """
        if filename in self.metadata:
            return self.metadata[filename].get("tags", [])
        return []

    def set_tags(self, filename: str, tags: list):
        """
        Establecer etiquetas para una transcripción.

        Args:
            filename: Nombre del archivo de audio
            tags: Lista de etiquetas
        """
        if filename not in self.metadata:
            self.metadata[filename] = {}

        self.metadata[filename]["tags"] = tags
        self.metadata[filename]["updated_at"] = datetime.now().isoformat()
        self._save_metadata()

    def get_notes(self, filename: str) -> Optional[str]:
        """
        Obtener notas de una transcripción.

        Args:
            filename: Nombre del archivo de audio

        Returns:
            Notas o None
        """
        if filename in self.metadata:
            return self.metadata[filename].get("notes")
        return None

    def set_notes(self, filename: str, notes: str):
        """
        Establecer notas para una transcripción.

        Args:
            filename: Nombre del archivo de audio
            notes: Notas a guardar
        """
        if filename not in self.metadata:
            self.metadata[filename] = {}

        self.metadata[filename]["notes"] = notes
        self.metadata[filename]["updated_at"] = datetime.now().isoformat()
        self._save_metadata()

    def get_all_metadata(self, filename: str) -> Dict[str, Any]:
        """
        Obtener toda la metadata de una transcripción.

        Args:
            filename: Nombre del archivo de audio

        Returns:
            Diccionario con toda la metadata
        """
        return self.metadata.get(filename, {})

    def delete_metadata(self, filename: str):
        """
        Eliminar metadata de una transcripción.

        Args:
            filename: Nombre del archivo de audio
        """
        if filename in self.metadata:
            del self.metadata[filename]
            self._save_metadata()

    def clear_all(self):
        """Eliminar toda la metadata."""
        self.metadata = {}
        self._save_metadata()


if __name__ == "__main__":
    # Test del gestor de metadata
    metadata = TranscriptionMetadata("test_metadata.json")

    # Test emoji
    metadata.set_emoji("audio_20260325_123456.wav", "💡")
    print(f"Emoji: {metadata.get_emoji('audio_20260325_123456.wav')}")

    # Test título
    metadata.set_title("audio_20260325_123456.wav", "Idea de proyecto")
    print(f"Título: {metadata.get_title('audio_20260325_123456.wav')}")

    # Test tags
    metadata.set_tags("audio_20260325_123456.wav", ["trabajo", "idea"])
    print(f"Tags: {metadata.get_tags('audio_20260325_123456.wav')}")

    # Test todas
    print(f"Toda la metadata: {metadata.get_all_metadata('audio_20260325_123456.wav')}")

    # Cleanup
    import os
    if os.path.exists("test_metadata.json"):
        os.remove("test_metadata.json")
