import flet as ft
import os

class AppUI:
    """
    アプリケーションのUI（見た目）を定義し、管理するクラス。
    UIのロジック（ファイル操作など）は持たず、main.pyの指揮者関数を呼び出す。
    """
    def __init__(self, page: ft.Page, on_open_file, on_save_file):
        # ページオブジェクトと、main.pyからの指揮者関数を受け取る
        self.page = page
        self.on_open_file = on_open_file
        self.on_save_file = on_save_file

        # --- UIコントロールの定義 ---
        self.tabs = ft.Tabs(selected_index=0, expand=True, tabs=[])
        self.file_list = ft.Column(scroll=ft.ScrollMode.AUTO)
        self.appbar = ft.AppBar(
            title=ft.Text("Project A.N.C."),
            actions=[
                ft.IconButton(ft.Icons.SAVE, on_click=self.save_button_clicked),
            ]
        )
        self.sidebar = ft.Container(
            content=self.file_list,
            width=200, padding=10, bgcolor=ft.Colors.BLACK12
        )

    def file_tile_clicked(self, e):
        """サイドバーのファイルがクリックされた時に指揮者関数を呼び出す"""
        self.on_open_file(e.control.data)

    def save_button_clicked(self, e):
        """保存ボタンがクリックされた時に指揮者関数を呼び出す"""
        active_tab = self.get_active_tab()
        # contentがTextFieldであり、data属性を持っているか確認
        if active_tab and hasattr(active_tab.content, 'data'):
            path = active_tab.content.data
            content = active_tab.content.value
            self.on_save_file(path, content)

    def update_file_list(self, files):
        """ファイルリストUIを更新する"""
        self.file_list.controls.clear()
        if not files:
            self.file_list.controls.append(ft.Text("メモがありません。"))
        else:
            for filename in files:
                self.file_list.controls.append(
                    ft.ListTile(title=ft.Text(filename), data=filename, on_click=self.file_tile_clicked)
                )
        self.page.update()

    def add_or_focus_tab(self, filename, content):
        """新しいタブを追加するか、既存のタブにフォーカスする"""
        path = filename
        for i, tab in enumerate(self.tabs.tabs):
            # contentがdata属性を持っているか安全にチェック
            if hasattr(tab.content, 'data') and tab.content.data == path:
                self.tabs.selected_index = i
                self.page.update()
                return

        # 新しいエディタ(TextField)にファイルパスをdataとして記録
        new_editor = ft.TextField(
            value=content,
            multiline=True,
            expand=True,
            data=path
        )

        new_tab = ft.Tab(
            text=filename,
            content=new_editor,
        )

        # Welcomeタブがあればそれを置き換える
        if self.tabs.tabs and self.tabs.tabs[0].text == "Welcome":
            self.tabs.tabs[0] = new_tab
        else:
            self.tabs.tabs.append(new_tab)
        # 新しく開いたタブを選択状態にする
        self.tabs.selected_index = len(self.tabs.tabs) - 1
        self.page.update()

    def get_active_tab(self):
        """現在アクティブなタブコントロールを返す"""
        if self.tabs.tabs:
            return self.tabs.tabs[self.tabs.selected_index]
        return None

    def build(self):
        """このUIコンポーネントの初期レイアウトを構築して返す"""
        # アプリ起動時に表示する初期メッセージ
        self.tabs.tabs.append(
            ft.Tab(text="Welcome", content=ft.Column(
                [ft.Text("← サイドバーからファイルを選択してください", size=20)],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ))
        )
        # 最終的なレイアウト
        return ft.Row(
            controls=[self.sidebar, ft.VerticalDivider(width=1), self.tabs],
            expand=True,
        )