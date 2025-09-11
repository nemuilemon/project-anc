import flet as ft

def main(page: ft.Page):
    # アプリのタイトルを設定
    page.title = "Project A.N.C. (Alice Nexus Core)"

    # ここに画面の部品（コントロール）を追加していく

    # ページの更新
    page.update()

# アプリケーションを起動
ft.app(target=main)