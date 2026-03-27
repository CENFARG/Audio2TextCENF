"""
Componente de Overlay de Grabación para Audio2Text en Flet.

Muestra un overlay flotante mientras se graba audio.

Author: Audio2Text Team
Version: 0.10.0
"""

import flet as ft


class RecordingOverlay:
    """
    Overlay de grabación flotante.

    Muestra estado de grabación y timer en tiempo real.
    """

    def __init__(self):
        """Inicializar overlay."""
        self.visible = False
        self.status = "ready"  # ready, recording, processing, error
        self.minutes = 0
        self.seconds = 0
        self.overlay_container = None

    def build(self) -> ft.Container:
        """
        Construir el overlay.

        Returns:
            Container con el overlay
        """
        # LED indicador de estado
        status_colors = {
            "ready": ft.colors.GREEN,
            "recording": ft.colors.RED,
            "processing": ft.colors.AMBER,
            "error": ft.colors.RED
        }

        status_icons = {
            "ready": ft.icons.CIRCLE,
            "recording": ft.icons.PAUSE_CIRCLE_FILLED,
            "processing": ft.icons.HOURGLASS_EMPTY,
            "error": ft.icons.ERROR
        }

        status_labels = {
            "ready": "Listo",
            "recording": "Grabando",
            "processing": "Procesando",
            "error": "Error"
        }

        # Contenido del overlay
        overlay_content = ft.Container(
            content=ft.Row([
                # LED indicador
                ft.Icon(
                    name=status_icons.get(self.status, ft.icons.CIRCLE),
                    color=status_colors.get(self.status, ft.colors.GREEN),
                    size=24
                ),
                # Timer y estado
                ft.Column([
                    ft.Text(
                        value=status_labels.get(self.status, "Listo"),
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.WHITE
                    ),
                    ft.Text(
                        value=f"{self.minutes:02d}:{self.seconds:02d}",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.WHITE
                    )
                ], spacing=5)
            ], spacing=15),
            padding=20,
            bgcolor=ft.colors.with_opacity(status_colors.get(self.status, ft.colors.GREEN), 0.9),
            border_radius=12,
            shadow=ft.BoxShadow(
                blur_radius=20,
                spread_radius=2,
                color=ft.colors.with_opacity(ft.colors.BLACK, 0.5)
            )
        )

        # Container del overlay (posicionado absoluto)
        self.overlay_container = ft.Container(
            content=overlay_content,
            visible=self.visible,
            alignment=ft.alignment.center,
            bgcolor=ft.colors.with_opacity(ft.colors.BLACK, 0.5),
            expand=True
        )

        return self.overlay_container

    def show(self, status: str = "ready"):
        """
        Mostrar overlay.

        Args:
            status: Estado del overlay (ready, recording, processing, error)
        """
        self.status = status
        self.visible = True

        if self.overlay_container:
            self.overlay_container.visible = True
            self.update_content()

    def hide(self):
        """Ocultar overlay."""
        self.visible = False
        self.reset_timer()

        if self.overlay_container:
            self.overlay_container.visible = False

    def update_content(self):
        """Actualizar contenido del overlay."""
        if not self.overlay_container:
            return

        # Re-construir overlay con nuevo contenido
        new_content = self.build().content.content
        self.overlay_container.content.content = new_content.content

    def set_recording(self, minutes: int, seconds: int):
        """
        Actualizar timer de grabación.

        Args:
            minutes: Minutos transcurridos
            seconds: Segundos transcurridos
        """
        self.status = "recording"
        self.minutes = minutes
        self.seconds = seconds

        if self.overlay_container:
            self.update_content()

    def set_processing(self):
        """Establecer estado de procesamiento."""
        self.status = "processing"

        if self.overlay_container:
            self.update_content()

    def set_ready(self):
        """Establecer estado listo."""
        self.status = "ready"
        self.reset_timer()

        if self.overlay_container:
            self.update_content()

    def set_error(self):
        """Establecer estado de error."""
        self.status = "error"

        if self.overlay_container:
            self.update_content()

    def reset_timer(self):
        """Reiniciar timer."""
        self.minutes = 0
        self.seconds = 0

    def toggle(self):
        """Toggle visibilidad del overlay."""
        if self.visible:
            self.hide()
        else:
            self.show("ready")


def create_recording_overlay() -> RecordingOverlay:
    """
    Crear instancia de RecordingOverlay.

    Returns:
        Instancia de RecordingOverlay
    """
    return RecordingOverlay()


# Ejemplo de uso
if __name__ == "__main__":
    import flet as ft

    def main(page: ft.Page):
        page.title = "Recording Overlay Test"
        page.window_width = 400
        page.window_height = 300

        overlay = create_recording_overlay()

        def show_recording(e):
            overlay.set_recording(0, 30)
            overlay.show("recording")
            page.update()

        def stop_recording(e):
            overlay.set_processing()
            page.update()

        def hide_overlay(e):
            overlay.hide()
            page.update()

        page.add(
            ft.Column([
                ft.ElevatedButton(
                    content=ft.Text("Show Recording"),
                    on_click=show_recording
                ),
                ft.ElevatedButton(
                    content=ft.Text("Stop Recording"),
                    on_click=stop_recording
                ),
                ft.ElevatedButton(
                    content=ft.Text("Hide Overlay"),
                    on_click=hide_overlay
                ),
                ft.Divider(height=20),
                overlay.build()
            ])
        )

    ft.app(target=main)
