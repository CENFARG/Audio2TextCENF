"""
App principal de Audio2Text en Flet - MIGRACIÓN COMPLETA DE CUSTOMTKINTER

Migración 1:1 de todas las funcionalidades de CustomTkinter a Flet.

Author: Audio2Text Team
Version: 0.10.0
"""

import os
import sys
import webbrowser
import threading
import logging
import flet as ft
from pathlib import Path
from typing import Optional

# Setup debug logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Añadir el directorio del proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config_manager import ConfigManager
from backend.transcriber import Transcriber
from backend.sound_manager import SoundManager
from backend.file_manager import FileManager
from backend.localization_manager import LocalizationManager
from backend.updater import Updater
from backend.transcription_metadata import TranscriptionMetadata


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
        "led_yellow": ft.Colors.AMBER,
        "led_grey": ft.Colors.GREY,
    }

    # Tipografía
    TYPOGRAPHY = {
        "heading_large": ft.TextStyle(
            size=20,
            weight=ft.FontWeight.BOLD,
            font_family="Segoe UI"
        ),
        "heading_medium": ft.TextStyle(
            size=16,
            weight=ft.FontWeight.BOLD,
            font_family="Segoe UI"
        ),
        "body_medium": ft.TextStyle(
            size=14,
            font_family="Segoe UI"
        ),
        "body_small": ft.TextStyle(
            size=12,
            font_family="Segoe UI"
        ),
        "link": ft.TextStyle(
            size=12,
            font_family="Segoe UI",
            decoration=ft.TextDecoration.UNDERLINE
        ),
    }


class Audio2TextApp:
    """
    Aplicación principal de Audio2Text en Flet.

    Migración completa de CustomTkinter a Flet con todas las funcionalidades.
    """

    def __init__(self):
        """Inicializar app."""
        # Configuración
        self.config = ConfigManager()
        self.localization = LocalizationManager()

        # Backend
        self.sound_manager = SoundManager()
        self.file_manager = FileManager(self.config)
        self.metadata_manager = TranscriptionMetadata("transcription_metadata.json")

        # Estado
        self.current_tab_index = 0
        self.history_items = []
        self.api_key_status = "grey"  # grey, green, red
        self.page = None
        self.tabs_container = None

        # Transcriber (se inicializará después)
        self.transcriber = None
        self.recording_overlay = None
        self.updater = None

        # Variables de UI
        self.api_key_var = None
        self.hotkey_var = None
        self.record_mode_var = None
        self.language_var = None
        self.auto_paste_var = None
        self.show_panel_var = None
        self.autostart_windows_var = None
        self.audio_path_var = None
        self.transcriptions_path_var = None
        self.save_audio_var = None
        self.save_logs_var = None
        self.status_var = None

    def init_transcriber(self):
        """Inicializar transcriber con callbacks."""
        if self.transcriber is None:
            self.transcriber = Transcriber(
                config_manager=self.config,
                sound_manager=self.sound_manager,
                file_manager=self.file_manager,
                update_status_callback=self.update_status,
                transcription_callback=self.on_transcription_complete,
                localization_manager=self.localization,
                overlay_callback=self.update_overlay
            )

    def init_updater(self):
        """Inicializar updater para actualizaciones."""
        if self.updater is None:
            self.updater = Updater(
                current_version=self.config.get("app_version"),
                github_repo="CENFARG/Audio2TextCENF"
            )

    def update_status(self, message: str, color: str = "white"):
        """
        Actualizar estado de la app (thread-safe).

        Args:
            message: Mensaje de estado
            color: Color del mensaje (white, green, yellow, red, orange)
        """
        def _update():
            if self.status_var:
                self.status_var.value = message
                # Actualizar color según estado
                if color == "white":
                    self.status_var.color = ft.Colors.WHITE
                elif color == "green":
                    self.status_var.color = ft.Colors.GREEN
                elif color == "yellow":
                    self.status_var.color = ft.Colors.AMBER
                elif color == "red":
                    self.status_var.color = ft.Colors.RED
                elif color == "orange":
                    self.status_var.color = ft.Colors.ORANGE

        if self.page:
            _update()

    def on_transcription_complete(self, transcription: str):
        """
        Callback cuando se completa una transcripción.

        Args:
            transcription: Texto transcribido
        """
        def _update():
            # Auto-paste si está activado
            if self.config.get("auto_paste_text"):
                self._auto_paste_transcription(transcription)

            # Mostrar en panel si está activo
            if self.config.get("show_transcription_panel") and self.transcription_display:
                self.transcription_display.value = transcription

        if self.page:
            _update()

    def _auto_paste_transcription(self, text: str):
        """
        Auto-pegar transcripción.

        Args:
            text: Texto a pegar
        """
        import pyperclip
        import pyautogui

        try:
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
            self.update_status("Auto-pegado", "green")
        except Exception as e:
            self.update_status(f"Error auto-pegando: {e}", "red")

    def update_overlay(self, status: str, minutes: int = 0, seconds: int = 0):
        """
        Actualizar overlay de grabación (thread-safe).

        Args:
            status: Estado del overlay (recording, processing, ready, error)
            minutes: Minutos transcurridos
            seconds: Segundos transcurridos
        """
        def _update():
            from ui_flet.components.recording_overlay import RecordingOverlay

            if self.recording_overlay is None:
                self.recording_overlay = RecordingOverlay()

            if status == "recording":
                self.recording_overlay.set_recording(minutes, seconds)
            elif status == "processing":
                self.recording_overlay.set_processing()
            elif status == "ready":
                self.recording_overlay.set_ready()
            elif status == "error":
                self.recording_overlay.set_error()

        if self.page:
            _update()

    def create_main_tab(self) -> ft.Container:
        """
        Construir pestaña principal.

        Returns:
            Container con contenido de la pestaña principal
        """
        logger.debug("[CREATE_MAIN_TAB] Creating main tab content")

        # Status frame - padding ajustado a CustomTkinter
        logger.debug("[CREATE_MAIN_TAB] Creating status_frame")
        status_frame = ft.Container(
            content=ft.Row([
                # LED indicador (API key) - simplificado
                ft.Text("●", size=18, color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD),
                ft.Container(width=8),
                ft.Column([
                    self.status_var,
                    ft.Text(
                        f"Hotkey: {self.config.get('hotkey', 'f9').upper()}",
                        size=11,
                        color=ft.Colors.WHITE
                    )
                ], spacing=3)
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.only(left=15, right=15, top=10, bottom=5),  # CustomTkinter: pady=(10,5), padx=15
            bgcolor=ft.Colors.BLUE_GREY_800,
            border_radius=ft.border_radius.all(6),
        )

        # Logo del cliente
        logo_content = self._create_client_logo()

        # Info frame - padding ajustado a CustomTkinter
        info_frame = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("Audio: N/A (0 archivos)", size=12, color=ft.Colors.WHITE),
                    ft.Text("Transcripciones: N/A KB", size=12, color=ft.Colors.WHITE)
                ], spacing=3),
                logo_content
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(left=15, right=15, top=0, bottom=5),  # CustomTkinter: padx=15, pady=(0,5)
        )

        # Button frame - padding ajustado a CustomTkinter
        button_frame = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.DELETE, color=ft.Colors.WHITE, size=16),
                        ft.Text("Eliminar Audio", color=ft.Colors.WHITE, size=12)
                    ], spacing=5),
                    bgcolor=ft.Colors.RED,
                    width=130,
                    height=40,
                    on_click=self.clear_audio_with_feedback
                ),
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.DELETE_OUTLINE, color=ft.Colors.WHITE, size=16),
                        ft.Text("Borrar Transcripciones", color=ft.Colors.WHITE, size=12)
                    ], spacing=5),
                    bgcolor=ft.Colors.RED,
                    width=180,
                    height=40,
                    on_click=self.clear_logs_with_feedback
                )
            ], spacing=8),
            padding=ft.padding.only(left=15, right=15, top=0, bottom=5),  # CustomTkinter: padx=15, pady=(0,5)
        )

        # Panel de transcripción (opcional) - padding ajustado a CustomTkinter
        transcription_panel = None
        if self.config.get("show_transcription_panel"):
            transcription_panel = ft.Container(
                content=ft.TextField(
                    value="",
                    multiline=True,
                    min_lines=8,
                    max_lines=20,
                    bgcolor=ft.Colors.BLUE_GREY_700,
                    color=ft.Colors.WHITE,
                    text_size=14,
                    hint_text="Transcripción aparecerá aquí..."
                ),
                padding=ft.padding.only(left=10, right=10, top=0, bottom=10),  # CustomTkinter: padx=10, pady=(0,10)
                border_radius=ft.border_radius.all(8),
                bgcolor=ft.Colors.BLUE_GREY_700,
                expand=True
            )
            self.transcription_display = transcription_panel.content

        # Content column - más compacto
        main_content = ft.Column([
            status_frame,
            ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
            info_frame,
            ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
            button_frame,
            ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
            ft.Container(content=transcription_panel, expand=True)
        ])

        logger.debug("[CREATE_MAIN_TAB] Returning container with main_content")

        return ft.Container(
            content=main_content,
            padding=0,  # CustomTkinter no tiene padding en el tab
            expand=True,
            bgcolor=ft.Colors.BLUE_GREY_900
        )

    def _create_client_logo(self) -> ft.Container:
        """
        Crear logo del cliente.

        Returns:
            Container con el logo
        """
        # Buscar logo
        logo_path = "logo.png"
        if getattr(sys, 'frozen', False):
            logo_path = os.path.join(sys._MEIPASS, "logo.png")

        if not os.path.exists(logo_path):
            # Fallback si no existe logo
            return ft.Container(
                content=ft.Text(
                    value="Audio2Text",
                    size=16, weight=ft.FontWeight.BOLD,
                    color=DesignSystem.COLORS["primary"]
                )
            )

        # En Flet, cargamos la imagen directamente
        try:
            from PIL import Image as PILImage
            pil_image = PILImage.open(logo_path)

            # Resize keeping aspect ratio, max height 50
            h_ratio = 50 / float(pil_image.size[1])
            w_size = int((float(pil_image.size[0]) * float(h_ratio)))

            return ft.Image(
                src=logo_path,
                width=w_size,
                height=50,
                fit=ft.ImageFit.CONTAIN
            )
        except Exception as e:
            return ft.Container(
                content=ft.Text(
                    value="Audio2Text",
                    size=16, weight=ft.FontWeight.BOLD,
                    color=DesignSystem.COLORS["primary"]
                )
            )

    def _get_led_color(self) -> str:
        """Obtener color del LED según estado de API key."""
        if self.api_key_status == "green":
            return DesignSystem.COLORS["success"]
        elif self.api_key_status == "red":
            return DesignSystem.COLORS["error"]
        else:
            return DesignSystem.COLORS["led_grey"]

    def create_config_tab(self) -> ft.Column:
        """
        Construir pestaña de configuración.

        Returns:
            Column con contenido de la pestaña de configuración
        """
        # API Key section
        api_key_section = ft.Column([
            ft.Text(
                value="Configuración Principal",
                size=16, weight=ft.FontWeight.BOLD, color="#F8FAFC"
            ),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            ft.Row([
                # LED de estado
                ft.Container(
                    content=ft.Text("●", size=24, weight=ft.FontWeight.BOLD),
                    padding=5,
                    bgcolor=self._get_led_color(),
                    border_radius=12
                ),
                ft.Container(width=10),
                ft.TextField(
                    label="API Key de Groq",
                    password=True,
                    can_reveal_password=True,
                    value="gsk_*****",  # Placeholder
                    width=400,
                    on_blur=self.save_config,
                    border_radius=8
                ),
                ft.Container(width=10),
                ft.ElevatedButton(
                    content=ft.Text("Verificar"),
                    width=100,
                    on_click=self.check_api_key
                )
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
        ])

        # Hotkey section
        hotkey_section = ft.Column([
            ft.Text(
                value="Hotkey de Grabación",
                size=16, weight=ft.FontWeight.BOLD, color="#F8FAFC"
            ),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            ft.Row([
                ft.Dropdown(
                    label="",
                    options=[
                        ft.dropdown.Option("f1", "F1"),
                        ft.dropdown.Option("f2", "F2"),
                        ft.dropdown.Option("f3", "F3"),
                        ft.dropdown.Option("f4", "F4"),
                        ft.dropdown.Option("f5", "F5"),
                        ft.dropdown.Option("f6", "F6"),
                        ft.dropdown.Option("f7", "F7"),
                        ft.dropdown.Option("f8", "F8"),
                        ft.dropdown.Option("f9", "F9"),
                        ft.dropdown.Option("f10", "F10"),
                        ft.dropdown.Option("f11", "F11"),
                        ft.dropdown.Option("f12", "F12"),
                    ],
                    width=150,
                    border_radius=8
                ),
                ft.ElevatedButton(
                    content=ft.Text("Grabar Hotkey"),
                    width=150,
                    on_click=self.start_hotkey_recording
                )
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
        ])

        # Recording mode section - usar Radio en lugar de SegmentedButton
        record_mode_section = ft.Column([
            ft.Text(
                value="Modo de Grabación",
                size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE
            ),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            ft.RadioGroup(
                content=ft.Column([
                    ft.Radio(value="toggle", label="Toggle"),
                    ft.Radio(value="hold", label="Mantener Presionado")
                ]),
                value=self.config.get('record_mode', 'toggle'),
                on_change=self.on_record_mode_change
            )
        ])

        # Switches section
        switches_section = ft.Column([
            ft.Switch(
                label="Auto-pegar texto",
                value=self.config.get("auto_paste_text", False),
                on_change=lambda e: self.save_config()
            ),
            ft.Switch(
                label="Mostrar panel de transcripción",
                value=self.config.get("show_transcription_panel", False),
                on_change=self.on_show_panel_change
            ),
        ])

        # Autostart section (sincronizado con estado real)
        actual_autostart = self._check_autostart_status()
        self.autostart_windows_var = actual_autostart
        autostart_section = ft.Column([
            ft.Switch(
                label="Iniciar con Windows",
                value=actual_autostart,
                on_change=lambda e: self.on_autostart_change(e)
            )
        ])

        # Language section
        current_language = self.config.get("language", "es")
        language_section = ft.Column([
            ft.Text(
                value="Idioma",
                size=16, weight=ft.FontWeight.BOLD, color="#F8FAFC"
            ),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            ft.Dropdown(
                label="",
                options=[
                    ft.dropdown.Option("es", "Español"),
                    ft.dropdown.Option("en", "English")
                ],
                value=current_language,
                width=200,
                border_radius=8,
                on_blur=lambda e: self.on_language_change(e)
            )
        ])

        # File management section
        file_management_section = ft.Column([
            ft.Text(
                value="Archivos",
                size=16, weight=ft.FontWeight.BOLD, color="#F8FAFC"
            ),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            # Audio path
            ft.Row([
                ft.ElevatedButton(
                    content=ft.Text("📁"),
                    width=50,
                    on_click=lambda: self._browse_path("audio")
                ),
                ft.TextField(
                    label="Carpeta de Audio",
                    value=self.config.get("audio_path", "./audio"),
                    width=400,
                    read_only=True,
                    border_radius=8
                )
            ], spacing=10),
            # Transcriptions path
            ft.Row([
                ft.ElevatedButton(
                    content=ft.Text("📁"),
                    width=50,
                    on_click=lambda: self._browse_path("transcriptions")
                ),
                ft.TextField(
                    label="Carpeta de Transcripciones",
                    value=self.config.get("transcriptions_path", "./transcriptions"),
                    width=400,
                    read_only=True,
                    border_radius=8
                )
            ], spacing=10),
            # Switches
            ft.Row([
                ft.Switch(
                    label="Guardar audio",
                    value=self.config.get("save_audio", True),
                    on_change=lambda e: self.save_config()
                ),
                ft.Switch(
                    label="Guardar transcripciones",
                    value=self.config.get("save_logs", True),
                    on_change=lambda e: self.save_config()
                )
            ], spacing=20)
        ])

        # Agrupar configuraciones de grabación (hotkey + modo)
        recording_settings = ft.Column([
            ft.Text(
                value="Configuración de Grabación",
                size=14, weight=ft.FontWeight.BOLD, color="#F8FAFC"
            ),
            ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
            hotkey_section,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            record_mode_section,
        ])

        # Agrupar configuraciones generales
        general_settings = ft.Column([
            ft.Text(
                value="Configuración General",
                size=14, weight=ft.FontWeight.BOLD, color="#F8FAFC"
            ),
            ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
            switches_section,
            ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
            autostart_section,
            ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
            language_section,
        ])

        return ft.Column([
            api_key_section,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            recording_settings,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            general_settings,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            file_management_section
        ], scroll=ft.ScrollMode.AUTO, expand=True)

    def create_info_tab(self) -> ft.Column:
        """
        Construir pestaña de información.

        Returns:
            Column con contenido de la pestaña de información
        """
        # Cargar template HTML
        html_content = self._load_info_template()

        if html_content:
            # Usar HTML view
            return ft.Column([
                ft.Markdown(
                    html_content,
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet(
                        code_theme=ft.MarkdownCodeTheme.GITHUB,
                        code_syntax_highlighting=ft.MarkdownCodeSyntaxHighlighting.PYTHON
                    )
                ),
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                ft.Row([
                    ft.ElevatedButton(
                        content=ft.Icon(ft.Icons.VPN_KEY),
                        on_click=lambda: webbrowser.open_new("https://console.groq.com/keys")
                    ),
                    ft.Text(
                        value="Obtener API Key",
                        size=12,
                        color=DesignSystem.COLORS["primary"]
                    )
                ], spacing=10)
            ], scroll=ft.ScrollMode.AUTO, expand=True)
        else:
            # Fallback con texto plano
            info_text = "Audio2Text v0.10.0 - Transcribe audio con IA"
            return ft.Column([
                ft.Text(
                    value=info_text,
                    size=14, color="#F8FAFC"
                ),
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                ft.Row([
                    ft.ElevatedButton(
                        content=ft.Icon(ft.Icons.VPN_KEY),
                        on_click=lambda: webbrowser.open_new("https://console.groq.com/keys")
                    ),
                    ft.Text(
                        value="Obtener API Key",
                        size=12,
                        color=DesignSystem.COLORS["primary"]
                    )
                ], spacing=10)
            ], scroll=ft.ScrollMode.AUTO, expand=True)

    def _load_info_template(self) -> Optional[str]:
        """
        Cargar template HTML de información.

        Returns:
            Contenido HTML o None si no existe
        """
        html_path = "templates/info_template.html"  # ✅ CORREGIDO: agregado "templates/"
        if getattr(sys, 'frozen', False):
            html_path = os.path.join(sys._MEIPASS, "templates/info_template.html")

        if os.path.exists(html_path):
            try:
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                # Reemplazar placeholder de versión
                html_content = html_content.replace("{version}", self.config.get("app_version", "0.10.0"))
                logger.info(f"[INFO_TEMPLATE] Loaded info_template.html successfully")
                return html_content
            except Exception as e:
                logger.error(f"[INFO_TEMPLATE] Error loading info_template.html: {e}")
                return None
        else:
            logger.warning(f"[INFO_TEMPLATE] File not found: {html_path}")
            return None

    def create_history_tab(self) -> ft.Column:
        """
        Construir pestaña de historial.

        Returns:
            Column con contenido de la pestaña de historial
        """
        # Header
        header = ft.Row([
            ft.Text(
                value="Historial de Grabaciones",
                size=16, weight=ft.FontWeight.BOLD, color="#F8FAFC"
            ),
            ft.Container(expand=True),
            ft.ElevatedButton(
                content=ft.Icon(ft.Icons.REFRESH),
                width=60,
                on_click=self.refresh_history
            )
        ], alignment=ft.MainAxisAlignment.CENTER)

        # History list
        history_list = ft.ListView(
            controls=[],
            expand=True,
            spacing=10
        )

        return ft.Column([
            header,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            ft.Container(
                content=history_list,
                border=ft.border.all(2, DesignSystem.COLORS["primary"]),
                border_radius=8,
                padding=10,
                expand=True
            )
        ], scroll=ft.ScrollMode.AUTO, expand=True)

    def create_update_tab(self) -> ft.Container:
        """
        Construir pestaña de actualizaciones - mejorada con más información.

        Returns:
            Container con contenido de la pestaña de actualizaciones
        """
        # Header mejorado con emoji
        header = ft.Row([
            ft.Text(
                value="🔄 Actualizaciones",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE
            ),
        ], alignment=ft.MainAxisAlignment.CENTER)

        # Estado de actualizaciones
        self.update_status_var = ft.Text(
            value="Haz clic en 'Verificar Actualizaciones' para buscar nuevas versiones",
            size=14,
            color=ft.Colors.CBD5E1
        )

        # Información de actualización - structured container
        self.update_info_container = ft.Container(
            content=ft.Column([
                ft.Text(
                    value="Información de la versión aparecerá aquí",
                    size=12,
                    color=ft.Colors.GREY_400,
                    italic=True
                )
            ], spacing=5),
            padding=15,
            bgcolor=ft.Colors.BLUE_GREY_800,
            border_radius=ft.border_radius.all(8),
            visible=False
        )

        # Documentación de uso
        doc_section = ft.Container(
            content=ft.Column([
                ft.Text(
                    value="📖 Instrucciones:",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE
                ),
                ft.Text(
                    value="1. Click en 'Verificar Actualizaciones' para buscar nuevas versiones",
                    size=12,
                    color=ft.Colors.WHITE
                ),
                ft.Text(
                    value="2. Si hay actualización, aparecerá información de versión y changelog",
                    size=12,
                    color=ft.Colors.WHITE
                ),
                ft.Text(
                    value="3. Click en 'Descargar e Instalar' para actualizar automáticamente",
                    size=12,
                    color=ft.Colors.WHITE
                ),
                ft.Text(
                    value="⚠️ La aplicación se cerrará durante la instalación",
                    size=12,
                    color=ft.Colors.AMBER
                )
            ], spacing=5),
            padding=15,
            bgcolor=ft.Colors.BLUE_GREY_800,
            border_radius=ft.border_radius.all(8),
        )

        # Barra de progreso (oculta inicialmente)
        self.update_progress = ft.ProgressBar(
            width=400,
            height=10,
            bgcolor=ft.Colors.BLUE_GREY_800,
            color=ft.Colors.BLUE,
            visible=False
        )

        self.progress_label = ft.Text(
            value="",
            size=12,
            color=ft.Colors.WHITE,
            visible=False
        )

        # Botones de actualización
        button_frame = ft.Row([
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.REFRESH, size=16),
                    ft.Text("Verificar Actualizaciones", color=ft.Colors.WHITE)
                ], spacing=5),
                width=200,
                height=40,
                bgcolor=ft.Colors.BLUE,
                on_click=self.check_updates_flet
            ),
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.DOWNLOAD, size=16),
                    ft.Text("Descargar e Instalar", color=ft.Colors.WHITE)
                ], spacing=5),
                width=200,
                height=40,
                bgcolor=ft.Colors.GREEN,
                disabled=True,
                on_click=self.download_and_install_flet
            )
        ], spacing=10)

        return ft.Container(
            content=ft.Column([
                header,
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                self.update_status_var,
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                self.update_info_container,
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                doc_section,
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                self.progress_label,
                self.update_progress,
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                button_frame
            ], scroll=ft.ScrollMode.AUTO, expand=True),
            padding=20,
            expand=True
        )

    # --- Callback methods ---

    def clear_audio_with_feedback(self, e):
        """Limpiar archivos de audio con feedback."""
        def _clear():
            if self.file_manager.clear_audio_files():
                self.update_status("Audio eliminado", "green")
            else:
                self.update_status("Error al eliminar audio", "red")
            self.update_file_info()
            self.refresh_history(e)

        _clear()

    def clear_logs_with_feedback(self, e):
        """Limpiar transcripciones con feedback."""
        def _clear():
            if self.file_manager.clear_transcriptions():
                self.update_status("Transcripciones eliminadas", "green")
            else:
                self.update_status("Error al eliminar transcripciones", "red")
            self.update_file_info()
            self.refresh_history(e)

        _clear()

    def refresh_history(self, e):
        """Refrescar historial."""
        def _refresh():
            self.update_file_info()
            self._load_history_list()

        _refresh()

    def _load_history_list(self):
        """Cargar lista de historial."""
        def _load():
            # Clear existing items
            self.history_items = []

            audio_path = self.config.get("audio_path")
            if not os.path.exists(audio_path):
                self.history_items.append(
                    ft.ListTile(
                        title=ft.Text(
                            value="Directorio no encontrado",
                            color=ft.Colors.RED
                        )
                    )
                )
            else:
                files = [f for f in os.listdir(audio_path) if f.endswith(".wav")]
                files.sort(key=lambda x: os.path.getmtime(os.path.join(audio_path, x)), reverse=True)

                if not files:
                    self.history_items.append(
                        ft.ListTile(
                            title=ft.Text(
                                value="No hay archivos de audio",
                                size=14, color="#F8FAFC"
                            )
                        )
                    )
                else:
                    for f in files:
                        full_path = os.path.join(audio_path, f)

                        # Obtener emoji personalizado (si existe)
                        custom_emoji = self.metadata_manager.get_emoji(f, default="🎤")

                        # Formatear nombre con emoji
                        display_name = f"{custom_emoji} {f}"

                        self.history_items.append(
                            ft.ListTile(
                                title=ft.Text(
                                    value=display_name,
                                    size=14, color="#F8FAFC",
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS
                                ),
                                leading=ft.Icon(ft.Icons.EMOJI_EMOTIONS),  # Icono de emoji
                                trailing=ft.Row([
                                    ft.TextButton(
                                        "Cambiar Emoji",
                                        icon=ft.Icons.EDIT,
                                        on_click=lambda filename=f: self._change_emoji_flet(filename),
                                        style=ft.ButtonStyle(
                                            bgcolor="#8B5CF6",
                                            color="#FFFFFF"
                                        )
                                    ),
                                    ft.ElevatedButton(
                                        content=ft.Text(
                                            value="Transcribir",
                                            size=12, color="#CBD5E1"
                                        ),
                                        on_click=lambda: self.start_retranscription(full_path),
                                        width=80
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        icon_color=ft.Colors.RED_500,
                                        on_click=lambda: self.delete_audio_file(full_path),
                                        width=40
                                    )
                                ], spacing=10)
                            )
                        )

        _load()

    def _change_emoji_flet(self, filename: str):
        """
        Cambiar emoji de una transcripción (versión Flet).

        Args:
            filename: Nombre del archivo de audio
        """
        # Mostrar diálogo simple para elegir emoji
        # Nota: Flet no tiene emoji picker nativo, usamos un dropdown con emojis comunes
        emojis_comunes = {
            "🎤 Micrófono": "🎤",
            "💡 Idea": "💡",
            "📞 Llamada": "📞",
            "✅ Tarea": "✅",
            "🎯 Objetivo": "🎯",
            "📅 Reunión": "📅",
            "📝 Nota": "📝",
            "💼 Trabajo": "💼",
            "🔧 Técnico": "🔧",
            "⭐ Favorito": "⭐",
        }

        def on_emoji_selected(e, selected_emoji):
            """Guardar emoji seleccionado."""
            self.metadata_manager.set_emoji(filename, selected_emoji)
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Emoji cambiado a {selected_emoji}"))
            self.page.snack_bar.open = True
            # Recargar historial
            self._load_history_list()
            # Cerrar diálogo
            self.page.dialog.open = False

        # Crear dropdown de emojis
        emoji_dropdown = ft.Dropdown(
            label="Seleccionar Emoji",
            options=[ft.dropdown.Option(key=k, text=f"{k} {v}") for k, v in emojis_comunes.items()],
            width=300,
        )

        def confirmar(e):
            if emoji_dropdown.value:
                # Extraer emoji del valor seleccionado
                selected_key = emoji_dropdown.value
                selected_emoji = emojis_comunes[selected_key]
                on_emoji_selected(e, selected_emoji)

        # Crear diálogo
        self.page.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Cambiar Emoji"),
            content=ft.Column([
                ft.Text("Seleccioná un emoji para esta transcripción:"),
                emoji_dropdown,
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._close_dialog(e)),
                ft.TextButton("Confirmar", on_click=confirmar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog.open = True
        self.page.update()

    def _close_dialog(self, e):
        """Cerrar diálogo."""
        self.page.dialog.open = False
        self.page.update()

    def start_retranscription(self, file_path: str):
        """
        Iniciar retranscripción de archivo.

        Args:
            file_path: Ruta del archivo a transcribir
        """
        def _start():
            self.update_status("Retranscribiendo...", "yellow")
            threading.Thread(target=self._retranscribe_thread, args=(file_path,), daemon=True).start()

        _start()

    def _retranscribe_thread(self, file_path: str):
        """Thread de retranscripción."""
        try:
            import logging
            logger = logging.getLogger(self.__class__.__name__)
            logger.info(f"Retranscribiendo archivo: {file_path}")
            text = self.transcriber.transcribe_with_groq(file_path)
            if text:
                self.on_transcription_complete(text)
                self.update_status("Transcripción completada", "green")
                self.sound_manager.sound_success()
            else:
                self.update_status("Transcripción fallida", "red")
        except Exception as e:
            logger.error(f"Error en retranscripción: {e}")
            self.update_status(f"Error: {e}", "red")

    def delete_audio_file(self, file_path: str):
        """
        Eliminar archivo de audio.

        Args:
            file_path: Ruta del archivo a eliminar
        """
        def _delete():
            try:
                os.remove(file_path)
                self.refresh_history(None)
                self.update_file_info()
            except Exception as e:
                pass  # Silencioso

        _delete()

    def check_api_key(self, e):
        """Verificar API key."""
        def _check():
            self.update_status("Verificando API key...", "yellow")

            # Simular verificación (en producción, llamar a Groq API)
            self._complete_api_check(True)

        _check()

    def _complete_api_check(self, success: bool):
        """Completar verificación de API key."""
        def _complete():
            if success:
                self.api_key_status = "green"
                self.update_status("API key válida", "green")
            else:
                self.api_key_status = "red"
                self.update_status("API key inválida", "red")

        _complete()

    def start_hotkey_recording(self, e):
        """Iniciar grabación de hotkey - diálogo modal."""
        logger.debug("[HOTKEY_RECORD] Opening hotkey recording dialog")

        # Crear diálogo modal
        def open_dialog():
            dlg = ft.AlertDialog(
                modal=True,
                title=self.localization.get_string("recording_hotkey_title"),
                content=ft.Text(
                    self.localization.get_string("recording_hotkey_prompt"),
                    size=14
                ),
                actions=[
                    ft.TextButton(
                        text="Cancelar",
                        on_click=lambda _: self.close_hotkey_dialog(dlg)
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            self.page.dialog = dlg
            dlg.open = True
            self.page.update()

            # Iniciar thread para detectar hotkey después de que el diálogo se abra
            import threading
            threading.Thread(
                target=self._record_hotkey_thread,
                args=(dlg,),
                daemon=True
            ).start()

        open_dialog()

    def _record_hotkey_thread(self, dialog):
        """Thread para grabar hotkey sin bloquear la UI."""
        try:
            import keyboard
            logger.debug("[HOTKEY_RECORD] Waiting for hotkey input...")

            # Esperar a que usuario presione una tecla
            hotkey = keyboard.read_hotkey(suppress=False)
            logger.debug(f"[HOTKEY_RECORD] Hotkey detected: {hotkey}")

            # Validar que sea F1-F12
            valid_hotkeys = [f"F{i}" for i in range(1, 13)]
            hotkey_upper = hotkey.upper()

            if hotkey_upper in valid_hotkeys:
                # Guardar en hotkey_var
                if self.hotkey_var:
                    self.hotkey_var.set(hotkey_upper)
                    logger.info(f"[HOTKEY_RECORD] New hotkey set: {hotkey_upper}")

                    # Guardar config
                    self.save_config_flet(None)

                    # Actualizar display
                    if self.hotkey_display:
                        self.hotkey_display.value = self.localization.get_string("hotkey_display", hotkey=hotkey_upper)
                        self.page.update()

                    # Cerrar diálogo
                    self.close_hotkey_dialog(dialog)

                    # Mostrar confirmación
                    self.update_status(f"Hotkey cambiado a {hotkey_upper}", "green")
                else:
                    logger.error("[HOTKEY_RECORD] hotkey_var is None")
                    self.update_status("Error: hotkey_var not initialized", "red")
                    self.close_hotkey_dialog(dialog)
            else:
                logger.warning(f"[HOTKEY_RECORD] Invalid hotkey: {hotkey_upper}")
                self.update_status(f"Hotkey inválido. Usa F1-F12.", "red")
                # No cerrar diálogo, dejar que intente de nuevo

        except Exception as ex:
            logger.error(f"[HOTKEY_RECORD] Error recording hotkey: {ex}")
            self.update_status(f"Error grabando hotkey: {str(ex)}", "red")
            self.close_hotkey_dialog(dialog)

    def close_hotkey_dialog(self, dialog):
        """Cerrar diálogo de hotkey de forma thread-safe."""
        def _close():
            try:
                dialog.open = False
                self.page.update()
            except Exception as e:
                logger.error(f"[HOTKEY_RECORD] Error closing dialog: {e}")

        if self.page:
            self.page.update(_close)

    def on_record_mode_change(self, e):
        """Manejar cambio de modo de grabación."""
        # TODO: Implementar
        pass

    def on_show_panel_change(self, e):
        """Manejar cambio de show panel - recrea tab Principal si es necesario."""
        logger.debug(f"[SHOW_PANEL_CHANGE] Switch changed, value: {e.data}")

        def _update():
            # Guardar nueva configuración
            show_panel = self.show_panel_var.value if hasattr(self.show_panel_var, 'value') else self.show_panel_var
            self.config.set("show_transcription_panel", show_panel)
            logger.info(f"[SHOW_PANEL_CHANGE] show_transcription_panel set to: {show_panel}")

            # Si estamos en el tab Principal, recargar para mostrar/ocultar panel
            if self.current_tab_index == 0:  # Tab Principal
                logger.debug("[SHOW_PANEL_CHANGE] Recreating Main tab to update transcription panel")
                self.content_container.content = self.create_main_tab()
                self.page.update()
                self.update_status(f"Panel de transcripción {'visible' if show_panel else 'oculto'}", "green")

        _update()

    def on_autostart_change(self, e):
        """Manejar cambio de autostart."""
        def _toggle():
            from backend.startup_manager import StartupManager
            startup_manager = StartupManager()
            success = startup_manager.toggle(self.autostart_windows_var)
            if not success:
                self.update_status(f"Error al configurar inicio automático", "red")
            else:
                self.autostart_windows_var = startup_manager.is_enabled()

        _toggle()

    def _check_autostart_status(self) -> bool:
        """
        Verificar estado real de autostart.

        Returns:
            Estado de autostart
        """
        try:
            from backend.startup_manager import StartupManager
            startup_manager = StartupManager()
            return startup_manager.is_enabled()
        except:
            return False

    def on_language_change(self, e):
        """Manejar cambio de idioma."""
        def _change():
            old_lang = self.config.get("default_language")
            new_lang = e.control.value

            if old_lang != new_lang:
                self.config.set("default_language", new_lang)
                self.config_manager.set_language(new_lang)

                # Recrear UI
                self.page.go(-1)

        _change()

    def _browse_path(self, path_type: str):
        """
        Navegar por ruta.

        Args:
            path_type: Tipo de ruta ("audio" o "transcriptions")
        """
        def _browse():
            try:
                # En Flet, usamos FilePicker
                if path_type == "audio":
                    initial_dir = self.config.get("audio_path", "./audio")
                else:
                    initial_dir = self.config.get("transcriptions_path", "./transcriptions")

                # En Windows, usamos openfiledialog
                import tkinter as tk
                from tkinter import filedialog

                root = tk.Tk()
                root.withdraw()
                folder_selected = filedialog.askdirectory(
                    initialdir=initial_dir if os.path.exists(initial_dir) else os.getcwd()
                )
                root.destroy()

                if folder_selected:
                    if path_type == "audio":
                        self.config.set("audio_path", folder_selected)
                    else:
                        self.config.set("transcriptions_path", folder_selected)
                    self.update_file_info()

            except Exception as e:
                pass  # Silencioso

        _browse()

    def save_config(self, e=None):
        """Guardar configuración."""
        def _save():
            self.update_status("Guardando configuración...", "yellow")

            old_lang = self.config.get("default_language")
            old_show_panel = self.config.get("show_transcription_panel")

            settings = {
                "groq_api_key": self.api_key_var.get() if self.api_key_var else self.config.get("groq_api_key"),
                "hotkey": self.hotkey_var.get() if self.hotkey_var else self.config.get("hotkey"),
                "record_mode": self.record_mode_var.get() if self.record_mode_var else self.config.get("record_mode"),
                "auto_paste_text": self.auto_paste_var.get() if self.auto_paste_var else self.config.get("auto_paste_text"),
                "show_transcription_panel": self.show_panel_var.get() if self.show_panel_var else self.config.get("show_transcription_panel"),
                "audio_path": self.audio_path_var.get() if self.audio_path_var else self.config.get("audio_path"),
                "transcriptions_path": self.transcriptions_path_var.get() if self.transcriptions_path_var else self.config.get("transcriptions_path"),
                "save_audio": self.save_audio_var.get() if self.save_audio_var else self.config.get("save_audio"),
                "save_logs": self.save_logs_var.get() if self.save_logs_var else self.config.get("save_logs"),
                "max_audio_files": int(self.config.get("max_audio_files")),
                "max_log_entries": int(self.config.get("max_log_entries")),
                "audio_priority_apps": self.config.get("audio_priority_apps"),
                "default_language": self.language_var.get() if self.language_var else self.config.get("default_language"),
                "autostart_windows": self.autostart_windows_var,
                "use_post_processing": self.config.get("use_post_processing", True),
                "use_llm_post_processing": self.config.get("use_llm_post_processing", True),
                "post_processing_model": self.config.get("post_processing_model", "llama-3.3-70b-versatile")
            }

            self.config.set_multiple(settings)

            # Sincronizar autostart con estado real del sistema
            from backend.startup_manager import StartupManager
            startup_manager = StartupManager()
            actual_autostart = startup_manager.is_enabled()
            self.config.set("autostart_windows", actual_autostart)

            # Check for language change
            if self.language_var.get() if self.language_var else settings["default_language"] != old_lang:
                self.config_manager.set_language(settings["default_language"])

            # Verify hotkey change
            if self.transcriber:
                if settings["hotkey"] != self.transcriber.hotkey:
                    self.transcriber.update_hotkey(settings["hotkey"])

            # Verify show panel change
            if settings["show_transcription_panel"] != old_show_panel:
                self.page.go(-1)  # Recargar UI

            # API Key logic fix
            if settings["groq_api_key"]:
                os.environ["GROQ_API_KEY"] = settings["groq_api_key"]
                self.transcriber.reload_client()

            self.update_status("Configuración guardada", "green")

        _save()

    def check_updates_flet(self, e):
        """Verificar actualizaciones disponibles."""
        def _check():
            if hasattr(self, 'update_status_var'):
                self.update_status_var.value = "Verificando actualizaciones..."
                self.page.update()

            if not self.updater:
                if hasattr(self, 'update_status_var'):
                    self.update_status_var.value = "❌ Error: Updater no disponible"
                    self.page.update()
                return

            # Verificar actualizaciones en thread
            import threading
            def check_thread():
                try:
                    update_info = self.updater.check_for_updates()

                    if "error" in update_info:
                        if hasattr(self, 'update_status_var'):
                            self.update_status_var.value = f"❌ Error: {update_info['error']}"
                            self.update_status_var.color = ft.Colors.RED
                        self.page.update()
                    elif update_info.get("available"):
                        if hasattr(self, 'update_status_var'):
                            self.update_status_var.value = f"✨ Nueva versión disponible: v{update_info['version']}"
                            self.update_status_var.color = ft.Colors.GREEN
                        # Mostrar información estructurada en container
                        if hasattr(self, 'update_info_container'):
                            version = update_info.get('version', '?')
                            changelog = update_info.get('changelog', 'No hay changelog disponible')
                            release_date = update_info.get('release_date', 'Desconocida')

                            self.update_info_container.content = ft.Column([
                                ft.Text(
                                    value=f"Versión: {version}",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE
                                ),
                                ft.Text(
                                    value=f"Fecha: {release_date}",
                                    size=12,
                                    color=ft.Colors.CBD5E1
                                ),
                                ft.Divider(height=2, color=ft.Colors.BLUE_GREY_700),
                                ft.Text(
                                    value="Novedades:",
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.BLUE
                                ),
                                ft.Text(
                                    value=changelog,
                                    size=12,
                                    color=ft.Colors.WHITE
                                )
                            ], spacing=5)
                            self.update_info_container.visible = True
                            self.page.update()
                    else:
                        if hasattr(self, 'update_status_var'):
                            self.update_status_var.value = "✅ Estás usando la última versión"
                            self.update_status_var.color = ft.Colors.GREEN
                        if hasattr(self, 'update_info_container'):
                            self.update_info_container.visible = False
                        self.page.update()

                except Exception as ex:
                    logger.error(f"Error checking updates: {ex}")
                    if hasattr(self, 'update_status_var'):
                        self.update_status_var.value = f"❌ Error: {str(ex)}"
                        self.update_status_var.color = ft.Colors.RED
                    self.page.update()

            thread = threading.Thread(target=check_thread, daemon=True)
            thread.start()

        _check()

    def download_and_install_flet(self, e):
        """Descargar e instalar actualización."""
        # TODO: Implementar descarga e instalación
        if hasattr(self, 'update_status_var'):
            self.update_status_var.value = "⚠️ Función de descarga no implementada aún"
            self.update_status_var.color = ft.Colors.YELLOW
            self.page.update()

    def update_file_info(self, e=None):
        """Actualizar información de archivos."""
        def _update():
            try:
                audio_size_mb = self.file_manager.get_audio_files_size() / (1024 * 1024)
                num_files = len([f for f in os.listdir(self.file_manager.audio_path) if f.endswith('.wav')])
                audio_info = f"{audio_size_mb:.2f} MB ({num_files} archivos)"
            except:
                audio_info = "N/A"

            try:
                log_size_kb = self.file_manager.get_transcriptions_size() / 1024
                log_info = f"{log_size_kb:.2f} KB"
            except:
                log_info = "N/A"

        _update()

    def on_tab_change(self, e):
        """Manejar cambio de pestaña."""
        logger.debug(f"[ON_TAB_CHANGE] Tab changed to index: {e.control.selected_index}")
        self.current_tab_index = e.control.selected_index

        # Actualizar contenido según pestaña seleccionada
        if self.current_tab_index == 0:  # Principal
            self.tabs_container.content = ft.Column([self.create_main_tab()])
            self.update_status("Listo para grabar", "#F8FAFC")
        elif self.current_tab_index == 1:  # Configuración
            self.tabs_container.content = ft.Column([self.create_config_tab()])
        elif self.current_tab_index == 2:  # Info
            self.tabs_container.content = ft.Column([self.create_info_tab()])
        elif self.current_tab_index == 3:  # Historial
            self.tabs_container.content = ft.Column([self.create_history_tab()])
            self._start_auto_refresh_history()
        elif self.current_tab_index == 4:  # Actualizaciones
            self.tabs_container.content = ft.Column([self.create_update_tab()])

        # Actualizar la página
        logger.debug(f"[ON_TAB_CHANGE] Updating page with new tab content")
        self.page.update()

    def _start_auto_refresh_history(self):
        """Iniciar auto-refresh de historial."""
        if self.current_tab_index == 3:
            self.update_file_info()
            self._load_history_list()

    def _on_tab_change_flet(self, e):
        """Manejar cambio de pestaña con ft.Tabs."""
        logger.debug(f"[ON_TAB_CHANGE_FLET] Tab changed to index: {e}")
        self.current_tab_index = e

        # Actualizar estado según pestaña seleccionada
        if self.current_tab_index == 0:  # Principal
            self.update_status("Listo para grabar", "#F8FAFC")
        elif self.current_tab_index == 3:  # Historial
            self._start_auto_refresh_history()

        # Actualizar la página
        logger.debug(f"[ON_TAB_CHANGE_FLET] Updating page")
        self.page.update()

    def _on_tab_click(self, index: int):
        """Manejar click en botón de tab (implementación manual)."""
        logger.debug(f"[ON_TAB_CLICK] Tab clicked: {index}")
        old_index = self.current_tab_index
        self.current_tab_index = index

        # Actualizar estilos de botones
        for i, btn in enumerate(self.tab_buttons):
            if i == index:
                btn.bgcolor = ft.Colors.BLUE_GREY_700
                btn.style = ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.BLUE_GREY_700
                )
            else:
                btn.bgcolor = ft.Colors.BLUE_GREY_800
                btn.style = ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.BLUE_GREY_800
                )

        # Actualizar contenido según pestaña
        if index == 0:
            self.content_container.content = self.create_main_tab()
            self.update_status("Listo para grabar", "#F8FAFC")
        elif index == 1:
            self.content_container.content = self.create_config_tab()
        elif index == 2:
            self.content_container.content = self.create_info_tab()
        elif index == 3:
            self.content_container.content = self.create_history_tab()
            self._start_auto_refresh_history()
        elif index == 4:
            self.content_container.content = self.create_update_tab()

        # Actualizar la página
        self.page.update()
        logger.debug(f"[ON_TAB_CLICK] Tab changed from {old_index} to {index}")

    def build(self):
        """
        Construir la app principal.

        Returns:
            Contenido principal de la app
        """
        logger.debug("[BUILD] Starting build() method")

        self.status_var = ft.Text(
            value="Listo para grabar",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE
        )

        # Tab buttons container - horizontal como CustomTkinter
        self.tab_buttons = []
        tab_names = ["Principal", "Configuración", "Info", "Historial", "Actualizaciones"]

        for i, name in enumerate(tab_names):
            btn = ft.ElevatedButton(
                content=ft.Text(name),
                width=180,  # Aumentado de 100 a 180 para "Configuración"
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.BLUE_GREY_700 if i == 0 else ft.Colors.BLUE_GREY_800,
                    color=ft.Colors.WHITE
                ),
                on_click=lambda e, idx=i: self._on_tab_click(idx)
            )
            self.tab_buttons.append(btn)

        tabs_row = ft.Row(
            self.tab_buttons,
            spacing=0,
            alignment=ft.MainAxisAlignment.START
        )

        # Content container - muestra contenido según tab seleccionado
        self.content_container = ft.Container(
            content=self.create_main_tab(),
            padding=10,
            expand=True,
            bgcolor=ft.Colors.BLUE_GREY_900
        )

        logger.debug("[BUILD] Created manual horizontal tabs like CustomTkinter")

        # Layout principal - vertical (Tabs arriba + contenido abajo)
        main_content = ft.Column(
            [
                tabs_row,
                ft.Divider(height=1, color=ft.Colors.BLUE_GREY_700),
                self.content_container
            ],
            expand=True
        )

        # Bottom frame con link a CENF - más compacto
        bottom_frame = ft.Container(
            content=ft.Row([
                ft.Container(expand=True),
                ft.Text(
                    "Audio2Text CENF",
                    size=11,
                    color=ft.Colors.BLUE
                )
            ]),
            padding=5,
            bgcolor=ft.Colors.BLUE_GREY_800
        )

        return ft.Column([
            main_content,
            bottom_frame
        ], expand=True)

    def main(self, page: ft.Page):
        """
        Punto de entrada de la app.

        Args:
            page: Página de Flet
        """
        self.page = page

        # Configurar página - tamaño compacto según feedback de usuario
        page.title = f"Audio2Text v{self.config.get('app_version', '0.10.0')}"
        page.theme_mode = ft.ThemeMode.DARK
        page.window_width = 350  # Reducido de 500 (más compacto)
        page.window_height = 450  # Aumentado de 400 (más alto para contenido)
        # Eliminados max_width/max_height para permitir expansión si usuario desea
        page.window_min_width = 300  # Reducido de 400
        page.window_min_height = 400  # Aumentado de 350
        page.bgcolor = ft.Colors.BLUE_GREY_900
        page.theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE)
        page.window_centered = True
        page.resizable = True  # Cambiado de False a True (permitir redimensionar)

        # Icono de la ventana
        try:
            icon_path = "icon.ico"
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, "icon.ico")

            if os.path.exists(icon_path):
                page.window_icon = icon_path
        except:
            pass

        # Inicializar transcriber
        self.init_transcriber()

        # Inicializar updater
        self.init_updater()

        # Iniciar tutorial si corresponde
        # TODO: Implementar tutorial

        # Construir contenido
        page.add(self.build())
        page.update()

        # Auto-check API key (disabled for now, requires event object)
        # self.check_api_key(None)


def main():
    """Punto de entrada."""
    app = Audio2TextApp()
    ft.app(target=app.main)


if __name__ == "__main__":
    main()
