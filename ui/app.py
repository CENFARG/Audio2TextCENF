# C:\Users\gonza\Dropbox\DOC. RECA\06-Software\Audio2Text\audio2text_v0.8.1\ui\app.py
print("!!! UI_APP_PY_LOADED_ROOT !!!")
import os
import sys
import webbrowser
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import pyperclip
import pyautogui
import threading
import keyboard
from groq import Groq
import logging
from datetime import datetime

# Backend imports
from backend.config_manager import ConfigManager
from backend.file_manager import FileManager
from backend.sound_manager import SoundManager
from backend.transcriber import Transcriber
from backend.updater import Updater

# Importar LocalizationManager directamente para usar sus strings
from backend.localization_manager import LocalizationManager

# UI imports
from ui.recording_overlay import RecordingOverlay
from ui.update_tab import UpdateTab

class DesignSystem:
    COLORS = {
        "primary": "#2563EB", "primary_hover": "#1D4ED8",
        "success": "#10B981", "error": "#EF4444", "warning": "#F59E0B",
        "background": "#0F172A", "surface": "#1E293B",
        "text_primary": "#F8FAFC", "text_secondary": "#CBD5E1",
    }
    TYPOGRAPHY = {
        "heading_large": ("Segoe UI", 20, "bold"), "heading_medium": ("Segoe UI", 16, "bold"),
        "body_medium": ("Segoe UI", 14, "normal"), "body_small": ("Segoe UI", 12, "normal"),
        "link": ("Segoe UI", 12, "underline"),
    }

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing application UI.")

        self.config_manager = ConfigManager(config_file="config.json")
        self.localization_manager = self.config_manager.localization_manager # Usa la instancia de localization_manager de config_manager
        self.title(self.localization_manager.get_string("app_title"))
        self.geometry("500x400")  # Reducido de 550 a 400
        self.minsize(400, 350)  # Reducido de 450x450 a 400x350
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        try: 
            self.iconbitmap("icono.ico")
            self.logger.info("Icono 'icono.ico' cargado exitosamente.")
        except Exception: # TclError or others
            print("No se pudo cargar 'icono.ico'") # Keep print for immediate console visibility
            self.logger.warning("No se pudo cargar 'icono.ico'.")

        self.sound_manager = SoundManager()
        self.file_manager = FileManager(self.config_manager)
        
        # --- Tutorial ---
        from ui.tutorial import TutorialManager
        self.tutorial_manager = TutorialManager(self)
        
        # Crear overlay de grabación - TEMPORALMENTE DESHABILITADO
        # self.recording_overlay = RecordingOverlay(self)
        self.recording_overlay = None  # Placeholder
        
        # Crear transcriber con callback de overlay
        self.transcriber = Transcriber(
            self.config_manager, 
            self.sound_manager, 
            self.file_manager, 
            self.update_status, 
            self.display_transcription, 
            self.localization_manager,
            overlay_callback=self.update_overlay
        )

        # Crear sistema de actualizaciones
        self.updater = Updater(
            current_version=self.config_manager.get("app_version"),
            github_repo="CENFARG/Audio2Text"
        )

        self.tray_icon = None
        self.hotkey_recording_window = None
        self.create_widgets()
        self.update_file_info()
        self.after(1000, self._check_api_key)
        
        # Iniciar tutorial si corresponde (después de que la UI cargue)
        if self.tutorial_manager.should_start():
            self.after(1500, self.tutorial_manager.start)

    def create_widgets(self):
        self.logger.debug("Creando widgets de la interfaz de usuario.")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.main_frame = ctk.CTkTabview(self)
        self.main_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="nsew")
        self.main_frame.add(self.localization_manager.get_string("tab_main"))
        self.main_frame.add(self.localization_manager.get_string("tab_settings"))
        self.main_frame.add(self.localization_manager.get_string("tab_info"))
        self.main_frame.add(self.localization_manager.get_string("tab_history"))
        self.main_frame.add(self.localization_manager.get_string("tab_updates"))
        
        self.create_main_tab()
        self.create_config_tab()
        self.create_info_tab()
        self.create_history_tab()
        self.create_update_tab()

        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")  # Cambio de row=2 a row=1
        cenf_link = ctk.CTkLabel(self.bottom_frame, text=self.localization_manager.get_string("cenf_website"), font=DesignSystem.TYPOGRAPHY["link"], text_color=DesignSystem.COLORS["primary"], cursor="hand2")
        cenf_link.pack(side="right")
        cenf_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://www.cenfarg.com.ar"))
        self.logger.debug("Widgets de la interfaz de usuario creados.")

    def update_overlay(self, state, minutes=0, seconds=0):
        """Actualizar el overlay de grabación según el estado (Thread-safe)"""
        def _update():
            if not self.recording_overlay:
                return
                
            if state == "recording":
                self.recording_overlay.set_recording()
                self.recording_overlay.update_timer(minutes, seconds)
            elif state == "processing":
                self.recording_overlay.set_processing()
            elif state == "ready":
                self.recording_overlay.set_ready()
            elif state == "error":
                self.recording_overlay.set_error()
        
        self.after(0, _update)


    def create_main_tab(self):
        self.logger.debug("Creando pestaña 'Principal'.")
        tab = self.main_frame.tab(self.localization_manager.get_string("tab_main"))
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(3, weight=1)  # Row 3 será el panel de transcripción (antes row 4)
        
        # Status frame - REDUCIDO padding de 20 a 10
        status_frame = ctk.CTkFrame(tab, fg_color="transparent")
        status_frame.grid(row=0, column=0, pady=(10, 5), padx=15, sticky="ew")  # Reducido pady
        status_frame.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(status_frame, text=self.localization_manager.get_string("status_ready"), font=DesignSystem.TYPOGRAPHY["heading_large"])
        self.status_label.grid(row=0, column=0, sticky="ew")
        self.hotkey_display_label = ctk.CTkLabel(status_frame, text=self.localization_manager.get_string("hotkey_display", hotkey=self.config_manager.get('hotkey').upper()), font=DesignSystem.TYPOGRAPHY["body_small"])
        self.hotkey_display_label.grid(row=1, column=0, pady=(3, 5), sticky="ew")  # Reducido pady

        # Logo del cliente (si existe)
        logo_path = "logo.png"
        if getattr(sys, 'frozen', False):
            logo_path = os.path.join(sys._MEIPASS, "logo.png")
        
        if os.path.exists(logo_path):
            try:
                pil_image = Image.open(logo_path)
                # Resize keeping aspect ratio, max height 50
                h_ratio = 50 / float(pil_image.size[1])
                w_size = int((float(pil_image.size[0]) * float(h_ratio)))
                logo_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(w_size, 50))
                
                logo_label = ctk.CTkLabel(status_frame, text="", image=logo_image)
                logo_label.grid(row=0, column=1, rowspan=2, padx=10, sticky="e")
            except Exception as e:
                self.logger.error(f"Error cargando logo: {e}")

        # Info frame - REDUCIDO padding
        info_frame = ctk.CTkFrame(tab, fg_color="transparent")
        info_frame.grid(row=1, column=0, padx=15, pady=(0, 5), sticky="ew")  # Reducido padding
        info_frame.grid_columnconfigure((0, 1), weight=1)
        self.audio_size_label = ctk.CTkLabel(info_frame, text=self.localization_manager.get_string("audio_info", size="...", count="..."))
        self.audio_size_label.grid(row=0, column=0, sticky="w")
        self.log_size_label = ctk.CTkLabel(info_frame, text=self.localization_manager.get_string("transcriptions_info", size="..."))
        self.log_size_label.grid(row=0, column=1, sticky="e")

        # Button frame - REDUCIDO padding
        button_frame = ctk.CTkFrame(tab, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=15, pady=(0, 5), sticky="ew")  # Reducido padding
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)
        ctk.CTkButton(button_frame, text=self.localization_manager.get_string("clear_audio_button"), command=self.clear_audio_with_feedback).grid(row=0, column=0, padx=5, sticky="ew")
        ctk.CTkButton(button_frame, text=self.localization_manager.get_string("clear_transcriptions_button"), command=self.clear_logs_with_feedback).grid(row=0, column=1, padx=5, sticky="ew")
        

        
        # --- Panel de Transcripción (AMPLIADO - ahora en row 3) ---
        if self.config_manager.get("show_transcription_panel"):
            self.transcription_frame = ctk.CTkFrame(tab, fg_color="transparent")
            self.transcription_frame.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="nsew")
            self.transcription_textbox = ctk.CTkTextbox(self.transcription_frame, wrap="word", font=DesignSystem.TYPOGRAPHY["body_medium"])
            self.transcription_textbox.pack(expand=True, fill="both")
        else:
            self.transcription_frame = None
            self.transcription_textbox = None
            
        self.logger.debug("Pestaña 'Principal' creada.")

    def create_config_tab(self):
        self.logger.debug("Creando pestaña 'Configuración'.")
        tab = self.main_frame.tab(self.localization_manager.get_string("tab_settings"))
        tab.grid_columnconfigure(0, weight=1)

        scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True)
        scroll_frame.grid_columnconfigure(0, weight=1)

        # --- API, Hotkey & Behavior Frame ---
        main_conf_frame = ctk.CTkFrame(scroll_frame)
        main_conf_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        main_conf_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(main_conf_frame, text=self.localization_manager.get_string("settings_title_main"), font=DesignSystem.TYPOGRAPHY["heading_medium"]).grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky="w")

        self.api_key_status_label = ctk.CTkLabel(main_conf_frame, text="●", font=("Segoe UI", 20), text_color="grey")
        self.api_key_status_label.grid(row=1, column=0, padx=(10,0), sticky="w")
        self.api_key_var = tk.StringVar(value=self.config_manager.get("groq_api_key"))
        api_entry = ctk.CTkEntry(main_conf_frame, textvariable=self.api_key_var, show="*", placeholder_text=self.localization_manager.get_string("api_key_placeholder"))
        api_entry.grid(row=1, column=1, padx=5, sticky="ew")
        api_entry.bind("<FocusOut>", lambda e: self.save_config()) # Autosave on focus out
        verify_btn = ctk.CTkButton(main_conf_frame, text=self.localization_manager.get_string("verify_button"), width=70, command=self._check_api_key)
        verify_btn.grid(row=1, column=2, padx=(0,10))



        # Hotkey
        ctk.CTkLabel(main_conf_frame, text=self.localization_manager.get_string("hotkey_label")).grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.hotkey_var = tk.StringVar(value=self.config_manager.get('hotkey'))
        f_keys = [f"F{i}" for i in range(1, 13)]
        # Command triggers when selection changes
        ctk.CTkComboBox(main_conf_frame, values=f_keys, variable=self.hotkey_var, state="readonly", command=lambda e: self.save_config()).grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        record_hotkey_btn = ctk.CTkButton(main_conf_frame, text=self.localization_manager.get_string("record_hotkey_button"), width=70, command=self._start_hotkey_recording)
        record_hotkey_btn.grid(row=3, column=2, padx=(0,10), pady=5)

        # Recording Mode
        ctk.CTkLabel(main_conf_frame, text=self.localization_manager.get_string("record_mode_label")).grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.record_mode_var = tk.StringVar(value=self.config_manager.get("record_mode"))
        record_mode_frame = ctk.CTkFrame(main_conf_frame, fg_color="transparent")
        record_mode_frame.grid(row=4, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        ctk.CTkRadioButton(record_mode_frame, text=self.localization_manager.get_string("record_mode_hold"), variable=self.record_mode_var, value="hold", command=self.save_config).grid(row=0, column=0, padx=5, sticky="w")
        ctk.CTkRadioButton(record_mode_frame, text=self.localization_manager.get_string("record_mode_toggle"), variable=self.record_mode_var, value="toggle", command=self.save_config).grid(row=0, column=1, padx=10, sticky="w")

        # Auto-paste & Show panel
        self.auto_paste_var = tk.BooleanVar(value=self.config_manager.get("auto_paste_text"))
        ctk.CTkSwitch(main_conf_frame, text=self.localization_manager.get_string("auto_paste_switch"), variable=self.auto_paste_var, command=self.save_config).grid(row=5, column=0, columnspan=3, padx=10, pady=5, sticky="w")
        self.show_panel_var = tk.BooleanVar(value=self.config_manager.get("show_transcription_panel"))
        ctk.CTkSwitch(main_conf_frame, text=self.localization_manager.get_string("show_panel_switch"), variable=self.show_panel_var, command=self.save_config).grid(row=6, column=0, columnspan=3, padx=10, pady=5, sticky="w")

        # Language selection
        ctk.CTkLabel(main_conf_frame, text=self.localization_manager.get_string("language_label")).grid(row=7, column=0, padx=10, pady=5, sticky="w")
        self.language_var = tk.StringVar(value=self.config_manager.get("default_language"))
        # Command triggers when selection changes
        ctk.CTkComboBox(main_conf_frame, values=["es", "en"], variable=self.language_var, state="readonly", command=lambda e: self.save_config()).grid(row=7, column=1, padx=5, pady=5, sticky="ew", columnspan=2)

        # --- File Management Frame ---
        files_frame = ctk.CTkFrame(scroll_frame)
        files_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        files_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(files_frame, text=self.localization_manager.get_string("settings_title_files"), font=DesignSystem.TYPOGRAPHY["heading_medium"]).grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(files_frame, text=self.localization_manager.get_string("audio_path_label")).grid(row=1, column=0, padx=10, sticky="w")
        self.audio_path_var = tk.StringVar(value=self.config_manager.get("audio_path"))
        audio_path_entry = ctk.CTkEntry(files_frame, textvariable=self.audio_path_var)
        audio_path_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        audio_path_entry.bind("<FocusOut>", lambda e: self.save_config())
        ctk.CTkButton(files_frame, text=self.localization_manager.get_string("browse_button"), width=70, command=lambda: self._browse_path(self.audio_path_var)).grid(row=1, column=2, padx=(0,10))

        ctk.CTkLabel(files_frame, text=self.localization_manager.get_string("transcriptions_path_label")).grid(row=2, column=0, padx=10, sticky="w")
        self.transcriptions_path_var = tk.StringVar(value=self.config_manager.get("transcriptions_path"))
        logs_path_entry = ctk.CTkEntry(files_frame, textvariable=self.transcriptions_path_var)
        logs_path_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        logs_path_entry.bind("<FocusOut>", lambda e: self.save_config())
        ctk.CTkButton(files_frame, text=self.localization_manager.get_string("browse_button"), width=70, command=lambda: self._browse_path(self.transcriptions_path_var)).grid(row=2, column=2, padx=(0,10))
        
        switch_frame = ctk.CTkFrame(files_frame, fg_color="transparent")
        switch_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=10, pady=5)
        switch_frame.grid_columnconfigure((0,1), weight=1)
        self.save_audio_var = tk.BooleanVar(value=self.config_manager.get("save_audio"))
        ctk.CTkSwitch(switch_frame, text=self.localization_manager.get_string("save_audio_switch"), variable=self.save_audio_var, command=self.save_config).grid(row=0, column=0, sticky="w")
        self.save_logs_var = tk.BooleanVar(value=self.config_manager.get("save_logs"))
        ctk.CTkSwitch(switch_frame, text=self.localization_manager.get_string("save_logs_switch"), variable=self.save_logs_var, command=self.save_config).grid(row=0, column=1, sticky="w")

        # --- Client Logo Settings REMOVED (Build parameter) ---
        # ctk.CTkLabel(files_frame, text=self.localization_manager.get_string("client_logo_label")...

        self.logger.debug("Pestaña 'Configuración' creada.")

    def create_history_tab(self):
        self.logger.debug("Creando pestaña 'Historial'.")
        tab = self.main_frame.tab(self.localization_manager.get_string("tab_history"))
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Header
        header_frame = ctk.CTkFrame(tab, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(header_frame, text=self.localization_manager.get_string("history_title"), font=DesignSystem.TYPOGRAPHY["heading_medium"]).pack(side="left")
        ctk.CTkButton(header_frame, text=self.localization_manager.get_string("refresh_button"), width=80, command=self.refresh_history_list).pack(side="right")

        # List Area
        self.history_scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.history_scroll_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        self.refresh_history_list()
        
        # Auto-refresh cada 5 segundos
        self.after(5000, self.auto_refresh_history)

    def auto_refresh_history(self):
        if self.main_frame.get() == self.localization_manager.get_string("tab_history"):
            self.refresh_history_list()
        self.after(5000, self.auto_refresh_history)
        self.logger.debug("Pestaña 'Historial' creada.")

    def refresh_history_list(self):
        # Clear existing
        for widget in self.history_scroll_frame.winfo_children():
            widget.destroy()

        audio_path = self.config_manager.get("audio_path")
        if not os.path.exists(audio_path):
            ctk.CTkLabel(self.history_scroll_frame, text="Directorio no encontrado").pack(pady=20)
            return

        files = [f for f in os.listdir(audio_path) if f.endswith(".wav")]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(audio_path, x)), reverse=True) # Newest first

        if not files:
            ctk.CTkLabel(self.history_scroll_frame, text=self.localization_manager.get_string("no_audio_files")).pack(pady=20)
            return

        for f in files:
            self._create_history_item(f, os.path.join(audio_path, f))

    def _create_history_item(self, filename, full_path):
        item_frame = ctk.CTkFrame(self.history_scroll_frame)
        item_frame.pack(fill="x", pady=2, padx=5)
        
        # Icon/Name
        name_label = ctk.CTkLabel(item_frame, text=filename, font=DesignSystem.TYPOGRAPHY["body_small"], anchor="w")
        name_label.pack(side="left", padx=10, pady=5, fill="x", expand=True)

        # Action Button Frame
        action_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        action_frame.pack(side="right", padx=5)

        # Transcribe Button
        ctk.CTkButton(action_frame, text=self.localization_manager.get_string("transcribe_button"), width=80, height=24,
                      command=lambda p=full_path: self._start_retranscription(p)).pack(side="left", padx=2)
        
        # Delete Button
        ctk.CTkButton(action_frame, text="🗑️", width=30, height=24, fg_color="#EF4444", hover_color="#DC2626",
                      command=lambda p=full_path: self._delete_audio_file(p)).pack(side="left", padx=2)

    def _delete_audio_file(self, full_path):
        if messagebox.askyesno(self.localization_manager.get_string("confirm_delete_title"), 
                              self.localization_manager.get_string("confirm_delete_msg")):
            try:
                os.remove(full_path)
                self.refresh_history_list()
                self.update_file_info()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _start_retranscription(self, file_path):
        self.update_status(self.localization_manager.get_string("retranscribing"), "yellow")
        threading.Thread(target=self._retranscribe_thread, args=(file_path,), daemon=True).start()

    def _retranscribe_thread(self, file_path):
        try:
            self.logger.info(f"Retranscribiendo archivo: {file_path}")
            text = self.transcriber.transcribe_with_groq(file_path)
            if text:
                self.display_transcription(text)
                self.file_manager.save_transcription_entry({
                    "text": text, "duration": 0, # Duration unknown/irrelevant for re-transcription
                    "language": self.config_manager.get("default_language"), "audio_file": file_path
                })
                self.update_status(self.localization_manager.get_string("transcription_completed"), "green")
                self.sound_manager.sound_success()
            else:
                 self.update_status(self.localization_manager.get_string("transcription_failed"), "red")
        except Exception as e:
            self.logger.error(f"Error en retranscripción: {e}")
            self.update_status(f"Error: {e}", "red")

    def create_info_tab(self):
        self.logger.debug("Creando pestaña 'Información'.")
        tab = self.main_frame.tab(self.localization_manager.get_string("tab_info"))
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        
        try:
            from tkhtmlview import HTMLScrolledText
            
            # Cargar template HTML
            html_path = "info_template.html"
            if getattr(sys, 'frozen', False):
                html_path = os.path.join(sys._MEIPASS, "info_template.html")
            
            if os.path.exists(html_path):
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Reemplazar placeholder de versión
                html_content = html_content.replace("{version}", self.config_manager.get("app_version"))
                
                # Crear visor HTML
                html_view = HTMLScrolledText(tab, html=html_content)
                html_view.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
            else:
                # Fallback si no se encuentra el HTML
                self._create_info_tab_fallback(tab)
                
        except ImportError:
            self.logger.warning("tkhtmlview no disponible, usando fallback")
            self._create_info_tab_fallback(tab)
        
        self.logger.debug("Pestaña 'Información' creada.")
    
    def _create_info_tab_fallback(self, tab):
        """Fallback para info tab si tkhtmlview no está disponible"""
        scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)

        info_text = self.localization_manager.get_string("info_text_simplified", version=self.config_manager.get("app_version"))
        
        # Usar wraplength fijo más amplio para evitar cortes
        info_label = ctk.CTkLabel(
            scroll_frame, 
            text=info_text, 
            wraplength=450,  # Aumentado de 380 a 450
            justify="left", 
            font=DesignSystem.TYPOGRAPHY["body_medium"],
            anchor="w"
        )
        info_label.pack(pady=10, padx=10, fill="x", expand=True)

        groq_link = ctk.CTkLabel(scroll_frame, text=self.localization_manager.get_string("groq_api_key_link"), text_color=DesignSystem.COLORS["primary"], cursor="hand2", font=DesignSystem.TYPOGRAPHY["link"])
        groq_link.pack(pady=5, padx=10, anchor="w")
        groq_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://console.groq.com/keys"))
    
    def create_update_tab(self):
        """Crear pestaña de actualizaciones"""
        self.logger.debug("Creando pestaña 'Actualizaciones'.")
        tab = self.main_frame.tab(self.localization_manager.get_string("tab_updates"))
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        
        # Crear UpdateTab
        update_tab = UpdateTab(tab, self.updater)
        update_tab.grid(row=0, column=0, sticky="nsew")
        
        self.logger.debug("Pestaña 'Actualizaciones' creada.")

    def _check_api_key(self):
        self.logger.info("Verificando claves API...")
        
        # Groq Check
        groq_key = self.api_key_var.get()
        if groq_key:
            self.api_key_status_label.configure(text="●", text_color=DesignSystem.COLORS["warning"]); self.update_idletasks()
            try:
                Groq(api_key=groq_key).models.list()
                self.api_key_status_label.configure(text="●", text_color=DesignSystem.COLORS["success"])
            except Exception as e:
                self.api_key_status_label.configure(text="●", text_color=DesignSystem.COLORS["error"])
        else:
            self.api_key_status_label.configure(text="●", text_color="grey")



    def _start_hotkey_recording(self):
        self.logger.debug("Iniciando grabación de hotkey.")
        if self.hotkey_recording_window: 
            try:
                self.hotkey_recording_window.destroy()
            except:
                pass
        
        self.hotkey_recording_window = ctk.CTkToplevel(self)
        self.hotkey_recording_window.title(self.localization_manager.get_string("recording_hotkey_title"))
        self.hotkey_recording_window.geometry("300x100")
        self.hotkey_recording_window.transient(self)
        self.hotkey_recording_window.grab_set()
        
        label = ctk.CTkLabel(self.hotkey_recording_window, text=self.localization_manager.get_string("recording_hotkey_prompt"))
        label.pack(pady=20, padx=20, expand=True, fill="both")
        
        # Usar after para no bloquear la UI mientras se prepara el thread
        self.after(100, lambda: threading.Thread(target=self._record_hotkey_thread, daemon=True).start())

    def _record_hotkey_thread(self):
        try:
            hotkey = keyboard.read_hotkey(suppress=False)
            self.after(0, self._set_new_hotkey, hotkey)
        except Exception as e: 
            self.logger.error(f"Error grabando hotkey: {e}")
            if self.hotkey_recording_window:
                self.after(0, self.hotkey_recording_window.destroy)

    def _set_new_hotkey(self, hotkey):
        self.hotkey_var.set(hotkey.upper())
        self.logger.info(f"Nuevo hotkey establecido: {hotkey.upper()}")
        if self.hotkey_recording_window: self.hotkey_recording_window.destroy()

    def _browse_path(self, path_var):
        self.logger.debug(f"Navegando por la ruta actual: {path_var.get()}")
        folder_selected = filedialog.askdirectory(initialdir=path_var.get() if os.path.exists(path_var.get()) else os.getcwd())
        if folder_selected: 
            path_var.set(folder_selected)
            self.logger.info(f"Ruta seleccionada: {folder_selected}")
            self.save_config()
        else:
            self.logger.info("Selección de ruta cancelada.")

    def _browse_file(self, path_var, file_types):
        self.logger.debug(f"Navegando por archivo en: {path_var.get()}")
        file_selected = filedialog.askopenfilename(initialdir=path_var.get() if os.path.exists(os.path.dirname(path_var.get())) else os.getcwd(), filetypes=file_types)
        if file_selected:
            path_var.set(file_selected)
            self.logger.info(f"Archivo seleccionado: {file_selected}")
            self.save_config()

    def save_config(self, event=None):
        self.logger.info("Guardando configuración...")
        old_lang = self.config_manager.get("default_language")
        old_show_panel = self.config_manager.get("show_transcription_panel")
        
        settings = {
            "groq_api_key": self.api_key_var.get(),
            "openrouter_api_key": self.openrouter_api_key_var.get(),
            "hotkey": self.hotkey_var.get(),
            "record_mode": self.record_mode_var.get(),
            "auto_paste_text": self.auto_paste_var.get(), "show_transcription_panel": self.show_panel_var.get(),
            "audio_path": self.audio_path_var.get(), "transcriptions_path": self.transcriptions_path_var.get(),
            "save_audio": self.save_audio_var.get(), "save_logs": self.save_logs_var.get(),
            "max_audio_files": int(self.config_manager.get("max_audio_files")), 
            "max_log_entries": int(self.config_manager.get("max_log_entries")),
            "audio_priority_apps": self.config_manager.get("audio_priority_apps"), 
            "default_language": self.language_var.get()
        }
        self.config_manager.set_multiple(settings)
        
        # Check for language change
        if self.language_var.get() != old_lang:
            self.config_manager.set_language(self.language_var.get())
            self.recreate_ui_for_language_change()
        
        # --- API Key Logic Fix ---
        if settings["groq_api_key"]:
            os.environ["GROQ_API_KEY"] = settings["groq_api_key"]
            self.transcriber.reload_client()
        
        if settings["openrouter_api_key"]:
            os.environ["OPENROUTER_API_KEY"] = settings["openrouter_api_key"]
            self.logger.info("OPENROUTER_API_KEY configurada en el entorno.")
        # -------------------------

        # Verify hotkey change
        if settings["hotkey"] != self.transcriber.hotkey:
             self.transcriber.update_hotkey(settings["hotkey"])
        
        self.transcriber.record_mode = settings["record_mode"]
        self.hotkey_display_label.configure(text=self.localization_manager.get_string("hotkey_display", hotkey=settings['hotkey'].upper()))
        
        if self.config_manager.get("show_transcription_panel"):
            if self.transcription_frame is None:
                # Recrear panel si no existe
                self.transcription_frame = ctk.CTkFrame(self.main_frame.tab(self.localization_manager.get_string("tab_main")), fg_color="transparent")
                self.transcription_frame.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="nsew")
                self.transcription_textbox = ctk.CTkTextbox(self.transcription_frame, wrap="word", font=DesignSystem.TYPOGRAPHY["body_medium"])
                self.transcription_textbox.pack(expand=True, fill="both")
            else:
                self.transcription_frame.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="nsew")
        else:
             if self.transcription_frame:
                self.transcription_frame.grid_remove()

        self._check_api_key()
        self.logger.info("Configuración guardada.")

    def _update_status_on_main_thread(self, message, color):
        self.logger.debug(f"Actualizando estado de UI: {message} ({color})")
        color_map = {"green": "success", "yellow": "warning", "red": "error", "orange": "warning"}
        text_color = DesignSystem.COLORS.get(color_map.get(color), DesignSystem.COLORS["text_primary"])
        self.status_label.configure(text=message, text_color=text_color)

    def update_status(self, message, color="white"):
        self.after(0, self._update_status_on_main_thread, message, color)

    def _safe_display_transcription_on_main_thread(self, text):
        self.logger.info(f"Mostrando transcripción (truncada): {text[:100]}...")
        if self.config_manager.get("show_transcription_panel") and self.transcription_textbox: 
            self.transcription_textbox.delete("1.0", "end"); 
            self.transcription_textbox.insert("1.0", text)
        pyperclip.copy(text)
        if self.config_manager.get("auto_paste_text"): 
            self.logger.info("Auto-pegando transcripción.")
            pyautogui.hotkey('ctrl', 'v')

    def display_transcription(self, text):
        self.after(0, self._safe_display_transcription_on_main_thread, text)


    def update_file_info(self):
        try:
            audio_size_mb = self.file_manager.get_audio_files_size() / (1024 * 1024)
            num_files = len([f for f in os.listdir(self.file_manager.audio_path) if f.endswith('.wav')])
            self.audio_size_label.configure(text=self.localization_manager.get_string("audio_info", size=f"{audio_size_mb:.2f}", count=num_files))
            log_size_kb = self.file_manager.get_transcriptions_size() / 1024
            self.log_size_label.configure(text=self.localization_manager.get_string("transcriptions_info", size=f"{log_size_kb:.2f}"))
            self.logger.debug(f"Información de archivos actualizada: Audio {audio_size_mb:.2f}MB, Transcripciones {log_size_kb:.2f}KB")
        except FileNotFoundError:
            self.audio_size_label.configure(text=self.localization_manager.get_string("audio_info", size="N/A", count="N/A"))
            self.log_size_label.configure(text=self.localization_manager.get_string("transcriptions_info", size="N/A"))
            self.logger.warning("No se encontraron archivos de audio o de logs para actualizar la información.")
        except Exception as e:
            self.logger.error(f"Error al actualizar la información de archivos: {e}")
        self.after(5000, self.update_file_info)

    def clear_audio_with_feedback(self):
        self.logger.info("Intentando limpiar archivos de audio.")
        if self.file_manager.clear_audio_files(): 
            self.update_status(self.localization_manager.get_string("audio_deleted"), "green")
            self.logger.info("Archivos de audio eliminados exitosamente.")
        else: 
            self.update_status(self.localization_manager.get_string("error_deleting_audio"), "red")
            self.logger.error("Error al eliminar archivos de audio.")
        self.update_file_info()

    def clear_logs_with_feedback(self):
        self.logger.info("Intentando limpiar archivos de transcripciones.")
        if self.file_manager.clear_transcriptions(): 
            self.update_status(self.localization_manager.get_string("transcriptions_deleted"), "green")
            self.logger.info("Archivos de transcripciones eliminados exitosamente.")
        else: 
            self.update_status(self.localization_manager.get_string("error_deleting_transcriptions"), "red")
            self.logger.error("Error al eliminar archivos de transcripciones.")
        self.update_file_info()

    def on_closing(self):
        self.logger.info("Cerrando ventana principal, minimizando a la bandeja del sistema.")
        self.withdraw()
        self.show_system_tray()

    def show_system_tray(self):
        self.logger.debug("Mostrando icono en la bandeja del sistema.")
        if self.tray_icon and self.tray_icon.visible: 
            self.logger.debug("Icono de bandeja ya visible, omitiendo recreación.")
            return
        image = Image.new('RGB', (64, 64), DesignSystem.COLORS["background"])
        draw = ImageDraw.Draw(image); draw.ellipse((10, 10, 54, 54), fill=DesignSystem.COLORS["primary"])
        menu = (item(self.localization_manager.get_string("tray_menu_show"), self.show_window), item(self.localization_manager.get_string("tray_menu_exit"), self.quit_application))
        self.tray_icon = pystray.Icon("audio2text", image, f"Audio2Text CENF {self.config_manager.get('app_version')}", menu); self.tray_icon.run_detached()
        self.logger.info("Aplicación minimizada a la bandeja del sistema.")

    def show_window(self):
        self.logger.info("Restaurando ventana desde la bandeja del sistema.")
        if self.tray_icon: self.tray_icon.stop()
        self.deiconify(); self.attributes('-topmost', 1); self.attributes('-topmost', 0)

    def recreate_ui_for_language_change(self):
        self.logger.info("Recreando UI debido a cambio de idioma.")
        # Destroy current main frame
        self.main_frame.destroy()
        self.bottom_frame.destroy()
        
        # Recreate widgets
        self.create_widgets()
        self.update_file_info()
        self.after(1000, self._check_api_key)
        self.logger.info("UI recreada.")

    def quit_application(self):
        self.logger.info("Cerrando aplicación.")
        self.transcriber.stop()
        if self.tray_icon: self.tray_icon.stop()
        self.destroy()
        sys.exit()