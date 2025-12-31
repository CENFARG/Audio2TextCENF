import customtkinter as ctk
from typing import List, Dict, Optional, Any
import logging

class TutorialManager:
    """
    Gestor del tutorial interactivo de onboarding.
    Muestra tooltips suaves sobre la interfaz (in-app).
    """
    
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger("TutorialManager")
        self.current_step_index = 0
        self.tooltip_frame: Optional[ctk.CTkFrame] = None
        self.steps: List[Dict[str, Any]] = self._define_steps()
        
    def _define_steps(self) -> List[Dict[str, Any]]:
        return [
            {
                "title": "Bienvenido",
                "message": "Bienvenido a Audio2Text.\nTe guiaremos brevemente.",
                "target": None, 
                "tab": None 
            },
            {
                "title": "Estado",
                "message": "Aquí verás si estás 'Listo' o 'Grabando'.\nUsa tu Hotkey (F12) para controlar.",
                "target": "status_label",
                "tab": self.app.localization_manager.get_string("tab_main")
            },
            {
                "title": "Transcripción",
                "message": "Tu texto aparecerá aquí automáticamente.\nPuedes copiarlo o editarlo.",
                "target": "transcription_textbox",
                "position": "bottom", # Forzar abajo
                "tab": self.app.localization_manager.get_string("tab_main")
            },
            {
                "title": "Ajustes",
                "message": "Configura tu API Key, Hotkeys y rutas de guardado aquí.",
                "target": "tab_settings_placeholder", 
                "position": "bottom_dock", # Dockeado abajo para no tapar inputs
                "tab": self.app.localization_manager.get_string("tab_settings")
            },
            {
                "title": "Historial",
                "message": "Accede a tus grabaciones previas.",
                "target": "tab_history_placeholder",
                "position": "bottom_dock",
                "tab": self.app.localization_manager.get_string("tab_history")
            },
            {
                "title": "¡Listo!",
                "message": "Ya puedes empezar a usar Audio2Text.\nConfigura tu API Key si falta.",
                "target": None,
                "tab": self.app.localization_manager.get_string("tab_main")
            }
        ]

    def should_start(self) -> bool:
        return not self.app.config_manager.get("tutorial_completed", False)

    def start(self):
        self.logger.info("Iniciando tutorial interactivo...")
        self.app.deiconify()
        self.app.focus_force()
        self.current_step_index = 0
        self.show_step()

    def show_step(self):
        if self.tooltip_frame:
            self.tooltip_frame.destroy()
            self.tooltip_frame = None

        step = self.steps[self.current_step_index]
        
        # 1. Cambiar tab
        if step.get('tab'):
            try:
                self.app.main_frame.set(step['tab'])
                self.app.update_idletasks()
            except:
                pass

        # 2. Crear Frame "Tooltip" Compacto
        self.tooltip_frame = ctk.CTkFrame(self.app, corner_radius=8, fg_color="#2B2B2B", border_width=1, border_color="#444444")
        
        # Layout Compacto
        header = ctk.CTkFrame(self.tooltip_frame, fg_color="transparent", height=20)
        header.pack(fill="x", padx=8, pady=(8, 2))
        
        ctk.CTkLabel(header, text=step['title'], font=("Segoe UI", 12, "bold"), text_color="#60A5FA").pack(side="left")
        ctk.CTkLabel(header, text=f"{self.current_step_index + 1}/{len(self.steps)}", font=("Segoe UI", 9), text_color="#888888").pack(side="right")
        
        ctk.CTkLabel(self.tooltip_frame, text=step['message'], font=("Segoe UI", 11), text_color="#E5E5E5", justify="left", wraplength=240).pack(padx=8, pady=2, fill="x")

        # Botonera
        btns = ctk.CTkFrame(self.tooltip_frame, fg_color="transparent")
        btns.pack(fill="x", padx=8, pady=8)
        
        ctk.CTkButton(btns, text="✕", width=24, height=20, fg_color="transparent", text_color="#888888", hover_color="#444444", command=self.end_tutorial).pack(side="left")
        
        next_text = "Sig." if self.current_step_index < len(self.steps) - 1 else "Fin"
        ctk.CTkButton(btns, text=next_text, width=40, height=20, font=("Segoe UI", 10), command=self.next_step).pack(side="right")

        if self.current_step_index > 0:
            ctk.CTkButton(btns, text="Ant.", width=40, height=20, fg_color="#333333", hover_color="#444444", font=("Segoe UI", 10), command=self.prev_step).pack(side="right", padx=4)

        # 3. Posicionar
        self._place_tooltip(step)
        self.tooltip_frame.lift()

    def _place_tooltip(self, step):
        # Medidas aproximadas del tooltip (width=260 approx, height=varies ~120)
        tt_w = 260
        tt_h = 130 
        
        app_w = self.app.winfo_width()
        app_h = self.app.winfo_height()
        
        target_name = step.get('target')
        position_mode = step.get('position', 'auto') # auto, bottom, bottom_dock
        
        x = (app_w // 2) - (tt_w // 2)
        y = (app_h // 2) - (tt_h // 2)
        
        if position_mode == "bottom_dock" or target_name in ["tab_settings_placeholder", "tab_history_placeholder"]:
            # Posicionar abajo al centro (Toast style)
            x = (app_w // 2) - (tt_w // 2)
            y = app_h - tt_h - 20 # 20px padding bottom
            
        elif target_name == "status_label":
             target_widget = getattr(self.app, target_name, None)
             if target_widget:
                self.app.update_idletasks()
                t_x = target_widget.winfo_rootx() - self.app.winfo_rootx()
                t_y = target_widget.winfo_rooty() - self.app.winfo_rooty()
                t_h_widget = target_widget.winfo_height()
                t_w_widget = target_widget.winfo_width()
                
                # Intentar ponerlo a la derecha si entra
                if t_x + t_w_widget + tt_w + 20 < app_w:
                    x = t_x + t_w_widget + 20
                    y = t_y
                else:
                    # Si no, abajo pero con offset extra para saltar la info
                    x = (app_w // 2) - (tt_w // 2)
                    y = t_y + t_h_widget + 50 # 50px extra para saltar texto de info
                    
        elif target_name and position_mode != "bottom_dock":
            target_widget = getattr(self.app, target_name, None)
            if target_widget:
                self.app.update_idletasks()
                t_x = target_widget.winfo_rootx() - self.app.winfo_rootx()
                t_y = target_widget.winfo_rooty() - self.app.winfo_rooty()
                t_h_widget = target_widget.winfo_height()
                t_w_widget = target_widget.winfo_width()
                
                # Centrado horizontal respecto al widget
                x = t_x + (t_w_widget // 2) - (tt_w // 2)
                
                if position_mode == "bottom":
                     # Abajo del todo del área del widget (útil para textbox grande)
                     y = t_y + t_h_widget - tt_h - 10
                else:
                    # Debajo standard
                    y = t_y + t_h_widget + 10
        
        # Safety bounds
        if x < 10: x = 10
        if x + tt_w > app_w: x = app_w - tt_w - 10
        if y < 10: y = 10
        if y + tt_h > app_h: y = app_h - tt_h - 10

        self.tooltip_frame.place(x=x, y=y)

    def next_step(self):
        self.current_step_index += 1
        if self.current_step_index >= len(self.steps):
            self.end_tutorial(completed=True)
        else:
            self.show_step()

    def prev_step(self):
        if self.current_step_index > 0:
            self.current_step_index -= 1
            self.show_step()

    def end_tutorial(self, completed=False):
        if self.tooltip_frame:
            self.tooltip_frame.destroy()
            self.tooltip_frame = None
        if completed:
            self.app.config_manager.set("tutorial_completed", True)
