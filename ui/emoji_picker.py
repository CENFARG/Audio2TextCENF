"""
Emoji Picker - Selector de emojis para renombrar transcripciones.

Permite al usuario seleccionar un emoji para identificar visualmente
sus transcripciones en el historial.
"""

import customtkinter as ctk
from typing import Optional, Callable


class EmojiPicker(ctk.CTkToplevel):
    """Selector de emojis minimalista para Audio2Text."""

    # Emojis organizados por categoría (los más útiles para transcripciones)
    EMOJIS = {
        "Trabajo": [
            "📞", "💼", "📧", "📅", "📝",
            "✅", "🎯", "📊", "📈", "💡",
            "🗂️", "📁", "🏷️", "📋", "✏️"
        ],
        "Ideas": [
            "💭", "🧠", "💡", "✨", "🌟",
            "🚀", "💫", "⚡", "🔥", "💎",
            "🎨", "🎬", "🎵", "📚", "🔬"
        ],
        "Tareas": [
            "⏰", "📌", "📍", "🔔", "⏳",
            "🔧", "🛠️", "⚙️", "🔨", "🧩",
            "📦", "📮", "✉️", "📨", "📩"
        ],
        "Personas": [
            "👤", "👥", "🧑‍💻", "👨‍💼", "👩‍💼",
            "👨‍🏫", "👩‍🏫", "🧑‍🎓", "👨‍🎓", "👩‍🎓",
            "👔", "👩‍⚕️", "🧑‍⚕️", "👨‍⚕️", "👩‍🔬"
        ],
        "Favoritos": [
            "❤️", "⭐", "🌟", "💛", "💚",
            "💙", "💜", "🖤", "🤍", "🤎",
            "🧡", "💝", "💖", "💗", "💓"
        ],
        "Otros": [
            "🎤", "🎧", "📹", "🎥", "🎞️",
            "💻", "🖥️", "⌨️", "🖱️", "💾",
            "☁️", "🔒", "🔓", "🔑", "📎"
        ]
    }

    def __init__(
        self,
        parent,
        on_emoji_selected: Callable[[str], None],
        current_emoji: str = "🎤",
        title: str = "Seleccionar Emoji"
    ):
        """
        Inicializar selector de emojis.

        Args:
            parent: Ventana padre
            on_emoji_selected: Callback cuando se selecciona un emoji
            current_emoji: Emoji actualmente seleccionado
            title: Título de la ventana
        """
        super().__init__(parent)

        self.on_emoji_selected = on_emoji_selected
        self.current_emoji = current_emoji
        self.selected_emoji = None

        # Configurar ventana
        self.title(title)
        self.geometry("500x450")
        self.resizable(False, False)

        # Hacer modal
        self.transient(parent)
        self.grab_set()

        # Centrar en pantalla
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (450 // 2)
        self.geometry(f"500x450+{x}+{y}")

        self._create_ui()

        # Foco en búsqueda
        self.search_entry.focus()

    def _create_ui(self):
        """Crear interfaz del selector."""
        # Header con búsqueda
        header_frame = ctk.CTkFrame(self, height=60)
        header_frame.pack(fill="x", padx=10, pady=10)
        header_frame.pack_propagate(False)

        ctk.CTkLabel(
            header_frame,
            text="🔍",
            font=ctk.CTkFont(size=16)
        ).pack(side="left", padx=(10, 5))

        self.search_entry = ctk.CTkEntry(
            header_frame,
            placeholder_text="Buscar emojis...",
            height=35
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", self._on_search)

        # Botón cancelar
        ctk.CTkButton(
            header_frame,
            text="✕",
            width=35,
            height=35,
            font=ctk.CTkFont(size=14),
            command=self.destroy,
            fg_color="gray"
        ).pack(side="right", padx=5)

        # Scrollable frame para categorías
        scroll_frame = ctk.CTkScrollableFrame(self, label_text="Categorías")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Crear categorías
        self.category_frames = {}
        for category, emojis in self.EMOJIS.items():
            self._create_category(scroll_frame, category, emojis)

        # Footer con emoji seleccionado
        footer_frame = ctk.CTkFrame(self, height=50)
        footer_frame.pack(fill="x", padx=10, pady=(0, 10))
        footer_frame.pack_propagate(False)

        self.selected_label = ctk.CTkLabel(
            footer_frame,
            text=f"Seleccionado: {self.current_emoji}",
            font=ctk.CTkFont(size=14)
        )
        self.selected_label.pack(side="left", padx=10)

        ctk.CTkButton(
            footer_frame,
            text="Confirmar",
            width=100,
            command=self._confirm_selection
        ).pack(side="right", padx=10)

    def _create_category(self, parent, category: str, emojis: list):
        """Crear categoría de emojis."""
        # Frame de categoría
        cat_frame = ctk.CTkFrame(parent)
        cat_frame.pack(fill="x", pady=5, padx=5)

        # Título de categoría
        cat_label = ctk.CTkLabel(
            cat_frame,
            text=category,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        cat_label.pack(anchor="w", padx=10, pady=(10, 5))

        # Grid de emojis
        emoji_grid = ctk.CTkFrame(cat_frame, fg_color="transparent")
        emoji_grid.pack(fill="x", padx=10, pady=(0, 10))

        # Crear botones de emoji (5 por fila)
        for i, emoji in enumerate(emojis):
            row = i // 5
            col = i % 5

            btn = ctk.CTkButton(
                emoji_grid,
                text=emoji,
                width=45,
                height=45,
                font=ctk.CTkFont(size=20),
                command=lambda e=emoji: self._on_emoji_click(e)
            )
            btn.grid(row=row, column=col, padx=3, pady=3)

            # Guardar referencia
            self.category_frames[emoji] = btn

    def _on_emoji_click(self, emoji: str):
        """Manejar clic en emoji."""
        self.selected_emoji = emoji
        self.selected_label.configure(text=f"Seleccionado: {emoji}")

        # Auto-confirmar
        self._confirm_selection()

    def _confirm_selection(self):
        """Confirmar selección y cerrar."""
        if self.selected_emoji:
            self.on_emoji_selected(self.selected_emoji)
            self.destroy()

    def _on_search(self, event):
        """Filtrar emojis por búsqueda."""
        search_text = self.search_entry.get().lower()

        if not search_text:
            # Mostrar todos
            for emoji, btn in self.category_frames.items():
                btn.configure(state="normal")
            return

        # Ocultar/mostrar según búsqueda
        for emoji, btn in self.category_frames.items():
            # Buscar por categoría o emoji
            matches = False
            for category, emojis in self.EMOJIS.items():
                if emoji in emojis and (search_text in category.lower() or search_text in emoji):
                    matches = True
                    break

            if matches:
                btn.configure(state="normal")
            else:
                btn.configure(state="disabled")


def show_emoji_picker(
    parent,
    on_emoji_selected: Callable[[str], None],
    current_emoji: str = "🎤"
) -> Optional[str]:
    """
    Mostrar selector de emojis y devolver emoji seleccionado.

    Args:
        parent: Ventana padre
        on_emoji_selected: Callback cuando se selecciona un emoji
        current_emoji: Emoji actualmente seleccionado

    Returns:
        Emoji seleccionado (si se confirma) o None
    """
    picker = EmojiPicker(parent, on_emoji_selected, current_emoji)
    parent.wait_window(picker)
    return picker.selected_emoji


if __name__ == "__main__":
    # Test del picker
    import tkinter as tk

    root = ctk.CTk()
    root.geometry("300x200")

    def on_select(emoji):
        print(f"Emoji seleccionado: {emoji}")

    ctk.CTkButton(
        root,
        text="Seleccionar Emoji",
        command=lambda: show_emoji_picker(root, on_select)
    ).pack(expand=True)

    root.mainloop()
