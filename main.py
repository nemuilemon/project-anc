# main.py
import flet as ft
import os
from tinydb import TinyDB
import config
from ui import AppUI
from logic import AppLogic

def main(page: ft.Page):
    page.title = "Project A.N.C. (Alice Nexus Core)"
    if not os.path.exists(config.NOTES_DIR):
        os.makedirs(config.NOTES_DIR)
    db = TinyDB(config.DB_FILE)

    app_logic = AppLogic(db)

    def handle_open_file(path: str):
        content = app_logic.read_file(path)
        if content is not None:
            app_ui.add_or_focus_tab(path, content)

    def handle_save_file(path: str, content: str):
        success, title = app_logic.save_file(path, content)
        if success:
            page.snack_bar = ft.SnackBar(content=ft.Text(f"『{title}』を保存しました。"))
            page.snack_bar.open = True
            # 保存時にもファイルリストを更新する
            all_files = app_logic.get_file_list()
            app_ui.update_file_list(all_files)
            page.update()

    # handle_analyze_tags関数を新しく追加
    def handle_analyze_tags(path: str, content: str):
        """タグ分析の命令を処理する"""
        if not path:
            page.snack_bar = ft.SnackBar(content=ft.Text("先にファイルを一度保存してください。"))
            page.snack_bar.open = True
            page.update()
            return
            
        # 分析中の表示
        page.snack_bar = ft.SnackBar(content=ft.Text("AIが分析中です..."))
        page.snack_bar.open = True
        page.update()
        
        success, message = app_logic.analyze_and_update_tags(path, content)
        
        page.snack_bar = ft.SnackBar(content=ft.Text(message))
        page.snack_bar.open = True
        
        if success:
            # 成功したらファイルリストを更新してタグを反映
            all_files = app_logic.get_file_list()
            app_ui.update_file_list(all_files)
        
        page.update()


    def handle_search(keyword: str):
        searched_files = app_logic.search_files(keyword)
        app_ui.update_file_list(searched_files)

    # AppUIの呼び出しを更新
    app_ui = AppUI(
        page,
        on_open_file=handle_open_file, 
        on_save_file=handle_save_file,
        on_search=handle_search,
        on_analyze_tags=handle_analyze_tags # 新しいハンドラを渡す
    )
    page.appbar = app_ui.appbar

    page.add(app_ui.build())

    initial_files = app_logic.get_file_list()
    app_ui.update_file_list(initial_files)

ft.app(target=main)