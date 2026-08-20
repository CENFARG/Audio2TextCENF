"""
Hotkey Selector - Selector de hotkeys con modificadores.

Permite al usuario seleccionar combinaciones de teclas con Ctrl, Alt, Shift.
"""

import customtkinter as ctk
from typing import Optional, Callable, List, Tuple
from backend.hotkey_manager import HotkeyManager


class HotkeySelector(ctk.CTkToplevel):
    """Selector de hotkeys con modificadores."""

    def __init__(
        self,
        parent,
        localization_manager,
        on_hotkey_selected: Callable[[str], None],
        current_hotkey: str = "f12",
        title: str = None
    ):
        """
        Inicializar selector de hotkeys.

        Args:
            parent: Ventana padre
            localization_manager: Gestor de localizaci├│n
            on_hotkey_selected: Callback cuando se selecciona hotkey
            current_hotkey: Hotkey actual
            title: T├¡tulo de la ventana
        """
        super().__init__(parent)

        self.localization_manager = localization_manager
        self.on_hotkey_selected = on_hotkey_selected
        self.current_hotkey = current_hotkey
        self.selected_hotkey = None
        self.hotkey_manager = HotkeyManager()

        # T├¡tulo localizado
        if not title:
            title = self.localization_manager.get_string("hotkey_selector_title", "Seleccionar Hotkey")

        # Configurar ventana
        self.title(title)
        self.geometry("450x550")
        self.resizable(False, False)

        # Hacer modal
        self.transient(parent)
        self.attributes("-topmost", True)
        self.grab_set()

        # Centrar en pantalla
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.winfo_screenheight() // 2) - (550 // 2)
        self.geometry(f"450x550+{x}+{y}")

        # Parsear hotkey actual
        parsed = self.hotkey_manager.parse_hotkey_string(current_hotkey)
        self.current_key = parsed.key
        self.current_modifiers = parsed.modifiers

        self._create_ui()

    def _create_ui(self):
        """Crear interfaz del selector."""
        # Header
        header_frame = ctk.CTkFrame(self, height=60)
        header_frame.pack(fill="x", padx=10, pady=10)
        header_frame.pack_propagate(False)

        ctk.CTkLabel(
            header_frame,
            text="Ôî¿´©Å",
            font=ctk.CTkFont(size=20)
        ).pack(side="left", padx=(10, 5))

        ctk.CTkLabel(
            header_frame,
            text=self.localization_manager.get_string("hotkey_configure"),
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")

        # Contenedor scrollable
        scroll_frame = ctk.CTkScrollableFrame(self, label_text=self.localization_manager.get_string("hotkey_configuration"))
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Secci├│n: Modificadores
        ctk.CTkLabel(
            scroll_frame,
            text=self.localization_manager.get_string("hotkey_modifiers"),
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        modifiers_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        modifiers_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Checkboxes de modificadores
        self.modifier_vars = {
            "ctrl": ctk.BooleanVar(value="ctrl" in self.current_modifiers),
            "alt": ctk.BooleanVar(value="alt" in self.current_modifiers),
            "shift": ctk.BooleanVar(value="shift" in self.current_modifiers),
        }

        ctk.CTkCheckBox(
            modifiers_frame,
            text="Ctrl",
            variable=self.modifier_vars["ctrl"],
            command=self._update_preview
        ).grid(row=0, column=0, padx=5, pady=5)

        ctk.CTkCheckBox(
            modifiers_frame,
            text="Alt",
            variable=self.modifier_vars["alt"],
            command=self._update_preview
        ).grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkCheckBox(
            modifiers_frame,
            text="Shift",
            variable=self.modifier_vars["shift"],
            command=self._update_preview
        ).grid(row=0, column=2, padx=5, pady=5)

        # Secci├│n: Tecla principal
        ctk.CTkLabel(
            scroll_frame,
            text=self.localization_manager.get_string("hotkey_main_key"),
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # Tabs para teclas F y alfanum├®ricas
        tabview = ctk.CTkTabview(scroll_frame)
        tabview.pack(fill="x", padx=10, pady=(0, 10))

        # Tab F1-F12
        tab_f = tabview.add(self.localization_manager.get_string("hotkey_tab_f_keys", "Teclas F"))
        self._create_f_keys(tab_f)

        # Tab alfanum├®ricas
        tab_alpha = tabview.add(self.localization_manager.get_string("hotkey_tab_alpha_keys", "A-Z"))
        self._create_alpha_keys(tab_alpha)

        # Preview
        ctk.CTkLabel(
            scroll_frame,
            text=self.localization_manager.get_string("hotkey_selected_preview"),
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        self.preview_label = ctk.CTkLabel(
            scroll_frame,
            text=self.current_hotkey.upper(),
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#1E293B",
            corner_radius=8,
            width=300,
            height=40
        )
        self.preview_label.pack(padx=10, pady=(0, 10))

        # Sugerencias por categor├¡a
        ctk.CTkLabel(
            scroll_frame,
            text=self.localization_manager.get_string("hotkey_suggestions"),
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        suggestions_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        suggestions_frame.pack(fill="x", padx=10, pady=(0, 10))

        suggestions = {
            self.localization_manager.get_string("hotkey_suggestions_work"): ["f1", "f2", "ctrl+f1"],
            self.localization_manager.get_string("hotkey_suggestions_ideas"): ["f3", "f4", "ctrl+f3"],
            self.localization_manager.get_string("hotkey_suggestions_personal"): ["f5", "f6", "alt+f5"],
            self.localization_manager.get_string("hotkey_suggestions_tech"): ["f7", "f8", "ctrl+shift+f7"],
        }

        for category, hotkeys in suggestions.items():
            cat_frame = ctk.CTkFrame(suggestions_frame, fg_color="transparent")
            cat_frame.pack(fill="x", pady=2)

            ctk.CTkLabel(
                cat_frame,
                text=category,
                font=ctk.CTkFont(size=11),
                width=80
            ).pack(side="left", padx=5)

            for hk in hotkeys:
                btn = ctk.CTkButton(
                    cat_frame,
                    text=hk.upper(),
                    width=70,
                    height=28,
                    command=lambda h=hk: self._select_suggestion(h)
                )
                btn.pack(side="left", padx=2)

        # Footer con botones
        footer_frame = ctk.CTkFrame(self, height=50)
        footer_frame.pack(fill="x", padx=10, pady=(0, 10))
        footer_frame.pack_propagate(False)

        ctk.CTkButton(
            footer_frame,
            text=self.localization_manager.get_string("hotkey_cancel"),
            width=100,
            command=self.destroy
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            footer_frame,
            text=self.localization_manager.get_string("hotkey_confirm"),
            width=100,
            command=self._confirm_selection,
            fg_color="#10B981",
            hover_color="#059669"
        ).pack(side="right", padx=5)

    def _create_f_keys(self, parent):
        """Crear botones de teclas F."""
        keys_grid = ctk.CTkFrame(parent, fg_color="transparent")
        keys_grid.pack(fill="x", padx=10, pady=10)

        # F1-F12 en 2 filas de 6
        self.key_vars = {}
        for i, f_key in enumerate([f"f{j}" for j in range(1, 13)]):
            row = i // 6
            col = i % 6

            var = ctk.BooleanVar(value=(f_key == self.current_key))
            self.key_vars[f_key] = var

            btn = ctk.CTkCheckBox(
                keys_grid,
                text=f_key.upper(),
                variable=var,
                command=self._update_preview
            )
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="w")

    def _create_alpha_keys(self, parent):
        """Crear botones de teclas A-Z."""
        keys_grid = ctk.CTkFrame(parent, fg_color="transparent")
        keys_grid.pack(fill="x", padx=10, pady=10)

        # A-Z en 4 filas de 7 (├║ltima fila con 5)
        alphabet = [chr(i) for i in range(ord('a'), ord('z') + 1)]

        # Agregar n├║meros 0-9 tambi├®n
        for i, char in enumerate(["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"] + alphabet):
            row = i // 7
            col = i % 7

            var = ctk.BooleanVar(value=(char == self.current_key))
            self.key_vars[char] = var

            btn = ctk.CTkCheckBox(
                keys_grid,
                text=char.upper(),
                variable=var,
                command=self._update_preview
            )
            btn.grid(row=row, column=col, padx=2, pady=2, sticky="w")

    def _update_preview(self):
        """Actualizar preview del hotkey."""
        # Obtener tecla seleccionada
        selected_key = None
        for key, var in self.key_vars.items():
            if var.get():
                selected_key = key
                break

        if not selected_key:
            selected_key = "f1"  # Default

        # Obtener modificadores
        modifiers = []
        if self.modifier_vars["ctrl"].get():
            modifiers.append("ctrl")
        if self.modifier_vars["alt"].get():
            modifiers.append("alt")
        if self.modifier_vars["shift"].get():
            modifiers.append("shift")

        # Construir string
        if modifiers:
            hotkey_str = "+".join(modifiers + [selected_key])
        else:
            hotkey_str = selected_key

        # Actualizar preview
        self.preview_label.configure(text=hotkey_str.upper())
        self.selected_hotkey = hotkey_str

    def _select_suggestion(self, hotkey_str: str):
        """Seleccionar hotkey desde sugerencias."""
        parsed = self.hotkey_manager.parse_hotkey_string(hotkey_str)

        # Actualizar checkboxes de modificadores
        self.modifier_vars["ctrl"].set("ctrl" in parsed.modifiers)
        self.modifier_vars["alt"].set("alt" in parsed.modifiers)
        self.modifier_vars["shift"].set("shift" in parsed.modifiers)

        # Actualizar checkboxes de teclas
        for key, var in self.key_vars.items():
            var.set(key == parsed.key)

        # Actualizar preview
        self._update_preview()

    def _confirm_selection(self):
        """Confirmar selecci├│n."""
        if self.selected_hotkey:
            self.on_hotkey_selected(self.selected_hotkey)
            self.destroy()


def show_hotkey_selector(
    parent,
    localization_manager,
    on_hotkey_selected: Callable[[str], None],
    current_hotkey: str = "f12"
) -> Optional[str]:
    """
    Mostrar selector de hotkeys.

    Args:
        parent: Ventana padre
        localization_manager: Gestor de localizaci├│n
        on_hotkey_selected: Callback cuando se selecciona
        current_hotkey: Hotkey actual

    Returns:
        Hotkey seleccionado
    """
    selector = HotkeySelector(parent, localization_manager, on_hotkey_selected, current_hotkey)
    parent.wait_window(selector)
    return selector.selected_hotkey


if __name__ == "__main__":
    # Test del selector
    import tkinter as tk

    root = ctk.CTk()
    root.geometry("300x200")

    def on_select(hotkey):
        print(f"Hotkey seleccionado: {hotkey}")

    ctk.CTkButton(
        root,
        text="Seleccionar Hotkey",
        command=lambda: show_hotkey_selector(root, on_select)
    ).pack(expand=True)

    root.mainloop()
