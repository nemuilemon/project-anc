# main.py
import flet as ft
import os
import sys
from pathlib import Path
from tinydb import TinyDB

# Add config directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
import config
from ui_redesign import RedesignedAppUI  # 新しいUI実装を使用
from logic import AppLogic
from handlers import AppHandlers
from logger import app_logger, PerformanceTimer
from threading import Thread, Event
from state_manager import AppState

def main(page: ft.Page):
    print("[DIAGNOSTIC] Entered main(page)")
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

            # Set window icon (must use absolute path and .ico format for Windows)
            # Note: Flet has known issues with relative paths for page.window.icon
            project_root = Path(__file__).parent.parent
            icon_path = project_root / "assets" / "icon.ico"

            if icon_path.exists():
                page.window.icon = str(icon_path)
                app_logger.log_ui_event("page_icon_set", "main_page", str(icon_path))
            else:
                app_logger.main_logger.warning(f"Icon file not found: {icon_path}")

            app_logger.log_ui_event("page_title_set", "main_page", page.title)
            
            # ディレクトリの安全な作成
            print("[DIAGNOSTIC] Creating directories...")
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
            print("[DIAGNOSTIC] Directories created.")
            
            # データベースの安全な初期化
            print("[DIAGNOSTIC] Initializing database...")
            try:
                db = TinyDB(config.DB_FILE)
                app_logger.log_database_operation("initialize", "main_db", True, config.DB_FILE)
            except Exception as e:
                app_logger.log_error(e, "database_initialization")
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Database initialization failed: {str(e)}"))
                page.snack_bar.open = True
                page.update()
                return
            print("[DIAGNOSTIC] Database initialized.")

            # アプリケーションロジックの初期化
            print("[DIAGNOSTIC] Initializing AppLogic...")
            try:
                app_logic = AppLogic(db)
                app_logger.main_logger.info("Application logic initialized successfully")

                # Get available AI plugins for UI dropdown
                available_ai_functions = app_logic.get_available_ai_functions()
                app_logger.main_logger.info(f"Found {len(available_ai_functions)} AI analysis plugins")
            except Exception as e:
                app_logger.log_error(e, "app_logic_initialization")
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Application logic initialization failed: {str(e)}"))
                page.snack_bar.open = True
                page.update()
                return
            print("[DIAGNOSTIC] AppLogic initialized.")
                
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

    # Initialize AppState with persistence
    print("[DIAGNOSTIC] Initializing AppState...")
    from state_manager import app_state
    persistence_file = os.path.join(config.DATA_DIR, 'conversation_state.json')
    app_state._persistence_file = persistence_file
    app_state.load_conversations(persistence_file)
    app_logger.main_logger.info(f"AppState initialized with persistence file: {persistence_file}")
    print("[DIAGNOSTIC] AppState initialized.")

    # Create centralized event handlers (app_ui will be set later)
    print("[DIAGNOSTIC] Initializing AppHandlers...")
    handlers = AppHandlers(page, AppLogic, None, cancel_event)
    print("[DIAGNOSTIC] AppHandlers initialized.")
    
    # RedesignedAppUIのインスタンス作成とエラーハンドリング
    print("[DIAGNOSTIC] Initializing RedesignedAppUI...")
    try:
        app_ui = RedesignedAppUI(
            page,
            on_open_file=handlers.handle_open_file,
            on_analyze_tags=handlers.handle_analyze_tags,
            on_refresh_files=handlers.handle_refresh_files,
            on_update_tags=handlers.handle_update_tags,
            on_cancel_tags=handlers.handle_cancel_tags,
            on_rename_file=handlers.handle_rename_file,
            on_close_tab=handlers.handle_close_tab,
            on_create_file=handlers.handle_create_file,
            on_archive_file=handlers.handle_archive_file,
            on_delete_file=handlers.handle_delete_file,
            on_run_ai_analysis=handlers.handle_ai_analysis,
            # New automation callbacks
            on_run_automation=handlers.handle_run_automation,
            on_cancel_automation=handlers.handle_cancel_automation,
            on_get_automation_preview=handlers.handle_get_automation_preview,
            # Available AI functions for dynamic dropdown
            available_ai_functions=available_ai_functions,
            # Chat functionality
            on_send_chat_message=lambda user_message, alice_response, image_path: handlers.handle_send_chat_message(user_message, alice_response, image_path),
            config=config,
            # AppState for conversation management
            app_state=app_state
        )
        
        # Now update the handlers with the initialized app_ui
        handlers.app_ui = app_ui

        # Add reference to app_logic in UI for archive functionality
        app_ui._app_logic_ref = app_logic

        # Add handlers reference to UI for memory functionality
        app_ui.handlers = handlers

        # 新しいUIではappbarは使用しないため、設定を省略
        # page.appbar = app_ui.appbar  # コメントアウト
        print("[DIAGNOSTIC] RedesignedAppUI initialized. Building and adding to page...")
        page.add(app_ui.build())
        print("[DIAGNOSTIC] UI added to page.")

        # 初期ファイルリストの読み込み
        print("[DIAGNOSTIC] Loading initial file list...")
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
        print("[DIAGNOSTIC] Initial file list loaded.")
            
    except Exception as e:
        app_logger.log_error(e, "ui_creation")
        print(f"Error creating UI: {e}")
        page.snack_bar = ft.SnackBar(content=ft.Text(f"UIの作成でエラーが発生しました: {str(e)}"))
        page.snack_bar.open = True
        page.update()
        return
    
    # Log successful application startup
    app_logger.main_logger.info("Application initialization completed successfully")
    print("[DIAGNOSTIC] main() function finished successfully.")
    
    # Register cleanup on page close
    def on_page_close(e):
        # Auto-save all open tabs before closing
        app_ui.auto_save_all_tabs()

        # Save conversation state
        if app_state:
            app_state.save_conversations()
            app_logger.main_logger.info("Conversation state saved on application close")

        app_logger.log_app_shutdown()
        # Cleanup async operations
        from async_operations import async_manager
        async_manager.shutdown()

    page.on_window_event = lambda e: on_page_close(e) if e.data == "close" else None

# アプリケーションエントリーポイントのセーフラッパー
def safe_main():
    """アプリケーションのメイン関数を安全に実行するラッパー"""
    print("[DIAGNOSTIC] Entered safe_main()"),
    try:
        # Get absolute path to assets directory
        project_root = Path(__file__).parent.parent
        assets_path = project_root / "assets"

        # Run with assets_dir specified for flet run compatibility
        print("[DIAGNOSTIC] Calling ft.app()...")
        ft.app(
            target=main,
            assets_dir=str(assets_path) if assets_path.exists() else None
        )
        print("[DIAGNOSTIC] ft.app() exited.")
    except Exception as e:
        print(f"Critical application error: {e}")
        print("Please check your configuration and try again.")

if __name__ == "__main__":
    safe_main()