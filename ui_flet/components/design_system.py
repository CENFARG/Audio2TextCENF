"""
Design System for Audio2Text Flet UI.

Centralizes colors, typography, and design tokens.
"""

import flet as ft


class DesignSystem:
    """Sistema de diseño para Audio2Text en Flet."""

    # Colores
    COLORS = {
        "primary": "#2563EB",
        "primary_hover": "#1D4ED8",
        "success": "#10B981",
        "error": "#EF4444",
        "warning": "#F59E0B",
        "background": "#0F172A",
        "surface": "#1E293B",
        "text_primary": "#F8FAFC",
        "text_secondary": "#CBD5E1",
        "overlay_bg": "rgba(0,0,0,0.7)",
        "led_green": ft.Colors.GREEN,
        "led_red": ft.Colors.RED,
        "led_yellow": ft.Colors.YELLOW,
        "led_grey": ft.Colors.GREY,
    }

    # Tipografía (text sizes)
    TEXT_SIZES = {
        "heading_large": 24,
        "heading_medium": 18,
        "body_large": 16,
        "body_medium": 14,
        "body_small": 12,
        "caption": 10,
    }

    # Spacing
    SPACING = {
        "xs": 4,
        "sm": 8,
        "md": 16,
        "lg": 24,
        "xl": 32,
    }

    # Border radius
    RADIUS = {
        "sm": 4,
        "md": 8,
        "lg": 12,
        "xl": 16,
        "full": 9999,
    }

    # Iconos comunes
    ICONS = {
        "microphone": ft.Icons.MIC,
        "stop": ft.Icons.STOP,
        "settings": ft.Icons.SETTINGS,
        "history": ft.Icons.HISTORY,
        "info": ft.Icons.INFO,
        "update": ft.Icons.SYSTEM_UPDATE,
        "delete": ft.Icons.DELETE,
        "edit": ft.Icons.EDIT,
        "play": ft.Icons.PLAY_ARROW,
        "audio_file": ft.Icons.AUDIO_FILE,
        "emoji": ft.Icons.EMOJI_EMOTIONS,
    }

    @classmethod
    def get_color(cls, color_name: str) -> str:
        """Obtener color por nombre."""
        return cls.COLORS.get(color_name, "#FFFFFF")

    @classmethod
    def get_text_size(cls, size_name: str) -> int:
        """Obtener tamaño de texto por nombre."""
        return cls.TEXT_SIZES.get(size_name, 14)

    @classmethod
    def get_spacing(cls, spacing_name: str) -> int:
        """Obtener espaciado por nombre."""
        return cls.SPACING.get(spacing_name, 16)

    @classmethod
    def get_radius(cls, radius_name: str) -> int:
        """Obtener border radius por nombre."""
        return cls.RADIUS.get(radius_name, 8)
