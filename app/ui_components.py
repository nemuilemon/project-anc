"""Reusable UI Components for Project A.N.C.

This module provides common, reusable UI components to reduce code duplication
and maintain consistency across the application.
"""

import flet as ft
from datetime import datetime, timedelta
from typing import List, Callable, Optional, Dict, Any


class DatePickerButton(ft.Container):
    """A date picker with button component.

    Combines a date picker dialog with a button and displays the selected date.
    """

    def __init__(
        self,
        label: str = "日付選択",
        initial_date: Optional[datetime] = None,
        on_date_change: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.on_date_change = on_date_change
        self.selected_date = initial_date or datetime.now()

        # Date picker dialog
        self.date_picker = ft.DatePicker(
            first_date=datetime(2020, 1, 1),
            last_date=datetime.now() + timedelta(days=365),
            on_change=self._handle_date_change
        )

        # Date display text
        self.date_text = ft.Text(
            self.selected_date.strftime("%Y-%m-%d"),
            size=14,
            weight=ft.FontWeight.BOLD
        )

        # Date picker button
        self.button = ft.ElevatedButton(
            label,
            icon=ft.Icons.CALENDAR_MONTH,
            on_click=lambda e: self.page.open(self.date_picker) if hasattr(self, 'page') else None
        )

        self.content = ft.Row(
            [self.button, self.date_text],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )

    def _handle_date_change(self, e):
        """Handle date picker change event."""
        self.selected_date = self.date_picker.value
        self.date_text.value = self.selected_date.strftime("%Y-%m-%d")
        self.date_text.update()

        if self.on_date_change:
            self.on_date_change(self.selected_date)

    def get_selected_date(self) -> datetime:
        """Get the currently selected date."""
        return self.selected_date

    def get_date_string(self, format: str = "%Y-%m-%d") -> str:
        """Get the selected date as a formatted string."""
        return self.selected_date.strftime(format)


class ProgressButton(ft.Row):
    """A button with an integrated progress ring.

    Shows a progress indicator when the button action is in progress.
    """

    def __init__(
        self,
        text: str,
        icon: Optional[str] = None,
        on_click: Optional[Callable] = None,
        button_style: Optional[ft.ButtonStyle] = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.button = ft.ElevatedButton(
            text,
            icon=icon,
            on_click=on_click,
            style=button_style
        )

        self.progress_ring = ft.ProgressRing(
            visible=False,
            width=20,
            height=20
        )

        self.controls = [self.button, self.progress_ring]
        self.alignment = ft.MainAxisAlignment.CENTER
        self.spacing = 10

    def show_progress(self):
        """Show the progress indicator and disable the button."""
        self.progress_ring.visible = True
        self.button.disabled = True
        self.update()

    def hide_progress(self):
        """Hide the progress indicator and enable the button."""
        self.progress_ring.visible = False
        self.button.disabled = False
        self.update()


class ExpandableSection(ft.Column):
    """An expandable/collapsible section with header and content.

    Provides a clickable header that expands/collapses the content section.
    """

    def __init__(
        self,
        title: str,
        icon: str,
        content_items: List[ft.Control],
        initial_expanded: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.title = title
        self.icon = icon
        self.is_expanded = initial_expanded
        self.content_items = content_items

        # Section content
        self.section_content = ft.Column(
            content_items,
            spacing=10,
            visible=self.is_expanded
        )

        # Expansion icon
        self.expand_icon = ft.Icon(
            ft.Icons.EXPAND_LESS if self.is_expanded else ft.Icons.EXPAND_MORE,
            size=16,
            color=ft.Colors.GREY_700
        )

        # Header button (clickable)
        self.header_button = ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=16, color=ft.Colors.GREY_700),
                ft.Text(title, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                self.expand_icon
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            bgcolor=ft.Colors.GREY_100,
            border_radius=5,
            on_click=self._toggle,
            animate=200
        )

        # Animated content container
        self.animated_content = ft.Container(
            content=self.section_content,
            padding=ft.padding.symmetric(horizontal=10, vertical=5) if self.is_expanded else ft.padding.all(0),
            animate=300
        )

        self.controls = [self.header_button, self.animated_content]
        self.spacing = 0

    def _toggle(self, e=None):
        """Toggle the section expansion state."""
        self.is_expanded = not self.is_expanded
        self.section_content.visible = self.is_expanded

        # Update expand icon
        self.expand_icon.name = ft.Icons.EXPAND_LESS if self.is_expanded else ft.Icons.EXPAND_MORE

        # Update padding
        self.animated_content.padding = (
            ft.padding.symmetric(horizontal=10, vertical=5) if self.is_expanded
            else ft.padding.all(0)
        )

        self.update()

    def expand(self):
        """Programmatically expand the section."""
        if not self.is_expanded:
            self._toggle()

    def collapse(self):
        """Programmatically collapse the section."""
        if self.is_expanded:
            self._toggle()


class EditableTextField(ft.Container):
    """A multiline text field with edit capabilities and save button.

    Provides a text editing area with automatic save button state management.
    """

    def __init__(
        self,
        label: str = "編集",
        initial_value: str = "",
        min_lines: int = 10,
        max_lines: int = 20,
        on_save: Optional[Callable] = None,
        save_button_text: str = "保存",
        **kwargs
    ):
        super().__init__(**kwargs)

        self.on_save = on_save

        # Text field
        self.text_field = ft.TextField(
            label=label,
            value=initial_value,
            multiline=True,
            min_lines=min_lines,
            max_lines=max_lines,
            expand=True,
            on_change=self._on_text_change
        )

        # Save button
        self.save_button = ft.ElevatedButton(
            save_button_text,
            icon=ft.Icons.SAVE,
            on_click=self._handle_save,
            disabled=True
        )

        self.content = ft.Column([
            self.text_field,
            ft.Container(
                content=self.save_button,
                padding=ft.padding.symmetric(vertical=5)
            )
        ], spacing=10)

    def _on_text_change(self, e):
        """Enable save button when text changes."""
        self.save_button.disabled = not bool(self.text_field.value.strip())
        self.save_button.update()

    def _handle_save(self, e):
        """Handle save button click."""
        if self.on_save:
            self.on_save(self.text_field.value)
        self.save_button.disabled = True
        self.save_button.update()

    def get_value(self) -> str:
        """Get the current text value."""
        return self.text_field.value

    def set_value(self, value: str):
        """Set the text value."""
        self.text_field.value = value
        self.text_field.update()
        self._on_text_change(None)


class FileListItem(ft.Container):
    """A file list item with icon, title, and action buttons.

    Displays file information with optional actions like view, edit, delete.
    """

    def __init__(
        self,
        icon: str,
        icon_color: str,
        title: str,
        subtitle: Optional[str] = None,
        on_click: Optional[Callable] = None,
        actions: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Title and subtitle column
        info_column = ft.Column([
            ft.Text(title, size=12, weight=ft.FontWeight.BOLD),
        ], spacing=2, expand=True)

        if subtitle:
            info_column.controls.append(
                ft.Text(subtitle, size=10, color=ft.Colors.GREY_600)
            )

        # Action buttons
        action_controls = []
        if actions:
            for action in actions:
                action_controls.append(
                    ft.IconButton(
                        icon=action.get('icon', ft.Icons.MORE_VERT),
                        tooltip=action.get('tooltip', ''),
                        icon_size=16,
                        on_click=action.get('on_click')
                    )
                )

        # Main row
        self.content = ft.Row([
            ft.Icon(icon, color=icon_color, size=16),
            info_column,
            *action_controls
        ], spacing=5)

        self.padding = ft.padding.all(8)
        self.margin = ft.margin.symmetric(vertical=2)
        self.bgcolor = ft.Colors.WHITE
        self.border = ft.border.all(1, ft.Colors.GREY_200)
        self.border_radius = 5
        self.animate = 200

        if on_click:
            self.on_click = on_click


class SectionHeader(ft.Container):
    """A styled section header with title and optional actions.

    Provides consistent header styling across different sections.
    """

    def __init__(
        self,
        title: str,
        bgcolor: str = ft.Colors.BLUE_50,
        actions: Optional[List[ft.Control]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        title_text = ft.Text(
            title,
            size=14,
            weight=ft.FontWeight.BOLD
        )

        if actions:
            content = ft.Row([
                title_text,
                ft.Row(actions, spacing=2)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        else:
            content = title_text

        self.content = content
        self.padding = ft.padding.symmetric(horizontal=10, vertical=5)
        self.bgcolor = bgcolor
        self.border_radius = 5


class SearchField(ft.TextField):
    """A search field with search icon and clear button.

    Provides a standardized search input field.
    """

    def __init__(
        self,
        hint_text: str = "検索...",
        on_change: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.hint_text = hint_text
        self.prefix_icon = ft.Icons.SEARCH
        self.border = ft.InputBorder.OUTLINE
        self.dense = True

        if on_change:
            self.on_change = on_change


class StatusMessage(ft.Container):
    """A colored status message container.

    Displays success, error, warning, or info messages.
    """

    def __init__(
        self,
        message: str,
        status_type: str = "info",  # info, success, warning, error
        **kwargs
    ):
        super().__init__(**kwargs)

        colors = {
            'info': ft.Colors.BLUE_100,
            'success': ft.Colors.GREEN_100,
            'warning': ft.Colors.ORANGE_100,
            'error': ft.Colors.RED_100
        }

        icons = {
            'info': ft.Icons.INFO_OUTLINE,
            'success': ft.Icons.CHECK_CIRCLE_OUTLINE,
            'warning': ft.Icons.WARNING_AMBER,
            'error': ft.Icons.ERROR_OUTLINE
        }

        self.content = ft.Row([
            ft.Icon(icons.get(status_type, ft.Icons.INFO_OUTLINE), size=20),
            ft.Text(message, size=12)
        ], spacing=10)

        self.padding = ft.padding.all(10)
        self.bgcolor = colors.get(status_type, ft.Colors.BLUE_100)
        self.border_radius = 5
        self.margin = ft.margin.symmetric(vertical=5)


# Utility functions for common UI operations

def create_loading_overlay(message: str = "処理中...") -> ft.Container:
    """Create a loading overlay with progress indicator.

    Args:
        message: Loading message to display

    Returns:
        Container with loading UI
    """
    return ft.Container(
        content=ft.Column([
            ft.ProgressRing(),
            ft.Text(message, size=14)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        alignment=ft.alignment.center,
        bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLACK),
        expand=True
    )


def create_confirmation_dialog(
    title: str,
    message: str,
    on_confirm: Callable,
    on_cancel: Optional[Callable] = None,
    confirm_text: str = "確認",
    cancel_text: str = "キャンセル"
) -> ft.AlertDialog:
    """Create a confirmation dialog.

    Args:
        title: Dialog title
        message: Dialog message
        on_confirm: Callback for confirm action
        on_cancel: Optional callback for cancel action
        confirm_text: Text for confirm button
        cancel_text: Text for cancel button

    Returns:
        AlertDialog instance
    """
    return ft.AlertDialog(
        title=ft.Text(title),
        content=ft.Text(message),
        actions=[
            ft.TextButton(cancel_text, on_click=on_cancel),
            ft.ElevatedButton(confirm_text, on_click=on_confirm)
        ]
    )
