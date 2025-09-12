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
    def __init__(self, file_info, on_update_tags, on_open_file, on_rename_intent, on_archive_intent, on_move_file, on_delete_intent):
        super().__init__()

        self.file_info = file_info
        self.on_update_tags = on_update_tags
        self.on_open_file = on_open_file
        self.on_rename_intent = on_rename_intent
        self.on_archive_intent = on_archive_intent
        self.on_move_file = on_move_file
        self.on_delete_intent = on_delete_intent
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
            ft.PopupMenuItem(
                text="Move to top",
                icon=ft.Icons.KEYBOARD_ARROW_UP,
                on_click=self.move_to_top_clicked
            ),
            ft.PopupMenuItem(
                text="Move to bottom", 
                icon=ft.Icons.KEYBOARD_ARROW_DOWN,
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
        self.set_view_mode() # Set initial controls

    def set_view_mode(self):
        """表示モードに切り替える。
        
        タグをテキスト表示し、ポップアップメニューボタンを表示する。
        編集モードから表示モードに戻る際に使用される。
        """
        self.subtitle = self.tags_text
        self.trailing = self.menu_button
        self.editing = False
        if self.page: self.update()

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
        self.on_archive_intent(self.file_info)
    
    def move_to_top_clicked(self, e):
        self.on_move_file('top', self.file_info)
    
    def move_to_bottom_clicked(self, e):
        self.on_move_file('bottom', self.file_info)
    
    def delete_intent_clicked(self, e):
        self.on_delete_intent(self.file_info)

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
        show_archived_switch (ft.Switch): アーカイブファイル表示切替
    
    Callbacks:
        各操作に対応するコールバック関数群（on_open_file, on_save_file等）
    """
    def __init__(self, page: ft.Page, on_open_file, on_save_file, on_analyze_tags, on_refresh_files, on_update_tags, on_cancel_tags, on_rename_file, on_close_tab, on_create_file, on_archive_file, on_update_order, on_delete_file):
        self.page = page
        self.on_open_file = on_open_file
        self.on_save_file = on_save_file
        self.on_analyze_tags = on_analyze_tags
        self.on_refresh_files = on_refresh_files
        self.on_update_tags = on_update_tags
        self.on_cancel_tags = on_cancel_tags
        self.on_rename_file = on_rename_file
        self.on_close_tab = on_close_tab
        self.on_create_file = on_create_file
        self.on_archive_file = on_archive_file
        self.on_update_order = on_update_order
        self.on_delete_file = on_delete_file
        
        self.tabs = ft.Tabs(selected_index=0, expand=True, tabs=[])
        # ファイルリスト用のコンテナ
        self.file_list_column = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        self.file_list = self.file_list_column
        
        # アーカイブファイル表示切替スイッチ
        self.show_archived_switch = ft.Switch(
            label="Show Archived Files",
            value=False,
            on_change=self.show_archived_changed
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
                self.analyze_button,
                self.cancel_button
            ]
        )
        
        self.sidebar = ft.Container(
            content=ft.Column([
                self.show_archived_switch,
                ft.Divider(height=10),
                self.file_list
            ]),
            width=250, padding=10, bgcolor=ft.Colors.BLACK12
        )

    def start_analysis_view(self):
        """分析中のUI表示に切り替える"""
        self.analyze_button.visible = False
        self.progress_ring.visible = True
        self.cancel_button.visible = True
        self.page.update()


    def stop_analysis_view(self):
        """通常のUI表示に戻す"""
        self.analyze_button.visible = True
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

        
    def analyze_button_clicked(self, e):
        active_tab = self.get_active_tab()
        if active_tab and hasattr(active_tab.content, 'data'):
            path = active_tab.content.data
            content = active_tab.content.value
            self.on_analyze_tags(path, content)

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
    
    def show_archived_changed(self, e):
        """アーカイブファイル表示切替スイッチの変更を処理する"""
        # コールバックを呼び出してファイルリストを更新
        self.on_refresh_files(show_archived=self.show_archived_switch.value)
    
    def handle_archive_intent(self, file_info):
        """アーカイブ操作の意図を受け取り処理する"""
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
            if direction == 'top':
                new_order.insert(0, target_file)  # 最初に挿入
            elif direction == 'bottom':
                new_order.append(target_file)  # 最後に追加
            
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
                    on_delete_intent=self.handle_delete_intent
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