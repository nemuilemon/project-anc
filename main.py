# main.py
import flet as ft
import os
from tinydb import TinyDB
import config
from ui import AppUI
from logic import AppLogic
from threading import Thread, Event # Eventを追加でインポート

def main(page: ft.Page):
    """Project A.N.C.のメイン関数。
    
    アプリケーションの初期化、各コンポーネントの連携、
    イベントハンドラの設定を行う。
    
    Args:
        page (ft.Page): Fletページオブジェクト
    
    Note:
        この関数はFletアプリケーションのエントリーポイントとして
        ft.app()から呼び出される。
    """
    try:
        page.title = "Project A.N.C. (Alice Nexus Core)"
        
        # ディレクトリの安全な作成
        try:
            if not os.path.exists(config.NOTES_DIR):
                os.makedirs(config.NOTES_DIR, exist_ok=True)
        except PermissionError:
            page.snack_bar = ft.SnackBar(content=ft.Text(f"Permission denied creating directory: {config.NOTES_DIR}"))
            page.snack_bar.open = True
            page.update()
            return
        except OSError as e:
            page.snack_bar = ft.SnackBar(content=ft.Text(f"Error creating directory: {str(e)}"))
            page.snack_bar.open = True
            page.update()
            return
        
        # データベースの安全な初期化
        try:
            db = TinyDB(config.DB_FILE)
        except Exception as e:
            page.snack_bar = ft.SnackBar(content=ft.Text(f"Database initialization failed: {str(e)}"))
            page.snack_bar.open = True
            page.update()
            return

        # アプリケーションロジックの初期化
        try:
            app_logic = AppLogic(db)
        except Exception as e:
            page.snack_bar = ft.SnackBar(content=ft.Text(f"Application logic initialization failed: {str(e)}"))
            page.snack_bar.open = True
            page.update()
            return
    except Exception as e:
        print(f"Critical error during application initialization: {e}")
        if hasattr(page, 'snack_bar'):
            page.snack_bar = ft.SnackBar(content=ft.Text(f"Critical initialization error: {str(e)}"))
            page.snack_bar.open = True
            page.update()
        return

    # --- 状態管理用の変数を追加 ---
    # 分析処理の実行状態を管理するフラグ
    is_analyzing = False
    # キャンセル命令をスレッドに伝えるためのイベントオブジェクト
    cancel_event = Event()

    def handle_open_file(path: str):
        try:
            content = app_logic.read_file(path)
            if content is not None:
                app_ui.add_or_focus_tab(path, content)
            else:
                page.snack_bar = ft.SnackBar(content=ft.Text("ファイルの読み込みに失敗しました。"))
                page.snack_bar.open = True
                page.update()
        except Exception as e:
            print(f"Error in handle_open_file: {e}")
            page.snack_bar = ft.SnackBar(content=ft.Text(f"ファイルオープンエラー: {str(e)}"))
            page.snack_bar.open = True
            page.update()

    def handle_save_file(path: str, content: str):
        try:
            success, title = app_logic.save_file(path, content)
            if success:
                page.snack_bar = ft.SnackBar(content=ft.Text(f"『{title}』を保存しました。"))
                page.snack_bar.open = True
                
                try:
                    all_files = app_logic.get_file_list()
                    app_ui.update_file_list(all_files)
                except Exception as list_error:
                    print(f"Error updating file list after save: {list_error}")
                    # Continue anyway since file was saved successfully
                
                page.update()
            else:
                page.snack_bar = ft.SnackBar(content=ft.Text("ファイルの保存に失敗しました。"))
                page.snack_bar.open = True
                page.update()
        except Exception as e:
            print(f"Error in handle_save_file: {e}")
            page.snack_bar = ft.SnackBar(content=ft.Text(f"保存処理エラー: {str(e)}"))
            page.snack_bar.open = True
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

    def handle_refresh_files(show_archived=False):
        """ファイルリストの更新命令を処理する"""
        try:
            app_logic.sync_database()
            all_files = app_logic.get_file_list(show_archived=show_archived)
            app_ui.update_file_list(all_files)
            page.snack_bar = ft.SnackBar(content=ft.Text("ファイルリストを更新しました。"))
            page.snack_bar.open = True
            page.update()
        except Exception as e:
            print(f"Error in handle_refresh_files: {e}")
            page.snack_bar = ft.SnackBar(content=ft.Text(f"ファイルリスト更新エラー: {str(e)}"))
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

    def handle_create_file(filename: str):
        """新しいファイルの作成命令を処理する"""
        success, message = app_logic.create_new_file(filename)
        
        page.snack_bar = ft.SnackBar(content=ft.Text(message))
        page.snack_bar.open = True
        
        if success:
            # ファイルリストを更新
            all_files = app_logic.get_file_list()
            app_ui.update_file_list(all_files)
            
            # 新しく作成したファイルを自動的に開く
            full_path = os.path.join(config.NOTES_DIR, filename if filename.endswith('.md') else filename + '.md')
            handle_open_file(full_path)
        
        page.update()

    def handle_archive_file(file_path: str):
        """ファイルのアーカイブ/アンアーカイブ命令を処理する"""
        # ファイルの現在のステータスを確認
        from tinydb import Query
        File = Query()
        file_record = app_logic.db.get(File.path == file_path)
        
        if not file_record:
            page.snack_bar = ft.SnackBar(content=ft.Text("ファイルが見つかりません。"))
            page.snack_bar.open = True
            page.update()
            return
        
        current_status = file_record.get('status', 'active')
        
        if current_status == 'archived':
            # アンアーカイブ
            success, message = app_logic.unarchive_file(file_path)
        else:
            # アーカイブ
            success, message = app_logic.archive_file(file_path)
        
        page.snack_bar = ft.SnackBar(content=ft.Text(message))
        page.snack_bar.open = True
        
        if success:
            # ファイルリストを更新
            show_archived = app_ui.show_archived_switch.value
            all_files = app_logic.get_file_list(show_archived=show_archived)
            app_ui.update_file_list(all_files)
            
            # アーカイブされたファイルが現在開いているタブにある場合は閉じる
            if current_status != 'archived':  # アーカイブ操作の場合
                for i, tab in enumerate(app_ui.tabs.tabs):
                    if hasattr(tab.content, 'data') and tab.content.data == file_path:
                        app_ui.tabs.tabs.remove(tab)
                        if not app_ui.tabs.tabs:
                            app_ui.tabs.tabs.append(
                                ft.Tab(text="Welcome", content=ft.Column(
                                    [ft.Text("← サイドバーからファイルを選択してください", size=20)],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ))
                            )
                        break
        
        page.update()

    def handle_update_order(ordered_paths: list):
        """ファイルの順番更新命令を処理する"""
        print(f"Handle update order called with: {len(ordered_paths)} files")  # Debug
        success, message = app_logic.update_file_order(ordered_paths)
        print(f"Update order result: {success}, {message}")  # Debug
        
        if success:
            # ファイルリストを更新（現在の表示状態を保持）
            show_archived = app_ui.show_archived_switch.value
            all_files = app_logic.get_file_list(show_archived=show_archived)
            app_ui.update_file_list(all_files)
            
            # 成功メッセージを表示
            page.snack_bar = ft.SnackBar(content=ft.Text(message))
            page.snack_bar.open = True
        else:
            # エラーメッセージを表示
            page.snack_bar = ft.SnackBar(content=ft.Text(message))
            page.snack_bar.open = True
        
        page.update()

    # AppUIのインスタンス作成とエラーハンドリング
    try:
        app_ui = AppUI(
            page,
            on_open_file=handle_open_file, 
            on_save_file=handle_save_file,
            on_analyze_tags=handle_analyze_tags,
            on_refresh_files=handle_refresh_files,
            on_update_tags=handle_update_tags,
            on_cancel_tags=handle_cancel_tags, # 追加
            on_rename_file=handle_rename_file, # ★追加
            on_close_tab=handle_close_tab, # ★追加
            on_create_file=handle_create_file, # ★追加
            on_archive_file=handle_archive_file, # ★追加
            on_update_order=handle_update_order # ★追加
        )
        
        page.appbar = app_ui.appbar
        page.add(app_ui.build())

        # 初期ファイルリストの読み込み
        try:
            initial_files = app_logic.get_file_list()
            app_ui.update_file_list(initial_files)
        except Exception as e:
            print(f"Error loading initial file list: {e}")
            page.snack_bar = ft.SnackBar(content=ft.Text("ファイルリストの初期読み込みでエラーが発生しました。"))
            page.snack_bar.open = True
            page.update()
            
    except Exception as e:
        print(f"Error creating UI: {e}")
        page.snack_bar = ft.SnackBar(content=ft.Text(f"UIの作成でエラーが発生しました: {str(e)}"))
        page.snack_bar.open = True
        page.update()
        return

# アプリケーションエントリーポイントのセーフラッパー
def safe_main():
    """アプリケーションのメイン関数を安全に実行するラッパー"""
    try:
        ft.app(target=main)
    except Exception as e:
        print(f"Critical application error: {e}")
        print("Please check your configuration and try again.")
        
if __name__ == "__main__":
    safe_main()