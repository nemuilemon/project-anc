# main.py
import flet as ft
import os
from tinydb import TinyDB
import config
from ui import AppUI
from logic import AppLogic
from threading import Thread, Event # Eventを追加でインポート

def main(page: ft.Page):
    page.title = "Project A.N.C. (Alice Nexus Core)"
    if not os.path.exists(config.NOTES_DIR):
        os.makedirs(config.NOTES_DIR)
    db = TinyDB(config.DB_FILE)

    app_logic = AppLogic(db)

    # --- 状態管理用の変数を追加 ---
    # 分析処理の実行状態を管理するフラグ
    is_analyzing = False
    # キャンセル命令をスレッドに伝えるためのイベントオブジェクト
    cancel_event = Event()

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

    def run_tag_analysis(path, content):
        """AI分析を別スレッドで実行するためのラッパー関数"""
        nonlocal is_analyzing # 外側のis_analyzing変数を変更できるようにする
        
        try:
            # cancel_eventを渡す
            success, message = app_logic.analyze_and_update_tags(path, content, cancel_event)
            
            # 分析完了をUIに通知
            page.snack_bar = ft.SnackBar(content=ft.Text(message))
            page.snack_bar.open = True
            
            # 成功したらファイルリストを更新
            if success:
                all_files = app_logic.get_file_list()
                # UIの更新はpage.run()のスレッドで行う必要がある
                page.run_thread(lambda: app_ui.update_file_list(all_files))
            
            page.update()
        finally:
            # 処理が完了したら、必ずフラグを戻し、UIを通常モードに戻す
            is_analyzing = False
            page.run_thread(app_ui.stop_analysis_view)

    def handle_analyze_tags(path: str, content: str):
        nonlocal is_analyzing
        
        # すでに分析中なら、新しい分析を開始しない
        if is_analyzing:
            page.snack_bar = ft.SnackBar(content=ft.Text("現在、別の分析を実行中です。"))
            page.snack_bar.open = True
            page.update()
            return

        if not path:
            page.snack_bar = ft.SnackBar(content=ft.Text("先にファイルを一度保存してください。"))
            page.snack_bar.open = True
            page.update()
            return
            
        # --- ここからが分析開始のメイン処理 ---
        # 1. 分析中フラグを立てる
        is_analyzing = True
        # 2. キャンセルイベントをリセット（前のキャンセルが残らないように）
        cancel_event.clear()
        # 3. UIを「分析中」モードに変更
        app_ui.start_analysis_view()
        
        # 4. バックグラウンドスレッドを開始
        thread = Thread(target=run_tag_analysis, args=(path, content))
        thread.start()

    def handle_refresh_files():
        """ファイルリストの更新命令を処理する"""
        app_logic.sync_database()
        all_files = app_logic.get_file_list()
        app_ui.update_file_list(all_files)
        page.snack_bar = ft.SnackBar(content=ft.Text("ファイルリストを更新しました。"))
        page.snack_bar.open = True
        page.update()

    def handle_update_tags(path: str, tags: list):
        """タグの手動更新命令を処理する"""
        success, message = app_logic.update_tags(path, tags)
        page.snack_bar = ft.SnackBar(content=ft.Text(message))
        page.snack_bar.open = True
        
        if success:
            all_files = app_logic.get_file_list()
            app_ui.update_file_list(all_files)

        page.update()

    def handle_cancel_tags():
        """分析のキャンセル命令を処理する"""
        if is_analyzing:
            print("Cancellation requested by user.")
            cancel_event.set() # イベントをセットして、スレッドに伝える

    def handle_rename_file(old_path: str, new_name: str):
        """ファイル名の変更命令を処理する"""
        success, message, old_path, new_path = app_logic.rename_file(old_path, new_name)
        
        page.snack_bar = ft.SnackBar(content=ft.Text(message))
        page.snack_bar.open = True
        
        if success:
            # ファイルリストを更新
            all_files = app_logic.get_file_list()
            app_ui.update_file_list(all_files)
            # 開いているタブがあれば、そちらも更新
            app_ui.update_tab_after_rename(old_path, new_path)

        page.update()

    def handle_close_tab(tab_to_close: ft.Tab):
        """タブを閉じる処理（自動保存付き）"""
        path = tab_to_close.content.data
        content = tab_to_close.content.value
        
        # 1. ファイルを保存
        handle_save_file(path, content)
        
        # 2. タブをリストから削除
        app_ui.tabs.tabs.remove(tab_to_close)
        
        # 3. もし最後のタブが閉じられたら、Welcome画面を出す
        if not app_ui.tabs.tabs:
            app_ui.tabs.tabs.append(
                ft.Tab(text="Welcome", content=ft.Column(
                    [ft.Text("← サイドバーからファイルを選択してください", size=20)],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ))
            )
        
        page.update()

    # AppUIのインスタンス作成時に、新しい on_cancel_tags を渡す
    app_ui = AppUI(
        page,
        on_open_file=handle_open_file, 
        on_save_file=handle_save_file,
        on_analyze_tags=handle_analyze_tags,
        on_refresh_files=handle_refresh_files,
        on_update_tags=handle_update_tags,
        on_cancel_tags=handle_cancel_tags, # 追加
        on_rename_file=handle_rename_file, # ★追加
        on_close_tab=handle_close_tab # ★追加
    )
    
    page.appbar = app_ui.appbar
    page.add(app_ui.build())

    initial_files = app_logic.get_file_list()
    app_ui.update_file_list(initial_files)

ft.app(target=main)