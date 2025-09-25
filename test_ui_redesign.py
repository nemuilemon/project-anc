"""Project A.N.C. UI Redesign Test

新しく設計されたカンバセーション・ファーストUIの動作テスト。
基本的な機能の動作を確認し、既存システムとの統合をテストする。
"""

import flet as ft
import sys
import os

# プロジェクトのappディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from ui_redesign import RedesignedAppUI


def main(page: ft.Page):
    """テストアプリケーションのメイン関数"""
    page.title = "Project A.N.C. - UI Redesign Test"
    page.window_width = 1200
    page.window_height = 800
    page.theme_mode = ft.ThemeMode.LIGHT

    # テスト用のダミーコールバック関数
    def dummy_open_file(file_info):
        print(f"Opening file: {file_info}")

    def dummy_save_file(file_info, content):
        print(f"Saving file: {file_info['title']} with {len(content)} characters")

    def dummy_analyze_tags(file_info):
        print(f"Analyzing tags for: {file_info}")

    def dummy_refresh_files():
        print("Refreshing file list")
        # テスト用ファイルリストを返す
        return test_files

    def dummy_update_tags(file_info, new_tags):
        print(f"Updating tags for {file_info['title']}: {new_tags}")

    def dummy_cancel_tags():
        print("Canceling tag operation")

    def dummy_rename_file(file_info, new_name):
        print(f"Renaming {file_info['title']} to {new_name}")

    def dummy_close_tab(file_info):
        print(f"Closing tab: {file_info['title']}")

    def dummy_create_file(file_name):
        print(f"Creating new file: {file_name}")

    def dummy_archive_file(file_info):
        print(f"Archiving file: {file_info['title']}")

    def dummy_delete_file(file_info):
        print(f"Deleting file: {file_info['title']}")

    def dummy_run_ai_analysis(function_key):
        print(f"Running AI analysis: {function_key}")
        return f"Analysis result for {function_key}: This is a test result."

    def dummy_send_chat_message(message):
        print(f"Chat message: {message}")
        # シンプルなエコー応答
        return f"Alice: You said '{message}'. This is a test response!"

    # テスト用設定クラス
    class TestConfig:
        def __init__(self):
            self.GEMINI_API_KEY = "test_key"
            self.ALICE_CHAT_CONFIG = {
                'max_history_length': 50
            }

    # テスト用ファイルリスト
    test_files = [
        {
            'title': 'test_file1.py',
            'path': '/test/path/test_file1.py',
            'tags': ['python', 'test'],
            'status': 'active',
            'order_index': 1
        },
        {
            'title': 'readme.md',
            'path': '/test/path/readme.md',
            'tags': ['documentation'],
            'status': 'active',
            'order_index': 2
        },
        {
            'title': 'old_file.txt',
            'path': '/test/path/old_file.txt',
            'tags': ['archive'],
            'status': 'archived',
            'order_index': 3
        }
    ]

    # テスト用AI機能リスト
    test_ai_functions = [
        {'key': 'summary', 'name': 'テキスト要約'},
        {'key': 'tags', 'name': 'タグ分析'},
        {'key': 'sentiment', 'name': '感情分析'}
    ]

    # RedesignedAppUIを作成
    try:
        app_ui = RedesignedAppUI(
            page=page,
            on_open_file=dummy_open_file,
            on_save_file=dummy_save_file,
            on_analyze_tags=dummy_analyze_tags,
            on_refresh_files=dummy_refresh_files,
            on_update_tags=dummy_update_tags,
            on_cancel_tags=dummy_cancel_tags,
            on_rename_file=dummy_rename_file,
            on_close_tab=dummy_close_tab,
            on_create_file=dummy_create_file,
            on_archive_file=dummy_archive_file,
            on_delete_file=dummy_delete_file,
            on_run_ai_analysis=dummy_run_ai_analysis,
            available_ai_functions=test_ai_functions,
            on_send_chat_message=dummy_send_chat_message,
            config=TestConfig()
        )

        # UIをページに追加
        ui_component = app_ui.build()
        page.add(ui_component)

        # テスト用ファイルリストを読み込み
        app_ui.update_file_list(test_files)

        # 成功メッセージ
        page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text("UI Redesign Test: Successfully loaded!"),
                bgcolor=ft.Colors.GREEN
            )
        )

        print("UI Redesign Test: Application started successfully!")
        print("Test features:")
        print("1. Chat with Alice in the main conversation area")
        print("2. Browse files in the Files tab")
        print("3. Open files in the Editor tab")
        print("4. Run AI analysis in the Analysis tab")
        print("5. Check settings in the Settings tab")

    except Exception as e:
        print(f"Error initializing UI: {e}")
        page.add(
            ft.Text(
                f"Error loading UI: {str(e)}",
                color=ft.Colors.RED,
                size=20
            )
        )


def run_test():
    """テストアプリケーションを実行"""
    print("Starting Project A.N.C. UI Redesign Test...")
    ft.app(target=main, view=ft.WEB_BROWSER)


if __name__ == "__main__":
    run_test()