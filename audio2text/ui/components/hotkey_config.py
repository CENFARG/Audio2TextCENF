"""@File: audio2text/ui/components/hotkey_config.py
@Description: Hotkey binding UI — modifier checkboxes (Ctrl/Alt/Shift) + key selector.
    Emits normalized combo string (e.g., "ctrl+alt+f12").
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import flet as ft

from audio2text.localization.manager import LocalizationManager
from audio2text.ui.theme.theme import Colors, Spacing, Typography

_KEY_OPTIONS = [f"F{i}" for i in range(1, 13)]


class HotkeyConfig(ft.Column):
    """Hotkey configuration — modifier checkboxes + key selector dropdown."""

    def __init__(
        self,
        t: LocalizationManager,
        current_hotkey: str = "f8",
        on_change: ft.OptionalEventCallable = None,
    ) -> None:
        self._t = t
        self._current_hotkey = current_hotkey
        self._on_change = on_change

        self._cb_ctrl: ft.Checkbox = ft.Checkbox()
        self._cb_alt: ft.Checkbox = ft.Checkbox()
        self._cb_shift: ft.Checkbox = ft.Checkbox()
        self._key_dropdown: ft.Dropdown = ft.Dropdown()
        self._current_text: ft.Text = ft.Text()

        self._parse_current_hotkey(current_hotkey)
        ui = self.build()
        super().__init__(controls=[ui])

    def build(self) -> ft.Control:
        """Build the hotkey config UI."""
        self._cb_ctrl = ft.Checkbox(
            key="mod_ctrl", label="Ctrl",
            value=self._ctrl, on_change=self._on_selection_change,
        )
        self._cb_alt = ft.Checkbox(
            key="mod_alt", label="Alt",
            value=self._alt, on_change=self._on_selection_change,
        )
        self._cb_shift = ft.Checkbox(
            key="mod_shift", label="Shift",
            value=self._shift, on_change=self._on_selection_change,
        )
        self._key_dropdown = ft.Dropdown(
            key="key_select",
            label=self._t.get("hotkey.key"),
            options=[ft.dropdown.Option(key=k, text=k) for k in _KEY_OPTIONS],
            value=self._key,
            width=120,
        )
        self._key_dropdown.on_change = self._on_selection_change
        self._current_text = ft.Text(
            value=self._t.get("hotkey.current", hotkey=self._current_hotkey),
            size=Typography.SIZE_MD,
            color=Colors.TEXT_PRIMARY_DARK,
            font_family=Typography.FONT_FAMILY,
        )

        return ft.Container(
            content=ft.Column([
                ft.Text(self._t.get("hotkey.title"),
                        size=Typography.SIZE_LG, weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY_DARK,
                        font_family=Typography.FONT_FAMILY),
                ft.Text(self._t.get("hotkey.description"),
                        size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY_DARK,
                        font_family=Typography.FONT_FAMILY),
                ft.Row(
                    controls=[self._cb_ctrl, self._cb_alt, self._cb_shift],
                    spacing=Spacing.SM,
                ),
                ft.Row(
                    controls=[
                        ft.Text("+", size=Typography.SIZE_LG),
                        self._key_dropdown,
                    ],
                    spacing=Spacing.SM,
                ),
                self._current_text,
            ], spacing=Spacing.MD),
            padding=Spacing.MD,
        )

    def _parse_current_hotkey(self, hotkey: str) -> None:
        """Parse a hotkey string into modifier flags and key."""
        parts = hotkey.lower().split("+")
        self._ctrl = "ctrl" in parts
        self._alt = "alt" in parts
        self._shift = "shift" in parts
        for p in parts:
            if p.startswith("f") and p[1:].isdigit():
                self._key = p
                return
        self._key = "f8"

    def _build_combo(self) -> str:
        """Build the normalized combo string from current state."""
        mods: list[str] = []
        if self._cb_ctrl.value:
            mods.append("ctrl")
        if self._cb_alt.value:
            mods.append("alt")
        if self._cb_shift.value:
            mods.append("shift")
        key = self._key_dropdown.value or "f8"
        mods.append(key.lower())
        self._current_hotkey = "+".join(mods)
        return self._current_hotkey

    def _on_selection_change(self, e: ft.ControlEvent) -> None:
        """Update composed hotkey when any control changes."""
        self._ctrl = bool(self._cb_ctrl.value)
        self._alt = bool(self._cb_alt.value)
        self._shift = bool(self._cb_shift.value)
        self._key = str(self._key_dropdown.value or "f8")

        combo = self._build_combo()
        self._current_text.value = self._t.get("hotkey.current", hotkey=combo)
        if self._on_change:
            self._on_change(e)
        self.update()

    @property
    def current_hotkey(self) -> str:
        """The currently composed hotkey string."""
        self._build_combo()
        return self._current_hotkey

    @current_hotkey.setter
    def current_hotkey(self, value: str) -> None:
        self._current_hotkey = value
