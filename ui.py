# ui.py
import flet as ft
import os

class AppUI:
    def __init__(self, page: ft.Page, on_open_file, on_save_file, on_analyze_tags, on_refresh_files, on_update_tags):
        self.page = page
        self.on_open_file = on_open_file
        self.on_save_file = on_save_file
        # self.on_search = on_search
        self.on_analyze_tags = on_analyze_tags
        self.on_refresh_files = on_refresh_files
        self.on_update_tags = on_update_tags

        # --- UIコントロールの定義 ---
        self.tabs = ft.Tabs(selected_index=0, expand=True, tabs=[])
        
        # v0.3で追加 動かず一旦コメントアウト
        # self.search_box = ft.TextField(
        #     label="Search notes...",
        #     on_change=self.search_box_changed,
        #     prefix_icon=ft.Icons.SEARCH
        # )
        
        self.file_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True) # expand=Trueを追加
        
        self.appbar = ft.AppBar(
            title=ft.Text("Project A.N.C."),
            actions=[
                    ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Refresh file list",
                    on_click=lambda e: self.on_refresh_files() 
                    ),
                ft.ElevatedButton("Save", icon=ft.Icons.SAVE, on_click=self.save_button_clicked), # 見た目を少し変更
                ft.ElevatedButton("Analyze Tags", icon=ft.Icons.AUTO_AWESOME, on_click=self.analyze_button_clicked) # 新しいボタン
            ]
        )
        # サイドバーの構成を変更
        self.sidebar = ft.Container(
            content=ft.Column([
                # 2. 検索ボックスの無効化：レイアウトからも削除
                # self.search_box,
                # ft.Divider(),
                self.file_list
            ]),
            width=250, padding=10, bgcolor=ft.Colors.BLACK12
        )

        # 3. タグ編集機能の追加：編集用ウィンドウ（ダイアログ）を定義しておく
        self.edit_tags_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Tags"),
            content=ft.TextField(label="Tags (comma-separated)"),
            actions=[
                ft.TextButton("Cancel", on_click=self.close_dialog),
                ft.TextButton("Save", on_click=self.save_tags_and_close_dialog),
            ],
        )
        self.page.dialog = self.edit_tags_dialog

    def analyze_button_clicked(self, e):
        """タグ分析ボタンがクリックされた時に指揮者関数を呼び出す"""
        active_tab = self.get_active_tab()
        if active_tab and hasattr(active_tab.content, 'data'):
            path = active_tab.content.data
            content = active_tab.content.value
            self.on_analyze_tags(path, content) # 新しい指揮者関数を呼び出し
            
    # 2. 検索ボックスの無効化：関連する関数も一旦コメントアウト
    # def search_box_changed(self, e):
    #     self.on_search(e.control.value)

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


    # 3. タグ編集機能の追加：編集ボタンが押された時の処理
    def open_edit_tags_dialog(self, e):
        file_info = e.control.data
        # ダイアログのテキストボックスに、現在のタグをカンマ区切りで表示
        self.edit_tags_dialog.content.value = ", ".join(file_info.get('tags', []))
        # どのファイルの情報かをダイアログにこっそり覚えておいてもらう
        self.edit_tags_dialog.data = file_info['path']
        
        self.edit_tags_dialog.open = True
        self.page.update()

    # 3. タグ編集機能の追加：ダイアログの「キャンセル」が押された時
    def close_dialog(self, e):
        self.edit_tags_dialog.open = False
        self.page.update()

    # 3. タグ編集機能の追加：ダイアログの「保存」が押された時
    def save_tags_and_close_dialog(self, e):
        path = self.edit_tags_dialog.data
        tags_str = self.edit_tags_dialog.content.value
        # 入力された文字列をカンマで区切って、リストに変換する
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        
        # 5. 指揮系統の変更：新しい指揮官を呼び出して、タグ更新を依頼する
        self.on_update_tags(path, tags)
        
        self.edit_tags_dialog.open = False
        self.page.update()


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
                        on_click=self.file_tile_clicked,
                        # ↓↓↓ この6行を追加してね！ ↓↓↓
                        trailing=ft.IconButton(
                            icon=ft.Icons.EDIT,
                            tooltip="Edit tags",
                            data=info,
                            on_click=self.open_edit_tags_dialog
                        ),
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
    
