import flet as ft
import os
from security import sanitize_filename, validate_search_input, SecurityError

# --- New Approach: Inherit from a specific layout control (Flet >= 0.21.0) ---
class FileListItem(ft.ListTile):
    """ファイルリスト項目を表すカスタムUIコンポーネント。
    
    ListTileを継承し、ファイル情報の表示とタグ編集機能を提供する。
    表示モード（タグ表示 + ポップアップメニュー）と編集モード（タグ入力フィールド + 保存ボタン）
    を動的に切り替えることができる。
    
    Attributes:
        file_info (dict): ファイル情報辞書（title, path, tags, status, order_index）
        editing (bool): 現在編集モードかどうかのフラグ
        
    Callbacks:
        on_update_tags: タグ更新時のコールバック
        on_open_file: ファイルオープン時のコールバック
        on_rename_intent: ファイル名変更時のコールバック
        on_archive_intent: アーカイブ操作時のコールバック
        on_move_file: ファイル移動操作時のコールバック
        on_delete_intent: ファイル削除時のコールバック
    """
    def __init__(self, file_info, on_update_tags, on_open_file, on_rename_intent, on_archive_intent, on_move_file, on_delete_intent, on_ai_analysis=None, page=None):
        super().__init__()

        self.file_info = file_info
        self.on_update_tags = on_update_tags
        self.on_open_file = on_open_file
        self.on_rename_intent = on_rename_intent
        self.on_archive_intent = on_archive_intent
        self.on_move_file = on_move_file
        self.on_delete_intent = on_delete_intent
        self.on_ai_analysis = on_ai_analysis
        self.page = page  # Add page reference for snackbar
        self.editing = False

        # --- Define all controls that will be used/swapped ---
        self.tags_text = ft.Text(
            ", ".join(self.file_info.get('tags', [])), 
            size=10, 
            color=ft.Colors.GREY
        )
        self.tags_field = ft.TextField(
            dense=True,
            on_submit=self.save_clicked,
            
            border=ft.InputBorder.UNDERLINE,
            text_size=12,
        )
        
        # --- Control Group for View Mode (now a PopupMenuButton) ---
        # メニュー項目を動的に構築（アーカイブ状態に応じて）
        menu_items = [
            ft.PopupMenuItem(
                text="Rename file",
                icon=ft.Icons.DRIVE_FILE_RENAME_OUTLINE,
                on_click=self.rename_intent_clicked
            ),
            ft.PopupMenuItem(
                text="Edit tags",
                icon=ft.Icons.EDIT,
                on_click=self.edit_clicked
            ),
        ]
        
        # アーカイブ状態に応じてメニュー項目を追加
        file_status = self.file_info.get('status', 'active')
        if file_status == 'archived':
            menu_items.append(ft.PopupMenuItem(
                text="Unarchive file",
                icon=ft.Icons.UNARCHIVE,
                on_click=self.archive_intent_clicked
            ))
        else:
            menu_items.append(ft.PopupMenuItem(
                text="Archive file",
                icon=ft.Icons.ARCHIVE,
                on_click=self.archive_intent_clicked
            ))
        
        # 順番変更用のメニュー項目を追加
        menu_items.extend([
            ft.PopupMenuItem(),  # Separator
            ft.PopupMenuItem(
                text="Move Up",
                icon=ft.Icons.ARROW_UPWARD,
                on_click=self.move_up_clicked
            ),
            ft.PopupMenuItem(
                text="Move Down",
                icon=ft.Icons.ARROW_DOWNWARD,
                on_click=self.move_down_clicked
            ),
            ft.PopupMenuItem(
                text="Move to top",
                icon=ft.Icons.KEYBOARD_DOUBLE_ARROW_UP,
                on_click=self.move_to_top_clicked
            ),
            ft.PopupMenuItem(
                text="Move to bottom",
                icon=ft.Icons.KEYBOARD_DOUBLE_ARROW_DOWN,
                on_click=self.move_to_bottom_clicked
            ),
            ft.PopupMenuItem(),  # Separator
            ft.PopupMenuItem(
                text="Delete file",
                icon=ft.Icons.DELETE,
                on_click=self.delete_intent_clicked
            )
        ])
        
        self.menu_button = ft.PopupMenuButton(items=menu_items)

        self.save_button = ft.IconButton(
            icon=ft.Icons.SAVE,
            tooltip="Save tags",
            on_click=self.save_clicked
        )

        # --- Configure the initial state of the ListTile (self) ---
        self.title = ft.Text(self.file_info['title'])
        self.on_click = self.open_file_clicked
        # Use on_secondary_tap for right-click support
        self.on_secondary_tap = self.show_context_menu

        # Add drag and drop support
        self.data = self.file_info['path']  # Data to be transferred during drag
        self.set_view_mode() # Set initial controls

    def set_view_mode(self):
        """表示モードに切り替える。

        タグをテキスト表示し、ポップアップメニューボタンを表示する。
        編集モードから表示モードに戻る際に使用される。
        """
        self.subtitle = self.tags_text
        self.trailing = self.menu_button
        self.editing = False
        # Only call update if we're not in initialization (page exists and we're already part of a control tree)
        if self.page and hasattr(self, 'parent') and self.parent:
            try:
                self.update()
            except Exception as e:
                print(f"Warning: Failed to update FileListItem during set_view_mode: {e}")

    def set_edit_mode(self):
        """編集モードに切り替える。
        
        タグ入力用のテキストフィールドを表示し、保存ボタンを表示する。
        現在のタグ情報がテキストフィールドにプリセットされ、フォーカスが当たる。
        """
        self.tags_field.value = ", ".join(self.file_info.get('tags', []))
        self.subtitle = self.tags_field
        self.trailing = self.save_button
        self.editing = True
        if self.page: 
            self.update()
            self.tags_field.focus()

    def edit_clicked(self, e):
        self.set_edit_mode()

    def rename_intent_clicked(self, e):
        self.on_rename_intent(self.file_info)
    
    def archive_intent_clicked(self, e):
        print(f"Archive intent clicked for: {self.file_info['title']}")  # Debug log
        self.on_archive_intent(self.file_info)
    
    def move_up_clicked(self, e):
        self.on_move_file('up', self.file_info)

    def move_down_clicked(self, e):
        self.on_move_file('down', self.file_info)

    def move_to_top_clicked(self, e):
        self.on_move_file('top', self.file_info)

    def move_to_bottom_clicked(self, e):
        self.on_move_file('bottom', self.file_info)
    
    def delete_intent_clicked(self, e):
        self.on_delete_intent(self.file_info)

    def show_context_menu(self, e):
        """Show context menu on right-click."""
        # Show the existing popup menu button when right-clicked
        print(f"Right-click on {self.file_info['title']}")  # Debug
        # This will show a snackbar to confirm right-click works, then show menu
        if hasattr(self, 'page'):  # If we have page reference
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Right-clicked on {self.file_info['title']}"),
                duration=1000
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def ai_analysis_clicked(self, analysis_type):
        """AI分析を実行するコールバック"""
        if self.on_ai_analysis:
            self.on_ai_analysis(self.file_info['path'], analysis_type)

    def rename_clicked(self, e):
        """Shows a dialog to get a new file name."""
        
        new_name_field = ft.TextField(
            label="New file name",
            value=self.file_info['title'],
            autofocus=True,
        )

        def close_dialog(e):
            self.page.dialog.open = False
            self.page.update()

        def perform_rename(e):
            new_name = new_name_field.value.strip()
            if new_name:
                # 親に処理を依頼
                self.on_rename_file(self.file_info['path'], new_name)
            close_dialog(e)

        rename_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Rename File"),
            content=new_name_field,
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.FilledButton("Rename", on_click=perform_rename),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = rename_dialog
        self.page.dialog.open = True
        self.page.update()

    def save_clicked(self, e):
        new_tags_str = self.tags_field.value
        new_tags = [tag.strip() for tag in new_tags_str.split(',') if tag.strip()]
        
        # Update the display text for the next time we enter view mode
        self.file_info['tags'] = new_tags
        self.tags_text.value = new_tags_str
        
        # Switch back to view mode
        self.set_view_mode()

        # Call the main logic to save the data to the backend
        self.on_update_tags(self.file_info['path'], new_tags)

    def open_file_clicked(self, e):
        if not self.editing:
            self.on_open_file(self.file_info['path'])


class AppUI:
    """Project A.N.C.のメインユーザーインターフェースクラス。
    
    アプリケーションの全ユーザーインターフェース要素を管理し、
    ユーザーの操作をビジネスロジック層への適切なコールバックに転送する。
    
    主要機能:
    - タブベースのテキストエディタ
    - ファイルリスト表示・管理
    - AIタグ分析機能
    - アーカイブ機能
    - ファイル順序変更機能
    
    Attributes:
        page (ft.Page): Fletページオブジェクト
        tabs (ft.Tabs): メインのタブコンテナ
        file_list_column (ft.Column): ファイルリスト表示用コンテナ
        show_archived_button (ft.ElevatedButton): アーカイブエクスプローラーボタン
    
    Callbacks:
        各操作に対応するコールバック関数群（on_open_file, on_save_file等）
    """
    def __init__(self, page: ft.Page, on_open_file, on_save_file, on_analyze_tags, on_refresh_files, on_update_tags, on_cancel_tags, on_rename_file, on_close_tab, on_create_file, on_archive_file, on_update_order, on_delete_file, on_run_ai_analysis=None):
        self.page = page
        self.on_open_file = on_open_file
        self.on_save_file = on_save_file
        self.on_analyze_tags = on_analyze_tags
        self.on_refresh_files = on_refresh_files
        self.on_update_tags = on_update_tags
        self.on_cancel_tags = on_cancel_tags
        self.on_run_ai_analysis = on_run_ai_analysis
        self.on_rename_file = on_rename_file
        self.on_close_tab = on_close_tab
        self.on_create_file = on_create_file
        self.on_archive_file = on_archive_file
        self.on_update_order = on_update_order
        self.on_delete_file = on_delete_file
        
        self.tabs = ft.Tabs(selected_index=0, expand=True, tabs=[], on_change=self.on_tab_change)
        # ファイルリスト用のコンテナ
        self.file_list_column = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        self.file_list = self.file_list_column
        
        # アーカイブファイル表示ボタン
        self.show_archived_button = ft.ElevatedButton(
            text="Archive Explorer",
            icon=ft.Icons.ARCHIVE,
            on_click=self.show_archived_clicked,
            tooltip="Open Archive Explorer to view archived files"
        )
        
        # AI Analysis dropdown and button
        self.ai_analysis_dropdown = ft.Dropdown(
            label="AI Analysis Type",
            width=150,
            value="tagging",
            options=[
                ft.dropdown.Option("tagging", "Tags"),
                ft.dropdown.Option("summarization", "Summary"),
                ft.dropdown.Option("sentiment", "Sentiment")
            ],
            dense=True,
            on_change=self.ai_analysis_type_changed
        )
        
        self.analyze_button = ft.ElevatedButton(
            "Analyze Tags",
            icon=ft.Icons.AUTO_AWESOME,
            on_click=self.analyze_button_clicked
        )
        self.cancel_button = ft.ElevatedButton(
            "Cancel",
            icon=ft.Icons.CANCEL,
            on_click=lambda e: self.on_cancel_tags(),
            visible=False # 最初は隠しておく
        )
        self.progress_ring = ft.ProgressRing(visible=False) # 最初は隠しておく
        
        # Progress indicators for various operations
        self.file_progress_bar = ft.ProgressBar(
            value=0,
            visible=False,
            width=200,
            height=4,
            bgcolor=ft.Colors.GREY_300,
            color=ft.Colors.BLUE
        )
        self.operation_status_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.GREY_600,
            visible=False
        )

        # Create new file button separately for testing
        self.new_file_button = ft.IconButton(
            icon=ft.Icons.ADD,
            tooltip="New File",
            on_click=self.new_file_button_clicked
        )
        
        self.appbar = ft.AppBar(
            title=ft.Text("Project A.N.C."),
            actions=[
                self.new_file_button,  # Use the separate button
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Refresh file list",
                    on_click=lambda e: self.on_refresh_files()
                ),
                ft.ElevatedButton("Save", icon=ft.Icons.SAVE, on_click=self.save_button_clicked),
                # Progress indicators section
                ft.Column([
                    self.operation_status_text,
                    self.file_progress_bar
                ], spacing=2, tight=True),
                self.progress_ring,
                self.ai_analysis_dropdown,
                self.analyze_button,
                self.cancel_button
            ]
        )
        
        self.sidebar = ft.Container(
            content=ft.Column([
                self.show_archived_button,
                ft.Divider(height=10),
                self.file_list
            ]),
            width=250, padding=10, bgcolor=ft.Colors.BLACK12
        )

    def start_analysis_view(self):
        """分析中のUI表示に切り替える"""
        self.analyze_button.visible = False
        self.ai_analysis_dropdown.visible = False
        self.progress_ring.visible = True
        self.cancel_button.visible = True
        self.page.update()


    def stop_analysis_view(self):
        """通常のUI表示に戻す"""
        self.analyze_button.visible = True
        self.ai_analysis_dropdown.visible = True
        self.progress_ring.visible = False
        self.cancel_button.visible = False
        self.hide_progress_indicators()
        self.page.update()
    
    def show_progress_indicators(self, status_text: str = "Processing...", show_progress_bar: bool = True):
        """進捗インジケーターを表示する"""
        self.operation_status_text.value = status_text
        self.operation_status_text.visible = True
        
        if show_progress_bar:
            self.file_progress_bar.value = 0
            self.file_progress_bar.visible = True
        
        self.page.update()
    
    def update_progress(self, progress: int, status_text: str = None):
        """進捗を更新する（0-100の範囲）"""
        if self.file_progress_bar.visible:
            self.file_progress_bar.value = progress / 100
        
        if status_text:
            self.operation_status_text.value = status_text
        
        self.page.update()
    
    def hide_progress_indicators(self):
        """進捗インジケーターを非表示にする"""
        self.operation_status_text.visible = False
        self.file_progress_bar.visible = False
        self.file_progress_bar.value = 0
        self.page.update()
    
    def show_loading_state(self, message: str = "Loading...", show_spinner: bool = True):
        """ローディング状態を表示する"""
        self.operation_status_text.value = message
        self.operation_status_text.visible = True
        
        if show_spinner:
            self.progress_ring.visible = True
        
        self.page.update()
    
    def hide_loading_state(self):
        """ローディング状態を非表示にする"""
        self.operation_status_text.visible = False
        self.progress_ring.visible = False
        self.page.update()
    
    def show_ai_analysis_results(self, analysis_type: str, result_data: dict):
        """AI分析結果を表示するダイアログ"""
        title_map = {
            "summarization": "Summary Results",
            "sentiment": "Sentiment Analysis Results",
            "tagging": "Tagging Results"
        }
        
        content_widgets = []
        
        if analysis_type == "summarization":
            summary = result_data.get("summary", "No summary generated")
            summary_type = result_data.get("summary_type", "brief")
            compression_ratio = result_data.get("compression_ratio", 0)
            
            content_widgets.extend([
                ft.Text(f"Summary Type: {summary_type.title()}", weight=ft.FontWeight.BOLD),
                ft.Divider(height=1),
                ft.Container(
                    content=ft.Text(summary, selectable=True),
                    bgcolor=ft.Colors.GREY_100,
                    padding=10,
                    border_radius=5
                ),
                ft.Text(f"Compression Ratio: {compression_ratio:.2%}", size=12, color=ft.Colors.GREY_600)
            ])
            
        elif analysis_type == "sentiment":
            overall_sentiment = result_data.get("overall_sentiment", "Unknown")
            emotions = result_data.get("emotions_detected", [])
            intensity = result_data.get("intensity", "Unknown")
            
            # Sentiment color coding
            sentiment_color = ft.Colors.GREY
            if "ポジティブ" in overall_sentiment:
                sentiment_color = ft.Colors.GREEN
            elif "ネガティブ" in overall_sentiment:
                sentiment_color = ft.Colors.RED
                
            content_widgets.extend([
                ft.Row([
                    ft.Text("Overall Sentiment:", weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.Text(overall_sentiment, color=ft.Colors.WHITE),
                        bgcolor=sentiment_color,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=15
                    )
                ]),
                ft.Text(f"Intensity: {intensity}", size=14),
                ft.Text("Detected Emotions:", weight=ft.FontWeight.BOLD, size=14),
                ft.Row([
                    ft.Chip(
                        label=ft.Text(emotion.title()),
                        bgcolor=ft.Colors.BLUE_100
                    ) for emotion in emotions
                ] if emotions else [ft.Text("No specific emotions detected", color=ft.Colors.GREY)], wrap=True)
            ])
            
        elif analysis_type == "tagging":
            tags = result_data.get("tags", [])
            content_widgets.extend([
                ft.Text(f"Generated {len(tags)} tags:", weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.Chip(
                        label=ft.Text(tag),
                        bgcolor=ft.Colors.BLUE_100
                    ) for tag in tags
                ] if tags else [ft.Text("No tags generated", color=ft.Colors.GREY)], wrap=True)
            ])
        
        # Create and show dialog
        dialog = ft.AlertDialog(
            title=ft.Text(title_map.get(analysis_type, "Analysis Results")),
            content=ft.Container(
                content=ft.Column(
                    content_widgets,
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO
                ),
                width=500,
                height=300
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self.close_ai_results_dialog())
            ]
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.ai_results_dialog = dialog
        self.page.update()
    
    def close_ai_results_dialog(self):
        """AI分析結果ダイアログを閉じる"""
        if hasattr(self, 'ai_results_dialog') and self.ai_results_dialog in self.page.overlay:
            self.page.overlay.remove(self.ai_results_dialog)
            self.page.update()

        
    def ai_analysis_type_changed(self, e):
        """AI分析タイプが変更されたときの処理"""
        analysis_type = self.ai_analysis_dropdown.value
        if analysis_type == "tagging":
            self.analyze_button.text = "Analyze Tags"
            self.analyze_button.icon = ft.Icons.AUTO_AWESOME
        elif analysis_type == "summarization":
            self.analyze_button.text = "Generate Summary"
            self.analyze_button.icon = ft.Icons.SUMMARIZE
        elif analysis_type == "sentiment":
            self.analyze_button.text = "Analyze Sentiment"
            self.analyze_button.icon = ft.Icons.SENTIMENT_SATISFIED
        self.page.update()
    
    def auto_save_active_tab(self):
        """Auto-save the active tab if it has unsaved changes."""
        active_tab = self.get_active_tab()
        if active_tab and hasattr(active_tab.content, 'data'):
            path = active_tab.content.data
            content = active_tab.content.value
            if self.on_save_file:
                self.on_save_file(path, content)
                return True
        return False

    def auto_save_all_tabs(self):
        """Auto-save all open tabs."""
        saved_count = 0
        for tab in self.tabs.tabs:
            if hasattr(tab.content, 'data') and hasattr(tab.content, 'value'):
                path = tab.content.data
                content = tab.content.value
                if self.on_save_file:
                    self.on_save_file(path, content)
                    saved_count += 1
        return saved_count

    def on_tab_change(self, e):
        """Handle tab change event - auto-save the previously active tab."""
        # Auto-save the previously active tab (before switching)
        # Note: e.control.selected_index is the new tab index, we need to save the previous one
        # Since we can't easily track the previous tab, we'll auto-save all tabs with changes
        self.auto_save_all_tabs()


    def handle_keyboard_event(self, e):
        """Handle keyboard events for shortcuts like Ctrl+S."""
        if e.key == "S" and e.ctrl:
            # Ctrl+S: Save active tab
            if self.auto_save_active_tab():
                # Show brief confirmation
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("File saved"),
                    duration=1000  # 1 second
                )
                self.page.snack_bar.open = True
                self.page.update()

    def analyze_button_clicked(self, e):
        # Auto-save before AI analysis
        self.auto_save_active_tab()

        active_tab = self.get_active_tab()
        if active_tab and hasattr(active_tab.content, 'data'):
            path = active_tab.content.data
            content = active_tab.content.value
            analysis_type = self.ai_analysis_dropdown.value

            if analysis_type == "tagging":
                self.on_analyze_tags(path, content)
            else:
                # Use new AI analysis system for other types
                if self.on_run_ai_analysis:
                    self.on_run_ai_analysis(path, content, analysis_type)

    def save_button_clicked(self, e):
        active_tab = self.get_active_tab()
        if active_tab and hasattr(active_tab.content, 'data'):
            path = active_tab.content.data
            content = active_tab.content.value
            self.on_save_file(path, content)

    def handle_rename_intent(self, file_info):
        """Receives the intent to rename a file and shows a custom modal dialog."""
        
        new_name_field = ft.TextField(
            label="New file name",
            value=file_info['title'],
            autofocus=True,
            expand=True
        )

        def close_rename_dialog(e=None):
            # Remove the overlay
            if hasattr(self, 'rename_dialog_overlay') and self.rename_dialog_overlay in self.page.overlay:
                self.page.overlay.remove(self.rename_dialog_overlay)
                self.page.update()

        def perform_rename_action(e):
            new_name = new_name_field.value.strip()
            if not new_name:
                # Show error message
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Please enter a filename"))
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            # Validate and sanitize filename
            try:
                sanitized_name = sanitize_filename(new_name)
                close_rename_dialog()
                self.on_rename_file(file_info['path'], sanitized_name)
            except SecurityError as security_error:
                # Show security error message
                self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Invalid filename: {str(security_error)}"))
                self.page.snack_bar.open = True
                self.page.update()
            except Exception as e:
                # Show general error message
                self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Error validating filename: {str(e)}"))
                self.page.snack_bar.open = True
                self.page.update()

        # Create custom modal dialog using Container overlay
        self.rename_dialog_overlay = ft.Container(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Rename File", size=20, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=20),
                    new_name_field,
                    ft.Row([
                        ft.TextButton("Cancel", on_click=close_rename_dialog),
                        ft.FilledButton("Rename", on_click=perform_rename_action),
                    ], alignment=ft.MainAxisAlignment.END, spacing=10)
                ], spacing=15, tight=True),
                padding=ft.padding.all(20),
                bgcolor=ft.Colors.WHITE,
                border_radius=10,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=15,
                    color=ft.Colors.BLACK26,
                    offset=ft.Offset(0, 4),
                ),
                width=400,
            ),
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.BLACK54,  # Semi-transparent background
            expand=True,
            on_click=close_rename_dialog  # Close when clicking outside
        )
        
        self.page.overlay.append(self.rename_dialog_overlay)
        self.page.update()
    
    def show_archived_clicked(self, e):
        """アーカイブエクスプローラーボタンのクリックを処理する"""
        # Always open Archive Explorer modal when button is clicked
        self.open_archive_explorer()
    
    def open_archive_explorer(self):
        """Open the Archive Explorer modal dialog."""
        # Get archived files using the app_logic reference
        archived_files = []
        if hasattr(self, '_app_logic_ref'):
            try:
                all_files = self._app_logic_ref.get_file_list(show_archived=True)
                archived_files = [f for f in all_files if f.get('status') == 'archived']
            except Exception as e:
                print(f"Error getting archived files: {e}")
                archived_files = []

        # Create archive file list
        archive_file_controls = []
        for file_info in archived_files:
            archive_item = ft.ListTile(
                title=ft.Text(file_info['title']),
                subtitle=ft.Text(", ".join(file_info.get('tags', []))) if file_info.get('tags') else None,
                trailing=ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.UNARCHIVE,
                        tooltip="Unarchive file",
                        on_click=lambda e, path=file_info['path']: self.unarchive_from_modal(path)
                    ),
                    ft.IconButton(
                        icon=ft.Icons.OPEN_IN_NEW,
                        tooltip="Open file",
                        on_click=lambda e, path=file_info['path']: self.open_file_from_modal(path)
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_FOREVER,
                        tooltip="Delete permanently",
                        on_click=lambda e, file_info=file_info: self.delete_from_modal(file_info)
                    )
                ], tight=True)
            )
            archive_file_controls.append(archive_item)

        # Create scrollable list
        archive_list = ft.Column(
            controls=archive_file_controls if archive_file_controls else [
                ft.Text("No archived files found",
                       text_align=ft.TextAlign.CENTER,
                       color=ft.Colors.GREY_600)
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

        def close_archive_modal(e=None):
            if hasattr(self, 'archive_dialog_overlay') and self.archive_dialog_overlay in self.page.overlay:
                self.page.overlay.remove(self.archive_dialog_overlay)
                self.page.update()
                # Refresh the main file list to reflect any changes
                self.on_refresh_files(show_archived=False)

        # Create modal dialog
        modal_content = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Archive Explorer", size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),  # Spacer equivalent
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        on_click=close_archive_modal,
                        tooltip="Close"
                    )
                ]),
                ft.Divider(),
                ft.Text(f"Found {len(archive_file_controls)} archived files"),
                ft.Divider(),
                archive_list,
                ft.Row([
                    ft.ElevatedButton(
                        "Close",
                        on_click=close_archive_modal
                    )
                ], alignment=ft.MainAxisAlignment.END)
            ]),
            width=600,
            height=500,
            padding=20,
            bgcolor=ft.Colors.SURFACE,
            border_radius=10
        )

        # Create overlay
        self.archive_dialog_overlay = ft.Container(
            content=modal_content,
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
            expand=True
        )

        self.page.overlay.append(self.archive_dialog_overlay)
        self.page.update()

    def show_error_dialog(self, title: str, message: str):
        """エラーダイアログを表示する"""
        def close_dialog(e):
            if hasattr(self, 'error_dialog') and self.error_dialog in self.page.overlay:
                self.page.overlay.remove(self.error_dialog)
                self.page.update()

        self.error_dialog = ft.AlertDialog(
            title=ft.Text(title, weight=ft.FontWeight.BOLD),
            content=ft.Text(message),
            actions=[
                ft.TextButton("OK", on_click=close_dialog)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(self.error_dialog)
        self.error_dialog.open = True
        self.page.update()

    def unarchive_from_modal(self, file_path):
        """Unarchive a file from the modal."""
        if hasattr(self, 'on_archive_file'):
            self.on_archive_file(file_path)  # This should unarchive if already archived
        # Refresh the modal
        self.refresh_archive_modal()

    def open_file_from_modal(self, file_path):
        """Open a file from the archive modal."""
        if hasattr(self, 'on_open_file'):
            self.on_open_file(file_path)

    def delete_from_modal(self, file_info):
        """Delete a file permanently from the archive modal."""
        if hasattr(self, 'on_delete_file'):
            self.on_delete_file(file_info['path'])
        # Refresh the modal
        self.refresh_archive_modal()

    def refresh_archive_modal(self):
        """Refresh the archive modal contents."""
        # Close and reopen the modal with updated content
        if hasattr(self, 'archive_dialog_overlay') and self.archive_dialog_overlay in self.page.overlay:
            self.page.overlay.remove(self.archive_dialog_overlay)
            self.page.update()
            self.open_archive_explorer()

    def handle_archive_intent(self, file_info):
        """アーカイブ操作の意図を受け取り処理する"""
        print(f"Handle archive intent for: {file_info['title']} at path: {file_info['path']}")  # Debug log
        self.on_archive_file(file_info['path'])
    
    def handle_delete_intent(self, file_info):
        """ファイル削除の意図を受け取り、確認ダイアログを表示する"""
        
        filename = file_info['title']
        
        def close_delete_dialog(e=None):
            # Remove the overlay
            if hasattr(self, 'delete_dialog_overlay') and self.delete_dialog_overlay in self.page.overlay:
                self.page.overlay.remove(self.delete_dialog_overlay)
                self.page.update()

        def confirm_delete_action(e):
            close_delete_dialog()
            self.on_delete_file(file_info['path'])

        # Create warning dialog with custom styling
        self.delete_dialog_overlay = ft.Container(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.WARNING, color=ft.Colors.RED, size=32),
                        ft.Text("Delete File", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.RED)
                    ], spacing=10),
                    ft.Divider(height=20),
                    ft.Text(
                        f"Are you sure you want to permanently delete '{filename}'?",
                        size=16,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        "This action cannot be undone.",
                        size=14,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Row([
                        ft.TextButton("Cancel", on_click=close_delete_dialog),
                        ft.FilledButton(
                            "Delete", 
                            on_click=confirm_delete_action,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.RED,
                                color=ft.Colors.WHITE
                            )
                        ),
                    ], alignment=ft.MainAxisAlignment.END, spacing=10)
                ], spacing=15, tight=True),
                padding=ft.padding.all(20),
                bgcolor=ft.Colors.WHITE,
                border_radius=10,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=15,
                    color=ft.Colors.BLACK26,
                    offset=ft.Offset(0, 4),
                ),
                width=450,
            ),
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.BLACK54,  # Semi-transparent background
            expand=True,
            on_click=close_delete_dialog  # Close when clicking outside
        )
        
        self.page.overlay.append(self.delete_dialog_overlay)
        self.page.update()
    
    def handle_ai_analysis(self, file_path, analysis_type):
        """ファイルリストからのAI分析リクエストを処理する"""
        try:
            # ファイルの内容を読み込む
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # AI分析を実行
            if self.on_run_ai_analysis:
                self.on_run_ai_analysis(file_path, content, analysis_type)
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("AI analysis is not available")
                )
                self.page.snack_bar.open = True
                self.page.update()
                
        except Exception as e:
            from log_utils import log_error
            log_error(f"AI analysis from file list failed for file '{file_path}': {e}")
            print(f"Error in AI analysis from file list: {e}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error reading file: {str(e)}")
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def handle_move_file(self, direction, file_info):
        """ファイルの移動操作を処理する"""
        print(f"Moving file {file_info['title']} to {direction}")  # Debug
        
        # 現在のファイル一覧を取得
        current_files = []
        for control in self.file_list_column.controls:
            if hasattr(control, 'file_info'):
                current_files.append(control.file_info)
        
        # ファイルの新しい位置を計算
        target_file_path = file_info['path']
        new_order = []
        target_file = None
        
        # 対象ファイルを除いたリストを作成
        for f in current_files:
            if f['path'] == target_file_path:
                target_file = f
            else:
                new_order.append(f)
        
        if target_file:
            # Find current position of the target file
            current_index = next((i for i, f in enumerate(current_files) if f['path'] == target_file_path), -1)

            if direction == 'top':
                new_order.insert(0, target_file)  # 最初に挿入
            elif direction == 'bottom':
                new_order.append(target_file)  # 最後に追加
            elif direction == 'up':
                # Move one position up (insert at current position - 1, or 0 if already at top)
                insert_pos = max(0, current_index - 1)
                new_order.insert(insert_pos, target_file)
            elif direction == 'down':
                # Move one position down (insert at current position + 1, or end if already at bottom)
                insert_pos = min(len(new_order), current_index + 1)
                new_order.insert(insert_pos, target_file)

            # 新しい順番を更新
            ordered_paths = [f['path'] for f in new_order]
            self.on_update_order(ordered_paths)

    def new_file_button_clicked(self, e):
        """Shows a custom modal dialog to get a filename for the new file."""
        
        filename_field = ft.TextField(
            label="File name",
            autofocus=True,
            hint_text="Enter filename (without .md extension)",
            expand=True
        )

        def close_custom_dialog(e=None):
            # Remove the overlay
            if hasattr(self, 'dialog_overlay') and self.dialog_overlay in self.page.overlay:
                self.page.overlay.remove(self.dialog_overlay)
                self.page.update()

        def create_file_action(e):
            filename = filename_field.value.strip()
            if not filename:
                # Show error message
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Please enter a filename"))
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            # Validate and sanitize filename
            try:
                sanitized_filename = sanitize_filename(filename)
                close_custom_dialog()
                self.on_create_file(sanitized_filename)
            except SecurityError as security_error:
                # Show security error message
                self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Invalid filename: {str(security_error)}"))
                self.page.snack_bar.open = True
                self.page.update()
            except Exception as e:
                # Show general error message
                self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Error validating filename: {str(e)}"))
                self.page.snack_bar.open = True
                self.page.update()

        # Create custom modal dialog using Container
        self.dialog_overlay = ft.Container(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Create New File", size=20, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=20),
                    filename_field,
                    ft.Row([
                        ft.TextButton("Cancel", on_click=close_custom_dialog),
                        ft.FilledButton("Create", on_click=create_file_action),
                    ], alignment=ft.MainAxisAlignment.END, spacing=10)
                ], spacing=15, tight=True),
                padding=ft.padding.all(20),
                bgcolor=ft.Colors.WHITE,
                border_radius=10,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=15,
                    color=ft.Colors.BLACK26,
                    offset=ft.Offset(0, 4),
                ),
                width=400,
            ),
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.BLACK54,  # Semi-transparent background
            expand=True,
            on_click=close_custom_dialog  # Close when clicking outside
        )
        
        self.page.overlay.append(self.dialog_overlay)
        self.page.update()

    def update_file_list(self, files_info):
        """ファイルリストUIを更新する。
        
        Args:
            files_info (list): ファイル情報辞書のリスト。各辞書は
                              title, path, tags, status, order_indexを含む。
        
        Note:
            既存のリスト項目をすべてクリアしてから新しい項目を追加する。
            アーカイブされたファイルは視覚的に区別される（グレー表示 + アーカイブアイコン）。
        """
        self.file_list_column.controls.clear()
        if not files_info:
            self.file_list_column.controls.append(ft.Text("該当するメモがありません。"))
        else:
            for info in files_info:
                list_item = FileListItem(
                    file_info=info,
                    on_update_tags=self.on_update_tags,
                    on_open_file=self.on_open_file,
                    on_rename_intent=self.handle_rename_intent,
                    on_archive_intent=self.handle_archive_intent,
                    on_move_file=self.handle_move_file,
                    on_delete_intent=self.handle_delete_intent,
                    on_ai_analysis=self.handle_ai_analysis,
                    page=self.page
                )
                
                # アーカイブされたファイルの視覚的区別
                if info.get('status') == 'archived':
                    list_item.title.color = ft.Colors.GREY_600
                    list_item.subtitle.color = ft.Colors.GREY_500
                    # アーカイブアイコンを追加
                    list_item.leading = ft.Icon(ft.Icons.ARCHIVE, color=ft.Colors.GREY_600)
                
                self.file_list_column.controls.append(list_item)
        self.page.update()

    def add_or_focus_tab(self, path, content):
        """指定されたファイルのタブを開くか、既存の場合はフォーカスする。
        
        Args:
            path (str): ファイルの絶対パス
            content (str): ファイルの内容
        
        Note:
            同じファイルが既に開かれている場合は、そのタブにフォーカスを移す。
            新しいファイルの場合は新しいタブを作成し、Welcomeタブがあれば削除する。
        """
        filename = os.path.basename(path)
        for i, tab in enumerate(self.tabs.tabs):
            if hasattr(tab.content, 'data') and tab.content.data == path:
                self.tabs.selected_index = i
                self.page.update()
                return

        new_editor = ft.TextField(value=content, multiline=True, expand=True, data=path)
        
        # Tabの参照を先に作っておく
        new_tab = ft.Tab(content=new_editor)
        
        new_tab.tab_content = ft.Row(
            spacing=5,
            controls=[
                ft.Text(filename),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_size=12,
                    tooltip="Close file",
                    on_click=lambda e: self.on_close_tab(new_tab),
                )
            ]
        )

        if self.tabs.tabs and self.tabs.tabs[0].text == "Welcome":
            self.tabs.tabs[0] = new_tab
        else:
            self.tabs.tabs.append(new_tab)
        
        self.tabs.selected_index = len(self.tabs.tabs) - 1
        self.page.update()

    def update_tab_after_rename(self, old_path, new_path):
        """ファイル名変更後、開いているタブの情報を更新する"""
        new_filename = os.path.basename(new_path)
        for i, tab in enumerate(self.tabs.tabs):
            if hasattr(tab.content, 'data') and tab.content.data == old_path:
                tab.text = new_filename
                tab.content.data = new_path
                self.page.update()
                return

    def get_active_tab(self):
        if self.tabs.tabs and len(self.tabs.tabs) > self.tabs.selected_index:
             return self.tabs.tabs[self.tabs.selected_index]
        return None

    def build(self):
        self.tabs.tabs.append(
            ft.Tab(text="Welcome", content=ft.Column(
                [ft.Text("← サイドバーからファイルを選択してください", size=20)],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ))
        )
        return ft.Row(
            controls=[self.sidebar, ft.VerticalDivider(width=1), self.tabs],
            expand=True,
        )