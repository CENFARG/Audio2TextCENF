"""
Hotkey Manager - Gestión de hotkeys con modificadores y mouse.

Soporta:
- Modificadores de teclado: Ctrl, Alt, Shift, Ctrl+Shift, Ctrl+Alt, etc.
- Teclas F1-F12 y teclas alfanuméricas
- Botones de mouse: izquierdo, derecho, medio, side, extra
- Combinaciones teclado + mouse
"""

import logging
import keyboard
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass


@dataclass
class Hotkey:
    """Representa un hotkey completo."""
    key: str  # Tecla principal: "f1", "a", "1", etc.
    modifiers: List[str]  # Modificadores: ["ctrl", "shift"], ["alt"], etc.
    mouse_button: Optional[str] = None  # Botón mouse: "left", "right", "middle", etc.

    def __str__(self) -> str:
        """Representación legible del hotkey."""
        parts = []
        parts.extend([m.capitalize() for m in self.modifiers])
        if self.mouse_button:
            parts.append(self.mouse_button.capitalize())
            parts.append("+")
        parts.append(self.key.upper())
        return "+".join(parts)

    def to_keyboard_format(self) -> str:
        """
        Convertir a formato que entiende keyboard library.

        Returns:
            String como "ctrl+shift+f1"
        """
        parts = []
        parts.extend(self.modifiers)
        parts.append(self.key)
        return "+".join(parts)


class HotkeyManager:
    """Gestor de hotkeys con modificadores."""

    # Modificadores soportados
    MODIFIERS = ["ctrl", "alt", "shift"]

    # Botones de mouse soportados
    MOUSE_BUTTONS = ["left", "right", "middle", "side", "extra"]

    # Teclas F soportadas
    F_KEYS = [f"f{i}" for i in range(1, 13)]

    def __init__(self):
        """Inicializar gestor de hotkeys."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.registered_hotkeys: Dict[str, keyboard.KeyboardEvent] = {}

    def parse_hotkey_string(self, hotkey_str: str) -> Hotkey:
        """
        Parsear string de hotkey a objeto Hotkey.

        Args:
            hotkey_str: String como "ctrl+shift+f1", "alt+f5", "f12"

        Returns:
            Objeto Hotkey parseado
        """
        parts = [part.strip() for part in hotkey_str.lower().split("+") if part.strip()]

        key = parts[-1]  # Última parte es la tecla
        # Keep unknown modifiers so validation can reject them explicitly.
        modifiers = [p for p in parts[:-1] if p not in self.MOUSE_BUTTONS]
        mouse_button = None

        # Detectar si incluye botón mouse
        for part in parts:
            if part in self.MOUSE_BUTTONS:
                mouse_button = part
                break

        return Hotkey(key=key, modifiers=modifiers, mouse_button=mouse_button)

    def format_hotkey_string(self, key: str, modifiers: List[str], mouse_button: Optional[str] = None) -> str:
        """
        Formatear componentes de hotkey a string.

        Args:
            key: Tecla principal
            modifiers: Lista de modificadores
            mouse_button: Botón mouse (opcional)

        Returns:
            String formateado como "ctrl+shift+f1"
        """
        parts = []
        parts.extend(modifiers)
        if mouse_button:
            parts.append(mouse_button)
        parts.append(key)
        return "+".join(parts)

    def is_hotkey_valid(self, hotkey_str: str) -> bool:
        """
        Validar si un string de hotkey es válido.

        Args:
            hotkey_str: String a validar

        Returns:
            True si es válido, False si no
        """
        try:
            hotkey = self.parse_hotkey_string(hotkey_str)

            # Validar tecla
            valid_keys = self.F_KEYS + [chr(i) for i in range(ord('a'), ord('z') + 1)]
            valid_keys += [str(i) for i in range(10)]

            if hotkey.key not in valid_keys:
                self.logger.warning(f"Tecla inválida: {hotkey.key}")
                return False

            # Validar modificadores
            for mod in hotkey.modifiers:
                if mod not in self.MODIFIERS:
                    self.logger.warning(f"Modificador inválido: {mod}")
                    return False

            # Validar botón mouse
            if hotkey.mouse_button and hotkey.mouse_button not in self.MOUSE_BUTTONS:
                self.logger.warning(f"Botón mouse inválido: {hotkey.mouse_button}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error parseando hotkey: {e}")
            return False

    def register_hotkey(
        self,
        hotkey_str: str,
        callback: Callable,
        suppress: bool = True
    ) -> bool:
        """
        Registrar un hotkey con keyboard library.

        Args:
            hotkey_str: String del hotkey como "ctrl+shift+f1"
            callback: Función a ejecutar
            suppress: Si True, suprime la tecla

        Returns:
            True si se registró correctamente
        """
        if not self.is_hotkey_valid(hotkey_str):
            return False

        try:
            keyboard.add_hotkey(
                hotkey_str,
                callback,
                suppress=suppress
            )
            self.logger.info(f"Hotkey registrado: {hotkey_str}")
            return True
        except Exception as e:
            self.logger.error(f"Error registrando hotkey {hotkey_str}: {e}")
            return False

    def unregister_hotkey(self, hotkey_str: str) -> bool:
        """
        Desregistrar un hotkey.

        Args:
            hotkey_str: String del hotkey

        Returns:
            True si se desregistró correctamente
        """
        try:
            keyboard.remove_hotkey(hotkey_str)
            self.logger.info(f"Hotkey desregistrado: {hotkey_str}")
            return True
        except Exception as e:
            self.logger.error(f"Error desregistrando hotkey {hotkey_str}: {e}")
            return False

    def get_available_hotkeys(self) -> List[str]:
        """
        Obtener lista de hotkeys disponibles.

        Returns:
            Lista de strings con hotkeys comunes
        """
        hotkeys = []

        # F1-F12 sin modificadores
        for f in self.F_KEYS:
            hotkeys.append(f)

        # Ctrl + F1-F12
        for f in self.F_KEYS:
            hotkeys.append(f"ctrl+{f}")

        # Alt + F1-F12
        for f in self.F_KEYS:
            hotkeys.append(f"alt+{f}")

        # Shift + F1-F12
        for f in self.F_KEYS:
            hotkeys.append(f"shift+{f}")

        # Ctrl+Shift + F1-F12
        for f in self.F_KEYS:
            hotkeys.append(f"ctrl+shift+{f}")

        # Ctrl+Alt + F1-F12
        for f in self.F_KEYS:
            hotkeys.append(f"ctrl+alt+{f}")

        return hotkeys

    def get_hotkey_suggestions(self, category: str = "trabajo") -> List[str]:
        """
        Obtener sugerencias de hotkeys por categoría.

        Args:
            category: Categoría (trabajo, idea, personal, etc.)

        Returns:
            Lista de hotkeys sugeridos
        """
        suggestions = {
            "trabajo": ["f1", "f2", "ctrl+f1", "ctrl+f2", "alt+f1"],
            "idea": ["f3", "f4", "ctrl+f3", "shift+f3"],
            "personal": ["f5", "f6", "alt+f5"],
            "técnico": ["f7", "f8", "ctrl+shift+f7"],
            "favoritos": ["f9", "f10", "ctrl+f9"],
        }

        return suggestions.get(category, ["f1", "f2", "f3"])


if __name__ == "__main__":
    # Test del gestor de hotkeys
    manager = HotkeyManager()

    # Test parseo
    hotkey = manager.parse_hotkey_string("ctrl+shift+f1")
    print(f"Hotkey: {hotkey}")
    print(f"Legible: {hotkey}")
    print(f"Keyboard format: {hotkey.to_keyboard_format()}")

    # Test validación
    print(f"Es válido 'ctrl+shift+f1': {manager.is_hotkey_valid('ctrl+shift+f1')}")
    print(f"Es válido 'invalid+f1': {manager.is_hotkey_valid('invalid+f1')}")

    # Test hotkeys disponibles
    disponibles = manager.get_available_hotkeys()
    print(f"Hotkeys disponibles: {len(disponibles)}")
    print(f"Primeros 10: {disponibles[:10]}")
