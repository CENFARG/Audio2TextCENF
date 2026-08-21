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

class ToolTip:
    """Tooltip widget para CustomTkinter - Muestra ventana emergente flotante"""
    def __init__(self, widget, text=None, wraplength=400, background="#1E293B", foreground="#F8FAFC", bordercolor="#2563EB"):
        self.widget = widget
        self.text = text
        self.wraplength = wraplength
        self.background = background
        self.foreground = foreground
        self.bordercolor = bordercolor
        self.tip_window = None
        self.tip_id = None
        self.x = self.y = 0

    def show_tip(self, text=None):
        """Mostrar tooltip en posición del mouse"""
        self.text = text or self.text

        if self.tip_window or not self.text:
            return

        # Obtener posición del mouse
        x = self.widget.winfo_pointerx()
        y = self.widget.winfo_pointery()

        # Crear ventana flotante (toplevel)
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # Sin bordes de ventana
        tw.wm_geometry(f"+{x + 15}+{y + 15}")  # Offset del cursor

        # Frame con borde y color de fondo
        frame = tk.Frame(tw, background=self.bordercolor, borderwidth=1, relief="solid")
        frame.pack(ipadx=1, ipady=1)

        # Label con el texto del tooltip
        label = tk.Label(
            frame,
            text=self.text,
            justify=tk.LEFT,
            background=self.background,
            foreground=self.foreground,
            relief=tk.FLAT,
            borderwidth=0,
            wraplength=self.wraplength,
            font=("Segoe UI", 10),
            padx=10,
            pady=8
        )
        label.pack(ipadx=1)

    def hide_tip(self):
        """Ocultar tooltip"""
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

def create_tooltip(widget, text):
    """Crear y asociar tooltip a un widget"""
    tool_tip = ToolTip(widget)

    def enter(event):
        tool_tip.show_tip(text)

    def leave(event):
        tool_tip.hide_tip()

    widget.bind("<Enter>", enter)
    widget.bind("<Leave>", leave)

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
        # Título dinámico con versión desde config (no depende de lang files)
        _version = self.config_manager.get("app_version", "0.0.0")
        self.title(f"Audio2Text CENF v{_version}")
        # Ventana cuadrada por defecto (mismo ancho que alto)
        self.geometry("590x590")
        self.minsize(540, 540)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Cargar geometry guardada v0.14.0
        self._load_window_geometry()

        # Bind para guardar geometry cuando se redimensiona
        self.bind('<Configure>', self._on_window_resize)

        try:
            # Buscar icono en múltiples ubicaciones
            import os
            _icon_paths = [
                "icono.ico",
                os.path.join("assets", "icons", "icono.ico"),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons", "icono.ico"),
            ]
            _icon_loaded = False
            for _ip in _icon_paths:
                if os.path.exists(_ip):
                    self.iconbitmap(_ip)
                    self.logger.info(f"Icono cargado desde: {_ip}")
                    _icon_loaded = True
                    break
            if not _icon_loaded:
                self.logger.warning("No se encontró icono.ico en ninguna ubicación.")
        except Exception as e:
            self.logger.warning(f"Error cargando icono: {e}")

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

        # --- Tutorial ELIMINADO (requisito v0.15.1): no mostrar instructivo al iniciar ---
        self.tutorial_manager = None

        # Crear overlay de grabación - REACTIVADO
        from ui.recording_overlay import RecordingOverlay
        self.recording_overlay = RecordingOverlay(self)
        
        # Crear transcriber — FIX v0.15.0: la UI ya NO se actualiza desde el thread
        # de grabación (eso trababa la captura en grabaciones largas). El timer se
        # consume por polling desde el main thread con _poll_recording_timer().
        self.transcriber = Transcriber(
            self.config_manager, 
            self.sound_manager, 
            self.file_manager, 
            self.update_status, 
            self.display_transcription, 
            self.localization_manager,
            overlay_callback=None  # el overlay ahora se actualiza vía cola + polling
        )
        # Iniciar el polling del timer de grabación (main thread, nunca bloquea audio)
        self.after(250, self._poll_recording_timer)

        self.updater = Updater(
            current_version=self.config_manager.get("app_version"),
            github_repo="CENFARG/Audio2TextCENF"
        )

        self.tray_icon = None
        self.hotkey_recording_window = None
        self.create_widgets()
        self.update_file_info()
        self.after(1000, self._check_api_key)
        
        # Tutorial deshabilitado — no iniciar

    def create_widgets(self):
        self.logger.debug("Creando widgets de la interfaz de usuario.")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Switch omnipresente de idioma de transcripción (visible en todas las pestañas) ---
        self._create_omnipresent_lang_switch()

        self.main_frame = ctk.CTkTabview(self)
        self.main_frame.grid(row=1, column=0, padx=10, pady=(10, 5), sticky="nsew")
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
        self.bottom_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        cenf_link = ctk.CTkLabel(self.bottom_frame, text=self.localization_manager.get_string("cenf_website"), font=DesignSystem.TYPOGRAPHY["link"], text_color=DesignSystem.COLORS["primary"], cursor="hand2")
        cenf_link.pack(side="right")
        cenf_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://www.cenfarg.com.ar"))
        self.logger.debug("Widgets de la interfaz de usuario creados.")

    def _create_omnipresent_lang_switch(self):
        """Barra superior omnipresente con switch ES ⟷ EN para idioma de transcripción."""
        top_bar = ctk.CTkFrame(self, fg_color="transparent", height=28)
        top_bar.grid(row=0, column=0, padx=10, pady=(5, 0), sticky="ew")
        top_bar.grid_columnconfigure(0, weight=1)

        # Idioma actual de transcripción
        current = self.config_manager.get("transcription_language", self.config_manager.get("default_language", "es"))
        self._lang_switch_var = tk.StringVar(value=current)

        # Label + SegmentedButton (ES / EN) — 1 clic para cambiar
        ctk.CTkLabel(top_bar, text="🌐 Transcripción:", font=DesignSystem.TYPOGRAPHY["body_small"]).pack(side="left", padx=(5, 5))

        self._lang_switch = ctk.CTkSegmentedButton(
            top_bar,
            values=["ES", "EN"],
            variable=self._lang_switch_var,
            command=self._on_omnipresent_lang_change,
            width=90,
            height=24,
            font=ctk.CTkFont(size=11, weight="bold"),
            selected_color=DesignSystem.COLORS["primary"],
            selected_hover_color=DesignSystem.COLORS["primary_hover"],
        )
        self._lang_switch.pack(side="left")
        # Seleccionar valor inicial correctamente (SegmentedButton usa el string exacto)
        self._lang_switch.set(current.upper())

        self._lang_switch_label = ctk.CTkLabel(
            top_bar,
            text="Español" if current == "es" else "English",
            font=DesignSystem.TYPOGRAPHY["body_small"],
            text_color=DesignSystem.COLORS["text_secondary"],
        )
        self._lang_switch_label.pack(side="left", padx=(8, 0))

    def _on_omnipresent_lang_change(self, value: str):
        """Callback del switch omnipresente — cambia idioma de transcripción y sincroniza config."""
        new_lang = value.lower()  # "ES" -> "es"
        old = self.config_manager.get("transcription_language", "es")
        if new_lang == old:
            return
        self.config_manager.set("transcription_language", new_lang)
        # Mantener default_language en es (interfaz siempre español) pero también actualizarlo
        # para compatibilidad si alguien lee default_language
        if self.config_manager.get("default_language") != "es":
            self.config_manager.set("default_language", "es")
        self._update_lang_switch_label(new_lang)
        # Sincronizar el ComboBox de Configuración si existe
        if hasattr(self, 'language_var'):
            self.language_var.set(new_lang)
        self.logger.info(f"Idioma de transcripción (omnipresente): {old} → {new_lang}")
        self.update_status(f"🌐 Transcripción: {'Español' if new_lang == 'es' else 'English'}", "green")

    def _update_lang_switch_label(self, lang: str):
        if hasattr(self, '_lang_switch_label'):
            self._lang_switch_label.configure(text="Español" if lang == "es" else "English")

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

    def _poll_recording_timer(self):
        """FIX v0.15.0: polling del timer/overlay de grabación desde el main thread.

        El bucle de captura de audio ya NO actualiza la UI directamente (eso
        trababa la lectura en grabaciones largas → audio cortado → tildes/palabras
        perdidas). Los eventos llegan por cola y este método los pinta cada 250ms.
        """
        try:
            transcriber = getattr(self, 'transcriber', None)
            if transcriber is not None:
                while True:
                    event = transcriber.get_timer_event()
                    if event is None:
                        break
                    if event[0] == "timer" and len(event) >= 3:
                        _, minutes, seconds = event
                        # Timer en el status label
                        msg = self.localization_manager.get_string("status_recording")
                        self.status_label.configure(text=f"{msg} {minutes:02d}:{seconds:02d}", text_color=DesignSystem.COLORS["success"])
                        # Overlay de grabación
                        if self.recording_overlay:
                            self.recording_overlay.set_recording()
                            self.recording_overlay.update_timer(minutes, seconds)
                    elif event[0] == "limit" and len(event) >= 2:
                        _, max_seconds = event
                        self.update_status(f"Grabación cortada por límite de {max_seconds}s", "orange")
                    elif event[0] == "overlay" and len(event) >= 3:
                        _, state, minutes, seconds = (event + (0, 0))[:4]
                        # Mantener compatibilidad con update_overlay (que usa after(0))
                        self.update_overlay(state, minutes or 0, seconds or 0)
        except Exception as e:
            self.logger.debug(f"Error en poll del timer: {e}")
        finally:
            self.after(250, self._poll_recording_timer)


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

        # Button frame - FIX: 2 botones ocupan todo el ancho del textbox, centrados e iguales
        button_frame = ctk.CTkFrame(tab, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=10, pady=(0, 5), sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1, uniform="btn")
        ctk.CTkButton(button_frame, text=self.localization_manager.get_string("clear_audio_button"), command=self.clear_audio_with_feedback).grid(row=0, column=0, padx=(0, 5), sticky="ew")
        ctk.CTkButton(button_frame, text=self.localization_manager.get_string("clear_transcriptions_button"), command=self.clear_logs_with_feedback).grid(row=0, column=1, padx=(5, 0), sticky="ew")
        

        
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

        self.api_key_status_label = ctk.CTkLabel(main_conf_frame, text="●", font=("Segoe UI", 20), text_color="grey", cursor="hand2")
        self.api_key_status_label.grid(row=1, column=0, padx=(10,0), sticky="w")
        self.api_key_status_label.bind("<Button-1>", lambda e: self._on_api_dot_click())
        self.api_key_var = tk.StringVar(value=self.config_manager.get("groq_api_key"))
        api_entry = ctk.CTkEntry(main_conf_frame, textvariable=self.api_key_var, show="*", placeholder_text=self.localization_manager.get_string("api_key_placeholder"))
        api_entry.grid(row=1, column=1, padx=5, sticky="ew")
        api_entry.bind("<FocusOut>", lambda e: self.save_config()) # Autosave on focus out
        verify_btn = ctk.CTkButton(main_conf_frame, text=self.localization_manager.get_string("verify_button"), width=70, command=lambda: self._check_api_key(show_popup=True))
        verify_btn.grid(row=1, column=2, padx=(0,10))

        # ASR Provider Selection (solo Groq — Gemini ELIMINADO por completo de la
        # herramienta: benchmark 5-87s por transcripción vs 1-2s de Groq, inutilizable)
        ctk.CTkLabel(main_conf_frame, text=self.localization_manager.get_string("asr_provider_label")).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.asr_provider_var = tk.StringVar(value=self.config_manager.get("asr_provider", "groq"))
        asr_provider_frame = ctk.CTkFrame(main_conf_frame, fg_color="transparent")
        asr_provider_frame.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        ctk.CTkRadioButton(asr_provider_frame, text=self.localization_manager.get_string("asr_provider_groq"), variable=self.asr_provider_var, value="groq", command=self.save_config).grid(row=0, column=0, padx=5, sticky="w")
        # FIX v0.15.0: Gemini ELIMINADO (backend + frontend) — solo Groq, el que funciona
        # NVIDIA oculto de la UI pero funcional en config.json

        # Hotkey (v0.14.0 - Selector inline compacto)
        ctk.CTkLabel(main_conf_frame, text=self.localization_manager.get_string("hotkey_label")).grid(row=7, column=0, padx=10, pady=5, sticky="w")

        # Parsear hotkey actual
        current_hotkey = self.config_manager.get('hotkey', default='f12')
        from backend.hotkey_manager import HotkeyManager
        hm = HotkeyManager()
        parsed = hm.parse_hotkey_string(current_hotkey)

        # Frame compacto para hotkey selector - GRID interno mejor control
        hotkey_frame = ctk.CTkFrame(main_conf_frame, fg_color="transparent")
        hotkey_frame.grid(row=7, column=1, columnspan=2, padx=2, pady=2, sticky="ew")

        # Fila 1: Modificadores (checkboxes compactos)
        self.hotkey_ctrl_var = tk.BooleanVar(value="ctrl" in parsed.modifiers)
        self.hotkey_alt_var = tk.BooleanVar(value="alt" in parsed.modifiers)
        self.hotkey_shift_var = tk.BooleanVar(value="shift" in parsed.modifiers)

        ctk.CTkCheckBox(hotkey_frame, text="Ctrl", variable=self.hotkey_ctrl_var, command=self._update_hotkey_from_inline, width=50).grid(row=0, column=0, padx=1)
        ctk.CTkCheckBox(hotkey_frame, text="Alt", variable=self.hotkey_alt_var, command=self._update_hotkey_from_inline, width=50).grid(row=0, column=1, padx=1)
        ctk.CTkCheckBox(hotkey_frame, text="Shift", variable=self.hotkey_shift_var, command=self._update_hotkey_from_inline, width=50).grid(row=0, column=2, padx=1)

        # Fila 2: Tecla principal + Preview
        self.hotkey_key_var = tk.StringVar(value=parsed.key.upper())
        all_keys = [f"F{i}" for i in range(1, 13)] + [chr(ord('A') + i) for i in range(26)]

        self.hotkey_dropdown = ctk.CTkOptionMenu(
            hotkey_frame,
            variable=self.hotkey_key_var,
            values=all_keys,
            command=lambda x: self._update_hotkey_from_inline(),
            width=60
        )
        self.hotkey_dropdown.grid(row=1, column=0, columnspan=2, padx=1, pady=(3,0), sticky="w")

        # Preview compacto
        self.hotkey_preview_label = ctk.CTkLabel(
            hotkey_frame,
            text=current_hotkey.upper(),
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1E293B",
            corner_radius=4,
            width=70,
            height=24
        )
        self.hotkey_preview_label.grid(row=1, column=2, padx=(3,0), pady=(3,0))

        # OCULTO v0.14.0: Botón "grabar hotkey" eliminado (no tiene sentido con selector inline)
        # record_hotkey_btn = ctk.CTkButton(main_conf_frame, text=self.localization_manager.get_string("record_hotkey_button"), width=70, command=self._start_hotkey_recording)
        # record_hotkey_btn.grid(row=3, column=2, padx=(0,10), pady=5)

        # Recording Mode
        ctk.CTkLabel(main_conf_frame, text=self.localization_manager.get_string("record_mode_label")).grid(row=8, column=0, padx=10, pady=5, sticky="w")
        self.record_mode_var = tk.StringVar(value=self.config_manager.get("record_mode"))
        record_mode_frame = ctk.CTkFrame(main_conf_frame, fg_color="transparent")
        record_mode_frame.grid(row=8, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        ctk.CTkRadioButton(record_mode_frame, text=self.localization_manager.get_string("record_mode_hold"), variable=self.record_mode_var, value="hold", command=self.save_config).grid(row=0, column=0, padx=5, sticky="w")
        ctk.CTkRadioButton(record_mode_frame, text=self.localization_manager.get_string("record_mode_toggle"), variable=self.record_mode_var, value="toggle", command=self.save_config).grid(row=0, column=1, padx=10, sticky="w")

        # Max Recording Duration — label a la izquierda (col 0) como todos los demás campos
        ctk.CTkLabel(main_conf_frame, text=self.localization_manager.get_string("max_duration_label")).grid(row=9, column=0, padx=10, pady=5, sticky="w")
        current_duration = self.config_manager.get("max_recording_time", 1200)
        duration_options = {"5 min": 300, "10 min": 600, "15 min": 900, "20 min": 1200}
        reverse_map = {v: k for k, v in duration_options.items()}
        current_label = reverse_map.get(current_duration, "20 min")
        self.max_duration_var = tk.StringVar(value=current_label)
        ctk.CTkComboBox(main_conf_frame, values=list(duration_options.keys()), variable=self.max_duration_var, state="readonly", width=120, command=lambda e: self.save_config()).grid(row=9, column=1, columnspan=2, padx=5, pady=5, sticky="w")

        # Auto-paste & Show panel (filas propias, sin superposición)
        self.auto_paste_var = tk.BooleanVar(value=self.config_manager.get("auto_paste_text"))
        ctk.CTkSwitch(main_conf_frame, text=self.localization_manager.get_string("auto_paste_switch"), variable=self.auto_paste_var, command=self.save_config).grid(row=10, column=0, columnspan=3, padx=10, pady=5, sticky="w")
        self.show_panel_var = tk.BooleanVar(value=self.config_manager.get("show_transcription_panel"))
        ctk.CTkSwitch(main_conf_frame, text=self.localization_manager.get_string("show_panel_switch"), variable=self.show_panel_var, command=self.save_config).grid(row=11, column=0, columnspan=3, padx=10, pady=5, sticky="w")

        # Windows autostart (sincronizado con estado real de Startup folder)
        from backend.startup_manager import StartupManager
        startup_manager = StartupManager()
        # Sincronizar el valor del config con el estado real del sistema
        actual_autostart_state = startup_manager.is_enabled()
        self.config_manager.set("autostart_windows", actual_autostart_state)

        self.autostart_windows_var = tk.BooleanVar(value=actual_autostart_state)
        ctk.CTkSwitch(main_conf_frame, text=self.localization_manager.get_string("autostart_windows_switch"), variable=self.autostart_windows_var, command=self.save_config).grid(row=12, column=0, columnspan=3, padx=10, pady=5, sticky="w")

        # Idioma de transcripción (NO cambia interfaz — siempre ES)
        ctk.CTkLabel(main_conf_frame, text=self.localization_manager.get_string("transcription_language_label")).grid(row=13, column=0, padx=10, pady=5, sticky="w")
        self.language_var = tk.StringVar(value=self.config_manager.get("transcription_language", self.config_manager.get("default_language", "es")))
        ctk.CTkComboBox(main_conf_frame, values=["es", "en"], variable=self.language_var, state="readonly", command=lambda e: self.save_config()).grid(row=13, column=1, padx=5, pady=5, sticky="ew", columnspan=2)

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
        # OCULTO v0.14.0 - Bloques desactivados por completo
        # blocks_frame = ctk.CTkFrame(scroll_frame)
        # blocks_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        # blocks_frame.grid_columnconfigure(1, weight=1)
        # ctk.CTkLabel(blocks_frame, text="Bloques de Procesamiento (v0.11.0)", font=DesignSystem.TYPOGRAPHY["heading_medium"]).grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky="w")
        # self.block_task_enabled_var = tk.BooleanVar(value=self.config_manager.get("blocks", {}).get("task_extractor_enabled", True))
        # ctk.CTkSwitch(blocks_frame, text="Extractor de Tareas", variable=self.block_task_enabled_var, command=self.save_config).grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="w")
        # self.block_summary_enabled_var = tk.BooleanVar(value=self.config_manager.get("blocks", {}).get("summary_enabled", True))
        # ctk.CTkSwitch(blocks_frame, text="Generar Resúmenes", variable=self.block_summary_enabled_var, command=self.save_config).grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="w")
        # self.block_keyword_enabled_var = tk.BooleanVar(value=self.config_manager.get("blocks", {}).get("keyword_extractor_enabled", True))
        # ctk.CTkSwitch(blocks_frame, text="Extractor de Palabras Clave", variable=self.block_keyword_enabled_var, command=self.save_config).grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="w")
        # block_stats_btn = ctk.CTkButton(blocks_frame, text="Ver Estadísticas de Bloques", width=150, command=self._show_block_stats)
        # block_stats_btn.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="w")
        # Dummy vars para save_config (bloques siempre desactivados)
        self.block_task_enabled_var = tk.BooleanVar(value=False)
        self.block_summary_enabled_var = tk.BooleanVar(value=False)
        self.block_keyword_enabled_var = tk.BooleanVar(value=False)

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

        # Botones: ver/editar, importar archivo, exportar (FIX v0.15.0)
        vocab_buttons_frame = ctk.CTkFrame(vocab_frame, fg_color="transparent")
        vocab_buttons_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="w")
        manage_vocab_btn = ctk.CTkButton(vocab_buttons_frame, text="Ver/Editar Correcciones", width=150, command=self._show_vocab_corrections)
        manage_vocab_btn.pack(side="left", padx=(0, 5))
        import_vocab_btn = ctk.CTkButton(vocab_buttons_frame, text="📂 Importar archivo (TXT/MD/JSON)", width=200, command=self._import_vocab_file)
        import_vocab_btn.pack(side="left", padx=5)
        export_vocab_btn = ctk.CTkButton(vocab_buttons_frame, text="💾 Exportar", width=100, command=self._export_vocab_file)
        export_vocab_btn.pack(side="left", padx=5)

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

    def _load_transcriptions_cache(self, force_reload=False):
        """
        Cargar cache de transcripciones desde el archivo JSONL.

        Args:
            force_reload: Si True, recarga el cache aunque el archivo no haya cambiado.
                         Si False (default), solo recarga si el archivo fue modificado.
        """
        transcriptions_path = os.path.join("transcriptions", "transcriptions_log.jsonl")
        if not os.path.exists(transcriptions_path):
            return

        try:
            # Verificar si el archivo cambió desde la última carga (OPTIMIZACIÓN v0.15.0)
            if not force_reload and hasattr(self, '_transcriptions_cache_mtime'):
                current_mtime = os.path.getmtime(transcriptions_path)
                if current_mtime == self._transcriptions_cache_mtime:
                    # El archivo no cambió, no recargar
                    return

            # Cargar cache
            cache = {}
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
                            cache[audio_filename] = transcription
                    except json.JSONDecodeError:
                        continue

            # Actualizar cache y mtime
            self.transcriptions_cache = cache
            self._transcriptions_cache_mtime = os.path.getmtime(transcriptions_path)

            self.logger.debug(f"Cache de transcripciones cargado: {len(self.transcriptions_cache)} entradas")
        except Exception as e:
            self.logger.error(f"Error cargando cache de transcripciones: {e}")

    def refresh_history_list(self, full_reload=False):
        """
        Actualizar lista de historial con estrategia inteligente.

        Args:
            full_reload: Si True, recarga toda la lista. Si False, solo agrega nuevos archivos.
        """
        # OPTIMIZACIÓN v0.15.0: No recargar cache cada vez
        # Solo recargar si es full_reload o si el cache está vacío
        if full_reload or not self.transcriptions_cache:
            self._load_transcriptions_cache(force_reload=full_reload)
        else:
            # Verificar si el archivo de transcripciones cambió
            self._load_transcriptions_cache(force_reload=False)

        audio_path = self.config_manager.get("audio_path")
        if not os.path.exists(audio_path):
            if full_reload:  # Solo limpiar si es recarga completa
                for widget in self.history_scroll_frame.winfo_children():
                    widget.destroy()
                ctk.CTkLabel(self.history_scroll_frame, text="Directorio no encontrado").pack(pady=20)
            return

        # Obtener lista de archivos actuales
        max_display_files = 200  # FIX: subido a 200 (antes 100)
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

        # Detectar eliminados: estaban cargados pero ya no están en disco -> full reload
        removed = self.loaded_history_files - current_files
        if removed:
            self.logger.debug(f"Detectados {len(removed)} archivos eliminados, haciendo full reload")
            for widget in self.history_scroll_frame.winfo_children():
                widget.destroy()
            self.loaded_history_files.clear()
            self._history_pending = []
            self._history_pending_pos = 0
            if not files_list:
                ctk.CTkLabel(self.history_scroll_frame, text=self.localization_manager.get_string("no_audio_files")).pack(pady=20)
                self.loaded_history_files = set()
                return
            # Recargar todo
            self._history_pending = files_list
            self._history_pending_pos = 0
            self._process_history_batch(batch_size=20)
            self.loaded_history_files = current_files
            return

        # Encontrar archivos nuevos (que no están cargados)
        new_files = [f for f in files_list if f["name"] not in self.loaded_history_files]

        if new_files:
            # FIX: carga por LOTES (batch) para no congelar la UI con muchos archivos.
            # Crear cientos de widgets de golpe bloqueaba la interfaz.
            self._history_pending = new_files
            self._history_pending_pos = 0
            self._process_history_batch(batch_size=20)
            self.logger.debug(f"Agregados {len(new_files)} archivos nuevos al historial (por lotes)")

        # Si no hay archivos y no se hizo reload, mostrar vacío
        if not files_list and not self.history_scroll_frame.winfo_children():
            ctk.CTkLabel(self.history_scroll_frame, text=self.localization_manager.get_string("no_audio_files")).pack(pady=20)

        # Actualizar archivos conocidos
        self.loaded_history_files = current_files

    def _process_history_batch(self, batch_size=20):
        """
        FIX: crear items de historial en lotes para no congelar la UI.

        Con cientos de audios, crear todos los widgets de golpe en el hilo
        principal bloqueaba la interfaz (la app se 'trababa'). Se procesan
        de a 20 y se reprograma el resto con after(), dejando que la UI respire.
        """
        pending = getattr(self, '_history_pending', [])
        pos = getattr(self, '_history_pending_pos', 0)

        end = min(pos + batch_size, len(pending))
        for file_info in pending[pos:end]:
            try:
                self._create_history_item(file_info["name"], file_info["path"], file_info.get("duration", 0))
                self.loaded_history_files.add(file_info["name"])
            except Exception as e:
                self.logger.error(f"Error creando item de historial: {e}")

        self._history_pending_pos = end
        if end < len(pending):
            # Programar el siguiente lote — deja que la UI pinte entre lotes
            self.after(15, self._process_history_batch, batch_size)
        else:
            # Terminado: limpiar estado temporal
            self._history_pending = []
            self._history_pending_pos = 0

    def _format_duration(self, seconds: float) -> str:
        """Formatear duración en formato humano: 42s, 2m 35s, 1h 5m 20s"""
        try:
            s = int(round(seconds))
            if s < 60:
                return f"{s}s"
            m, sec = divmod(s, 60)
            if m < 60:
                return f"{m}m {sec:02d}s"
            h, m = divmod(m, 60)
            return f"{h}h {m}m {sec:02d}s"
        except Exception:
            return "—"

    def _create_history_item(self, filename, full_path, duration: float = 0):
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

            # Calcular duración si no vino (fallback)
            if not duration:
                try:
                    duration = self.file_manager._get_wav_duration(full_path)
                except Exception:
                    duration = 0
            duration_str = self._format_duration(duration) if duration else "—"

            # Tooltip con información completa y transcripción
            tooltip_text = f"📁 {filename}\n📅 {file_mtime.strftime('%d/%m/%Y %H:%M:%S')}\n⏱️ {duration_str}\n💾 {size_str}\n📍 {full_path}"

            # Agregar transcripción si está disponible en el cache
            if filename in self.transcriptions_cache:
                transcription = self.transcriptions_cache[filename]
                # Truncar transcripción si es muy larga (máx 200 chars)
                if len(transcription) > 200:
                    transcription = transcription[:200] + "..."
                tooltip_text += f"\n\n💬 {transcription}"

            # Agregar metadatos automáticos del LLM (NUEVO v0.13.0)
            auto_metadata = self.metadata_manager.get_auto_metadata(filename)
            if auto_metadata:
                # Título generado
                if auto_metadata.get("title"):
                    tooltip_text += f"\n\n🏷️ {auto_metadata['title']}"

                # Categoría
                if auto_metadata.get("category"):
                    category_emoji = {
                        "trabajo": "💼",
                        "idea": "💡",
                        "personal": "👤",
                        "aprendizaje": "📚",
                        "técnico": "🔧"
                    }.get(auto_metadata['category'].lower(), "📁")
                    tooltip_text += f"\n{category_emoji} {auto_metadata['category'].title()}"

                # Tags
                if auto_metadata.get("tags"):
                    tags_str = ", ".join(auto_metadata['tags'][:5])  # Máx 5 tags
                    if tags_str:
                        tooltip_text += f"\n🏷️ {tags_str}"

                # Summary (resumen)
                if auto_metadata.get("summary"):
                    summary = auto_metadata['summary']
                    if len(summary) > 150:
                        summary = summary[:150] + "..."
                    tooltip_text += f"\n\n📝 {summary}"

                # Sentiment
                if auto_metadata.get("sentiment"):
                    sentiment_emoji = {
                        "positivo": "😊",
                        "neutral": "😐",
                        "negativo": "😔"
                    }.get(auto_metadata['sentiment'].lower(), "😐")
                    tooltip_text += f"\n{sentiment_emoji} {auto_metadata['sentiment'].title()}"

                # Action items (tareas)
                if auto_metadata.get("action_items") and len(auto_metadata['action_items']) > 0:
                    tasks = auto_metadata['action_items'][:3]  # Máx 3 tareas
                    if tasks:
                        tooltip_text += f"\n\n✅ Tareas:"
                        for i, task in enumerate(tasks, 1):
                            tooltip_text += f"\n   {i}. {task}"

        except Exception as e:
            self.logger.error(f"Error obteniendo metadata de {filename}: {e}")
            display_name = f"🎤 {filename}"
            tooltip_text = f"📁 {filename}\n📍 {full_path}"
            duration = 0
            duration_str = "—"

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

        # Duración visible en la lista (a la izquierda del emoji)
        duration_label = ctk.CTkLabel(
            action_frame,
            text=f"⏱️ {duration_str}",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8",
            width=62,
            anchor="e"
        )
        duration_label.pack(side="left", padx=(0, 4))
        self._bind_tooltip(duration_label, f"Duración: {duration_str}")

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
        """Crear tooltip flotante con ventana emergente"""
        create_tooltip(widget, text)

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
        show_hotkey_selector(self, self.localization_manager, on_hotkey_selected, current_hotkey)

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

    def _update_hotkey_from_inline(self):
        """Actualizar hotkey desde el selector inline en config"""
        try:
            # Leer modificadores
            modifiers = []
            if self.hotkey_ctrl_var.get():
                modifiers.append("ctrl")
            if self.hotkey_alt_var.get():
                modifiers.append("alt")
            if self.hotkey_shift_var.get():
                modifiers.append("shift")

            # Leer tecla principal
            key = self.hotkey_key_var.get().lower()

            # Construir hotkey string
            modifier_str = "+".join(modifiers)
            if modifier_str:
                new_hotkey = f"{modifier_str}+{key}"
            else:
                new_hotkey = key

            # Actualizar preview
            self.hotkey_preview_label.configure(text=new_hotkey.upper())

            # Guardar en config
            self.config_manager.config["hotkey"] = new_hotkey
            self.config_manager.save_config()

            # Re-registrar hotkey en el Transcriber (no en la UI)
            self.transcriber.update_hotkey(new_hotkey)

            # Actualizar display label en status bar si existe
            if hasattr(self, 'hotkey_display_label'):
                self.hotkey_display_label.configure(
                    text=self.localization_manager.get_string("hotkey_display", hotkey=new_hotkey.upper())
                )

            self.logger.info(f"Hotkey actualizado: {new_hotkey}")

        except Exception as e:
            self.logger.error(f"Error actualizando hotkey: {e}")

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
                    "language": self.config_manager.get("transcription_language", self.config_manager.get("default_language", "es")), "audio_file": file_path
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

        # Usar directamente fallback de CustomTkinter (tkhtmlview tiene problemas de renderizado)
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

    def _check_api_key(self, show_popup: bool = False):
        """Verificar API Key. Si show_popup=False (auto-check), solo actualiza dot y status sin modal."""
        self.logger.info(f"Verificando claves API (popup={show_popup})...")

        groq_key = self.api_key_var.get()
        if groq_key:
            self.api_key_status_label.configure(text="●", text_color=DesignSystem.COLORS["warning"]); self.update_idletasks()
            try:
                Groq(api_key=groq_key).models.list()
                self.api_key_status_label.configure(text="●", text_color=DesignSystem.COLORS["success"])
                self._api_key_last_valid = True
                self.update_status("✅ API Key de Groq verificada", "green")
            except Exception as e:
                self.logger.error(f"Error verificando API Key de Groq: {e}")
                self.api_key_status_label.configure(text="●", text_color=DesignSystem.COLORS["error"])
                self._api_key_last_valid = False
                self.update_status("❌ API Key de Groq inválida — ver Información para configurarla", "red")
                if show_popup:
                    self._show_api_key_error_hint(str(e))
        else:
            self.api_key_status_label.configure(text="●", text_color="grey")
            self._api_key_last_valid = None
            self.update_status("⚠️ Sin API Key — configurala en Configuración", "orange")
            if show_popup:
                self._show_api_key_error_hint("Sin API Key configurada")

    def _on_api_dot_click(self):
        """Click en el dot de estado — si está en rojo, llevar a Información."""
        try:
            if getattr(self, '_api_key_last_valid', None) is False:
                self.main_frame.set(self.localization_manager.get_string("tab_info"))
                self.update_status("ℹ️ Ver Información para configurar tu API Key de Groq", "orange")
            else:
                self._check_api_key(show_popup=True)
        except Exception:
            self._check_api_key(show_popup=True)

    def _show_api_key_error_hint(self, error_detail: str = ""):
        """Mostrar hint y ofrecer navegar a Información cuando la API Key falla."""
        # Evitar spam: solo mostrar si no se mostró hace poco (debounce 10s)
        import time
        now = time.time()
        if hasattr(self, '_last_api_hint_time') and (now - self._last_api_hint_time) < 10:
            return
        self._last_api_hint_time = now

        def _go_to_info():
            try:
                self.main_frame.set(self.localization_manager.get_string("tab_info"))
            except Exception:
                pass
            hint_win.destroy()

        hint_win = ctk.CTkToplevel(self)
        hint_win.title("API Key no válida")
        hint_win.geometry("460x220")
        hint_win.transient(self)
        hint_win.lift()
        hint_win.attributes('-topmost', True)
        hint_win.after(100, lambda: hint_win.attributes('-topmost', False))
        hint_win.grab_set()

        ctk.CTkLabel(hint_win, text="❌ API Key de Groq no válida", font=DesignSystem.TYPOGRAPHY["heading_medium"], text_color=DesignSystem.COLORS["error"]).pack(pady=(15, 5))
        ctk.CTkLabel(hint_win, text="La verificación falló. Configurá tu API Key gratis en:", font=DesignSystem.TYPOGRAPHY["body_small"]).pack(pady=2)
        link = ctk.CTkLabel(hint_win, text="https://console.groq.com/keys", font=DesignSystem.TYPOGRAPHY["link"], text_color=DesignSystem.COLORS["primary"], cursor="hand2")
        link.pack(pady=2)
        link.bind("<Button-1>", lambda e: webbrowser.open_new("https://console.groq.com/keys"))
        if error_detail:
            ctk.CTkLabel(hint_win, text=error_detail[:80], font=ctk.CTkFont(size=10), text_color="gray").pack(pady=2)
        ctk.CTkLabel(hint_win, text="Pegá la clave en Configuración → API Key → Verificar", font=DesignSystem.TYPOGRAPHY["body_small"], text_color=DesignSystem.COLORS["text_secondary"]).pack(pady=2)

        btn_frame = ctk.CTkFrame(hint_win, fg_color="transparent")
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="Ir a Información", width=140, command=_go_to_info).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Cerrar", width=100, fg_color="gray", hover_color="#555", command=hint_win.destroy).pack(side="left", padx=5)

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

    def _import_vocab_file(self):
        """Importar correcciones de vocabulario desde un archivo (TXT/MD/JSON)."""
        try:
            if not hasattr(self.transcriber, 'custom_vocab'):
                self.update_status("CustomVocabulary no disponible", "red")
                return

            from tkinter import filedialog
            file_path = filedialog.askopenfilename(
                title="Importar vocabulario",
                filetypes=[
                    ("Archivos de vocabulario", "*.txt;*.md;*.json"),
                    ("Texto", "*.txt;*.md"),
                    ("JSON", "*.json"),
                    ("Todos", "*.*")
                ]
            )
            if not file_path:
                return

            count = self.transcriber.custom_vocab.import_from_file(file_path)
            if count > 0:
                self.update_status(f"✅ {count} correcciones importadas de {os.path.basename(file_path)}", "green")
                self._refresh_vocab_list()
            else:
                self.update_status("No se importó ninguna corrección (revisá el formato: 'incorrecta=correcta' por línea o JSON)", "orange")
        except Exception as e:
            self.logger.error(f"Error importando vocabulario: {e}")
            self.update_status(f"Error importando vocabulario: {e}", "red")

    def _export_vocab_file(self):
        """Exportar el vocabulario actual a un archivo de texto."""
        try:
            if not hasattr(self.transcriber, 'custom_vocab'):
                self.update_status("CustomVocabulary no disponible", "red")
                return

            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                title="Exportar vocabulario",
                defaultextension=".txt",
                filetypes=[("Texto", "*.txt"), ("Markdown", "*.md"), ("JSON", "*.json"), ("Todos", "*.*")]
            )
            if not file_path:
                return

            if self.transcriber.custom_vocab.export_to_file(file_path):
                self.update_status(f"✅ Vocabulario exportado a {os.path.basename(file_path)}", "green")
            else:
                self.update_status("Error exportando vocabulario", "red")
        except Exception as e:
            self.logger.error(f"Error exportando vocabulario: {e}")
            self.update_status(f"Error exportando vocabulario: {e}", "red")

    def _show_vocab_corrections(self):
        """Mostrar ventana para ver/editar/eliminar correcciones — con selección múltiple bulk."""
        try:
            if not hasattr(self.transcriber, 'custom_vocab'):
                self.update_status("CustomVocabulary no disponible", "red")
                return

            vocab_window = ctk.CTkToplevel(self)
            vocab_window.title("Correcciones de Vocabulario")
            vocab_window.geometry("680x540")
            vocab_window.transient(self)
            vocab_window.lift()
            vocab_window.attributes('-topmost', True)
            vocab_window.after(100, lambda: vocab_window.attributes('-topmost', False))
            vocab_window.grab_set()

            main_frame = ctk.CTkScrollableFrame(vocab_window)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)

            ctk.CTkLabel(main_frame, text="Correcciones de Vocabulario Personalizado", font=DesignSystem.TYPOGRAPHY["heading_medium"]).pack(pady=10)
            ctk.CTkLabel(main_frame, text="Palabras que el modelo entiende mal y su corrección:", font=DesignSystem.TYPOGRAPHY["body_small"]).pack(pady=5)

            # Barra de acciones bulk
            bulk_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            bulk_frame.pack(fill="x", padx=5, pady=(5, 8))

            select_all_var = tk.BooleanVar(value=False)
            bulk_state = {"order": [], "vars": {}, "last_idx": [-1], "select_all_var": select_all_var}

            def _is_shift_pressed() -> bool:
                # HC-03 FIX: ctypes.windll solo Windows — fallback keyboard/Tk sin crash en Linux/macOS
                try:
                    import ctypes
                    # windll no existe fuera de Windows -> AttributeError
                    return (ctypes.windll.user32.GetKeyState(0x10) & 0x8000) != 0
                except Exception as e:
                    # Fallback 1: keyboard.is_pressed si disponible
                    try:
                        import keyboard as _kb
                        if _kb.is_pressed('shift'):
                            return True
                        # si no está presionado, igual no es error — retornar False sin warning
                        # pero si ctypes falló por plataforma, loguear una vez
                        if not getattr(_is_shift_pressed, "_warned", False):
                            self.logger.warning(f"Shift fallback activo (ctypes no disponible: {e}) — keyboard.is_pressed usado")
                            _is_shift_pressed._warned = True
                        return False
                    except Exception:
                        pass
                    # Fallback 2: Tk Shift tracking vía event.state no disponible aquí (sin event), retornar False
                    if not getattr(_is_shift_pressed, "_warned", False):
                        self.logger.warning(f"Shift ctypes fallback sin keyboard (Linux/macOS): {e} — rango Shift deshabilitado, usar 'Seleccionar todos'")
                        _is_shift_pressed._warned = True
                    return False

            def _update_bulk_button():
                cnt = sum(1 for v in bulk_state["vars"].values() if v.get())
                if cnt:
                    delete_bulk_btn.configure(state="normal", text=f"🗑️ Eliminar seleccionados ({cnt})")
                else:
                    delete_bulk_btn.configure(state="disabled", text="🗑️ Eliminar seleccionados")
                # Sincronizar "Seleccionar todos"
                total = len(bulk_state["order"])
                if total and cnt == total:
                    select_all_var.set(True)
                elif cnt == 0:
                    select_all_var.set(False)

            def _on_select_all():
                val = select_all_var.get()
                for v in bulk_state["vars"].values():
                    v.set(val)
                bulk_state["last_idx"][0] = -1
                _update_bulk_button()

            def _on_checkbox(idx: int):
                # Manejar Shift+rango
                if _is_shift_pressed() and bulk_state["last_idx"][0] != -1:
                    last = bulk_state["last_idx"][0]
                    lo, hi = (last, idx) if last < idx else (idx, last)
                    # El nuevo valor es el del checkbox cliqueado
                    key_clicked = bulk_state["order"][idx]
                    new_val = bulk_state["vars"][key_clicked].get()
                    for j in range(lo, hi + 1):
                        k = bulk_state["order"][j]
                        bulk_state["vars"][k].set(new_val)
                bulk_state["last_idx"][0] = idx
                _update_bulk_button()

            select_all_cb = ctk.CTkCheckBox(bulk_frame, text="Seleccionar todos", variable=select_all_var, command=_on_select_all)
            select_all_cb.pack(side="left", padx=5)

            delete_bulk_btn = ctk.CTkButton(bulk_frame, text="🗑️ Eliminar seleccionados", width=200, fg_color="#EF4444", hover_color="#DC2626", state="disabled")
            delete_bulk_btn.pack(side="right", padx=5)

            def _delete_selected():
                selected = [k for k, v in bulk_state["vars"].items() if v.get()]
                if not selected:
                    return
                if not messagebox.askyesno("Confirmar eliminación", f"¿Eliminar {len(selected)} correcciones seleccionadas?\n\n" + ", ".join(selected[:10]) + (f"\n...y {len(selected)-10} más" if len(selected) > 10 else ""), parent=vocab_window):
                    return
                for key in selected:
                    self.transcriber.custom_vocab.remove_correction(key)
                self.update_status(f"🗑️ {len(selected)} correcciones eliminadas", "green")
                self._refresh_vocab_list()
                reload_list()

            delete_bulk_btn.configure(command=_delete_selected)

            hint = ctk.CTkLabel(bulk_frame, text="Tip: Shift+clic para rango", font=ctk.CTkFont(size=10), text_color="#94A3B8")
            hint.pack(side="left", padx=12)

            list_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            list_frame.pack(fill="both", expand=True, padx=5, pady=5)

            def reload_list():
                for widget in list_frame.winfo_children():
                    widget.destroy()
                bulk_state["order"] = []
                bulk_state["vars"] = {}
                bulk_state["last_idx"][0] = -1

                corrections = self.transcriber.custom_vocab.get_corrections()
                if not corrections:
                    ctk.CTkLabel(list_frame, text="No hay correcciones configuradas").pack(pady=20)
                    _update_bulk_button()
                else:
                    for idx, (incorrect, correct) in enumerate(corrections.items()):
                        row_frame = ctk.CTkFrame(list_frame)
                        row_frame.pack(fill="x", pady=2, padx=5)

                        var = tk.BooleanVar(value=False)
                        bulk_state["order"].append(incorrect)
                        bulk_state["vars"][incorrect] = var

                        cb = ctk.CTkCheckBox(row_frame, text="", variable=var, width=20, command=lambda i=idx: _on_checkbox(i))
                        cb.pack(side="left", padx=(8, 2))

                        ctk.CTkLabel(row_frame, text=incorrect, font=DesignSystem.TYPOGRAPHY["body_bold"]).pack(side="left", padx=6)
                        ctk.CTkLabel(row_frame, text="→", font=DesignSystem.TYPOGRAPHY["heading_large"]).pack(side="left", padx=6)
                        ctk.CTkLabel(row_frame, text=correct, font=DesignSystem.TYPOGRAPHY["body_bold"], text_color="#10B981").pack(side="left", padx=6)

                        edit_btn = ctk.CTkButton(row_frame, text="✏️ Editar", width=70, fg_color="#2563EB", hover_color="#1D4ED8",
                                                 command=lambda inc=incorrect, cor=correct: self._edit_vocab_correction(inc, cor, reload_list))
                        edit_btn.pack(side="right", padx=2)
                        delete_btn = ctk.CTkButton(row_frame, text="🗑️", width=30, fg_color="#EF4444", hover_color="#DC2626",
                                                command=lambda inc=incorrect: self._delete_vocab_correction(inc, reload_list))
                        delete_btn.pack(side="right", padx=5)
                    _update_bulk_button()

            reload_list()
            ctk.CTkButton(main_frame, text="Cerrar", command=vocab_window.destroy, width=100).pack(pady=10)
            self.logger.info("Ventana de correcciones mostrada")

        except Exception as e:
            self.logger.error(f"Error mostrando correcciones: {e}")
            self.update_status("Error al mostrar correcciones", "red")

    def _delete_vocab_correction(self, incorrect: str, on_deleted=None):
        """Eliminar corrección de vocabulario con refresh INMEDIATO de la lista."""
        try:
            if hasattr(self.transcriber, 'custom_vocab'):
                success = self.transcriber.custom_vocab.remove_correction(incorrect)
                if success:
                    self.update_status(f"Corrección eliminada: {incorrect}", "green")
                    self.logger.info(f"Corrección eliminada: {incorrect}")
                    # FIX bug 5: refrescar la lista visible AL INSTANTE (no esperar a reabrir)
                    if on_deleted:
                        on_deleted()
                    self._refresh_vocab_list()
                else:
                    self.update_status("Error al eliminar corrección", "red")
        except Exception as e:
            self.logger.error(f"Error eliminando corrección: {e}")
            self.update_status("Error al eliminar corrección", "red")

    def _edit_vocab_correction(self, incorrect: str, current_correct: str, on_edited=None):
        """Editar una corrección existente — permite cambiar TANTO la palabra incorrecta como la correcta."""
        try:
            if not hasattr(self.transcriber, 'custom_vocab'):
                self.update_status("CustomVocabulary no disponible", "red")
                return

            edit_window = ctk.CTkToplevel(self)
            edit_window.title("Editar Corrección")
            edit_window.geometry("460x220")
            edit_window.transient(self)
            edit_window.lift()
            edit_window.attributes('-topmost', True)
            edit_window.after(100, lambda: edit_window.attributes('-topmost', False))
            edit_window.grab_set()
            edit_window.resizable(False, False)

            ctk.CTkLabel(edit_window, text="Palabra incorrecta (lo que el modelo entiende mal):", font=DesignSystem.TYPOGRAPHY["body_small"]).pack(padx=15, pady=(10, 2), anchor="w")
            new_incorrect_var = tk.StringVar(value=incorrect)
            incorrect_entry = ctk.CTkEntry(edit_window, textvariable=new_incorrect_var)
            incorrect_entry.pack(padx=15, pady=2, fill="x")

            ctk.CTkLabel(edit_window, text="Palabra correcta (como debe escribirse):", font=DesignSystem.TYPOGRAPHY["body_small"]).pack(padx=15, pady=(8, 2), anchor="w")
            new_correct_var = tk.StringVar(value=current_correct)
            correct_entry = ctk.CTkEntry(edit_window, textvariable=new_correct_var)
            correct_entry.pack(padx=15, pady=2, fill="x")

            def save_edit():
                new_incorrect = new_incorrect_var.get().strip()
                new_correct = new_correct_var.get().strip()
                if not new_incorrect or not new_correct:
                    self.update_status("Ambas palabras deben tener contenido", "orange")
                    return
                if new_incorrect == incorrect and new_correct == current_correct:
                    edit_window.destroy()
                    return
                # Si cambió la clave incorrecta, eliminar la vieja
                if new_incorrect != incorrect:
                    # Buscar y eliminar la clave vieja (case-insensitive)
                    for key in list(self.transcriber.custom_vocab.corrections.keys()):
                        if key.lower() == incorrect.lower():
                            del self.transcriber.custom_vocab.corrections[key]
                            break
                self.transcriber.custom_vocab.corrections[new_incorrect] = new_correct
                self.transcriber.custom_vocab._save_vocab()
                self.update_status(f"Corrección actualizada: {new_incorrect}={new_correct}", "green")
                if on_edited:
                    on_edited()
                self._refresh_vocab_list()
                edit_window.destroy()

            btn_frame = ctk.CTkFrame(edit_window, fg_color="transparent")
            btn_frame.pack(pady=12)
            ctk.CTkButton(btn_frame, text="Guardar", width=100, fg_color="#10B981", hover_color="#059669", command=save_edit).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="Cancelar", width=100, command=edit_window.destroy).pack(side="left", padx=5)

            incorrect_entry.focus_set()
            incorrect_entry.select_range(0, 'end')

        except Exception as e:
            self.logger.error(f"Error editando corrección: {e}")
            self.update_status(f"Error editando corrección: {e}", "red")

    def _refresh_vocab_list(self):
        """Refrescar lista de correcciones en la pestaña de configuración."""
        try:
            # Limpiar lista actual
            for widget in self.vocab_list_frame.winfo_children():
                widget.destroy()

            if hasattr(self, 'transcriber') and hasattr(self.transcriber, 'custom_vocab'):
                corrections = self.transcriber.custom_vocab.get_corrections()

                if not corrections:
                    ctk.CTkLabel(self.vocab_list_frame, text="No hay correcciones configuradas", font=DesignSystem.TYPOGRAPHY["body_small"]).pack(pady=5)
                else:
                    # Mostrar TODAS las correcciones en formato incorrecta=correcta (sin espacios)
                    for incorrect, correct in corrections.items():
                        item = ctk.CTkLabel(self.vocab_list_frame, text=f"{incorrect}={correct}", font=DesignSystem.TYPOGRAPHY["body_small"])
                        item.pack(anchor="w", padx=10, pady=1)

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
        # FIX: hotkey_var fue reemplazado por el selector inline (hotkey_key_var) en v0.14.0
        if hasattr(self, 'hotkey_key_var'):
            self.hotkey_key_var.set(hotkey.upper())
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
        # FIX Bug G: el guard original chequeaba 'hotkey_var' (StringVar eliminado en v0.14.0,
        # reemplazado por hotkey_ctrl_var/alt_var/shift_var/key_var del selector inline).
        # Como 'hotkey_var' ya no existía, save_config() SIEMPRE retornaba temprano y NUNCA guardaba.
        # Ahora chequeamos una variable que SÍ existe: 'api_key_var' (creada en create_config_tab).
        if not hasattr(self, 'api_key_var') or not hasattr(self, 'asr_provider_var'):
            return
        self.logger.info("Guardando configuración...")
        old_tlang = self.config_manager.get("transcription_language", self.config_manager.get("default_language", "es"))
        old_show_panel = self.config_manager.get("show_transcription_panel")

        # Obtener configuración de bloques actual
        blocks_config = self.config_manager.get("blocks", {})
        hotkey_actual = self.config_manager.get("hotkey", "f12")

        settings = {
            "groq_api_key": self.api_key_var.get(),
            "asr_provider": self.asr_provider_var.get(),
            "nvidia_enabled": self.nvidia_enabled_var.get() if hasattr(self, 'nvidia_enabled_var') else False,
            "nvidia_api_key": self.nvidia_api_key_var.get() if hasattr(self, 'nvidia_api_key_var') else "",
            "nvidia_mode": self.nvidia_mode_var.get() if hasattr(self, 'nvidia_mode_var') else "cloud",
            "hotkey": hotkey_actual,  # FIX: el hotkey se mantiene con su valor actual (viene del config_manager)
            "record_mode": self.record_mode_var.get(),
            "max_recording_time": {"5 min": 300, "10 min": 600, "15 min": 900, "20 min": 1200}.get(self.max_duration_var.get() if hasattr(self, "max_duration_var") else "20 min", 1200),
            "auto_paste_text": self.auto_paste_var.get(), "show_transcription_panel": self.show_panel_var.get(),
            "audio_path": self.audio_path_var.get(), "transcriptions_path": self.transcriptions_path_var.get(),
            "save_audio": self.save_audio_var.get(), "save_logs": self.save_logs_var.get(),
            "max_audio_files": int(self.config_manager.get("max_audio_files")),
            "max_log_entries": int(self.config_manager.get("max_log_entries")),
            "audio_priority_apps": self.config_manager.get("audio_priority_apps"),
            "default_language": "es",  # Interfaz siempre español
            "transcription_language": self.language_var.get(),
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
        
        # Idioma de transcripción cambió — sincronizar switch omnipresente si existe
        new_tlang = self.language_var.get()
        if new_tlang != old_tlang:
            self.logger.info(f"Idioma de transcripción: {old_tlang} → {new_tlang}")
            if hasattr(self, '_lang_switch_var') and self._lang_switch_var.get() != new_tlang:
                self._lang_switch_var.set(new_tlang)
                self._update_lang_switch_label(new_tlang)
        
        # --- API Key Logic Fix ---
        # FIX v0.15.0: recargar cliente SIEMPRE al guardar config (el provider
        # pudo cambiar). Antes solo se recargaba si había groq_api_key.
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
        # FIX v0.15.0 (punto 0): evitar acumular callbacks pendientes del thread de
        # grabación (en grabaciones largas, miles de after(0) pendientes colapsaban
        # la UI y congelaban la captura de audio). Se conserva solo el último.
        if hasattr(self, '_status_after_id'):
            try:
                self.after_cancel(self._status_after_id)
            except Exception:
                pass
        self._status_after_id = self.after(0, self._update_status_on_main_thread, message, color)

    def _safe_display_transcription_on_main_thread(self, text):
        self.logger.info(f"Mostrando transcripcion (truncada): {text[:100]}...")
        if self.config_manager.get("show_transcription_panel") and self.transcription_textbox:
            self.transcription_textbox.delete("1.0", "end")
            self.transcription_textbox.insert("1.0", text)

            # Mostrar resultados de bloques si existen
            if hasattr(self, "transcriber") and hasattr(self.transcriber, "last_block_display"):
                block_display = self.transcriber.last_block_display
                if block_display:
                    self.transcription_textbox.insert("end", block_display)

        pyperclip.copy(text)
        if self.config_manager.get("auto_paste_text"):
            self.logger.info("Auto-pegando transcripcion.")
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
            # Sincronizar historial: limpiar UI y estado
            self._sync_history_after_clear()
        else:
            self.update_status(self.localization_manager.get_string("error_deleting_audio"), "red")
            self.logger.error("Error al eliminar archivos de audio.")
        self.update_file_info()

    def clear_logs_with_feedback(self):
        self.logger.info("Intentando limpiar archivos de transcripciones.")
        if self.file_manager.clear_transcriptions():
            self.update_status(self.localization_manager.get_string("transcriptions_deleted"), "green")
            self.logger.info("Archivos de transcripciones eliminados exitosamente.")
            # Limpiar cache de transcripciones y refrescar tooltips
            self.transcriptions_cache = {}
            self._transcriptions_cache_mtime = 0
            # Si también hay audios, refrescar historial para actualizar tooltips
            self.refresh_history_list(full_reload=True)
        else:
            self.update_status(self.localization_manager.get_string("error_deleting_transcriptions"), "red")
            self.logger.error("Error al eliminar archivos de transcripciones.")
        self.update_file_info()

    def _sync_history_after_clear(self):
        """Sincronizar pestaña Historial después de limpiar audios: vaciar lista y mostrar estado vacío."""
        try:
            for widget in self.history_scroll_frame.winfo_children():
                widget.destroy()
            self.loaded_history_files = set()
            self.transcriptions_cache = {}
            self._transcriptions_cache_mtime = 0
            self._history_pending = []
            self._history_pending_pos = 0
            # Mostrar mensaje vacío
            ctk.CTkLabel(self.history_scroll_frame, text=self.localization_manager.get_string("no_audio_files")).pack(pady=20)
            self.last_history_file_count = 0
            self.last_history_mtime = 0
        except Exception as e:
            self.logger.error(f"Error sincronizando historial tras clear: {e}")

    def on_closing(self):
        self.logger.info("Cerrando aplicación por completo.")
        # Guardar geometry de la ventana antes de cerrar v0.14.0
        self._save_window_geometry()
        self.quit_application()

    def _save_window_geometry(self):
        """Guardar tamaño y posición de la ventana"""
        try:
            geometry = self.geometry()  # Formato: "widthxheight+x+y"
            self.config_manager.config["window_geometry"] = geometry
            self.config_manager.save_config()
            self.logger.debug(f"Geometry guardada: {geometry}")
        except Exception as e:
            self.logger.warning(f"No se pudo guardar geometry: {e}")

    def _load_window_geometry(self):
        """Cargar tamaño y posición de la ventana guardada"""
        try:
            saved_geometry = self.config_manager.get("window_geometry")
            if saved_geometry:
                self.geometry(saved_geometry)
                self.logger.debug(f"Geometry restaurada: {saved_geometry}")
        except Exception as e:
            self.logger.warning(f"No se pudo restaurar geometry: {e}")
            # Usar geometry por defecto
            self.geometry("650x550")

    def _on_window_resize(self, event):
        """Manejar evento de redimensionado de ventana"""
        # Solo guardar geometry periódicamente (debounce simple)
        # El evento <Configure> se dispara muchas veces durante redimensionado
        # Guardamos solo cuando el usuario termina de redimensionar (event.width != 1)
        if not hasattr(self, '_last_resize_time'):
            import time
            self._last_resize_time = 0
            return

        import time
        current_time = time.time()
        if current_time - self._last_resize_time < 0.5:  # Debounce de 500ms
            return
        self._last_resize_time = current_time

        # Guardar geometry actual
        try:
            geometry = self.geometry()
            self.config_manager.config["window_geometry"] = geometry
            # No guardar config aquí para no saturar disco, se guarda en on_closing
        except:
            pass

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
        # FIX: destruir overlay de grabación ANTES de cerrar la ventana principal,
        # para que el timer no quede huérfano y colgado en pantalla
        try:
            if self.recording_overlay:
                self.recording_overlay.withdraw()
                self.recording_overlay.destroy()
        except Exception as e:
            self.logger.warning(f"Error destruyendo overlay: {e}")
        if self.tray_icon: self.tray_icon.stop()
        self.destroy()
        sys.exit()