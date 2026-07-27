"""@File: audio2text/ui/components/history_panel.py
@Description: Scrollable list of past transcriptions with search/filter and actions.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from audio2text.localization.manager import LocalizationManager
from audio2text.ui.state.store import AppState
from audio2text.ui.theme.theme import Colors, Spacing, Typography


class HistoryPanel(ft.Column):
    """Scrollable list displaying past transcriptions.

    Features:
    - Search/filter by text.
    - Each item shows title, emoji, date, duration, provider.
    - Click to select, actions to view/copy/delete.
    """

    def __init__(
        self,
        store: AppState,
        t: LocalizationManager,
        on_select: Callable[[str], None] | None = None,
        on_delete: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize the history panel.

        Args:
            store: Central application state.
            t: Localization manager for translated strings.
            on_select: Callback when an item is selected (receives item ID).
            on_delete: Callback when an item is deleted (receives item ID).
        """
        self._store = store
        self._t = t
        self._on_select = on_select
        self._on_delete = on_delete

        self._search_field: ft.TextField = ft.TextField()
        self._list_view: ft.ListView = ft.ListView()
        self._items: list[dict[str, object]] = []
        self._empty_text: ft.Text = ft.Text()

        ui = self.build()
        super().__init__(controls=[ui])

    def build(self) -> ft.Control:
        """Build the history panel UI.

        Returns:
            A Flet container with search and scrollable list.
        """
        self._search_field = ft.TextField(
            hint_text=self._t.get("history.search"),
            prefix_icon=ft.Icons.SEARCH,
            on_change=self._on_search,
            border_color=Colors.BORDER_DARK,
            text_size=Typography.SIZE_SM,
        )
        self._empty_text = ft.Text(
            value=self._t.get("history.empty"),
            size=Typography.SIZE_MD,
            color=Colors.TEXT_SECONDARY_DARK,
            font_family=Typography.FONT_FAMILY,
            text_align=ft.TextAlign.CENTER,
        )
        self._list_view = ft.ListView(
            spacing=Spacing.SM,
            padding=Spacing.SM,
            expand=True,
            controls=(
                [self._empty_text]
                if not self._items
                else self._build_item_controls(self._items)
            ),
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        value=self._t.get("history.title"),
                        size=Typography.SIZE_XL,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_PRIMARY_DARK,
                        font_family=Typography.FONT_FAMILY,
                    ),
                    self._search_field,
                    self._list_view,
                ],
                spacing=Spacing.MD,
                expand=True,
            ),
            padding=Spacing.MD,
            expand=True,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_items(self, items: list[dict[str, object]]) -> None:
        """Update the displayed history items.

        Args:
            items: List of history item dicts with keys:
                id, title, emoji, text, provider, duration_s, created_at.
        """
        self._items = items
        self._refresh_list()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _refresh_list(self, filter_text: str = "") -> None:
        """Re-render the list with optional text filter.

        Args:
            filter_text: Optional search filter.
        """
        filtered = self._items
        if filter_text:
            lower = filter_text.lower()
            filtered = [
                item
                for item in self._items
                if lower in str(item.get("title", "")).lower()
                or lower in str(item.get("text", "")).lower()
            ]

        if not filtered:
            self._list_view.controls = [self._empty_text]
        else:
            self._list_view.controls = self._build_item_controls(filtered)
        self.update()

    def _build_item_controls(
        self, items: list[dict[str, object]]
    ) -> list[ft.Control]:
        """Build list item controls from data dicts.

        Args:
            items: List of history item dicts.

        Returns:
            List of Flet controls for the list view.
        """
        controls: list[ft.Control] = []
        for item in items:
            item_id = str(item.get("id", ""))
            emoji = str(item.get("emoji", ""))
            title = str(item.get("title", "") or item.get("text", "") or "")
            provider = str(item.get("provider", ""))
            duration_raw = item.get("duration_s", 0)
            duration = float(duration_raw) if isinstance(duration_raw, (int, float)) else 0.0
            created = str(item.get("created_at", ""))

            # Title row
            title_text = f"{emoji} {title}" if emoji else title or self._t.get("history.untitled")

            controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        value=title_text[:80],
                                        size=Typography.SIZE_MD,
                                        color=Colors.TEXT_PRIMARY_DARK,
                                        font_family=Typography.FONT_FAMILY,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                ],
                            ),
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        value=f"{provider} · {duration:.1f}s · {created[:10]}",
                                        size=Typography.SIZE_XS,
                                        color=Colors.TEXT_SECONDARY_DARK,
                                        font_family=Typography.FONT_FAMILY,
                                    ),
                                    ft.TextButton(
                                        content=ft.Text(self._t.get("history.view")),
                                        on_click=lambda e, iid=item_id: self._on_select_item(iid),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE_OUTLINE,
                                        icon_size=18,
                                        tooltip=self._t.get("history.delete"),
                                        on_click=lambda e, iid=item_id: self._on_delete_item(iid),
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                        ],
                        spacing=Spacing.XS,
                    ),
                    padding=Spacing.SM,
                    border=ft.Border(
                        bottom=ft.BorderSide(1, Colors.BORDER_DARK)
                    ),
                    on_click=lambda e, iid=item_id: self._on_select_item(iid),
                )
            )

        return controls

    def _on_search(self, e: ft.ControlEvent) -> None:
        """Handle search field changes.

        Args:
            e: Flet control event.
        """
        self._refresh_list(self._search_field.value or "")

    def _on_select_item(self, item_id: str) -> None:
        """Handle item selection.

        Args:
            item_id: ID of the selected item.
        """
        if self._on_select:
            self._on_select(item_id)

    def _on_delete_item(self, item_id: str) -> None:
        """Handle item deletion.

        Args:
            item_id: ID of the item to delete.
        """
        if self._on_delete:
            self._on_delete(item_id)
