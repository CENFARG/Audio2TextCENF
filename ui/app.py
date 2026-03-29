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
import json
from datetime import datetime

# Backend imports
from backend.config_manager import ConfigManager
from backend.file_manager import FileManager
from backend.sound_manager import SoundManager
from backend.transcriber import Transcriber
from backend.updater import Updater
from backend.transcription_metadata import TranscriptionMetadata

# UI imports
from ui.emoji_picker import show_emoji_picker
from ui.hotkey_selector import show_hotkey_selector
from backend.hotkey_manager import HotkeyManager

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
        "body_bold": ("Segoe UI", 13, "bold"),
        "body_medium": ("Segoe UI", 14, "normal"), "body_small": ("Segoe UI", 12, "normal"),
        "link": ("Segoe UI", 12, "underline"),
    }

class App(ctk.CTk):
    def __init__(self, config_manager=None):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing application UI.")

        self.config_manager = config_manager if config_manager else ConfigManager(config_file="config.json")
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
        self.metadata_manager = TranscriptionMetadata("transcription_metadata.json")

        # Para detectar cambios en historial sin refrescar constantemente
        self.last_history_file_count = 0
        self.last_history_mtime = 0
        self.loaded_history_files = set()  # Archivos ya cargados en el historial

        # Para rastrear reproducción de audio
        self.currently_playing = None  # (file_path, button)
        self.playing_threads = {}  # file_path -> stop_event

        # Para evitar llamadas duplicadas a display_transcription
        self.last_transcription_time = 0
        self.last_transcription_text = ""

        # --- Tutorial ---
        from ui.tutorial import TutorialManager
        self.tutorial_manager = TutorialManager(self)

        # Crear overlay de grabación - REACTIVADO
        from ui.recording_overlay import RecordingOverlay
        self.recording_overlay = RecordingOverlay(self)
        
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

        self.updater = Updater(
            current_version=self.config_manager.get("app_version"),
            github_repo="CENFARG/Audio2TextCENF"
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

        # ASR Provider Selection (Groq y faster-whisper visibles, NVIDIA oculto)
        ctk.CTkLabel(main_conf_frame, text=self.localization_manager.get_string("asr_provider_label")).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.asr_provider_var = tk.StringVar(value=self.config_manager.get("asr_provider", "groq"))
        asr_provider_frame = ctk.CTkFrame(main_conf_frame, fg_color="transparent")
        asr_provider_frame.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        ctk.CTkRadioButton(asr_provider_frame, text=self.localization_manager.get_string("asr_provider_groq"), variable=self.asr_provider_var, value="groq", command=self.save_config).grid(row=0, column=0, padx=5, sticky="w")
        ctk.CTkRadioButton(asr_provider_frame, text=self.localization_manager.get_string("asr_provider_faster_whisper"), variable=self.asr_provider_var, value="faster_whisper", command=self.save_config).grid(row=0, column=1, padx=10, sticky="w")
        # NVIDIA oculto de la UI pero funcional en config.json

        # faster-whisper Configuration
        self.faster_whisper_enabled_var = tk.BooleanVar(value=self.config_manager.get("faster_whisper_enabled", False))
        ctk.CTkSwitch(main_conf_frame, text=self.localization_manager.get_string("faster_whisper_enabled_label"), variable=self.faster_whisper_enabled_var, command=self.save_config).grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="w")

        # faster-whisper Model Selection
        ctk.CTkLabel(main_conf_frame, text=self.localization_manager.get_string("faster_whisper_model_label")).grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.faster_whisper_model_var = tk.StringVar(value=self.config_manager.get("faster_whisper_model", "base"))
        faster_whisper_model_frame = ctk.CTkFrame(main_conf_frame, fg_color="transparent")
        faster_whisper_model_frame.grid(row=4, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        ctk.CTkRadioButton(faster_whisper_model_frame, text=self.localization_manager.get_string("faster_whisper_model_base"), variable=self.faster_whisper_model_var, value="base", command=self.save_config).grid(row=0, column=0, padx=5, sticky="w")
        ctk.CTkRadioButton(faster_whisper_model_frame, text=self.localization_manager.get_string("faster_whisper_model_small"), variable=self.faster_whisper_model_var, value="small", command=self.save_config).grid(row=0, column=1, padx=10, sticky="w")

        # faster-whisper Device Selection
        ctk.CTkLabel(main_conf_frame, text=self.localization_manager.get_string("faster_whisper_device_label")).grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.faster_whisper_device_var = tk.StringVar(value=self.config_manager.get("faster_whisper_device", "auto"))
        faster_whisper_device_frame = ctk.CTkFrame(main_conf_frame, fg_color="transparent")
        faster_whisper_device_frame.grid(row=5, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        ctk.CTkRadioButton(faster_whisper_device_frame, text=self.localization_manager.get_string("faster_whisper_device_auto"), variable=self.faster_whisper_device_var, value="auto", command=self.save_config).grid(row=0, column=0, padx=5, sticky="w")
        ctk.CTkRadioButton(faster_whisper_device_frame, text=self.localization_manager.get_string("faster_whisper_device_cpu"), variable=self.faster_whisper_device_var, value="cpu", command=self.save_config).grid(row=0, column=1, padx=10, sticky="w")

        # faster-whisper Info
        faster_whisper_info = ctk.CTkLabel(main_conf_frame, text=self.localization_manager.get_string("faster_whisper_info"), text_color="gray", font=("Roboto", 10))
        faster_whisper_info.grid(row=6, column=0, columnspan=3, padx=10, pady=0, sticky="w")

        # Hotkey (v0.13.0 - Ahora con modificadores)
        ctk.CTkLabel(main_conf_frame, text=self.localization_manager.get_string("hotkey_label")).grid(row=7, column=0, padx=10, pady=5, sticky="w")

        # Botón para abrir selector de hotkey
        current_hotkey = self.config_manager.get('hotkey', default='f12')
        self.hotkey_display_button = ctk.CTkButton(
            main_conf_frame,
            text=current_hotkey.upper(),
            width=100,
            command=self._open_hotkey_selector
        )
        self.hotkey_display_button.grid(row=7, column=1, padx=5, pady=5, sticky="ew")
        record_hotkey_btn = ctk.CTkButton(main_conf_frame, text=self.localization_manager.get_string("record_hotkey_button"), width=70, command=self._start_hotkey_recording)
        record_hotkey_btn.grid(row=3, column=2, padx=(0,10), pady=5)

        # Recording Mode
        ctk.CTkLabel(main_conf_frame, text=self.localization_manager.get_string("record_mode_label")).grid(row=8, column=0, padx=10, pady=5, sticky="w")
        self.record_mode_var = tk.StringVar(value=self.config_manager.get("record_mode"))
        record_mode_frame = ctk.CTkFrame(main_conf_frame, fg_color="transparent")
        record_mode_frame.grid(row=8, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        ctk.CTkRadioButton(record_mode_frame, text=self.localization_manager.get_string("record_mode_hold"), variable=self.record_mode_var, value="hold", command=self.save_config).grid(row=0, column=0, padx=5, sticky="w")
        ctk.CTkRadioButton(record_mode_frame, text=self.localization_manager.get_string("record_mode_toggle"), variable=self.record_mode_var, value="toggle", command=self.save_config).grid(row=0, column=1, padx=10, sticky="w")

        # Auto-paste & Show panel
        self.auto_paste_var = tk.BooleanVar(value=self.config_manager.get("auto_paste_text"))
        ctk.CTkSwitch(main_conf_frame, text=self.localization_manager.get_string("auto_paste_switch"), variable=self.auto_paste_var, command=self.save_config).grid(row=9, column=0, columnspan=3, padx=10, pady=5, sticky="w")
        self.show_panel_var = tk.BooleanVar(value=self.config_manager.get("show_transcription_panel"))
        ctk.CTkSwitch(main_conf_frame, text=self.localization_manager.get_string("show_panel_switch"), variable=self.show_panel_var, command=self.save_config).grid(row=10, column=0, columnspan=3, padx=10, pady=5, sticky="w")

        # Windows autostart (sincronizado con estado real de Startup folder)
        from backend.startup_manager import StartupManager
        startup_manager = StartupManager()
        # Sincronizar el valor del config con el estado real del sistema
        actual_autostart_state = startup_manager.is_enabled()
        self.config_manager.set("autostart_windows", actual_autostart_state)

        self.autostart_windows_var = tk.BooleanVar(value=actual_autostart_state)
        ctk.CTkSwitch(main_conf_frame, text=self.localization_manager.get_string("autostart_windows_switch"), variable=self.autostart_windows_var, command=self.save_config).grid(row=11, column=0, columnspan=3, padx=10, pady=5, sticky="w")

        # Language selection
        ctk.CTkLabel(main_conf_frame, text=self.localization_manager.get_string("language_label")).grid(row=12, column=0, padx=10, pady=5, sticky="w")
        self.language_var = tk.StringVar(value=self.config_manager.get("default_language"))
        # Command triggers when selection changes
        ctk.CTkComboBox(main_conf_frame, values=["es", "en"], variable=self.language_var, state="readonly", command=lambda e: self.save_config()).grid(row=12, column=1, padx=5, pady=5, sticky="ew", columnspan=2)

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

        # --- Blocks Configuration Frame (v0.11.0) ---
        blocks_frame = ctk.CTkFrame(scroll_frame)
        blocks_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        blocks_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(blocks_frame, text="Bloques de Procesamiento (v0.11.0)", font=DesignSystem.TYPOGRAPHY["heading_medium"]).grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky="w")

        # Task Extractor Block
        self.block_task_enabled_var = tk.BooleanVar(value=self.config_manager.get("blocks", {}).get("task_extractor_enabled", True))
        ctk.CTkSwitch(blocks_frame, text="Extractor de Tareas", variable=self.block_task_enabled_var, command=self.save_config).grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="w")

        # Summary Block
        self.block_summary_enabled_var = tk.BooleanVar(value=self.config_manager.get("blocks", {}).get("summary_enabled", True))
        ctk.CTkSwitch(blocks_frame, text="Generar Resúmenes", variable=self.block_summary_enabled_var, command=self.save_config).grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="w")

        # Keyword Extractor Block
        self.block_keyword_enabled_var = tk.BooleanVar(value=self.config_manager.get("blocks", {}).get("keyword_extractor_enabled", True))
        ctk.CTkSwitch(blocks_frame, text="Extractor de Palabras Clave", variable=self.block_keyword_enabled_var, command=self.save_config).grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="w")

        # Botón para ver estadísticas de bloques
        block_stats_btn = ctk.CTkButton(blocks_frame, text="Ver Estadísticas de Bloques", width=150, command=self._show_block_stats)
        block_stats_btn.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="w")

        # --- Vocabulary Corrections Frame (v0.11.0) ---
        vocab_frame = ctk.CTkFrame(scroll_frame)
        vocab_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        vocab_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(vocab_frame, text="Correcciones de Vocabulario (v0.11.0)", font=DesignSystem.TYPOGRAPHY["heading_medium"]).grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky="w")

        # Descripción
        desc_label = ctk.CTkLabel(vocab_frame, text="Palabras que el modelo entiende mal (ej: CENF → zenf, cemp, cemf)", font=DesignSystem.TYPOGRAPHY["body_small"])
        desc_label.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="w")

        # Entry para agregar corrección
        input_frame = ctk.CTkFrame(vocab_frame, fg_color="transparent")
        input_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

        self.vocab_incorrect_var = tk.StringVar()
        incorrect_entry = ctk.CTkEntry(input_frame, textvariable=self.vocab_incorrect_var, placeholder_text="Palabra incorrecta (ej: zenf)")
        incorrect_entry.pack(side="left", padx=5, expand=True, fill="x")

        ctk.CTkLabel(input_frame, text="→").pack(side="left", padx=5)

        self.vocab_correct_var = tk.StringVar()
        correct_entry = ctk.CTkEntry(input_frame, textvariable=self.vocab_correct_var, placeholder_text="Palabra correcta (ej: CENF)")
        correct_entry.pack(side="left", padx=5, expand=True, fill="x")

        add_vocab_btn = ctk.CTkButton(input_frame, text="Agregar", width=80, command=self._add_vocab_correction)
        add_vocab_btn.pack(side="left", padx=5)

        # Lista de correcciones existentes
        self.vocab_list_frame = ctk.CTkScrollableFrame(vocab_frame, height=100)
        self.vocab_list_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")

        # Botón para ver/editar correcciones
        manage_vocab_btn = ctk.CTkButton(vocab_frame, text="Ver/Editar Correcciones", width=150, command=self._show_vocab_corrections)
        manage_vocab_btn.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="w")

        # Cargar lista de correcciones al iniciar
        self._refresh_vocab_list()

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
        ctk.CTkButton(header_frame, text=self.localization_manager.get_string("refresh_button"), width=80,
                      command=lambda: self.refresh_history_list(full_reload=True)).pack(side="right")

        # List Area
        self.history_scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.history_scroll_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        # Cache de transcripciones para tooltips (inicializar ANTES de refresh_history_list)
        self.transcriptions_cache = {}
        self._load_transcriptions_cache()

        self.refresh_history_list()

        # Auto-refresh cada 15 segundos (reducido de 5 para evitar bloqueos)
        self.after(15000, self.auto_refresh_history)

    def auto_refresh_history(self):
        """Auto-refresh optimizado: solo actualiza si hubo cambios"""
        if self.main_frame.get() == self.localization_manager.get_string("tab_history"):
            # Verificar si hubo cambios en el directorio de audio
            audio_path = self.config_manager.get("audio_path")
            if os.path.exists(audio_path):
                try:
                    # Obtener conteo actual y mtime más reciente
                    files = [f for f in os.listdir(audio_path) if f.endswith(".wav")]
                    current_count = len(files)
                    current_mtime = max([os.path.getmtime(os.path.join(audio_path, f)) for f in files]) if files else 0

                    # Solo refrescar si hubo cambios (agregando solo nuevos archivos)
                    if current_count != self.last_history_file_count or current_mtime != self.last_history_mtime:
                        self.refresh_history_list(full_reload=False)  # Solo agregar nuevos
                        self.last_history_file_count = current_count
                        self.last_history_mtime = current_mtime
                except Exception as e:
                    self.logger.error(f"Error verificando cambios en historial: {e}")

        self.after(15000, self.auto_refresh_history)
        self.logger.debug("Auto-optimizado: solo refresca si hay cambios (cada 15s)")

    def _load_transcriptions_cache(self):
        """Cargar cache de transcripciones desde el archivo JSONL"""
        transcriptions_path = os.path.join("transcriptions", "transcriptions_log.jsonl")
        if not os.path.exists(transcriptions_path):
            return

        try:
            with open(transcriptions_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                        audio_file = entry.get("audio_file", "")
                        transcription = entry.get("transcription", "")

                        if audio_file and transcription:
                            # Extraer solo el nombre del archivo sin la ruta
                            audio_filename = os.path.basename(audio_file)
                            self.transcriptions_cache[audio_filename] = transcription
                    except json.JSONDecodeError:
                        continue

            self.logger.debug(f"Cache de transcripciones cargado: {len(self.transcriptions_cache)} entradas")
        except Exception as e:
            self.logger.error(f"Error cargando cache de transcripciones: {e}")

    def refresh_history_list(self, full_reload=False):
        """
        Actualizar lista de historial con estrategia inteligente.

        Args:
            full_reload: Si True, recarga toda la lista. Si False, solo agrega nuevos archivos.
        """
        # Recargar cache de transcripciones
        self._load_transcriptions_cache()

        audio_path = self.config_manager.get("audio_path")
        if not os.path.exists(audio_path):
            if full_reload:  # Solo limpiar si es recarga completa
                for widget in self.history_scroll_frame.winfo_children():
                    widget.destroy()
                ctk.CTkLabel(self.history_scroll_frame, text="Directorio no encontrado").pack(pady=20)
            return

        # Obtener lista de archivos actuales
        max_display_files = 100
        files_list = self.file_manager.get_audio_files_list(limit=max_display_files)

        if not files_list:
            if full_reload and not self.loaded_history_files:
                ctk.CTkLabel(self.history_scroll_frame, text=self.localization_manager.get_string("no_audio_files")).pack(pady=20)
            return

        # Si es recarga completa, limpiar todo
        if full_reload:
            for widget in self.history_scroll_frame.winfo_children():
                widget.destroy()
            self.loaded_history_files.clear()

        # Obtener set de archivos actuales
        current_files = {f["name"] for f in files_list}

        # Encontrar archivos nuevos (que no están cargados)
        new_files = [f for f in files_list if f["name"] not in self.loaded_history_files]

        if new_files:
            # Agregar solo los archivos nuevos
            for file_info in new_files:
                self._create_history_item(file_info["name"], file_info["path"])
                self.loaded_history_files.add(file_info["name"])

            self.logger.debug(f"Agregados {len(new_files)} archivos nuevos al historial")

        # Actualizar archivos conocidos
        self.loaded_history_files = current_files

    def _create_history_item(self, filename, full_path):
        """Crear item de historial con emoji personalizable, play button y menú contextual"""
        import os
        from datetime import datetime

        item_frame = ctk.CTkFrame(self.history_scroll_frame)
        item_frame.pack(fill="x", pady=2, padx=5)

        # Obtener emoji personalizado (si existe)
        custom_emoji = self.metadata_manager.get_emoji(filename, default="🎤")

        # Obtener metadata del archivo
        try:
            file_stat = os.stat(full_path)
            file_size = file_stat.st_size
            file_mtime = datetime.fromtimestamp(file_stat.st_mtime)

            # Nombre representativo: fecha + hora
            if filename.startswith("audio_"):
                # Formato: audio_YYYYMMDD_HHMMSS.wav
                try:
                    parts = filename.replace(".wav", "").split("_")
                    if len(parts) >= 3:
                        date_part = parts[1]  # YYYYMMDD
                        time_part = parts[2]  # HHMMSS
                        # Formatear como DD/MM/YYYY HH:MM:SS
                        formatted_date = f"{date_part[6:8]}/{date_part[4:6]}/{date_part[0:4]}"
                        formatted_time = f"{time_part[0:2]}:{time_part[2:4]}:{time_part[4:6]}"
                        display_name = f"{custom_emoji} {formatted_date} {formatted_time}"
                    else:
                        display_name = f"{custom_emoji} {filename}"
                except:
                    display_name = f"{custom_emoji} {filename}"
            else:
                display_name = f"{custom_emoji} {filename}"

            # Formatear tamaño del archivo
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"

            # Tooltip con información completa y transcripción
            tooltip_text = f"📁 {filename}\n📅 {file_mtime.strftime('%d/%m/%Y %H:%M:%S')}\n💾 {size_str}\n📍 {full_path}"

            # Agregar transcripción si está disponible en el cache
            if filename in self.transcriptions_cache:
                transcription = self.transcriptions_cache[filename]
                # Truncar transcripción si es muy larga (máx 200 chars)
                if len(transcription) > 200:
                    transcription = transcription[:200] + "..."
                tooltip_text += f"\n\n💬 {transcription}"

        except Exception as e:
            self.logger.error(f"Error obteniendo metadata de {filename}: {e}")
            display_name = f"🎤 {filename}"
            tooltip_text = f"📁 {filename}\n📍 {full_path}"

        # Info Frame (con tooltip)
        info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        info_frame.pack(side="left", padx=10, pady=5, fill="x", expand=True)

        # Nombre representativo
        name_label = ctk.CTkLabel(info_frame, text=display_name, font=DesignSystem.TYPOGRAPHY["body_small"], anchor="w")
        name_label.pack(side="left", fill="x", expand=True)

        # Agregar tooltip (usando bind en CustomTkinter)
        self._bind_tooltip(name_label, tooltip_text)

        # Action Button Frame
        action_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        action_frame.pack(side="right", padx=5)

        # Emoji Picker Button (NUEVO v0.13.0)
        emoji_btn = ctk.CTkButton(
            action_frame,
            text=custom_emoji,
            width=35,
            height=24,
            font=ctk.CTkFont(size=14),
            fg_color="#8B5CF6",
            hover_color="#7C3AED",
            command=lambda f=filename, e=custom_emoji: self._change_emoji(f, e, emoji_btn, name_label)
        )
        emoji_btn.pack(side="left", padx=2)

        # Play Button (NUEVO)
        play_btn = ctk.CTkButton(action_frame, text="▶️", width=35, height=24, fg_color="#10B981", hover_color="#059669")
        play_btn.configure(command=lambda p=full_path, b=play_btn: self._play_audio_file(p, b))
        play_btn.pack(side="left", padx=2)

        # Transcribe Button
        ctk.CTkButton(action_frame, text=self.localization_manager.get_string("transcribe_button"), width=80, height=24,
                      command=lambda p=full_path: self._start_retranscription(p)).pack(side="left", padx=2)

        # Delete Button
        ctk.CTkButton(action_frame, text="🗑️", width=30, height=24, fg_color="#EF4444", hover_color="#DC2626",
                      command=lambda p=full_path: self._delete_audio_file(p)).pack(side="left", padx=2)

    def _bind_tooltip(self, widget, text):
        """Simular tooltip para CustomTkinter"""
        def on_enter(e):
            # Mostrar info en status bar
            self.update_status(text, "blue")

        def on_leave(e):
            # Restaurar estado
            self.update_status(self.localization_manager.get_string("status_ready"), "white")

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def _change_emoji(self, filename: str, current_emoji: str, emoji_btn, name_label):
        """
        Cambiar emoji de una transcripción.

        Args:
            filename: Nombre del archivo de audio
            current_emoji: Emoji actual
            emoji_btn: Botón de emoji a actualizar
            name_label: Label de nombre a actualizar
        """
        def on_emoji_selected(new_emoji: str):
            """Callback cuando se selecciona un emoji."""
            # Guardar en metadata
            self.metadata_manager.set_emoji(filename, new_emoji)

            # Actualizar botón
            emoji_btn.configure(text=new_emoji)

            # Actualizar label (reemplazar emoji anterior por nuevo)
            current_text = name_label.cget("text")
            if current_text.startswith(current_emoji):
                new_text = current_text.replace(current_emoji, new_emoji, 1)
            else:
                new_text = f"{new_emoji} {current_text}"
            name_label.configure(text=new_text)

            self.logger.info(f"Emoji cambiado para {filename}: {current_emoji} → {new_emoji}")

        # Mostrar selector de emoji
        show_emoji_picker(self, on_emoji_selected, current_emoji)

    def _open_hotkey_selector(self):
        """Abrir selector de hotkeys con modificadores."""
        def on_hotkey_selected(new_hotkey: str):
            """Callback cuando se selecciona un hotkey."""
            # Guardar en config
            self.config_manager.config["hotkey"] = new_hotkey
            self.config_manager.save_config()

            # Actualizar botón
            self.hotkey_display_button.configure(text=new_hotkey.upper())

            # Actualizar display label en status bar
            self.hotkey_display_label.configure(
                text=self.localization_manager.get_string("hotkey_display", hotkey=new_hotkey.upper())
            )

            # Re-registrar hotkey (detener anterior, registrar nuevo)
            self._reregister_hotkey(new_hotkey)

            self.logger.info(f"Hotkey cambiado: {self.config_manager.get('hotkey')} → {new_hotkey}")

        # Mostrar selector
        current_hotkey = self.config_manager.get('hotkey', default='f12')
        show_hotkey_selector(self, on_hotkey_selected, current_hotkey)

    def _reregister_hotkey(self, new_hotkey: str):
        """
        Re-registrar hotkey con el nuevo valor.

        Args:
            new_hotkey: Nuevo hotkey string
        """
        try:
            import keyboard

            # Remover hotkey anterior
            old_hotkey = self.config_manager.get('hotkey', default='f12')
            try:
                keyboard.remove_hotkey(old_hotkey)
                self.logger.debug(f"Hotkey removido: {old_hotkey}")
            except:
                pass  # No existía o ya fue removido

            # Remover todos los hooks anteriores
            keyboard.unhook_all()

            # Re-iniciar el sistema de hotkeys
            self._setup_hotkey_system()

            self.logger.info(f"Hotkey re-registrado: {new_hotkey}")

        except Exception as e:
            self.logger.error(f"Error re-registrando hotkey: {e}")

    def _play_audio_file(self, file_path, button):
        """Reproducir archivo de audio con toggle play/stop"""
        # Si ya está reproduciendo este archivo, detener
        if self.currently_playing and self.currently_playing[0] == file_path:
            self._stop_audio_file()
            return

        # Si está reproduciendo otro archivo, detenerlo primero
        if self.currently_playing:
            self._stop_audio_file()

        # Actualizar estado
        self.currently_playing = (file_path, button)
        button.configure(text="⏹️", fg_color="#EF4444", hover_color="#DC2626")

        def play_in_thread():
            try:
                import winsound
                # SND_FILENAME | SND_ASYNC = reproducción asíncrona
                winsound.PlaySound(file_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                self.after(100, lambda: self.update_status(f"▶️ Reproduciendo: {os.path.basename(file_path)}", "green"))

                # Esperar a que termine la reproducción (estimar duración del archivo)
                # WAV típico: ~1 segundo por 100KB (aproximado)
                import os
                file_size = os.path.getsize(file_path)
                estimated_duration = max(1, file_size / 100000)  # Estimación conservadora

                # Esperar duración + margen
                import time
                time.sleep(estimated_duration + 0.5)

                # Restaurar botón
                self.after(0, lambda: self._reset_play_button(file_path))

            except Exception as e:
                self.after(100, lambda: self.update_status(f"❌ Error reproduciendo audio: {e}", "red"))
                self.logger.error(f"Error reproduciendo audio: {e}")
                self.after(0, lambda: self._reset_play_button(file_path))

        # Ejecutar en thread separado
        import threading
        thread = threading.Thread(target=play_in_thread, daemon=True)
        self.playing_threads[file_path] = thread
        thread.start()

    def _stop_audio_file(self):
        """Detener reproducción actual"""
        if self.currently_playing:
            file_path, button = self.currently_playing
            # Detener cualquier sonido
            try:
                import winsound
                winsound.PlaySound(None, winsound.SND_PURGE)
            except:
                pass

            # Resetear botón SOLO si todavía existe (protección contra widgets destruidos)
            try:
                # Verificar que el widget todavía existe
                if button.winfo_exists():
                    button.configure(text="▶️", fg_color="#10B981", hover_color="#059669")
            except:
                # Widget fue destruido, ignorar
                pass

            self.currently_playing = None
            self.update_status("⏹️ Reproducción detenida", "white")

    def _reset_play_button(self, file_path):
        """Resetear botón de play después de terminar reproducción"""
        if self.currently_playing and self.currently_playing[0] == file_path:
            _, button = self.currently_playing

            # Resetear botón SOLO si todavía existe
            try:
                if button.winfo_exists():
                    button.configure(text="▶️", fg_color="#10B981", hover_color="#059669")
            except:
                # Widget fue destruido, ignorar
                pass

            self.currently_playing = None
            self.update_status("✔️ Reproducción terminada", "white")

        # Limpiar thread del diccionario
        if file_path in self.playing_threads:
            del self.playing_threads[file_path]

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
                self.logger.error(f"Error verificando API Key de Groq: {e}")
                self.api_key_status_label.configure(text="●", text_color=DesignSystem.COLORS["error"])
        else:
            self.api_key_status_label.configure(text="●", text_color="grey")

    def _show_block_stats(self):
        """Mostrar estadísticas de los bloques de procesamiento."""
        try:
            stats = self.transcriber.get_block_stats()

            # Crear ventana de estadísticas
            stats_window = ctk.CTkToplevel(self)
            stats_window.title("Estadísticas de Bloques")
            stats_window.geometry("500x400")

            # Frame principal
            main_frame = ctk.CTkScrollableFrame(stats_window)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)

            # Título
            ctk.CTkLabel(main_frame, text="Estadísticas de Bloques", font=DesignSystem.TYPOGRAPHY["heading_medium"]).pack(pady=10)

            if not stats:
                ctk.CTkLabel(main_frame, text="No hay bloques configurados").pack(pady=20)
                return

            # Mostrar estadísticas de cada bloque
            for block_name, block_stats in stats.items():
                frame = ctk.CTkFrame(main_frame)
                frame.pack(fill="x", pady=5, padx=5)

                # Nombre y estado
                status_text = "✅ Activo" if block_stats['enabled'] else "❌ Inactivo"
                status_color = "green" if block_stats['enabled'] else "gray"

                ctk.CTkLabel(
                    frame,
                    text=f"{block_name}",
                    font=DesignSystem.TYPOGRAPHY["body_bold"]
                ).pack(side="left", padx=10, pady=5)

                ctk.CTkLabel(
                    frame,
                    text=status_text,
                    text_color=status_color
                ).pack(side="right", padx=10, pady=5)

                # Estadísticas de procesamiento
                if 'stats' in block_stats:
                    stats_data = block_stats['stats']
                    stats_text = f"Procesados: {stats_data.get('processed', 0)} | Fallos: {stats_data.get('failed', 0)}"

                    ctk.CTkLabel(
                        frame,
                        text=stats_text,
                        font=DesignSystem.TYPOGRAPHY["body_small"]
                    ).pack(side="left", padx=10)

            # Botón cerrar
            ctk.CTkButton(
                main_frame,
                text="Cerrar",
                command=stats_window.destroy,
                width=100
            ).pack(pady=10)

            self.logger.info("Estadísticas de bloques mostradas")

        except Exception as e:
            self.logger.error(f"Error mostrando estadísticas de bloques: {e}")
            self.update_status("Error al mostrar estadísticas", "red")

    def _add_vocab_correction(self):
        """Agregar corrección de vocabulario personalizado."""
        incorrect = self.vocab_incorrect_var.get().strip()
        correct = self.vocab_correct_var.get().strip()

        if not incorrect or not correct:
            self.update_status("Debe ingresar ambas palabras", "orange")
            return

        # Usar el CustomVocabulary del transcriber
        if hasattr(self.transcriber, 'custom_vocab'):
            success = self.transcriber.custom_vocab.add_correction(incorrect, correct)
            if success:
                self.update_status(f"Corrección agregada: {incorrect} → {correct}", "green")
                # Limpiar campos
                self.vocab_incorrect_var.set("")
                self.vocab_correct_var.set("")
                # Actualizar lista de correcciones
                self._refresh_vocab_list()
            else:
                self.update_status("Error al agregar corrección", "red")
        else:
            self.update_status("CustomVocabulary no disponible", "red")

    def _show_vocab_corrections(self):
        """Mostrar ventana para ver/editar correcciones de vocabulario."""
        try:
            if not hasattr(self.transcriber, 'custom_vocab'):
                self.update_status("CustomVocabulary no disponible", "red")
                return

            corrections = self.transcriber.custom_vocab.get_corrections()

            # Crear ventana de correcciones
            vocab_window = ctk.CTkToplevel(self)
            vocab_window.title("Correcciones de Vocabulario")
            vocab_window.geometry("600x500")

            # Frame principal
            main_frame = ctk.CTkScrollableFrame(vocab_window)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)

            # Título
            ctk.CTkLabel(main_frame, text="Correcciones de Vocabulario Personalizado", font=DesignSystem.TYPOGRAPHY["heading_medium"]).pack(pady=10)

            # Instrucciones
            ctk.CTkLabel(main_frame, text="Palabras que el modelo entiende mal y su corrección:", font=DesignSystem.TYPOGRAPHY["body_small"]).pack(pady=5)

            if not corrections:
                ctk.CTkLabel(main_frame, text="No hay correcciones configuradas").pack(pady=20)
            else:
                # Mostrar lista de correcciones
                for incorrect, correct in corrections.items():
                    row_frame = ctk.CTkFrame(main_frame)
                    row_frame.pack(fill="x", pady=2, padx=5)

                    # Incorrecta
                    ctk.CTkLabel(row_frame, text=incorrect, font=DesignSystem.TYPOGRAPHY["body_bold"]).pack(side="left", padx=10)

                    # Flecha
                    ctk.CTkLabel(row_frame, text="→", font=DesignSystem.TYPOGRAPHY["heading_large"]).pack(side="left", padx=10)

                    # Correcta
                    ctk.CTkLabel(row_frame, text=correct, font=DesignSystem.TYPOGRAPHY["body_bold"], text_color="#10B981").pack(side="left", padx=10)

                    # Botón eliminar
                    delete_btn = ctk.CTkButton(row_frame, text="🗑️", width=30, fg_color="#EF4444", hover_color="#DC2626",
                                            command=lambda inc=incorrect: self._delete_vocab_correction(inc, vocab_window, main_frame))
                    delete_btn.pack(side="right", padx=5)

            # Botón cerrar
            ctk.CTkButton(main_frame, text="Cerrar", command=vocab_window.destroy, width=100).pack(pady=10)

            self.logger.info("Ventana de correcciones mostrada")

        except Exception as e:
            self.logger.error(f"Error mostrando correcciones: {e}")
            self.update_status("Error al mostrar correcciones", "red")

    def _delete_vocab_correction(self, incorrect: str, window, main_frame):
        """Eliminar corrección de vocabulario."""
        try:
            if hasattr(self.transcriber, 'custom_vocab'):
                success = self.transcriber.custom_vocab.remove_correction(incorrect)
                if success:
                    self.update_status(f"Corrección eliminada: {incorrect}", "green")
                    # Recrear contenido de la ventana
                    for widget in main_frame.winfo_children():
                        if isinstance(widget, ctk.CTkScrollableFrame):
                            # Limpiar y volver a cargar
                            for child in widget.winfo_children():
                                child.destroy()

                            # Recargar correcciones
                            corrections = self.transcriber.custom_vocab.get_corrections()
                            if corrections:
                                for inc, cor in corrections.items():
                                    row_frame = ctk.CTkFrame(widget)
                                    row_frame.pack(fill="x", pady=2, padx=5)

                                    ctk.CTkLabel(row_frame, text=inc, font=DesignSystem.TYPOGRAPHY["body_bold"]).pack(side="left", padx=10)
                                    ctk.CTkLabel(row_frame, text="→", font=DesignSystem.TYPOGRAPHY["heading_large"]).pack(side="left", padx=10)
                                    ctk.CTkLabel(row_frame, text=cor, font=DesignSystem.TYPOGRAPHY["body_bold"], text_color="#10B981").pack(side="left", padx=10)

                                    delete_btn = ctk.CTkButton(row_frame, text="🗑️", width=30, fg_color="#EF4444", hover_color="#DC2626",
                                                        command=lambda i=inc: self._delete_vocab_correction(i, window, widget))
                                    delete_btn.pack(side="right", padx=5)
                            break
                else:
                    self.update_status("Error al eliminar corrección", "red")
        except Exception as e:
            self.logger.error(f"Error eliminando corrección: {e}")
            self.update_status("Error al eliminar corrección", "red")

    def _refresh_vocab_list(self):
        """Refrescar lista de correcciones en la pestaña de configuración."""
        try:
            # Limpiar lista actual
            for widget in self.vocab_list_frame.winfo_children():
                widget.destroy()

            if hasattr(self.transcriber, 'custom_vocab'):
                corrections = self.transcriber.custom_vocab.get_corrections()

                if not corrections:
                    ctk.CTkLabel(self.vocab_list_frame, text="No hay correcciones configuradas", font=DesignSystem.TYPOGRAPHY["body_small"]).pack(pady=5)
                else:
                    # Mostrar últimas 5 correcciones
                    for incorrect, correct in list(corrections.items())[:5]:
                        item = ctk.CTkLabel(self.vocab_list_frame, text=f"{incorrect} → {correct}", font=DesignSystem.TYPOGRAPHY["body_small"])
                        item.pack(anchor="w", padx=10, pady=2)

        except Exception as e:
            self.logger.error(f"Error refrescando lista de vocabulario: {e}")



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

        # Obtener configuración de bloques actual
        blocks_config = self.config_manager.get("blocks", {})

        settings = {
            "groq_api_key": self.api_key_var.get(),
            "asr_provider": self.asr_provider_var.get(),
            "nvidia_enabled": self.nvidia_enabled_var.get() if hasattr(self, 'nvidia_enabled_var') else False,
            "nvidia_api_key": self.nvidia_api_key_var.get() if hasattr(self, 'nvidia_api_key_var') else "",
            "nvidia_mode": self.nvidia_mode_var.get() if hasattr(self, 'nvidia_mode_var') else "cloud",
            "faster_whisper_enabled": self.faster_whisper_enabled_var.get(),
            "faster_whisper_model": self.faster_whisper_model_var.get(),
            "faster_whisper_device": self.faster_whisper_device_var.get(),
            "hotkey": self.hotkey_var.get(),
            "record_mode": self.record_mode_var.get(),
            "auto_paste_text": self.auto_paste_var.get(), "show_transcription_panel": self.show_panel_var.get(),
            "audio_path": self.audio_path_var.get(), "transcriptions_path": self.transcriptions_path_var.get(),
            "save_audio": self.save_audio_var.get(), "save_logs": self.save_logs_var.get(),
            "max_audio_files": int(self.config_manager.get("max_audio_files")),
            "max_log_entries": int(self.config_manager.get("max_log_entries")),
            "audio_priority_apps": self.config_manager.get("audio_priority_apps"),
            "default_language": self.language_var.get(),
            "autostart_windows": self.autostart_windows_var.get(),
            "blocks": {
                **blocks_config,  # Mantener configuración existente
                "task_extractor_enabled": self.block_task_enabled_var.get(),
                "summary_enabled": self.block_summary_enabled_var.get(),
                "keyword_extractor_enabled": self.block_keyword_enabled_var.get()
            }
        }
        self.config_manager.set_multiple(settings)
        
        # --- Autostart con Windows ---
        from backend.startup_manager import StartupManager
        startup_manager = StartupManager()
        success = startup_manager.toggle(settings["autostart_windows"])
        if not success:
            self.logger.error(f"Error al configurar inicio automático: {settings['autostart_windows']}")
        # ----------------------------
        
        # Check for language change
        if self.language_var.get() != old_lang:
            self.config_manager.set_language(self.language_var.get())
            self.recreate_ui_for_language_change()
        
        # --- API Key Logic Fix ---
        if settings["groq_api_key"]:
            os.environ["GROQ_API_KEY"] = settings["groq_api_key"]
            self.transcriber.reload_client()
        # -------------------------

        # Verify hotkey change
        if settings["hotkey"] != self.transcriber.hotkey:
             self.transcriber.update_hotkey(settings["hotkey"])

        # Recargar bloques si cambió la configuración
        old_blocks_config = self.config_manager.get("blocks", {})
        new_blocks_config = settings.get("blocks", {})
        if old_blocks_config != new_blocks_config:
            self.logger.info("Configuración de bloques cambió, recargando...")
            self.transcriber.reload_blocks()
        
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
            self.transcription_textbox.delete("1.0", "end")
            self.transcription_textbox.insert("1.0", text)
        pyperclip.copy(text)
        if self.config_manager.get("auto_paste_text"):
            self.logger.info("Auto-pegando transcripción.")
            # Pequeño delay para asegurar que el portapapeles esté listo
            import time
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'v')

    def display_transcription(self, text):
        """Mostrar transcripción con protección contra duplicados"""
        import time
        current_time = time.time()

        # Evitar duplicados: mismo texto dentro de 1 segundo
        if text == self.last_transcription_text and (current_time - self.last_transcription_time) < 1.0:
            self.logger.warning("Detectada transcripción duplicada, ignorando...")
            return

        self.last_transcription_time = current_time
        self.last_transcription_text = text

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
        self.logger.info("Cerrando aplicación por completo.")
        self.quit_application()

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