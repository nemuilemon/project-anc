import flet as ft
import os

# --- New Approach: Inherit from a specific layout control (Flet >= 0.21.0) ---
class FileListItem(ft.ListTile):
    """
    A custom control inheriting from ListTile to represent a file item.
    It manages its own state (view vs. edit) by swapping its own controls.
    """
    def __init__(self, file_info, on_update_tags, on_open_file, on_rename_intent, on_archive_intent, on_move_file):
        super().__init__()

        self.file_info = file_info
        self.on_update_tags = on_update_tags
        self.on_open_file = on_open_file
        self.on_rename_intent = on_rename_intent
        self.on_archive_intent = on_archive_intent
        self.on_move_file = on_move_file
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
        """Sets the control to display tags as text and show the menu button."""
        self.subtitle = self.tags_text
        self.trailing = self.menu_button
        self.editing = False
        if self.page: self.update()

    def set_edit_mode(self):
        """Sets the control to display a textfield for tags and show a save button."""
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
    def __init__(self, page: ft.Page, on_open_file, on_save_file, on_analyze_tags, on_refresh_files, on_update_tags, on_cancel_tags, on_rename_file, on_close_tab, on_create_file, on_archive_file, on_update_order):
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
            if new_name:
                close_rename_dialog()
                self.on_rename_file(file_info['path'], new_name)
            else:
                # Show error message
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Please enter a filename"))
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
            if filename:
                close_custom_dialog()
                self.on_create_file(filename)
            else:
                # Show error message
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Please enter a filename"))
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
                    on_move_file=self.handle_move_file
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