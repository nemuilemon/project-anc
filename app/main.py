# main.py
import flet as ft
import os
import sys
from tinydb import TinyDB

# Add config directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
import config
from ui import AppUI
from logic import AppLogic
from handlers import AppHandlers
from logger import app_logger, PerformanceTimer
from threading import Thread, Event

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
    # Initialize logging
    app_logger.log_app_start()
    
    with PerformanceTimer("Application initialization"):
        try:
            page.title = "Project A.N.C. (Alice Nexus Core)"
            app_logger.log_ui_event("page_title_set", "main_page", page.title)
            
            # ディレクトリの安全な作成
            try:
                if not os.path.exists(config.NOTES_DIR):
                    os.makedirs(config.NOTES_DIR, exist_ok=True)
                    app_logger.log_file_operation("create_directory", config.NOTES_DIR, True)
            except PermissionError as e:
                app_logger.log_error(e, "directory_creation")
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Permission denied creating directory: {config.NOTES_DIR}"))
                page.snack_bar.open = True
                page.update()
                return
            except OSError as e:
                app_logger.log_error(e, "directory_creation")
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Error creating directory: {str(e)}"))
                page.snack_bar.open = True
                page.update()
                return
            
            # データベースの安全な初期化
            try:
                db = TinyDB(config.DB_FILE)
                app_logger.log_database_operation("initialize", "main_db", True, config.DB_FILE)
            except Exception as e:
                app_logger.log_error(e, "database_initialization")
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Database initialization failed: {str(e)}"))
                page.snack_bar.open = True
                page.update()
                return

            # アプリケーションロジックの初期化
            try:
                app_logic = AppLogic(db)
                app_logger.main_logger.info("Application logic initialized successfully")
            except Exception as e:
                app_logger.log_error(e, "app_logic_initialization")
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Application logic initialization failed: {str(e)}"))
                page.snack_bar.open = True
                page.update()
                return
                
        except Exception as e:
            app_logger.log_error(e, "critical_application_initialization")
            print(f"Critical error during application initialization: {e}")
            if hasattr(page, 'snack_bar'):
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Critical initialization error: {str(e)}"))
                page.snack_bar.open = True
                page.update()
            return

    # キャンセル命令をスレッドに伝えるためのイベントオブジェクト
    cancel_event = Event()
    
    # Create centralized event handlers (app_ui will be set later)
    handlers = AppHandlers(page, app_logic, None, cancel_event)
    
    # AppUIのインスタンス作成とエラーハンドリング
    try:
        app_ui = AppUI(
            page,
            on_open_file=handlers.handle_open_file, 
            on_save_file=handlers.handle_save_file,
            on_analyze_tags=handlers.handle_analyze_tags,
            on_refresh_files=handlers.handle_refresh_files,
            on_update_tags=handlers.handle_update_tags,
            on_cancel_tags=handlers.handle_cancel_tags,
            on_rename_file=handlers.handle_rename_file,
            on_close_tab=handlers.handle_close_tab,
            on_create_file=handlers.handle_create_file,
            on_archive_file=handlers.handle_archive_file,
            on_update_order=handlers.handle_update_order,
            on_delete_file=handlers.handle_delete_file,
            on_run_ai_analysis=handlers.handle_ai_analysis
        )
        
        # Now update the handlers with the initialized app_ui
        handlers.app_ui = app_ui
        
        page.appbar = app_ui.appbar
        page.add(app_ui.build())

        # 初期ファイルリストの読み込み
        try:
            with PerformanceTimer("Initial file list load"):
                initial_files = app_logic.get_file_list()
                app_ui.update_file_list(initial_files)
                app_logger.main_logger.info(f"Loaded {len(initial_files)} files in initial file list")
        except Exception as e:
            app_logger.log_error(e, "initial_file_list_load")
            print(f"Error loading initial file list: {e}")
            page.snack_bar = ft.SnackBar(content=ft.Text("ファイルリストの初期読み込みでエラーが発生しました。"))
            page.snack_bar.open = True
            page.update()
            
    except Exception as e:
        app_logger.log_error(e, "ui_creation")
        print(f"Error creating UI: {e}")
        page.snack_bar = ft.SnackBar(content=ft.Text(f"UIの作成でエラーが発生しました: {str(e)}"))
        page.snack_bar.open = True
        page.update()
        return
    
    # Log successful application startup
    app_logger.main_logger.info("Application initialization completed successfully")
    
    # Register cleanup on page close
    def on_page_close(e):
        app_logger.log_app_shutdown()
        # Cleanup async operations
        from async_operations import async_manager
        async_manager.shutdown()
    
    page.on_window_event = lambda e: on_page_close(e) if e.data == "close" else None

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