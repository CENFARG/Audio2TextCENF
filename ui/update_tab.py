import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from threading import Thread
import logging

class UpdateTab(ctk.CTkFrame):
    """Pestaña de actualizaciones de la aplicación"""
    
    def __init__(self, parent, updater, localization_manager=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.updater = updater
        self.localization_manager = localization_manager
        self.update_info = None
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.create_widgets()
        
        # Verificar actualizaciones al cargar la pestaña
        self.after(500, self.check_updates)
    
    def _get_string(self, key, **kwargs):
        if self.localization_manager:
            return self.localization_manager.get_string(key, **kwargs)
        return key
    
    def create_widgets(self):
        """Crear widgets de la interfaz"""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, pady=20, padx=20, sticky="ew")
        
        title = ctk.CTkLabel(header_frame, text=self._get_string("updates_title"), 
                            font=("Segoe UI", 24, "bold"))
        title.pack()
        
        # Estado
        self.status_label = ctk.CTkLabel(header_frame, 
                                         text=self._get_string("updates_checking"),
                                         font=("Segoe UI", 14))
        self.status_label.pack(pady=10)
        
        # Frame de contenido (scrollable)
        self.content_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Frame de información (oculto inicialmente)
        self.info_frame = ctk.CTkFrame(self.content_frame, fg_color="#1E293B", corner_radius=10)
        
        # Botones
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, pady=(0, 20), padx=20, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.check_btn = ctk.CTkButton(button_frame, text=self._get_string("updates_check_button"),
                                       command=self.check_updates)
        self.check_btn.grid(row=0, column=0, padx=5, sticky="ew")
        
        self.download_btn = ctk.CTkButton(button_frame, text=self._get_string("updates_download_install"),
                                         command=self.download_and_install,
                                         state="disabled",
                                         fg_color="#059669",
                                         hover_color="#047857",
                                         text_color="#FFFFFF",
                                         text_color_disabled="#E5E7EB")
        self.download_btn.grid(row=0, column=1, padx=5, sticky="ew")
        
        # Barra de progreso (oculta inicialmente)
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.progress_frame.grid_columnconfigure(0, weight=1)
        
        self.progress_label = ctk.CTkLabel(self.progress_frame, text=self._get_string("updates_downloading"))
        self.progress_label.grid(row=0, column=0, pady=(0, 5))
        
        self.progress = ctk.CTkProgressBar(self.progress_frame)
        self.progress.grid(row=1, column=0, sticky="ew")
        self.progress.set(0)
        
        self.progress_frame.grid_remove()  # Ocultar inicialmente
    
    def check_updates(self):
        """Verificar si hay actualizaciones disponibles"""
        self.status_label.configure(text=self._get_string("updates_checking"))
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
                text=self._get_string("updates_error", error=self.update_info['error']),
                text_color="#EF4444"
            )
        elif self.update_info["available"]:
            version = self.update_info["version"]
            self.status_label.configure(
                text=self._get_string("updates_new_version", version=version),
                text_color="#10B981"
            )
            self.download_btn.configure(state="normal")
            
            # Mostrar información de la actualización
            self._show_update_info()
        else:
            self.status_label.configure(
                text=self._get_string("updates_up_to_date"),
                text_color="#10B981"
            )
    
    def _show_update_info(self):
        """Mostrar información detallada de la actualización"""
        self.info_frame.grid(row=0, column=0, pady=10, sticky="ew")
        
        # Versión
        version_label = ctk.CTkLabel(self.info_frame, 
                                     text=self._get_string("updates_version", version=self.update_info['version']),
                                     font=("Segoe UI", 16, "bold"))
        version_label.pack(pady=(15, 5), padx=15, anchor="w")
        
        # Fecha
        if self.update_info.get('release_date'):
            date_label = ctk.CTkLabel(self.info_frame,
                                     text=self._get_string("updates_date", date=self.update_info['release_date']),
                                     font=("Segoe UI", 12))
            date_label.pack(pady=2, padx=15, anchor="w")
        
        # Tamaño
        if self.update_info.get('file_size'):
            size_mb = self.update_info['file_size'] / (1024 * 1024)
            size_label = ctk.CTkLabel(self.info_frame,
                                     text=self._get_string("updates_size", size=f"{size_mb:.2f}"),
                                     font=("Segoe UI", 12))
            size_label.pack(pady=2, padx=15, anchor="w")
        
        # Separador
        separator = ctk.CTkFrame(self.info_frame, height=2, fg_color="#334155")
        separator.pack(fill="x", padx=15, pady=10)
        
        # Changelog
        changelog_title = ctk.CTkLabel(self.info_frame,
                                      text=self._get_string("updates_changelog"),
                                      font=("Segoe UI", 14, "bold"))
        changelog_title.pack(pady=(5, 5), padx=15, anchor="w")
        
        changelog_text = ctk.CTkTextbox(self.info_frame, 
                                       height=150,
                                       wrap="word",
                                       font=("Segoe UI", 12))
        changelog_text.pack(pady=(0, 15), padx=15, fill="both", expand=True)
        changelog_text.insert("1.0", self.update_info['changelog'])
        changelog_text.configure(state="disabled")
    
    def download_and_install(self):
        """Descargar e instalar actualización"""
        # Confirmar con el usuario
        response = messagebox.askyesno(
            self._get_string("updates_confirm_title"),
            self._get_string("updates_confirm_msg", version=self.update_info['version']),
            icon='question'
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
                progress_callback=self._update_progress
            )
            self.after(0, lambda: self._install(temp_path))
        except Exception as e:
            self.after(0, lambda: self._show_error(str(e)))
    
    def _update_progress(self, downloaded, total):
        """Actualizar barra de progreso"""
        if total > 0:
            progress = downloaded / total
            percentage = int(progress * 100)
            self.after(0, lambda: self.progress.set(progress))
            self.after(0, lambda: self.progress_label.configure(
                text=self._get_string("updates_progress", percentage=percentage)
            ))
    
    def _install(self, temp_path):
        """Instalar actualización"""
        try:
            self.progress_label.configure(text=self._get_string("updates_installing"))
            self.updater.install_update(temp_path)
        except Exception as e:
            self._show_error(str(e))
    
    def _show_error(self, error):
        """Mostrar error"""
        self.logger.error(f"Error en actualización: {error}")
        self.status_label.configure(text=self._get_string("updates_error", error=error), text_color="#EF4444")
        self.download_btn.configure(state="normal")
        self.check_btn.configure(state="normal")
        self.progress_frame.grid_remove()
        
        messagebox.showerror(self._get_string("updates_install_error_title"), self._get_string("updates_install_error_msg", error=error))
