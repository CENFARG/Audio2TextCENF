"""
History Tab Component for Audio2Text Flet UI.

Manages transcription history display and operations.
"""

import os
import sys
import threading
import logging
import flet as ft
from typing import Optional, List, Callable
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.transcription_metadata import TranscriptionMetadata

logger = logging.getLogger(__name__)


class HistoryTab:
    """Componente de pestaña Historial."""

    def __init__(self, page, config, metadata_manager, on_refresh_callback: Callable = None):
        """
        Inicializar componente de historial.

        Args:
            page: Página Flet principal
            config: ConfigManager instance
            metadata_manager: TranscriptionMetadata instance
            on_refresh_callback: Callback cuando se actualiza historial
        """
        self.page = page
        self.config = config
        self.metadata_manager = metadata_manager
        self.on_refresh_callback = on_refresh_callback

        # Estado
        self.history_items: List[ft.ListTile] = []

    def create(self) -> ft.Column:
        """
        Crear pestaña de historial.

        Returns:
            Column con el contenido del historial
        """
        # Header con título y botón refresh
        header = ft.Row([
            ft.Text(
                "Historial de Transcripciones",
                size=20,
                weight=ft.FontWeight.BOLD,
                color="#F8FAFC"
            ),
            ft.IconButton(
                icon=ft.Icons.REFRESH,
                icon_color="#CBD5E1",
                tooltip="Actualizar historial",
                on_click=self.refresh_history
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # Lista de historial
        history_list = ft.ListView(
            controls=self.history_items,
            expand=True,
            spacing=5,
        )

        # Contenedor scrollable
        scroll_container = ft.Container(
            content=ft.Column([
                header,
                ft.Divider(color="#334155", height=1),
                ft.Container(
                    content=history_list,
                    expand=True,
                )
            ], expand=True),
            expand=True,
        )

        return ft.Column([scroll_container], expand=True)

    def refresh_history(self, e=None):
        """Actualizar lista de historial."""
        self._load_history_list()
        if self.on_refresh_callback:
            self.on_refresh_callback()

    def _load_history_list(self):
        """Cargar lista de historial."""
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
                    self.history_items.append(
                        self._create_history_item(f, full_path)
                    )

        # Update page if available
        if hasattr(self.page, 'update'):
            self.page.update()

    def _create_history_item(self, filename: str, full_path: str) -> ft.ListTile:
        """
        Crear item de historial con emoji personalizable.

        Args:
            filename: Nombre del archivo
            full_path: Ruta completa del archivo

        Returns:
            ListTile con el item formateado
        """
        # Obtener display name (emoji + custom title o fecha)
        display_name = self.metadata_manager.get_display_name(filename)

        # Obtener metadata para tooltip
        auto_metadata = self.metadata_manager.get_auto_metadata(filename)

        # Construir tooltip con metadata automática
        tooltip_lines = [f"📁 {filename}"]
        if auto_metadata:
            if "summary" in auto_metadata:
                tooltip_lines.append(f"📝 {auto_metadata['summary']}")
            if "category" in auto_metadata:
                tooltip_lines.append(f"📂 {auto_metadata['category']}")
            if "tags" in auto_metadata and auto_metadata["tags"]:
                tooltip_lines.append(f"🏷️ {', '.join(auto_metadata['tags'][:3])}")

        tooltip_text = "\n".join(tooltip_lines)

        return ft.ListTile(
            title=ft.Text(
                value=display_name,
                size=14, color="#F8FAFC",
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
                tooltip=tooltip_text
            ),
            leading=ft.Icon(ft.Icons.EMOJI_EMOTIONS),
            trailing=ft.Row([
                ft.TextButton(
                    "🎯",
                    tooltip="Cambiar emoji/título",
                    on_click=lambda _: self._rename_transcription(filename),
                    style=ft.ButtonStyle(bgcolor="#8B5CF6", color="#FFFFFF")
                ),
                ft.ElevatedButton(
                    content=ft.Text(
                        value="Transcribir",
                        size=12, color="#CBD5E1"
                    ),
                    on_click=lambda _: self.start_retranscription(full_path),
                    width=80
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_color=ft.Colors.RED_500,
                    tooltip="Eliminar",
                    on_click=lambda _: self.delete_audio_file(full_path)
                )
            ], spacing=10)
        )

    def _rename_transcription(self, filename: str):
        """
        Diálogo para renombrar transcripción (emoji + título).

        Args:
            filename: Nombre del archivo
        """
        # Obtener valores actuales
        current_emoji = self.metadata_manager.get_emoji(filename, default="🎤")
        current_title = self.metadata_manager.get_title(filename, default="")

        # Emojis comunes
        emojis = ["🎤", "💡", "📞", "✅", "🎯", "📅", "📝", "💼", "🔧", "⭐"]

        def confirmar(e):
            """Confirmar cambios."""
            new_emoji = emoji_dropdown.value
            new_title = title_field.value

            if new_emoji:
                self.metadata_manager.set_emoji(filename, new_emoji)
            if new_title:
                self.metadata_manager.set_title(filename, new_title)

            self.page.snack_bar = ft.SnackBar(
                ft.Text("✅ Transcripción renombrada")
            )
            self.page.snack_bar.open = True
            self.page.update()

            # Cerrar diálogo y recargar
            self.page.dialog.open = False
            self._load_history_list()

        # Crear diálogo
        emoji_dropdown = ft.Dropdown(
            label="Emoji",
            options=[ft.dropdown.Option(text=emoji, key=emoji) for emoji in emojis],
            value=current_emoji,
            width=100,
        )

        title_field = ft.TextField(
            label="Título personalizado",
            value=current_title,
            hint_text="Ej: Reunión con equipo",
            width=300,
        )

        self.page.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Renombrar: {filename}"),
            content=ft.Column([
                ft.Row([emoji_dropdown, title_field], spacing=10),
                ft.Text(
                    "Dejá el título vacío para usar la fecha automática.",
                    size=11, color="#94A3B8"
                )
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._close_dialog()),
                ft.TextButton("Confirmar", on_click=confirmar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog.open = True
        self.page.update()

    def _close_dialog(self):
        """Cerrar diálogo."""
        self.page.dialog.open = False
        self.page.update()

    def start_retranscription(self, file_path: str):
        """
        Iniciar retranscripción de archivo.

        Args:
            file_path: Ruta del archivo
        """
        def _start():
            self.page.update_status("Retranscribiendo...", "yellow")
            # TODO: Implementar retranscripción
            threading.Thread(
                target=self._retranscribe_thread,
                args=(file_path,),
                daemon=True
            ).start()

        _start()

    def _retranscribe_thread(self, file_path: str):
        """Thread de retranscripción."""
        # TODO: Implementar lógica de retranscripción
        logger.info(f"Retranscribiendo: {file_path}")

    def delete_audio_file(self, file_path: str):
        """
        Eliminar archivo de audio.

        Args:
            file_path: Ruta del archivo
        """
        def _delete():
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)

                    # Eliminar metadata también
                    filename = os.path.basename(file_path)
                    self.metadata_manager.delete_metadata(filename)

                    self.page.snack_bar = ft.SnackBar(
                        ft.Text("✅ Archivo eliminado")
                    )
                    self.page.snack_bar.open = True
                    self.page.update()

                    # Recargar historial
                    self._load_history_list()
            except Exception as e:
                logger.error(f"Error eliminando archivo: {e}")
                self.page.snack_bar = ft.SnackBar(
                    ft.Text(f"❌ Error: {e}")
                )
                self.page.snack_bar.open = True
                self.page.update()

        _delete()
