import flet as ft
import os

# --- New Approach: Inherit from a specific layout control (Flet >= 0.21.0) ---
class FileListItem(ft.ListTile):
    """
    A custom control inheriting from ListTile to represent a file item.
    It manages its own state (view vs. edit) by swapping its own controls.
    """
    def __init__(self, file_info, on_update_tags, on_open_file):
        super().__init__()

        self.file_info = file_info
        self.on_update_tags = on_update_tags
        self.on_open_file = on_open_file
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
        self.edit_button = ft.IconButton(
            icon=ft.Icons.EDIT,
            tooltip="Edit tags",
            on_click=self.edit_clicked
        )
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
        """Sets the control to display tags as text and show an edit button."""
        self.subtitle = self.tags_text
        self.trailing = self.edit_button
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
    def __init__(self, page: ft.Page, on_open_file, on_save_file, on_analyze_tags, on_refresh_files, on_update_tags):
        self.page = page
        self.on_open_file = on_open_file
        self.on_save_file = on_save_file
        self.on_analyze_tags = on_analyze_tags
        self.on_refresh_files = on_refresh_files
        self.on_update_tags = on_update_tags

        self.tabs = ft.Tabs(selected_index=0, expand=True, tabs=[])
        self.file_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        
        self.appbar = ft.AppBar(
            title=ft.Text("Project A.N.C."),
            actions=[
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Refresh file list",
                    on_click=lambda e: self.on_refresh_files()
                ),
                ft.ElevatedButton("Save", icon=ft.Icons.SAVE, on_click=self.save_button_clicked),
                ft.ElevatedButton("Analyze Tags", icon=ft.Icons.AUTO_AWESOME, on_click=self.analyze_button_clicked)
            ]
        )
        
        self.sidebar = ft.Container(
            content=ft.Column([self.file_list]),
            width=250, padding=10, bgcolor=ft.Colors.BLACK12
        )

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

    def update_file_list(self, files_info):
        self.file_list.controls.clear()
        if not files_info:
            self.file_list.controls.append(ft.Text("該当するメモがありません。"))
        else:
            for info in files_info:
                list_item = FileListItem(
                    file_info=info,
                    on_update_tags=self.on_update_tags,
                    on_open_file=self.on_open_file
                )
                self.file_list.controls.append(list_item)
        self.page.update()

    def add_or_focus_tab(self, path, content):
        filename = os.path.basename(path)
        for i, tab in enumerate(self.tabs.tabs):
            if hasattr(tab.content, 'data') and tab.content.data == path:
                self.tabs.selected_index = i
                self.page.update()
                return

        new_editor = ft.TextField(value=content, multiline=True, expand=True, data=path)
        new_tab = ft.Tab(text=filename, content=new_editor)

        if self.tabs.tabs and self.tabs.tabs[0].text == "Welcome":
            self.tabs.tabs[0] = new_tab
        else:
            self.tabs.tabs.append(new_tab)
        
        self.tabs.selected_index = len(self.tabs.tabs) - 1
        self.page.update()

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