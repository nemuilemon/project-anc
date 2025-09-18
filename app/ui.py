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
        on_delete_intent: ファイル削除時のコールバック
    """
    def __init__(self, file_info, on_update_tags, on_open_file, on_rename_intent, on_archive_intent, on_delete_intent, on_ai_analysis=None, on_view_summary=None, page=None):
        super().__init__()

        self.file_info = file_info
        self.on_update_tags = on_update_tags
        self.on_open_file = on_open_file
        self.on_rename_intent = on_rename_intent
        self.on_archive_intent = on_archive_intent
        self.on_delete_intent = on_delete_intent
        self.on_ai_analysis = on_ai_analysis
        self.on_view_summary = on_view_summary
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

        # サマリーが存在する場合はサマリー表示オプションを追加
        if self._has_ai_summary():
            menu_items.append(ft.PopupMenuItem(
                text="View AI Summary",
                icon=ft.Icons.SUMMARIZE,
                on_click=self.view_summary_clicked
            ))

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

        # Add separator and delete option
        menu_items.extend([
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
        # Check if summary is available and add indicator
        has_summary = self._has_ai_summary()
        title_row = [ft.Text(self.file_info['title'])]

        if has_summary:
            summary_button = ft.IconButton(
                icon=ft.Icons.SUMMARIZE,
                icon_size=16,
                tooltip="View AI Summary",
                on_click=self.view_summary_clicked,
                style=ft.ButtonStyle(
                    color=ft.Colors.BLUE_400,
                    padding=ft.Padding(2, 2, 2, 2)
                )
            )
            title_row.append(summary_button)

        self.title = ft.Row(title_row, spacing=5) if has_summary else ft.Text(self.file_info['title'])
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

    def _has_ai_summary(self):
        """ファイルにAIサマリーが保存されているかチェック"""
        ai_analysis = self.file_info.get('ai_analysis', {})
        return 'summarization' in ai_analysis and ai_analysis['summarization'].get('data', {}).get('summary', '')

    def view_summary_clicked(self, e):
        """サマリー表示ボタンクリック時の処理"""
        if self.on_view_summary:
            self.on_view_summary(self.file_info)

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
    def __init__(self, page: ft.Page, on_open_file, on_save_file, on_analyze_tags, on_refresh_files, on_update_tags, on_cancel_tags, on_rename_file, on_close_tab, on_create_file, on_archive_file, on_delete_file, on_run_ai_analysis=None, on_run_automation=None, on_cancel_automation=None, on_get_automation_preview=None, available_ai_functions=None):
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
        self.on_delete_file = on_delete_file

        # Automation callbacks
        self.on_run_automation = on_run_automation
        self.on_cancel_automation = on_cancel_automation
        self.on_get_automation_preview = on_get_automation_preview

        # Store available AI functions for dynamic dropdown
        self.available_ai_functions = available_ai_functions or []

        self.tabs = ft.Tabs(selected_index=0, expand=True, tabs=[], on_change=self.on_tab_change)
        # ファイルリスト用のコンテナ
        self.file_list_column = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        self.file_list = self.file_list_column

        # Current view state - "files" or "automation"
        self.current_view = "files"

        # ========== NAVIGATION CONTROLS ==========
        self.files_nav_button = ft.ElevatedButton(
            text="Files",
            icon=ft.Icons.FOLDER,
            on_click=self.switch_to_files_view,
            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE)  # Active initially
        )

        self.automation_nav_button = ft.ElevatedButton(
            text="Automation",
            icon=ft.Icons.SMART_TOY,
            on_click=self.switch_to_automation_view,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREY)  # Inactive initially
        )

        # ========== AUTOMATION UI COMPONENTS ==========
        self.automation_task_dropdown = ft.Dropdown(
            label="Select Automation Task",
            width=280,  # Adjusted to fit within sidebar
            options=[
                ft.dropdown.Option("batch_tag_untagged", "Batch Tag Untagged Files"),
                ft.dropdown.Option("batch_summarize", "Batch Generate Summaries"),
                ft.dropdown.Option("batch_sentiment", "Batch Sentiment Analysis"),
                ft.dropdown.Option("batch_tag_archived", "Batch Tag Archived Files"),
                ft.dropdown.Option("batch_summarize_archived", "Batch Summarize Archived Files"),
                ft.dropdown.Option("batch_sentiment_archived", "Batch Analyze Archived Sentiment")
            ],
            on_change=self.automation_task_changed
        )

        self.automation_preview_text = ft.Text(
            "Select a task to see preview information.",
            size=12,
            color=ft.Colors.GREY_600
        )

        self.run_automation_button = ft.ElevatedButton(
            text="Run Automation",
            icon=ft.Icons.PLAY_ARROW,
            on_click=self.run_automation_clicked,
            disabled=True,
            color=ft.Colors.GREEN
        )

        self.cancel_automation_button = ft.ElevatedButton(
            text="Cancel",
            icon=ft.Icons.STOP,
            on_click=lambda e: self.on_cancel_automation(),
            visible=False,
            color=ft.Colors.RED
        )

        # Automation progress indicators
        self.automation_progress_bar = ft.ProgressBar(
            value=0,
            visible=False,
            width=400,
            height=6,
            bgcolor=ft.Colors.GREY_300,
            color=ft.Colors.GREEN
        )

        self.automation_status_text = ft.Text(
            "",
            size=14,
            visible=False
        )

        # Container for the automation view
        self.automation_container = ft.Container(
            content=ft.Column([
                ft.Text("🤖 AI Automation Center", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=20),

                ft.Text("Available Automation Tasks:", size=16, weight=ft.FontWeight.BOLD),
                self.automation_task_dropdown,
                ft.Container(height=10),

                # Preview section
                ft.Container(
                    content=ft.Column([
                        ft.Text("Task Preview:", size=14, weight=ft.FontWeight.BOLD),
                        self.automation_preview_text,
                    ]),
                    bgcolor=ft.Colors.BLUE_50,
                    padding=15,
                    border_radius=8,
                    border=ft.border.all(1, ft.Colors.BLUE_200)
                ),

                ft.Container(height=20),

                # Control section
                ft.Row([
                    self.run_automation_button,
                    self.cancel_automation_button,
                ], spacing=10),

                ft.Container(height=20),

                # Progress section
                ft.Column([
                    self.automation_status_text,
                    self.automation_progress_bar,
                ], spacing=10),

            ], scroll=ft.ScrollMode.AUTO, spacing=15, expand=True),
            visible=True,  # Always visible when used as content
            padding=20
        )
        
        # アーカイブファイル表示ボタン
        self.show_archived_button = ft.ElevatedButton(
            text="Archive Explorer",
            icon=ft.Icons.ARCHIVE,
            on_click=self.show_archived_clicked,
            tooltip="Open Archive Explorer to view archived files"
        )
        
        # AI Analysis dropdown and button - dynamically populated
        self.ai_analysis_dropdown = self._create_ai_analysis_dropdown()
        
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
        
        # Files view container (current sidebar content)
        self.files_container = ft.Container(
            content=ft.Column([
                self.show_archived_button,
                ft.Divider(height=10),
                self.file_list
            ]),
            expand=True
        )

        # Dynamic content container that will switch between files and automation
        self.sidebar_content_container = ft.Container(
            content=self.files_container,  # Initially show files
            expand=True
        )

        self.sidebar = ft.Container(
            content=ft.Column([
                # Navigation controls
                ft.Row([
                    self.files_nav_button,
                    self.automation_nav_button
                ], spacing=5),
                ft.Divider(height=10),

                # Dynamic content container
                self.sidebar_content_container
            ]),
            width=320,  # Increased width for automation UI
            padding=10,
            bgcolor=ft.Colors.BLACK12
        )

    def _create_ai_analysis_dropdown(self):
        """Dynamically create AI analysis dropdown based on available plugins."""
        # Generate dropdown options from available AI functions
        dropdown_options = []
        default_value = None

        if self.available_ai_functions:
            for plugin_config in self.available_ai_functions:
                plugin_name = plugin_config.get("name", "unknown")
                plugin_description = plugin_config.get("description", plugin_name.title())

                # Create user-friendly display text
                if plugin_name == "tagging":
                    display_text = "Tags"
                elif plugin_name == "summarization":
                    display_text = "Summary"
                elif plugin_name == "sentiment":
                    display_text = "Sentiment"
                else:
                    # For any custom plugins, use description or capitalize name
                    display_text = plugin_description if len(plugin_description) < 20 else plugin_name.replace("_", " ").title()

                dropdown_options.append(ft.dropdown.Option(plugin_name, display_text))

                # Set default to tagging if available, otherwise first plugin
                if plugin_name == "tagging" or default_value is None:
                    default_value = plugin_name
        else:
            # Fallback if no plugins found
            dropdown_options = [
                ft.dropdown.Option("tagging", "Tags"),
                ft.dropdown.Option("summarization", "Summary"),
                ft.dropdown.Option("sentiment", "Sentiment")
            ]
            default_value = "tagging"

        return ft.Dropdown(
            label="AI Analysis Type",
            width=150,
            value=default_value,
            options=dropdown_options,
            dense=True,
            on_change=self.ai_analysis_type_changed
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

        # Also update automation progress if visible
        if self.automation_progress_bar.visible:
            self.automation_progress_bar.value = progress / 100

        if status_text:
            if self.operation_status_text.visible:
                self.operation_status_text.value = status_text
            if self.automation_status_text.visible:
                self.automation_status_text.value = status_text

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
        """Open the Archive Explorer modal dialog with filtering capabilities."""
        # Get archived files using the app_logic reference
        self.all_archived_files = []
        if hasattr(self, '_app_logic_ref'):
            try:
                all_files = self._app_logic_ref.get_file_list(show_archived=True)
                self.all_archived_files = [f for f in all_files if f.get('status') == 'archived']
            except Exception as e:
                print(f"Error getting archived files: {e}")
                self.all_archived_files = []

        # Create filter controls
        self.filename_filter = ft.TextField(
            label="Filter by filename",
            hint_text="Enter filename keywords...",
            width=250,
            on_change=self.filter_archived_files
        )

        self.tag_filter = ft.TextField(
            label="Filter by tags",
            hint_text="Enter tag keywords...",
            width=250,
            on_change=self.filter_archived_files
        )

        filter_row = ft.Row([
            self.filename_filter,
            self.tag_filter,
            ft.IconButton(
                icon=ft.Icons.CLEAR,
                tooltip="Clear filters",
                on_click=self.clear_archive_filters
            )
        ], spacing=10)

        # Create container for filtered file list
        self.archive_list_container = ft.Column(
            controls=[],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

        # Initial populate
        self.update_archive_file_list(self.all_archived_files)

        def close_archive_modal(e=None):
            if hasattr(self, 'archive_dialog_overlay') and self.archive_dialog_overlay in self.page.overlay:
                self.page.overlay.remove(self.archive_dialog_overlay)
                self.page.update()
                # Refresh the main file list to reflect any changes
                self.on_refresh_files(show_archived=False)

        # Create file count display
        self.archive_file_count_text = ft.Text(f"Found {len(self.all_archived_files)} archived files")

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
                filter_row,
                ft.Divider(),
                self.archive_file_count_text,
                ft.Divider(),
                self.archive_list_container,
                ft.Row([
                    ft.ElevatedButton(
                        "Close",
                        on_click=close_archive_modal
                    )
                ], alignment=ft.MainAxisAlignment.END)
            ]),
            width=700,
            height=600,
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

    def update_archive_file_list(self, files_to_display):
        """Update the archive file list display with given files."""
        archive_file_controls = []

        for file_info in files_to_display:
            # Check if file has summary
            has_summary = False
            summary_preview = ""
            ai_analysis = file_info.get('ai_analysis', {})
            if 'summarization' in ai_analysis and ai_analysis['summarization'].get('data', {}).get('summary', ''):
                has_summary = True
                summary_text = ai_analysis['summarization']['data']['summary']
                summary_preview = summary_text[:100] + "..." if len(summary_text) > 100 else summary_text

            # Create subtitle with tags and summary
            subtitle_parts = []
            if file_info.get('tags'):
                subtitle_parts.append(f"Tags: {', '.join(file_info['tags'])}")
            if has_summary:
                subtitle_parts.append(f"Summary: {summary_preview}")

            subtitle_text = " | ".join(subtitle_parts) if subtitle_parts else None

            # Create action buttons
            action_buttons = [
                ft.IconButton(
                    icon=ft.Icons.UNARCHIVE,
                    tooltip="Unarchive file",
                    on_click=lambda e, path=file_info['path']: self.unarchive_from_modal(path)
                ),
                ft.IconButton(
                    icon=ft.Icons.OPEN_IN_NEW,
                    tooltip="Open file",
                    on_click=lambda e, path=file_info['path']: self.open_file_from_modal(path)
                )
            ]

            # Add summary button if summary exists
            if has_summary:
                action_buttons.append(
                    ft.IconButton(
                        icon=ft.Icons.SUMMARIZE,
                        tooltip="View AI Summary",
                        on_click=lambda e, fi=file_info: self.handle_view_summary(fi),
                        style=ft.ButtonStyle(color=ft.Colors.BLUE_400)
                    )
                )

            action_buttons.append(
                ft.IconButton(
                    icon=ft.Icons.DELETE_FOREVER,
                    tooltip="Delete permanently",
                    on_click=lambda e, file_info=file_info: self.delete_from_modal(file_info)
                )
            )

            archive_item = ft.ListTile(
                title=ft.Text(file_info['title']),
                subtitle=ft.Text(subtitle_text, size=10) if subtitle_text else None,
                trailing=ft.Row(action_buttons, tight=True)
            )
            archive_file_controls.append(archive_item)

        # Update the container
        if archive_file_controls:
            self.archive_list_container.controls = archive_file_controls
        else:
            self.archive_list_container.controls = [
                ft.Text("No matching archived files found",
                       text_align=ft.TextAlign.CENTER,
                       color=ft.Colors.GREY_600)
            ]

        # Update file count
        if hasattr(self, 'archive_file_count_text'):
            self.archive_file_count_text.value = f"Showing {len(files_to_display)} of {len(self.all_archived_files)} archived files"

        if hasattr(self, 'page'):
            self.page.update()

    def filter_archived_files(self, e=None):
        """Filter archived files based on filename and tag criteria."""
        if not hasattr(self, 'all_archived_files'):
            return

        filename_query = self.filename_filter.value.lower() if self.filename_filter.value else ""
        tag_query = self.tag_filter.value.lower() if self.tag_filter.value else ""

        filtered_files = []
        for file_info in self.all_archived_files:
            filename_match = filename_query == "" or filename_query in file_info['title'].lower()

            tag_match = True
            if tag_query:
                file_tags = [tag.lower() for tag in file_info.get('tags', [])]
                tag_match = any(tag_query in tag for tag in file_tags)

            if filename_match and tag_match:
                filtered_files.append(file_info)

        self.update_archive_file_list(filtered_files)

    def clear_archive_filters(self, e=None):
        """Clear all archive filters and show all files."""
        if hasattr(self, 'filename_filter'):
            self.filename_filter.value = ""
        if hasattr(self, 'tag_filter'):
            self.tag_filter.value = ""

        if hasattr(self, 'all_archived_files'):
            self.update_archive_file_list(self.all_archived_files)

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

    def handle_view_summary(self, file_info):
        """サマリー表示ダイアログを表示する"""
        ai_analysis = file_info.get('ai_analysis', {})
        summary_data = ai_analysis.get('summarization', {})

        if not summary_data or 'data' not in summary_data:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("このファイルにはサマリーが保存されていません。")
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        summary_info = summary_data['data']
        summary_text = summary_info.get('summary', 'サマリーが見つかりません。')
        summary_type = summary_info.get('summary_type', 'brief')
        original_length = summary_info.get('original_length', 0)
        summary_length = summary_info.get('summary_length', 0)
        compression_ratio = summary_info.get('compression_ratio', 0)
        timestamp = summary_data.get('timestamp', 0)
        processing_time = summary_data.get('processing_time', 0)

        # タイムスタンプを日時に変換
        import time as time_module
        formatted_time = time_module.strftime("%Y/%m/%d %H:%M:%S", time_module.localtime(timestamp)) if timestamp > 0 else "不明"

        def close_summary_dialog(e=None):
            if hasattr(self, 'summary_dialog_overlay') and self.summary_dialog_overlay in self.page.overlay:
                self.page.overlay.remove(self.summary_dialog_overlay)
                self.page.update()

        # サマリー表示ダイアログを作成
        self.summary_dialog_overlay = ft.Container(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.SUMMARIZE, color=ft.Colors.BLUE, size=28),
                        ft.Text("AI サマリー", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE)
                    ], spacing=10),
                    ft.Divider(height=10),
                    ft.Text(f"ファイル: {file_info['title']}", size=14, weight=ft.FontWeight.W_500),
                    ft.Container(
                        content=ft.Text(
                            summary_text,
                            size=14,
                            selectable=True
                        ),
                        bgcolor=ft.Colors.GREY_100,
                        padding=ft.padding.all(15),
                        border_radius=8,
                        margin=ft.margin.symmetric(vertical=10)
                    ),
                    ft.Column([
                        ft.Text("詳細情報", size=12, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
                        ft.Text(f"生成日時: {formatted_time}", size=10, color=ft.Colors.GREY_600),
                        ft.Text(f"サマリータイプ: {summary_type}", size=10, color=ft.Colors.GREY_600),
                        ft.Text(f"元文書: {original_length}文字 → サマリー: {summary_length}文字 (圧縮率: {compression_ratio})", size=10, color=ft.Colors.GREY_600),
                        ft.Text(f"処理時間: {processing_time:.2f}秒", size=10, color=ft.Colors.GREY_600),
                    ], spacing=3, tight=True),
                    ft.Row([
                        ft.TextButton("閉じる", on_click=close_summary_dialog),
                    ], alignment=ft.MainAxisAlignment.END)
                ], spacing=10, tight=True),
                padding=ft.padding.all(20),
                bgcolor=ft.Colors.WHITE,
                border_radius=10,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=15,
                    color=ft.Colors.BLACK26,
                    offset=ft.Offset(0, 4),
                ),
                width=600,
                height=500,
            ),
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.BLACK54,
            expand=True,
            on_click=close_summary_dialog
        )

        self.page.overlay.append(self.summary_dialog_overlay)
        self.page.update()

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
                    on_delete_intent=self.handle_delete_intent,
                    on_ai_analysis=self.handle_ai_analysis,
                    on_view_summary=self.handle_view_summary,
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

    # ========== AUTOMATION UI METHODS ==========

    def switch_to_files_view(self, e=None):
        """ファイル表示ビューに切り替え"""
        self.current_view = "files"
        self.sidebar_content_container.content = self.files_container

        # Update button styles
        self.files_nav_button.style = ft.ButtonStyle(bgcolor=ft.Colors.BLUE)
        self.automation_nav_button.style = ft.ButtonStyle(bgcolor=ft.Colors.GREY)

        self.page.update()

    def switch_to_automation_view(self, e=None):
        """自動化ビューに切り替え"""
        self.current_view = "automation"
        self.sidebar_content_container.content = self.automation_container

        # Update button styles
        self.files_nav_button.style = ft.ButtonStyle(bgcolor=ft.Colors.GREY)
        self.automation_nav_button.style = ft.ButtonStyle(bgcolor=ft.Colors.BLUE)

        self.page.update()

    def automation_task_changed(self, e):
        """自動化タスクが選択された時の処理"""
        if e.control.value and self.on_get_automation_preview:
            try:
                preview_info = self.on_get_automation_preview(e.control.value)

                if preview_info:
                    file_count = preview_info.get("file_count", 0)
                    message = preview_info.get("message", "")
                    task_name = preview_info.get("task_name", "")

                    if file_count > 0:
                        file_list = preview_info.get("file_list", [])
                        file_list_text = "\n".join([f"• {name}" for name in file_list[:10]])  # Show first 10
                        if len(file_list) > 10:
                            file_list_text += f"\n... and {len(file_list) - 10} more files"

                        preview_text = f"{message}\n\nFiles to be processed:\n{file_list_text}"
                    else:
                        preview_text = message

                    self.automation_preview_text.value = preview_text
                    self.run_automation_button.disabled = (file_count == 0)
                else:
                    self.automation_preview_text.value = "Could not load preview information."
                    self.run_automation_button.disabled = True

            except Exception as ex:
                print(f"Error updating automation preview: {ex}")
                self.automation_preview_text.value = f"Error loading preview: {str(ex)}"
                self.run_automation_button.disabled = True
        else:
            self.automation_preview_text.value = "Select a task to see preview information."
            self.run_automation_button.disabled = True

        self.page.update()

    def run_automation_clicked(self, e):
        """自動化実行ボタンクリック処理"""
        selected_task = self.automation_task_dropdown.value
        if selected_task and self.on_run_automation:
            self.on_run_automation(selected_task)

    def start_automation_view(self):
        """自動化実行中のUI表示に切り替え"""
        self.run_automation_button.visible = False
        self.cancel_automation_button.visible = True
        self.automation_task_dropdown.disabled = True
        self.automation_progress_bar.visible = True
        self.automation_status_text.visible = True
        self.page.update()

    def stop_automation_view(self):
        """自動化完了後の通常UI表示に戻す"""
        self.run_automation_button.visible = True
        self.cancel_automation_button.visible = False
        self.automation_task_dropdown.disabled = False
        self.automation_progress_bar.visible = False
        self.automation_progress_bar.value = 0
        self.automation_status_text.visible = False
        self.page.update()

    def show_batch_results(self, result):
        """バッチ処理結果表示ダイアログ"""
        # Determine dialog styling based on success
        if result.get("success", False):
            title_icon = "✅"
            title_color = ft.Colors.GREEN
        else:
            title_icon = "❌"
            title_color = ft.Colors.RED

        # Build content widgets
        content_widgets = [
            ft.Text(
                f"Success: {result.get('success_count', 0)} files",
                color=ft.Colors.GREEN,
                weight=ft.FontWeight.BOLD
            )
        ]

        if result.get("failed_count", 0) > 0:
            content_widgets.append(
                ft.Text(
                    f"Failed: {result.get('failed_count', 0)} files",
                    color=ft.Colors.RED,
                    weight=ft.FontWeight.BOLD
                )
            )

        content_widgets.append(ft.Divider(height=10))

        # Show details for first few files
        details = result.get("details", [])
        for i, detail in enumerate(details[:10]):  # Show first 10 results
            status_icon = "✅" if detail.get("success", False) else "❌"
            content_widgets.append(
                ft.Text(f"{status_icon} {detail.get('file', 'Unknown')}: {detail.get('message', 'No message')}")
            )

        if len(details) > 10:
            content_widgets.append(ft.Text(f"... and {len(details) - 10} more files"))

        def close_dialog(e):
            if hasattr(self, 'batch_results_dialog'):
                self.page.overlay.remove(self.batch_results_dialog)
                self.page.update()

        self.batch_results_dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(name=ft.Icons.SMART_TOY, color=title_color),
                ft.Text(f"{title_icon} Batch Automation Results", color=title_color)
            ]),
            content=ft.Column(
                content_widgets,
                height=400,
                scroll=ft.ScrollMode.AUTO
            ),
            actions=[
                ft.TextButton("OK", on_click=close_dialog)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.page.overlay.append(self.batch_results_dialog)
        self.batch_results_dialog.open = True
        self.page.update()

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