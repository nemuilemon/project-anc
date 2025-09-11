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
            all_files = app_logic.get_file_list()
            app_ui.update_file_list(all_files)
            page.update()

    def handle_analyze_tags(path: str, content: str):
        if not path:
            page.snack_bar = ft.SnackBar(content=ft.Text("先にファイルを一度保存してください。"))
            page.snack_bar.open = True
            page.update()
            return
            
        page.snack_bar = ft.SnackBar(content=ft.Text("AIが分析中です..."))
        page.snack_bar.open = True
        page.update()
        
        success, message = app_logic.analyze_and_update_tags(path, content)
        
        page.snack_bar = ft.SnackBar(content=ft.Text(message))
        page.snack_bar.open = True
        
        if success:
            all_files = app_logic.get_file_list()
            app_ui.update_file_list(all_files)
        
        page.update()

    # 1. 新しい指揮官の追加：更新ボタンの命令を処理する
    def handle_refresh_files():
        """ファイルリストの更新命令を処理する"""
        app_logic.sync_database() # DBを同期して
        all_files = app_logic.get_file_list() # 最新のリストをもらって
        app_ui.update_file_list(all_files) # UIに反映する
        page.snack_bar = ft.SnackBar(content=ft.Text("ファイルリストを更新しました。"))
        page.snack_bar.open = True
        page.update()

    # 1. 新しい指揮官の追加：タグ編集の命令を処理する
    def handle_update_tags(path: str, tags: list):
        """タグの手動更新命令を処理する"""
        success, message = app_logic.update_tags(path, tags)
        page.snack_bar = ft.SnackBar(content=ft.Text(message))
        page.snack_bar.open = True
        
        if success:
            all_files = app_logic.get_file_list()
            app_ui.update_file_list(all_files) # UIを更新して変更を即時反映

        page.update()

    # 2. 指揮系統の整理：使わなくなった検索の指揮官をコメントアウト
    # def handle_search(keyword: str):
    #     searched_files = app_logic.search_files(keyword)
    #     app_ui.update_file_list(searched_files)

    # --- ★★★ここから下が、修正後の正しい順番だよ★★★ ---

    # 1. 【先に】AppUIのインスタンス（UI部品）を作成する
    app_ui = AppUI(
        page,
        on_open_file=handle_open_file, 
        on_save_file=handle_save_file,
        on_analyze_tags=handle_analyze_tags,
        on_refresh_files=handle_refresh_files,
        on_update_tags=handle_update_tags
    )
    
    # 2. AppBarを設定する
    page.appbar = app_ui.appbar

    # 3. 【最後に】準備したUI部品を使って、画面全体を組み立てる
    page.add(app_ui.build())

    # 4. 最初のファイルリストを読み込んで表示する
    initial_files = app_logic.get_file_list()
    app_ui.update_file_list(initial_files)


ft.app(target=main)