"""@File: audio2text/ui/views/history_view.py
@Description: Full history view with search, list, emoji picker, and item actions.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import logging

import flet as ft

from audio2text.localization.manager import LocalizationManager
from audio2text.ui.client.api_client import APIClient, APIError
from audio2text.ui.components.emoji_picker import EmojiPicker
from audio2text.ui.components.history_panel import HistoryPanel
from audio2text.ui.state.store import AppState
from audio2text.ui.theme.theme import Colors, Spacing, Typography

_logger = logging.getLogger("ui.views.history_view")


class HistoryView(ft.Column):
    """Full-page history browser with search, emoji picker, and item actions."""

    _page: ft.Page | None = None

    def __init__(
        self,
        store: AppState,
        api: APIClient,
        t: LocalizationManager,
    ) -> None:
        """Initialize the history view.

        Args:
            store: Central application state.
            api: API client for backend communication.
            t: Localization manager for translated strings.
        """
        self._store = store
        self._api = api
        self._t = t

        self._selected_item_id: str | None = None

        self._history_panel = HistoryPanel(
            store=store,
            t=t,
            on_select=self._on_item_select,
            on_delete=self._on_item_delete,
        )
        self._emoji_picker = EmojiPicker(
            t=t,
            on_pick=self._on_emoji_pick,
        )
        self._detail_panel = ft.Container(
            content=ft.Text(
                value=self._t.get("history.select_hint"),
                size=14,
                color=Colors.TEXT_SECONDARY_DARK,
            ),
            padding=Spacing.MD,
        )

        ui = self.build()
        super().__init__(controls=[ui], expand=True)

    def build(self) -> ft.Control:
        """Build the history view UI.

        Returns:
            A Flet container with split layout.
        """
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=self._history_panel,
                        expand=2,
                        border=ft.Border(
                            right=ft.BorderSide(1, Colors.BORDER_DARK)
                        ),
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                self._emoji_picker,
                                self._detail_panel,
                            ],
                            spacing=Spacing.MD,
                            expand=True,
                        ),
                        expand=1,
                        padding=Spacing.MD,
                    ),
                ],
                expand=True,
            ),
            expand=True,
            bgcolor=Colors.BACKGROUND_DARK,
        )

    def did_mount(self) -> None:
        """Load history items on mount."""
        self._store.on_history_change = self._on_history_changed  # type: ignore[assignment]
        page = self._get_page()
        if page is not None:
            page.run_task(self._load_history)

    def will_unmount(self) -> None:
        """Unsubscribe from state changes."""
        self._store.on_history_change = None

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    async def _load_history(self) -> None:
        """Fetch history items from API and populate the panel."""
        try:
            items = await self._api.get_history(limit=50, offset=0)
            self._store.hydrate_history(items)
            self._history_panel.set_items(items)
        except APIError as exc:
            _logger.warning("Failed to load history: %s", exc)
            self._api.show_error(self._get_page(), str(exc))
        except Exception as exc:
            _logger.error("Unexpected error loading history: %s", exc)

    def _on_history_changed(self, data: list[dict[str, object]]) -> None:
        """Handle external history changes."""
        self._history_panel.set_items(data)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_item_select(self, item_id: str) -> None:
        """Handle history item selection — display item details."""
        self._selected_item_id = item_id
        item = self._find_item(item_id)
        if item is None:
            self._detail_panel.content = ft.Text(
                value=self._t.get("history.select_hint"),
                size=14,
                color=Colors.TEXT_SECONDARY_DARK,
            )
        else:
            emoji = str(item.get("emoji", ""))
            title = str(item.get("title", "") or item.get("filename", "") or "")
            text = str(item.get("text", "") or "")
            provider = str(item.get("provider", ""))
            created = str(item.get("created_at", "") or "")

            title_text = f"{emoji} {title}" if emoji else title
            meta = provider
            if created:
                meta += f" · {created[:19]}"

            self._detail_panel.content = ft.Column(
                controls=[
                    ft.Text(
                        value=title_text[:120],
                        size=Typography.SIZE_LG,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY_DARK,
                        font_family=Typography.FONT_FAMILY,
                    ),
                    ft.Text(
                        value=meta,
                        size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY_DARK,
                        font_family=Typography.FONT_FAMILY,
                    ),
                    ft.Divider(color=Colors.BORDER_DARK, height=1),
                    ft.Text(
                        value=text if text else self._t.get("history.empty"),
                        size=Typography.SIZE_SM,
                        color=Colors.TEXT_PRIMARY_DARK,
                        font_family=Typography.FONT_FAMILY,
                        selectable=True,
                    ),
                ],
                spacing=Spacing.SM,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            )
        self._safe_update()

    def _on_item_delete(self, item_id: str) -> None:
        """Handle history item deletion via async API call."""
        page = self._get_page()
        if page is not None:
            page.run_task(self._do_delete_history_item, item_id)

    async def _do_delete_history_item(self, item_id: str) -> None:
        """Delete a history item via API and refresh."""
        try:
            await self._api.delete_history(item_id)
            _logger.info("Deleted history item: %s", item_id)
        except APIError as exc:
            _logger.warning("Failed to delete %s: %s", item_id, exc)
            self._api.show_error(self._get_page(), str(exc))
            return
        # Refresh after delete
        await self._load_history()

    def _on_emoji_pick(self, emoji: str) -> None:
        """Handle emoji selection — update selected history item metadata."""
        if self._selected_item_id is None:
            return
        page = self._get_page()
        if page is not None:
            page.run_task(self._do_update_emoji, self._selected_item_id, emoji)

    async def _do_update_emoji(self, item_id: str, emoji: str) -> None:
        """Update the emoji for a history item via API and refresh."""
        try:
            self._api.put(
                f"/api/v1/metadata/{item_id}",
                data={"emoji": emoji},
            )
            _logger.info("Updated emoji for %s: %s", item_id, emoji)
        except APIError as exc:
            _logger.warning("Failed to update emoji: %s", exc)
            self._api.show_error(self._get_page(), str(exc))
            return
        # Refresh to show updated emoji
        await self._load_history()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_page(self) -> ft.Page | None:
        """Return page reference or test-injected _page."""
        if self._page is not None:
            return self._page
        try:
            return self.page
        except RuntimeError:
            return None

    def _find_item(self, item_id: str) -> dict[str, object] | None:
        """Find a history item by ID in store.history."""
        for item in self._store.history:
            if item.get("id") == item_id:
                return item
        return None

    def _safe_update(self) -> None:
        """Call self.update(), guarded for test contexts without a page."""
        try:
            self.update()
        except RuntimeError:
            pass
