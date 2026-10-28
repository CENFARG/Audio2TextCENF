"""Updates tab: check, download and install flow (S7)."""

import logging
from collections.abc import Callable
from threading import Thread
from tkinter import messagebox
from typing import Protocol, cast

import customtkinter as ctk

from backend.updater import InstallResult
from ui.theme import COLORS as C, SURFACES as S


class _ClosableToplevel(Protocol):
    """Minimal window surface needed by the shutdown fallback."""

    def quit(self) -> None: ...

    def destroy(self) -> None: ...


def resolve_post_install_action(outcome: object) -> str:
    """Map a backend install outcome to a UI action without touching Tk.

    "shutdown": install_update returned an InstallResult; the UI owns the
    graceful app close. "error": anything else (exception or bad value).
    """
    return "shutdown" if isinstance(outcome, InstallResult) else "error"


def resolve_shutdown_callable(toplevel: object) -> Callable[[], None]:
    """Pick the graceful shutdown callable for the hosting window.

    Prefers the app's full-cleanup path (quit_application: transcriber,
    overlay, tray) and falls back to quit()+destroy() for generic
    toplevels. Pure and Tk-free, so tests can verify the contract.
    """
    quit_application = getattr(toplevel, "quit_application", None)
    if callable(quit_application):
        return cast("Callable[[], None]", quit_application)

    def fallback() -> None:
        closable = cast("_ClosableToplevel", toplevel)
        closable.quit()
        closable.destroy()

    return fallback


def progress_fraction(downloaded: int, total: int) -> float | None:
    """Return a clamped 0..1 fraction, or None when the total is unknown."""
    if total <= 0:
        return None
    return min(max(downloaded / total, 0.0), 1.0)


def format_progress_label(downloaded: int, total: int) -> str:
    """Human label for the download state.

    Known total -> "Descargando... N%". Unknown total (file_size=0 in
    version.json or missing content-length) -> downloaded MB with an
    explicit note, never a stuck 0%.
    """
    mb = downloaded / (1024 * 1024)
    if progress_fraction(downloaded, total) is None:
        return f"Descargando... {mb:.1f} MB (tamaño desconocido)"
    return f"Descargando... {int(round((downloaded / total) * 100))}%"


def format_up_to_date_text(current_version: str) -> str:
    """Up-to-date status line, always naming the running version."""
    return f"✅ Estás usando la última versión (v{current_version})"


class UpdateTab(ctk.CTkFrame):
    """Pestaña de actualizaciones de la aplicación"""

    def __init__(self, parent, updater, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.updater = updater
        self.update_info = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.create_widgets()

        # Verificar actualizaciones al cargar la pestaña
        self.after(500, self.check_updates)

    def create_widgets(self):
        """Crear widgets de la interfaz"""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, pady=20, padx=20, sticky="ew")

        title = ctk.CTkLabel(header_frame, text="🔄 Actualizaciones", font=("Segoe UI", 24, "bold"))
        title.pack()

        # Estado
        self.status_label = ctk.CTkLabel(
            header_frame, text="Verificando actualizaciones...", font=("Segoe UI", 14)
        )
        self.status_label.pack(pady=10)

        # Frame de contenido (scrollable)
        self.content_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Frame de información (oculto inicialmente)
        self.info_frame = ctk.CTkFrame(self.content_frame, fg_color=C["surface"], corner_radius=10)

        # Botones
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, pady=(0, 20), padx=20, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        self.check_btn = ctk.CTkButton(
            button_frame, text="Verificar Actualizaciones", command=self.check_updates
        )
        self.check_btn.grid(row=0, column=0, padx=5, sticky="ew")

        self.download_btn = ctk.CTkButton(
            button_frame,
            text="Descargar e Instalar",
            command=self.download_and_install,
            state="disabled",
            fg_color=C["success"],
            hover_color=C["success_hover"],
            text_color=C["text"],
            text_color_disabled=C["muted"],
        )
        self.download_btn.grid(row=0, column=1, padx=5, sticky="ew")

        # Barra de progreso (oculta inicialmente)
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_label = ctk.CTkLabel(self.progress_frame, text="Descargando...")
        self.progress_label.grid(row=0, column=0, pady=(0, 5))

        self.progress = ctk.CTkProgressBar(self.progress_frame)
        self.progress.grid(row=1, column=0, sticky="ew")
        self.progress.set(0)

        self.progress_frame.grid_remove()  # Ocultar inicialmente

    def check_updates(self):
        """Verificar si hay actualizaciones disponibles"""
        self.status_label.configure(text="Verificando actualizaciones...")
        self.check_btn.configure(state="disabled")
        self.download_btn.configure(state="disabled")

        # Limpiar info anterior (solo si info_frame tiene widgets)
        for widget in self.info_frame.winfo_children():
            widget.destroy()
        # Solo remover layout si el frame está en la grilla
        try:
            self.info_frame.grid_remove()
        except Exception:
            pass  # El frame ya no está en la grilla

        Thread(target=self._check_updates_thread, daemon=True).start()

    def _check_updates_thread(self):
        """Thread para verificar actualizaciones"""
        self.update_info = self.updater.check_for_updates()
        self.after(0, self._update_ui)

    def _update_ui(self):
        """Actualizar UI con resultado de verificación"""
        self.check_btn.configure(state="normal")

        if "error" in self.update_info:
            self.status_label.configure(
                text=f"❌ Error: {self.update_info['error']}", text_color=C["error"]
            )
        elif self.update_info["available"]:
            version = self.update_info["version"]
            self.status_label.configure(
                text=f"✨ Nueva versión disponible: v{version}", text_color=C["success"]
            )
            self.download_btn.configure(state="normal")

            # Mostrar información de la actualización
            self._show_update_info()
        else:
            self.status_label.configure(
                text=format_up_to_date_text(self.updater.current_version),
                text_color=C["success"],
            )

    def _show_update_info(self):
        """Mostrar información detallada de la actualización"""
        self.info_frame.grid(row=0, column=0, pady=10, sticky="ew")

        # Versión
        version_label = ctk.CTkLabel(
            self.info_frame,
            text=f"Versión: {self.update_info['version']}",
            font=("Segoe UI", 16, "bold"),
        )
        version_label.pack(pady=(15, 5), padx=15, anchor="w")

        # Fecha
        if self.update_info.get("release_date"):
            date_label = ctk.CTkLabel(
                self.info_frame,
                text=f"Fecha: {self.update_info['release_date']}",
                font=("Segoe UI", 12),
            )
            date_label.pack(pady=2, padx=15, anchor="w")

        # Tamaño
        if self.update_info.get("file_size"):
            size_mb = self.update_info["file_size"] / (1024 * 1024)
            size_label = ctk.CTkLabel(
                self.info_frame, text=f"Tamaño: {size_mb:.2f} MB", font=("Segoe UI", 12)
            )
            size_label.pack(pady=2, padx=15, anchor="w")
        else:
            size_label = ctk.CTkLabel(
                self.info_frame,
                text="Tamaño: se conocerá durante la descarga",
                font=("Segoe UI", 12),
            )
            size_label.pack(pady=2, padx=15, anchor="w")

        # Separador
        separator = ctk.CTkFrame(self.info_frame, height=2, fg_color=S["hi"])
        separator.pack(fill="x", padx=15, pady=10)

        # Changelog
        changelog_title = ctk.CTkLabel(
            self.info_frame, text="Novedades:", font=("Segoe UI", 14, "bold")
        )
        changelog_title.pack(pady=(5, 5), padx=15, anchor="w")

        changelog_text = ctk.CTkTextbox(
            self.info_frame, height=150, wrap="word", font=("Segoe UI", 12)
        )
        changelog_text.pack(pady=(0, 15), padx=15, fill="both", expand=True)
        changelog_text.insert("1.0", self.update_info["changelog"])
        changelog_text.configure(state="disabled")

    def download_and_install(self):
        """Descargar e instalar actualización"""
        # Confirmar con el usuario
        response = messagebox.askyesno(
            "Instalar Actualización",
            f"¿Deseas descargar e instalar la versión {self.update_info['version']}?\n\n"
            "La aplicación se cerrará y reiniciará automáticamente.",
            icon="question",
        )

        if not response:
            return

        self.download_btn.configure(state="disabled")
        self.check_btn.configure(state="disabled")
        self.progress_frame.grid()  # Mostrar barra de progreso

        Thread(target=self._download_thread, daemon=True).start()

    def _download_thread(self):
        """Thread para descargar actualización"""
        try:
            temp_path = self.updater.download_update(
                self.update_info["download_url"],
                progress_callback=self._update_progress,
            )
            self.after(0, lambda: self._install(temp_path))
        except Exception as e:
            self.after(0, lambda err=str(e): self._show_error(err))

    def _update_progress(self, downloaded: int, total: int) -> None:
        """Actualizar barra de progreso desde el thread de descarga."""
        fraction = progress_fraction(downloaded, total)
        label = format_progress_label(downloaded, total)

        def apply() -> None:
            # Total desconocido (file_size=0): nota de MB en la etiqueta,
            # nunca un "0%" congelado.
            self.progress.set(fraction if fraction is not None else 0.0)
            self.progress_label.configure(text=label)

        self.after(0, apply)

    def _install(self, temp_path: str) -> None:
        """Instalar la actualización: la UI es dueña del cierre de la app.

        El backend ya no termina el proceso (antes hacía sys.exit(0) desde
        un callback de Tk, abortando la limpieza). Ante un InstallResult
        programa el cierre limpio; ante un error muestra el motivo.
        """
        self.progress_label.configure(text="Instalando actualización...")
        try:
            outcome = self.updater.install_update(temp_path)
        except Exception as e:
            self._show_error(f"Error al instalar: {e}")
            return

        if resolve_post_install_action(outcome) == "shutdown":
            self.progress_label.configure(text="Instalación iniciada. La aplicación se cerrará...")
            self.after(1000, self._close_for_install)

    def _close_for_install(self) -> None:
        """Cierre limpio para que el batch reemplace el ejecutable."""
        self.logger.info("Cerrando la aplicación para completar la instalación")
        resolve_shutdown_callable(self.winfo_toplevel())()

    def _show_error(self, error):
        """Mostrar error"""
        self.logger.error(f"Error en actualización: {error}")
        self.status_label.configure(text=f"❌ Error: {error}", text_color=C["error"])
        self.download_btn.configure(state="normal")
        self.check_btn.configure(state="normal")
        self.progress_frame.grid_remove()

        messagebox.showerror("Error", f"Error al actualizar:\n{error}")
