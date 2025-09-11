# ui.py
import flet as ft
import os

class AppUI:
    def __init__(self, page: ft.Page, on_open_file, on_save_file, on_search, on_analyze_tags):
        self.page = page
        self.on_open_file = on_open_file
        self.on_save_file = on_save_file
        self.on_search = on_search
        self.on_analyze_tags = on_analyze_tags

        # --- UIコントロールの定義 ---
        self.tabs = ft.Tabs(selected_index=0, expand=True, tabs=[])
        
        # v0.3で追加
        self.search_box = ft.TextField(
            label="Search notes...",
            on_change=self.search_box_changed,
            prefix_icon=ft.Icons.SEARCH
        )
        
        self.file_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True) # expand=Trueを追加
        
        self.appbar = ft.AppBar(
            title=ft.Text("Project A.N.C."),
            actions=[
                ft.ElevatedButton("Save", icon=ft.Icons.SAVE, on_click=self.save_button_clicked), # 見た目を少し変更
                ft.ElevatedButton("Analyze Tags", icon=ft.Icons.AUTO_AWESOME, on_click=self.analyze_button_clicked) # 新しいボタン
            ]
        )
        # サイドバーの構成を変更
        self.sidebar = ft.Container(
            content=ft.Column([
                self.search_box,
                ft.Divider(),
                self.file_list
            ]),
            width=250, padding=10, bgcolor=ft.Colors.BLACK12
        )

    def analyze_button_clicked(self, e):
        """タグ分析ボタンがクリックされた時に指揮者関数を呼び出す"""
        active_tab = self.get_active_tab()
        if active_tab and hasattr(active_tab.content, 'data'):
            path = active_tab.content.data
            content = active_tab.content.value
            self.on_analyze_tags(path, content) # 新しい指揮者関数を呼び出し
            
    def search_box_changed(self, e):
        """検索ボックスの内容が変わった時に指揮者関数を呼び出す"""
        self.on_search(e.control.value) # 入力された値を指揮者に渡す

    def file_tile_clicked(self, e):
        """サイドバーのファイルがクリックされた時に指揮者関数を呼び出す"""
        self.on_open_file(e.control.data['path']) # pathを渡すように変更

    def save_button_clicked(self, e):
        """保存ボタンがクリックされた時に指揮者関数を呼び出す"""
        active_tab = self.get_active_tab()
        if active_tab and hasattr(active_tab.content, 'data'):
            path = active_tab.content.data
            content = active_tab.content.value
            self.on_save_file(path, content)

    def update_file_list(self, files_info):
        """ファイルリストUIを更新する"""
        self.file_list.controls.clear()
        if not files_info:
            self.file_list.controls.append(ft.Text("該当するメモがありません。"))
        else:
            for info in files_info:
                # v0.3変更: subtitleにタグを表示
                tags_display = ", ".join(info.get('tags', []))
                self.file_list.controls.append(
                    ft.ListTile(
                        title=ft.Text(info['title']),
                        subtitle=ft.Text(tags_display, size=10, color=ft.Colors.GREY),
                        data=info, 
                        on_click=self.file_tile_clicked
                    )
                )
        self.page.update()

    def add_or_focus_tab(self, path, content):
        """新しいタブを追加するか、既存のタブにフォーカスする"""
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
        """現在アクティブなタブコントロールを返す"""
        if self.tabs.tabs and len(self.tabs.tabs) > self.tabs.selected_index:
             return self.tabs.tabs[self.tabs.selected_index]
        return None

    def build(self):
        """このUIコンポーネントの初期レイアウトを構築して返す"""
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