# main.py
import flet as ft
import os
from tinydb import TinyDB
import config
from ui import AppUI
from logic import AppLogic

def main(page: ft.Page):
    # --- 1. 初期設定 ---
    page.title = "Project A.N.C. (Alice Nexus Core)"
    if not os.path.exists(config.NOTES_DIR):
        os.makedirs(config.NOTES_DIR)
    db = TinyDB(config.DB_FILE)

    # --- 2. 各担当のインスタンスを作成 ---
    app_logic = AppLogic(db)

    # --- 3. 指揮者としての処理を定義 ---
    def handle_open_file(filename: str):
        path = os.path.join(config.NOTES_DIR, filename)
        content = app_logic.read_file(path)
        if content is not None:
            app_ui.add_or_focus_tab(filename, content)

    def handle_save_file(path: str, content: str):
        # NOTE: pathは現在filenameと同じだが将来的にはフルパスになる
        full_path = os.path.join(config.NOTES_DIR, path)
        success, title = app_logic.save_file(full_path, content)
        if success:
            page.snack_bar = ft.SnackBar(content=ft.Text(f"『{title}』を保存しました。"))
            page.snack_bar.open = True
            page.update()

    # --- 4. UIに指揮者の処理を渡してインスタンスを作成 ---
    app_ui = AppUI(page,on_open_file=handle_open_file, on_save_file=handle_save_file)
    page.appbar = app_ui.appbar # appbarをページに設定

    # --- 5. アプリケーションの実行 ---
    page.add(app_ui.build())

    # 初回のファイルリストを読み込んでUIに反映
    initial_files = app_logic.get_file_list()
    app_ui.update_file_list(initial_files)


ft.app(target=main)