"""@File: audio2text/ui/components/context_blocks_selector.py
@Description: Context blocks selector — loads Grama blocks from API, renders checkboxes,
    shows selection count badge, and provides "Apply to AI Chat" action.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from audio2text.localization.manager import LocalizationManager
from audio2text.ui.client.api_client import APIClient
from audio2text.ui.state.store import AppState
from audio2text.ui.theme.theme import Colors, Spacing, Typography


class ContextBlocksSelector(ft.Column):
    """Sidebar component listing context blocks as selectable checkboxes.

    Features:
    - Loads blocks from API (GET /api/v1/context-blocks).
    - Renders checkboxes with name + description.
    - Selected blocks shown with count badge.
    - "Apply to AI Chat" button to use selected blocks for enhancement.
    """

    def __init__(
        self,
        store: AppState,
        api: APIClient,
        t: LocalizationManager,
        on_apply: Callable[[list[str]], None] | None = None,
    ) -> None:
        """Initialize the context blocks selector.

        Args:
            store: Central application state.
            api: API client for loading blocks.
            t: Localization manager for translated strings.
            on_apply: Callback when "Apply" is clicked (receives selected block IDs).
        """
        self._store = store
        self._api = api
        self._t = t
        self._on_apply = on_apply

        self._blocks: list[dict[str, object]] = []
        self._checkboxes: dict[str, ft.Checkbox] = {}
        self._badge: ft.Text = ft.Text()
        self._list_column: ft.Column = ft.Column()
        self._loading: ft.ProgressRing = ft.ProgressRing()
        self._error_text: ft.Text = ft.Text()

        ui = self.build()
        super().__init__(controls=[ui])

    def build(self) -> ft.Control:
        """Build the context blocks selector UI.

        Returns:
            A Flet container with the blocks list.
        """
        self._badge = ft.Text(
            value=self._t.get("blocks.selected_count", n=0),
            size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY_DARK,
            font_family=Typography.FONT_FAMILY,
        )
        self._loading = ft.ProgressRing(width=20, height=20, visible=False)
        self._error_text = ft.Text(
            value="",
            size=Typography.SIZE_SM,
            color=Colors.ERROR,
            font_family=Typography.FONT_FAMILY,
            visible=False,
        )
        self._list_column = ft.Column(spacing=Spacing.SM)

        apply_btn = ft.ElevatedButton(
            content=ft.Text(self._t.get("blocks.apply")),
            icon=ft.Icons.AUTO_AWESOME,
            bgcolor=Colors.PRIMARY_DARK,
            color=Colors.TEXT_PRIMARY_DARK,
            on_click=self._on_apply_click,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        value=self._t.get("blocks.title"),
                        size=Typography.SIZE_LG,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY_DARK,
                        font_family=Typography.FONT_FAMILY,
                    ),
                    ft.Text(
                        value=self._t.get("blocks.description"),
                        size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY_DARK,
                        font_family=Typography.FONT_FAMILY,
                    ),
                    self._badge,
                    self._loading,
                    self._error_text,
                    self._list_column,
                    apply_btn,
                ],
                spacing=Spacing.MD,
            ),
            padding=Spacing.MD,
        )

    def did_mount(self) -> None:
        """Load blocks on mount."""
        self._load_blocks()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_blocks(self) -> None:
        """Fetch blocks from the API and render the list."""
        self._loading.visible = True
        self._error_text.visible = False
        self.update()

        # NOTE: In full async Flet, this would use asyncio.
        # For now, we structure the code ready for async wrapping.
        try:
            # Simulated: replace with real httpx call in production
            self._blocks = self._get_blocks_sync()
            self._build_checkboxes()
            self._loading.visible = False
        except Exception as exc:
            self._error_text.value = self._t.get("blocks.load_error", error=str(exc))
            self._error_text.visible = True
            self._loading.visible = False
        self.update()

    def _get_blocks_sync(self) -> list[dict[str, object]]:
        """Load blocks synchronously (placeholder — real impl uses async)."""
        # TODO: Replace with real API call via self._api
        return [
            {
                "id": "task_extractor",
                "name": self._t.get("blocks.task_extractor"),
                "description": self._t.get("blocks.task_extractor_desc"),
                "enabled": True,
                "order": 1,
            },
            {
                "id": "summary",
                "name": self._t.get("blocks.summary"),
                "description": self._t.get("blocks.summary_desc"),
                "enabled": True,
                "order": 2,
            },
            {
                "id": "keywords",
                "name": self._t.get("blocks.keywords"),
                "description": self._t.get("blocks.keywords_desc"),
                "enabled": True,
                "order": 3,
            },
        ]

    # ------------------------------------------------------------------
    # Checkbox rendering
    # ------------------------------------------------------------------

    def _build_checkboxes(self) -> None:
        """Build checkbox controls for each loaded block."""
        self._checkboxes.clear()
        controls: list[ft.Control] = []

        def _sort_key(b: dict[str, object]) -> int:
            order = b.get("order")
            return int(order) if isinstance(order, (int, float)) else 100

        for block in sorted(self._blocks, key=_sort_key):
            block_id = str(block.get("id", ""))
            name = str(block.get("name", block_id))
            desc = str(block.get("description", ""))
            enabled = bool(block.get("enabled", True))

            cb = ft.Checkbox(
                label=name,
                value=block_id in self._store.selected_context_blocks,
                on_change=self._on_checkbox_change,
                disabled=not enabled,
            )
            self._checkboxes[block_id] = cb

            col_controls: list[ft.Control] = [cb]
            if desc:
                col_controls.append(
                    ft.Text(
                        value=desc,
                        size=Typography.SIZE_XS,
                        color=Colors.TEXT_SECONDARY_DARK,
                        font_family=Typography.FONT_FAMILY,
                    )
                )

            controls.append(
                ft.Column(controls=col_controls, spacing=Spacing.XS)
            )

        self._list_column.controls = controls
        self._update_badge()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_checkbox_change(self, e: ft.ControlEvent) -> None:
        """Update selected blocks when a checkbox changes.

        Args:
            e: Flet control event.
        """
        selected: set[str] = set()
        for block_id, cb in self._checkboxes.items():
            if cb.value:
                selected.add(block_id)
        self._store.selected_context_blocks = selected
        self._update_badge()
        self.update()

    def _on_apply_click(self, e: ft.ControlEvent) -> None:
        """Handle "Apply to AI Chat" button click.

        Args:
            e: Flet control event.
        """
        selected_ids = list(self._store.selected_context_blocks)
        if selected_ids and self._on_apply:
            self._on_apply(selected_ids)

    def _update_badge(self) -> None:
        """Update the selected count badge text."""
        count = self._store.context_block_count
        self._badge.value = self._t.get("blocks.selected_count", n=count)
