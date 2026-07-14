"""@File: audio2text/ui/views/settings_view.py
@Description: Settings view with ALL settings fields for v0.16 feature parity.
    Auto-saves on change with 400ms debounce.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import logging
import threading

import flet as ft

from audio2text.localization.manager import LocalizationManager
from audio2text.ui.client.api_client import APIClient
from audio2text.ui.components.hotkey_config import HotkeyConfig
from audio2text.ui.components.provider_config import ProviderConfig
from audio2text.ui.components.vocabulary_editor import VocabularyEditor
from audio2text.ui.state.store import AppState
from audio2text.ui.theme.theme import Colors, Spacing, Typography

_logger = logging.getLogger("ui.views.settings_view")

_FW_MODELS = ["tiny", "base", "small", "medium", "large-v3"]
_FW_DEVICES = ["auto", "cpu", "cuda"]
_RECORD_MODES = ["toggle", "hold"]
_MAX_RECORDING_TIMES = ["5min", "10min", "15min", "20min"]


class SettingsView(ft.Column):
    """Full settings page with all configuration fields.

    Features:
    - Provider: Groq/NVIDIA API keys, ASR provider, faster-whisper model/device
    - Audio: paths, max files, auto cleanup, save audio
    - Recording: mode, max time
    - UI toggles: auto-paste, show panel, post-processing, blocks, startup
    - Hotkey: modifier + key selector
    - Vocabulary: custom corrections
    - Auto-save: debounced 400ms PUT to API on any field change
    """

    def __init__(
        self,
        store: AppState,
        api: APIClient,
        t: LocalizationManager,
    ) -> None:
        self._store = store
        self._api = api
        self._t = t
        self._fields: dict[str, ft.Control] = {}
        self._debounce_timer: threading.Timer | None = None

        self._provider_config = ProviderConfig(store=store, t=t)
        self._hotkey_config = HotkeyConfig(t=t)
        self._vocab_editor = VocabularyEditor(t=t)

        ui = self.build()
        super().__init__(controls=[ui], expand=True)

    def did_mount(self) -> None:
        """Load settings from store on mount and populate all fields."""
        settings = self._store.settings
        if not settings:
            return
        for key, control in self._fields.items():
            value = settings.get(key)
            if value is None:
                continue
            try:
                if isinstance(control, ft.TextField):
                    control.value = str(value)
                elif isinstance(control, ft.Dropdown):
                    control.value = str(value)
                elif isinstance(control, ft.Switch):
                    control.value = bool(value)
                elif isinstance(control, ft.RadioGroup):
                    control.value = str(value)
            except Exception:
                pass

    def build(self) -> ft.Control:
        """Build the full settings form."""
        sections = [
            self._build_section_title("settings.title"),
            self._build_provider_section(),
            self._build_audio_section(),
            self._build_recording_section(),
            self._build_ui_section(),
            self._build_postprocessing_section(),
            self._build_blocks_section(),
            self._build_hotkey_section(),
            self._build_vocab_section(),
        ]

        return ft.Container(
            content=ft.Column(
                controls=sections,
                spacing=Spacing.MD,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            expand=True,
            bgcolor=Colors.BACKGROUND_DARK,
            padding=Spacing.MD,
        )

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _build_section_title(self, key: str) -> ft.Text:
        return ft.Text(
            value=self._t.get(key),
            size=Typography.SIZE_XL,
            weight=ft.FontWeight.BOLD,
            color=Colors.TEXT_PRIMARY_DARK,
            font_family=Typography.FONT_FAMILY,
        )

    def _build_provider_section(self) -> ft.Control:
        """Provider config: radio, API keys, ASR, fw model/device."""
        return ft.Container(
            content=ft.Column([
                ft.Text(self._t.get("settings.provider"),
                        size=Typography.SIZE_LG, weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY_DARK,
                        font_family=Typography.FONT_FAMILY),
                self._provider_config,
                self._mk_password("groq_api_key", "settings.groq_api_key", "settings.groq_api_key_hint"),
                self._mk_password("nvidia_api_key", "settings.nvidia_api_key", "settings.nvidia_api_key_hint"),
                self._mk_dropdown("asr_provider", "settings.asr_provider", [
                    ft.dropdown.Option("groq", self._t.get("providers.groq")),
                    ft.dropdown.Option("faster_whisper", self._t.get("providers.faster_whisper")),
                    ft.dropdown.Option("nvidia_riva", self._t.get("providers.nvidia_riva")),
                ]),
                self._mk_dropdown("fw_model", "settings.fw_model", [
                    ft.dropdown.Option(m, self._t.get(f"settings.fw_model_{m.replace('-', '')}",
                                           default=m)) for m in _FW_MODELS
                ]),
                self._mk_dropdown("fw_device", "settings.fw_device", [
                    ft.dropdown.Option(d, self._t.get(f"settings.fw_device_{d}",
                                           default=d)) for d in _FW_DEVICES
                ]),
            ], spacing=Spacing.SM),
            padding=ft.Padding(0, 0, 0, Spacing.MD),
        )

    def _build_audio_section(self) -> ft.Control:
        """Audio paths + max files + cleanup + save toggle."""
        audio_path_row = ft.Row([
            self._mk_textfield("audio_path", "settings.audio_path", "settings.audio_path_hint", expand=True),
            ft.ElevatedButton(
                key="audio_path_browse",
                content=ft.Text(self._t.get("settings.audio_path_browse")),
                on_click=self._on_browse_audio,
            ),
        ], spacing=Spacing.SM)
        tx_path_row = ft.Row([
            self._mk_textfield("transcriptions_path", "settings.transcriptions_path",
                               "settings.transcriptions_path_hint", expand=True),
            ft.ElevatedButton(
                key="transcriptions_path_browse",
                content=ft.Text(self._t.get("settings.transcriptions_path_browse")),
                on_click=self._on_browse_transcriptions,
            ),
        ], spacing=Spacing.SM)

        return ft.Container(
            content=ft.Column([
                ft.Text("Audio", size=Typography.SIZE_LG, weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY_DARK, font_family=Typography.FONT_FAMILY),
                audio_path_row, tx_path_row,
                self._mk_textfield("max_audio_files", "settings.max_audio_files",
                                   "settings.max_audio_files_hint", width=160),
                self._mk_switch("auto_cleanup", "settings.auto_cleanup", "settings.auto_cleanup_desc"),
                self._mk_switch("save_audio", "settings.save_audio", "settings.save_audio_desc"),
            ], spacing=Spacing.SM),
            padding=ft.Padding(0, 0, 0, Spacing.MD),
        )

    def _build_recording_section(self) -> ft.Control:
        """Record mode + max recording time."""
        return ft.Container(
            content=ft.Column([
                ft.Text("Recording", size=Typography.SIZE_LG, weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY_DARK, font_family=Typography.FONT_FAMILY),
                ft.RadioGroup(
                    key="record_mode",
                    content=ft.Row([
                        ft.Radio(value="toggle", label=self._t.get("settings.record_mode_toggle")),
                        ft.Radio(value="hold", label=self._t.get("settings.record_mode_hold")),
                    ]),
                    value="toggle",
                    on_change=self._on_field_change,
                ),
                self._mk_dropdown("max_recording_time", "settings.max_recording_time", [
                    ft.dropdown.Option(t, self._t.get(f"settings.max_recording_time_{t}",
                                           default=t.replace('min', ' min')))
                    for t in _MAX_RECORDING_TIMES
                ]),
            ], spacing=Spacing.SM),
            padding=ft.Padding(0, 0, 0, Spacing.MD),
        )

    def _build_ui_section(self) -> ft.Control:
        """UI toggles and startup."""
        return ft.Container(
            content=ft.Column([
                ft.Text("UI", size=Typography.SIZE_LG, weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY_DARK, font_family=Typography.FONT_FAMILY),
                self._mk_switch("auto_paste", "settings.auto_paste", "settings.auto_paste_desc"),
                self._mk_switch("show_panel", "settings.show_panel", "settings.show_panel_desc"),
                self._mk_switch("start_with_windows", "settings.start_with_windows",
                                "settings.start_with_windows_desc"),
            ], spacing=Spacing.SM),
            padding=ft.Padding(0, 0, 0, Spacing.MD),
        )

    def _build_postprocessing_section(self) -> ft.Control:
        """Post-processing toggle + model selector."""
        pp_toggle = self._mk_switch("post_processing", "settings.post_processing",
                                     "settings.post_processing_desc")
        return ft.Container(
            content=ft.Column([
                ft.Text("Post-processing", size=Typography.SIZE_LG, weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY_DARK, font_family=Typography.FONT_FAMILY),
                pp_toggle,
                self._mk_dropdown("post_model", "settings.post_model", [
                    ft.dropdown.Option("groq", self._t.get("settings.post_model_groq")),
                    ft.dropdown.Option("openai", self._t.get("settings.post_model_openai")),
                ]),
            ], spacing=Spacing.SM),
            padding=ft.Padding(0, 0, 0, Spacing.MD),
        )

    def _build_blocks_section(self) -> ft.Control:
        """Blocks toggles: task extractor, summary, keyword extractor."""
        return ft.Container(
            content=ft.Column([
                ft.Text("Blocks", size=Typography.SIZE_LG, weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY_DARK, font_family=Typography.FONT_FAMILY),
                self._mk_switch("blocks_task", "settings.blocks_task", "settings.blocks_task_desc"),
                self._mk_switch("blocks_summary", "settings.blocks_summary", "settings.blocks_summary_desc"),
                self._mk_switch("blocks_keyword", "settings.blocks_keyword", "settings.blocks_keyword_desc"),
            ], spacing=Spacing.SM),
            padding=ft.Padding(0, 0, 0, Spacing.MD),
        )

    def _build_hotkey_section(self) -> ft.Control:
        """Hotkey config."""
        return ft.Container(
            content=ft.Column([
                ft.Text(self._t.get("settings.hotkey_config"),
                        size=Typography.SIZE_LG, weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY_DARK, font_family=Typography.FONT_FAMILY),
                self._hotkey_config,
            ], spacing=Spacing.SM),
            padding=ft.Padding(0, 0, 0, Spacing.MD),
        )

    def _build_vocab_section(self) -> ft.Control:
        """Vocabulary editor section."""
        return ft.Container(
            content=self._vocab_editor,
            padding=ft.Padding(0, 0, 0, Spacing.MD),
        )

    # ------------------------------------------------------------------
    # Control factory helpers
    # ------------------------------------------------------------------

    def _mk_password(
        self, key: str, label_key: str, hint_key: str, **kw: object
    ) -> ft.TextField:
        field = ft.TextField(
            key=key,
            label=self._t.get(label_key),
            hint_text=self._t.get(hint_key),
            password=True,
            can_reveal_password=True,
            border_color=Colors.BORDER_DARK,
            text_size=Typography.SIZE_SM,
            on_change=self._on_field_change,
            **kw,  # type: ignore[arg-type]
        )
        self._fields[key] = field
        return field

    def _mk_textfield(
        self, key: str, label_key: str, hint_key: str, **kw: object
    ) -> ft.TextField:
        field = ft.TextField(
            key=key,
            label=self._t.get(label_key),
            hint_text=self._t.get(hint_key),
            border_color=Colors.BORDER_DARK,
            text_size=Typography.SIZE_SM,
            on_change=self._on_field_change,
            **kw,  # type: ignore[arg-type]
        )
        self._fields[key] = field
        return field

    def _mk_dropdown(
        self, key: str, label_key: str, options: list[ft.dropdown.Option]
    ) -> ft.Dropdown:
        dd = ft.Dropdown(
            key=key,
            label=self._t.get(label_key),
            options=options,
            border_color=Colors.BORDER_DARK,
            text_size=Typography.SIZE_SM,
        )
        dd.on_change = self._on_field_change
        self._fields[key] = dd
        return dd

    def _mk_switch(
        self, key: str, label_key: str, desc_key: str
    ) -> ft.Row:
        sw = ft.Switch(
            key=key,
            label=self._t.get(label_key),
            value=False,
            on_change=self._on_field_change,
        )
        self._fields[key] = sw
        return ft.Row([
            sw,
            ft.Text(self._t.get(desc_key),
                    size=Typography.SIZE_XS,
                    color=Colors.TEXT_SECONDARY_DARK,
                    font_family=Typography.FONT_FAMILY),
        ], spacing=Spacing.SM)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_field_change(self, e: ft.ControlEvent) -> None:
        """Debounced auto-save on any field change."""
        self._debounced_save()

    def _debounced_save(self) -> None:
        """Schedule a save after 400ms, cancelling previous."""
        import threading

        if self._debounce_timer and not self._debounce_timer.done():
            self._debounce_timer.cancel()
        # Use threading.Timer for sync-safe debounce
        timer = threading.Timer(0.4, self._collect_and_save_sync)
        timer.daemon = True
        timer.start()

    def _collect_and_save_sync(self) -> None:
        """Collect all field values and PUT to API (synchronous)."""
        partial: dict[str, object] = {}
        for key, control in self._fields.items():
            if isinstance(control, ft.TextField):
                partial[key] = control.value or ""
            elif isinstance(control, ft.Dropdown):
                partial[key] = control.value or ""
            elif isinstance(control, ft.Switch):
                partial[key] = control.value
            elif isinstance(control, ft.RadioGroup):
                partial[key] = control.value or ""

        if partial:
            try:
                self._api.update_settings(partial)
                _logger.debug("Settings auto-saved: %d keys", len(partial))
            except Exception as exc:
                _logger.warning("Auto-save settings failed: %s", exc)

    def _on_save_settings(self) -> None:
        """Manual save via API (debounced)."""
        self._debounced_save()

    # ------------------------------------------------------------------
    # Browse handlers (directory pickers)
    # ------------------------------------------------------------------

    def _on_browse_audio(self, e: ft.ControlEvent) -> None:
        """Open directory picker for audio path."""
        import tkinter.filedialog as fd
        path = fd.askdirectory(title=self._t.get("settings.audio_path"))
        if path and "audio_path" in self._fields:
            field = self._fields["audio_path"]
            if isinstance(field, ft.TextField):
                field.value = path
                try:
                    field.update()
                except RuntimeError:
                    _logger.debug("Browse audio: field not mounted, skipping update()")
                self._debounced_save()

    def _on_browse_transcriptions(self, e: ft.ControlEvent) -> None:
        """Open directory picker for transcriptions path."""
        import tkinter.filedialog as fd
        path = fd.askdirectory(title=self._t.get("settings.transcriptions_path"))
        if path and "transcriptions_path" in self._fields:
            field = self._fields["transcriptions_path"]
            if isinstance(field, ft.TextField):
                field.value = path
                try:
                    field.update()
                except RuntimeError:
                    _logger.debug("Browse transcriptions: field not mounted, skipping update()")
                self._debounced_save()
