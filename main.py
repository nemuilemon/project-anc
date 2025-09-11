import flet as ft
import os # osライブラリをインポート
from tinydb import TinyDB


def main(page: ft.Page):
    page.title = "Project A.N.C. (Alice Nexus Core)"

    db = TinyDB('anc_db.json') # DBを初期化
    
    # アプリ起動時に読み込むファイルの内容を準備
    initial_content = ""
    file_path = "test.md"
    
    # ファイルが存在するか確認して、あれば内容を読み込む
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            initial_content = f.read()

    # テキストエディタ本体を定義（valueに読み込んだ内容を設定）
    editor = ft.TextField(
        multiline=True,
        expand=True,
        hint_text="ここにメモを書いてね...",
        value=initial_content # ここがポイント！
    )

    # 保存ボタンが押された時の処理
    def save_file(e):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(editor.value)
        
        page.snack_bar = ft.SnackBar(content=ft.Text(f"保存しました！ ({file_path})"))
        page.snack_bar.open = True
        page.update()

    # アプリの上部バー（AppBar）を設定
    page.appbar = ft.AppBar(
        title=ft.Text("Untitled Note"),
        actions=[
            ft.IconButton(ft.Icons.SAVE, on_click=save_file),
        ]
    )

    # サイドバー
    sidebar = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.EDIT_NOTE,
                label="Files"
            ),
        ]
    )
    
    # メインビュー
    main_view = ft.Row(
        controls=[
            sidebar,
            ft.VerticalDivider(width=1),
            editor,
        ],
        expand=True,
    )

    page.add(main_view)
    page.update()

ft.app(target=main)