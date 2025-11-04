"""Event handlers for Project A.N.C.

This module contains all event handler functions that were previously
in main.py, implementing separation of concerns and improving code
organization.
"""

import flet as ft
import os
from threading import Thread, Event
from logic import AppLogic
from memory_creation_manager import MemoryCreationManager


class AppHandlers:
    """Centralized event handlers for the application.
    
    This class contains all event handling logic, separating it from
    the main application initialization code for better organization
    and maintainability.
    """
    
    def __init__(self, page: ft.Page, app_logic: AppLogic, app_ui, cancel_event: Event):
        self.page = page
        self.app_logic = app_logic
        self.app_ui = app_ui
        self.cancel_event = cancel_event
        self.is_analyzing = False

        # Initialize memory creation manager
        self.memory_manager = None
        self._init_memory_manager()
    
    def handle_open_file(self, path: str):
        """ファイルオープン処理のハンドラ"""
        try:
            # For large files, show progress
            file_size = os.path.getsize(path)
            if file_size > 1024 * 1024:  # 1MB+
                self.app_ui.show_progress_indicators("Reading file...")
                
                def progress_callback(progress):
                    self.app_ui.update_progress(progress, f"Reading file... {progress}%")
                
                def completion_callback(content):
                    self.app_ui.hide_progress_indicators()
                    if content is not None:
                        self.app_ui.add_or_focus_tab(path, content)
                    else:
                        self.page.snack_bar = ft.SnackBar(content=ft.Text("ファイルの読み込みに失敗しました。"))
                        self.page.snack_bar.open = True
                        self.page.update()
                
                def error_callback(error):
                    self.app_ui.hide_progress_indicators()
                    print(f"Error in async file read: {error}")
                    self.page.snack_bar = ft.SnackBar(content=ft.Text(f"ファイル読み込みエラー: {str(error)}"))
                    self.page.snack_bar.open = True
                    self.page.update()
                
                # Use async file reading for large files
                self.app_logic.read_file_async(
                    path,
                    progress_callback=progress_callback,
                    completion_callback=completion_callback,
                    error_callback=error_callback
                )
            else:
                # Small files read synchronously
                content = self.app_logic.read_file(path)
                if content is not None:
                    self.app_ui.add_or_focus_tab(path, content)
                else:
                    self.page.snack_bar = ft.SnackBar(content=ft.Text("ファイルの読み込みに失敗しました。"))
                    self.page.snack_bar.open = True
                    self.page.update()
                    
        except Exception as e:
            print(f"Error in handle_open_file: {e}")
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"ファイルオープンエラー: {str(e)}"))
            self.page.snack_bar.open = True
            self.page.update()


    def handle_analyze_tags(self, path: str, content: str):
        """AIタグ分析処理のハンドラ"""
        # すでに分析中なら、新しい分析を開始しない
        if self.is_analyzing:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("現在、別の分析を実行中です。"))
            self.page.snack_bar.open = True
            self.page.update()
            return

        if not path:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("先にファイルを一度保存してください。"))
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        # 分析開始
        self.is_analyzing = True
        self.cancel_event.clear()
        self.app_ui.start_analysis_view()
        self.app_ui.show_progress_indicators("Analyzing content with AI...", True)
        
        def progress_callback(progress):
            status_messages = {
                10: "Starting AI analysis...",
                50: "Processing content...",
                80: "Updating database...",
                100: "Analysis complete!"
            }
            status = next((msg for p, msg in status_messages.items() if progress >= p), f"Analyzing... {progress}%")
            self.app_ui.update_progress(progress, status)
        
        def completion_callback(result):
            self.is_analyzing = False
            self.app_ui.stop_analysis_view()
            
            success, message = result
            self.page.snack_bar = ft.SnackBar(content=ft.Text(message))
            self.page.snack_bar.open = True
            
            if success:
                try:
                    all_files = self.app_logic.get_file_list()
                    self.app_ui.update_file_list(all_files)
                except Exception as list_error:
                    print(f"Error updating file list after analysis: {list_error}")
            
            self.page.update()
        
        def error_callback(error):
            from log_utils import log_error
            self.is_analyzing = False
            self.app_ui.stop_analysis_view()
            log_error(f"Tag analysis failed for file {path}: {error}")
            print(f"Error in AI analysis: {error}")
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"分析エラー: {str(error)}"))
            self.page.snack_bar.open = True
            self.page.update()
        
        # Use async tag analysis
        self.app_logic.analyze_and_update_tags_async(
            path,
            content,
            progress_callback=progress_callback,
            completion_callback=completion_callback,
            error_callback=error_callback,
            cancel_event=self.cancel_event
        )
    
    def handle_ai_analysis(self, path: str, content: str, analysis_type: str):
        """AI分析処理のハンドラ（新しいモジュラーシステム用）"""
        # すでに分析中なら、新しい分析を開始しない
        if self.is_analyzing:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("現在、別の分析を実行中です。"))
            self.page.snack_bar.open = True
            self.page.update()
            return

        if not path:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("先にファイルを一度保存してください。"))
            self.page.snack_bar.open = True
            self.page.update()
            return

        # 分析開始
        self.is_analyzing = True
        self.cancel_event.clear()
        self.app_ui.start_analysis_view()

        # 分析タイプに応じたメッセージ
        analysis_messages = {
            "summarization": "Generating summary...",
            "tagging": "Extracting tags...",
            "sentiment_compass": "Analyzing growth dimensions..."
        }

        message = analysis_messages.get(analysis_type, "Processing AI analysis...")
        self.app_ui.show_progress_indicators(message, True)
        
        def progress_callback(progress):
            status_messages = {
                10: f"Starting {analysis_type} analysis...",
                50: "Processing content...",
                80: "Finalizing results...",
                100: "Analysis complete!"
            }
            status = next((msg for p, msg in status_messages.items() if progress >= p), f"Analyzing... {progress}%")
            self.app_ui.update_progress(progress, status)
        
        def completion_callback(result):
            self.is_analyzing = False
            self.app_ui.stop_analysis_view()
            
            success, message = result
            if success:
                # 結果を取得して表示
                analysis_result = self.app_logic.run_ai_analysis(content, analysis_type)
                if analysis_result["success"]:
                    # 結果表示ダイアログを表示
                    self.app_ui.show_ai_analysis_results(analysis_type, analysis_result["data"])
                else:
                    self.page.snack_bar = ft.SnackBar(content=ft.Text(analysis_result["message"]))
                    self.page.snack_bar.open = True
            else:
                self.page.snack_bar = ft.SnackBar(content=ft.Text(message))
                self.page.snack_bar.open = True
            
            self.page.update()
        
        def error_callback(error):
            from log_utils import log_error
            self.is_analyzing = False
            self.app_ui.stop_analysis_view()
            log_error(f"AI analysis ({analysis_type}) failed for file {path}: {error}")
            print(f"Error in AI analysis: {error}")
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"分析エラー: {str(error)}"))
            self.page.snack_bar.open = True
            self.page.update()
        
        # Use simplified approach for sentiment_compass to avoid async issues
        if analysis_type == "sentiment_compass":
            # Run synchronously and call completion callback directly
            try:
                if progress_callback:
                    progress_callback(50)

                result = self.app_logic.run_ai_analysis(content, analysis_type)

                if progress_callback:
                    progress_callback(100)

                # Call completion callback with the result
                if completion_callback:
                    completion_callback((result.get('success', False), result))

            except Exception as e:
                if error_callback:
                    error_callback(e)
        else:
            # Use async system for other analysis types
            self.app_logic.run_ai_analysis_async(
                path,
                content,
                analysis_type,
                progress_callback=progress_callback,
                completion_callback=completion_callback,
                error_callback=error_callback,
                cancel_event=self.cancel_event
            )

    def handle_refresh_files(self, show_archived=False):
        """ファイルリスト更新処理のハンドラ"""
        try:
            self.app_ui.show_loading_state("Refreshing file list...")
            
            self.app_logic.sync_database()
            all_files = self.app_logic.get_file_list(show_archived=show_archived)
            self.app_ui.update_file_list(all_files)
            
            self.app_ui.hide_loading_state()
            self.page.snack_bar = ft.SnackBar(content=ft.Text("ファイルリストを更新しました。"))
            self.page.snack_bar.open = True
            self.page.update()
        except Exception as e:
            self.app_ui.hide_loading_state()
            print(f"Error in handle_refresh_files: {e}")
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"ファイルリスト更新エラー: {str(e)}"))
            self.page.snack_bar.open = True
            self.page.update()

    def handle_update_tags(self, path: str, tags: list):
        """タグ手動更新処理のハンドラ"""
        try:
            success, message = self.app_logic.update_tags(path, tags)
            self.page.snack_bar = ft.SnackBar(content=ft.Text(message))
            self.page.snack_bar.open = True
            
            if success:
                all_files = self.app_logic.get_file_list()
                self.app_ui.update_file_list(all_files)

            self.page.update()
        except Exception as e:
            print(f"Error in handle_update_tags: {e}")
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"タグ更新エラー: {str(e)}"))
            self.page.snack_bar.open = True
            self.page.update()

    def handle_cancel_tags(self):
        """分析キャンセル処理のハンドラ"""
        if self.is_analyzing:
            print("Cancellation requested by user.")
            self.cancel_event.set()
            self.app_ui.update_progress(0, "Cancelling operation...")

    def handle_rename_file(self, old_path: str, new_name: str):
        """ファイル名変更処理のハンドラ"""
        try:
            success, message, old_path, new_path = self.app_logic.rename_file(old_path, new_name)
            
            self.page.snack_bar = ft.SnackBar(content=ft.Text(message))
            self.page.snack_bar.open = True
            
            if success:
                # ファイルリストを更新
                all_files = self.app_logic.get_file_list()
                self.app_ui.update_file_list(all_files)
                # 開いているタブがあれば、そちらも更新
                self.app_ui.update_tab_after_rename(old_path, new_path)

            self.page.update()
        except Exception as e:
            print(f"Error in handle_rename_file: {e}")
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"ファイル名変更エラー: {str(e)}"))
            self.page.snack_bar.open = True
            self.page.update()

    def handle_close_tab(self, tab_to_close: ft.Tab):
        """タブクローズ処理のハンドラ"""
        try:
            path = tab_to_close.content.data
            content = tab_to_close.content.value
            
            # ファイルを保存
            self.handle_save_file(path, content)
            
            # タブをリストから削除
            self.app_ui.tabs.tabs.remove(tab_to_close)
            
            # 最後のタブが閉じられたら、Welcome画面を出す
            if not self.app_ui.tabs.tabs:
                self.app_ui.tabs.tabs.append(
                    ft.Tab(text="Welcome", content=ft.Column(
                        [ft.Text("← サイドバーからファイルを選択してください", size=20)],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ))
                )
            
            self.page.update()
        except Exception as e:
            print(f"Error in handle_close_tab: {e}")
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"タブクローズエラー: {str(e)}"))
            self.page.snack_bar.open = True
            self.page.update()

    def handle_create_file(self, filename: str):
        """新規ファイル作成処理のハンドラ"""
        try:
            success, message = self.app_logic.create_new_file(filename)
            
            self.page.snack_bar = ft.SnackBar(content=ft.Text(message))
            self.page.snack_bar.open = True
            
            if success:
                # ファイルリストを更新
                all_files = self.app_logic.get_file_list()
                self.app_ui.update_file_list(all_files)
                
                # 新しく作成したファイルを自動的に開く
                import config
                full_path = os.path.join(config.NOTES_DIR, filename if filename.endswith('.md') else filename + '.md')
                self.handle_open_file(full_path)
            
            self.page.update()
        except Exception as e:
            print(f"Error in handle_create_file: {e}")
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"ファイル作成エラー: {str(e)}"))
            self.page.snack_bar.open = True
            self.page.update()

    def show_error_dialog(self, title: str, message: str):
        """エラーダイアログを表示する"""
        def close_dialog(e):
            if hasattr(self, 'error_dialog') and self.error_dialog in self.page.overlay:
                self.page.overlay.remove(self.error_dialog)
                self.page.update()

        self.error_dialog = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton("OK", on_click=close_dialog)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(self.error_dialog)
        self.error_dialog.open = True
        self.page.update()

    def handle_archive_file(self, file_path: str):
        """ファイルアーカイブ処理のハンドラ"""
        try:
            print(f"Handler: archive_file called with path: {file_path}")  # Debug log
            # ファイルの現在のステータスを確認
            from tinydb import Query
            File = Query()
            file_record = self.app_logic.db.get(File.path == file_path)
            
            if not file_record:
                self.page.snack_bar = ft.SnackBar(content=ft.Text("ファイルが見つかりません。"))
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            current_status = file_record.get('status', 'active')
            
            if current_status == 'archived':
                # アンアーカイブ
                success, message = self.app_logic.unarchive_file(file_path)
                operation_name = "アンアーカイブ"
            else:
                # アーカイブ
                success, message = self.app_logic.archive_file(file_path)
                operation_name = "アーカイブ"

            # Show different UI based on success/failure
            if success:
                # Success: Use SnackBar for brief confirmation
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(message),
                    bgcolor=ft.Colors.GREEN_100
                )
                self.page.snack_bar.open = True
            else:
                # Error: Use AlertDialog for more visible notification
                self.show_error_dialog(f"{operation_name}エラー", message)
            
            if success:
                # ファイルリストを更新（アクティブファイルのみ）
                all_files = self.app_logic.get_file_list(show_archived=False)
                self.app_ui.update_file_list(all_files)
                
                # アーカイブされたファイルが現在開いているタブにある場合は閉じる
                if current_status != 'archived':  # アーカイブ操作の場合
                    for i, tab in enumerate(self.app_ui.tabs.tabs):
                        if hasattr(tab.content, 'data') and tab.content.data == file_path:
                            self.app_ui.tabs.tabs.remove(tab)
                            if not self.app_ui.tabs.tabs:
                                self.app_ui.tabs.tabs.append(
                                    ft.Tab(text="Welcome", content=ft.Column(
                                        [ft.Text("← サイドバーからファイルを選択してください", size=20)],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    ))
                                )
                            break
            
            self.page.update()
        except Exception as e:
            print(f"Error in handle_archive_file: {e}")
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"アーカイブ処理エラー: {str(e)}"))
            self.page.snack_bar.open = True
            self.page.update()


    def handle_delete_file(self, file_path: str):
        """ファイル削除処理のハンドラ"""
        try:
            success, message = self.app_logic.delete_file(file_path)

            self.page.snack_bar = ft.SnackBar(content=ft.Text(message))
            self.page.snack_bar.open = True

            if success:
                # ファイルリストを更新
                try:
                    all_files = self.app_logic.get_file_list(show_archived=False)
                    self.app_ui.update_file_list(all_files)
                except Exception as list_error:
                    print(f"Error updating file list after delete: {list_error}")

                # 削除されたファイルが現在開いているタブにある場合は閉じる
                try:
                    for i, tab in enumerate(self.app_ui.tabs.tabs):
                        if hasattr(tab.content, 'data') and tab.content.data == file_path:
                            self.app_ui.tabs.tabs.remove(tab)
                            if not self.app_ui.tabs.tabs:
                                self.app_ui.tabs.tabs.append(
                                    ft.Tab(text="Welcome", content=ft.Column(
                                        [ft.Text("← サイドバーからファイルを選択してください", size=20)],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    ))
                                )
                            break
                except Exception as tab_error:
                    print(f"Error closing tab after delete: {tab_error}")

            self.page.update()

        except Exception as e:
            print(f"Error in handle_delete_file: {e}")
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"削除処理エラー: {str(e)}"))
            self.page.snack_bar.open = True
            self.page.update()

    # ========== AUTOMATION HANDLERS ==========

    def handle_run_automation(self, task_type: str):
        """自動化タスク実行のハンドラ"""
        # すでに分析中なら、新しいタスクを開始しない
        if self.is_analyzing:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("現在、別の処理を実行中です。"))
            self.page.snack_bar.open = True
            self.page.update()
            return

        self.is_analyzing = True
        self.cancel_event.clear()

        # タスクタイプに応じたメッセージを設定
        task_messages = {
            "batch_tag_untagged": "未タグファイルを自動タグ付け中...",
            "batch_summarize": "ファイルの要約を一括生成中...",
            "batch_tag_archived": "アーカイブファイルを自動タグ付け中...",
            "batch_summarize_archived": "アーカイブファイルの要約を一括生成中...",
        }

        initial_message = task_messages.get(task_type, "自動化タスクを実行中...")

        # UIの自動化ビューを開始
        self.app_ui.start_automation_view()
        self.app_ui.show_progress_indicators(initial_message, True)

        def progress_callback(progress, message):
            """進捗コールバック - プログレスバーとメッセージを更新"""
            self.app_ui.update_progress(progress, message)

        def completion_callback(result):
            """完了コールバック - 結果を表示し、UIを復元"""
            self.is_analyzing = False
            self.app_ui.stop_automation_view()

            # バッチ処理結果を表示
            self.app_ui.show_batch_results(result)

            # 成功時はファイルリストを更新
            if result.get("success", False) and result.get("success_count", 0) > 0:
                try:
                    all_files = self.app_logic.get_file_list()
                    self.app_ui.update_file_list(all_files)
                except Exception as list_error:
                    print(f"Error updating file list after automation: {list_error}")

            self.page.update()

        def error_callback(error):
            """エラーコールバック - エラーを表示し、UIを復元"""
            from log_utils import log_error
            self.is_analyzing = False
            self.app_ui.stop_automation_view()
            log_error(f"Batch automation failed for task_type '{task_type}': {error}")
            print(f"Error in automation task: {error}")
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"自動化タスクエラー: {str(error)}"))
            self.page.snack_bar.open = True
            self.page.update()

        # バッチ処理を非同期で実行
        self.app_logic.run_batch_processing_async(
            task_type,
            progress_callback=progress_callback,
            completion_callback=completion_callback,
            error_callback=error_callback,
            cancel_event=self.cancel_event
        )

    def handle_cancel_automation(self):
        """自動化タスクキャンセル処理のハンドラ"""
        if self.is_analyzing:
            print("Automation cancellation requested by user.")
            self.cancel_event.set()
            self.app_ui.update_progress(0, "Cancelling automation...")

    def handle_get_automation_preview(self, task_type: str):
        """自動化タスクのプレビュー情報取得ハンドラ"""
        try:
            # タスクタイプに応じて対象ファイルを取得
            if task_type == "batch_tag_untagged":
                target_files = self.app_logic.get_untagged_files()
                task_name = "未タグファイルの自動タグ付け"
            elif task_type == "batch_summarize":
                target_files = self.app_logic.get_files_without_analysis("summarization")
                task_name = "ファイル要約の一括生成"
            elif task_type == "batch_tag_archived":
                target_files = self.app_logic.get_untagged_archived_files()
                task_name = "アーカイブファイルの自動タグ付け"
            elif task_type == "batch_summarize_archived":
                target_files = self.app_logic.get_archived_files_without_analysis("summarization")
                task_name = "アーカイブファイル要約の一括生成"
            else:
                return {
                    "task_name": "不明なタスク",
                    "file_count": 0,
                    "file_list": [],
                    "message": "不明なタスクタイプです。"
                }

            file_names = [f.get('title', 'Unknown') for f in target_files]
            file_count = len(target_files)

            if file_count == 0:
                message = f"{task_name}の対象ファイルはありません。"
            else:
                message = f"{file_count}個のファイルが処理対象です。"

            return {
                "task_name": task_name,
                "file_count": file_count,
                "file_list": file_names,
                "message": message
            }

        except Exception as e:
            print(f"Error getting automation preview: {e}")
            return {
                "task_name": "エラー",
                "file_count": 0,
                "file_list": [],
                "message": f"プレビュー取得エラー: {str(e)}"
            }

    # ========== CHAT HANDLERS ==========

    def handle_send_chat_message(self, user_message: str, alice_response: str, image_path: str = None):
        """チャットメッセージ送受信のハンドラ"""
        try:
            from logger import log_chat

            # ログにチャットメッセージを記録
            log_chat(f"User: {user_message[:100]}{'...' if len(user_message) > 100 else ''}")
            if image_path:
                log_chat(f"  Image: {image_path}")
            log_chat(f"Alice: {alice_response[:100]}{'...' if len(alice_response) > 100 else ''}")

            # チャットログファイルに保存
            self._save_chat_log(user_message, alice_response, image_path)

        except Exception as e:
            from logger import log_error
            log_error(e, "handle_send_chat_message")
            print(f"Error in handle_send_chat_message: {e}")

    def _save_chat_log(self, user_message: str, alice_response: str, image_path: str = None):
        """チャットログをファイルに保存する"""
        try:
            import os
            from datetime import datetime
            import config
            from date_utils import get_current_log_date

            # チャットログディレクトリを作成
            chat_logs_dir = getattr(config, 'CHAT_LOGS_DIR', os.path.join(config.PROJECT_ROOT, "data", "chat_logs"))
            os.makedirs(chat_logs_dir, exist_ok=True)

            # 3AM ルールに基づいてログ日付を決定
            today = get_current_log_date()
            log_file_path = os.path.join(chat_logs_dir, f"{today}.md")

            # ログエントリを作成
            timestamp = datetime.now().strftime("%H:%M:%S")
            image_log = f"\n画像: {image_path}" if image_path else ""
            log_entry = f"""
## {timestamp}

**ご主人様:**
{user_message}{image_log}

**ありす:**
{alice_response}

---------

"""

            # ファイルに追記（リトライ機構付き）
            self._write_chat_log_with_retry(log_file_path, log_entry, today)

            from logger import log_chat
            log_chat(f"Chat log saved to: {log_file_path}")

        except Exception as e:
            from logger import log_error
            log_error(e, "save_chat_log")
            print(f"Failed to save chat log: {e}")

    def _write_chat_log_with_retry(self, log_file_path: str, log_entry: str, today: str, max_retries: int = 3):
        """リトライ機構付きでチャットログを書き込む

        Args:
            log_file_path (str): ログファイルのパス
            log_entry (str): 書き込むログエントリ
            today (str): 今日の日付文字列
            max_retries (int): 最大リトライ回数
        """
        import time

        for attempt in range(max_retries):
            try:
                # ファイルが存在するかチェック
                file_exists = os.path.exists(log_file_path)
                file_size = os.path.getsize(log_file_path) if file_exists else 0

                # ファイルを追記モードで開く（共有アクセス対応）
                with open(log_file_path, 'a', encoding='utf-8', buffering=1) as f:
                    # ファイルが新規作成の場合はヘッダーを追加
                    if file_size == 0:
                        f.write(f"# ありすとの対話ログ - {today}\n\n")

                    # ログエントリを書き込み
                    f.write(log_entry)
                    f.flush()  # バッファを強制的に書き込み

                # 成功したらリターン
                return

            except PermissionError as pe:
                if attempt < max_retries - 1:
                    # ファイルがロックされている場合、少し待ってリトライ
                    print(f"Chat log file is locked, retrying in {0.5 * (attempt + 1)}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(0.5 * (attempt + 1))  # 指数バックオフ
                else:
                    # 最後の試行でも失敗した場合、代替手段を試行
                    self._write_to_backup_log(log_entry, today)
                    raise pe

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Chat log write error, retrying... (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(0.5 * (attempt + 1))
                else:
                    # 最後の試行でも失敗した場合、代替手段を試行
                    self._write_to_backup_log(log_entry, today)
                    raise e

    def _write_to_backup_log(self, log_entry: str, today: str):
        """バックアップログファイルに書き込む

        Args:
            log_entry (str): 書き込むログエントリ
            today (str): 今日の日付文字列
        """
        try:
            import config
            chat_logs_dir = getattr(config, 'CHAT_LOGS_DIR', os.path.join(config.PROJECT_ROOT, "data", "chat_logs"))
            backup_log_path = os.path.join(chat_logs_dir, f"{today}_backup.md")

            with open(backup_log_path, 'a', encoding='utf-8', buffering=1) as f:
                if os.path.getsize(backup_log_path) == 0:
                    f.write(f"# ありすとの対話ログ (バックアップ) - {today}\n\n")
                f.write(log_entry)
                f.flush()

            print(f"Chat log written to backup file: {backup_log_path}")

        except Exception as backup_error:
            print(f"Failed to write to backup log: {backup_error}")
            # 最終手段：標準出力にログを出力
            print(f"CHAT LOG ENTRY:\n{log_entry}")

    # ========== MEMORY CREATION HANDLERS ==========

    def _init_memory_manager(self):
        """Initialize the memory creation manager."""
        try:
            import config
            self.memory_manager = MemoryCreationManager(config)
            print("Memory Creation Manager initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Memory Creation Manager: {e}")
            self.memory_manager = None

    def handle_create_memory(self):
        """記憶を作成するハンドラ"""
        if not self.memory_manager:
            self.app_ui.show_memory_error("記憶作成マネージャーが初期化されていません。")
            return

        if not self.memory_manager.is_available():
            self.app_ui.show_memory_error("記憶作成サービスが利用できません。API設定を確認してください。")
            return

        # Get selected date from UI
        target_date = self.app_ui.get_selected_date()

        # Show progress
        self.app_ui.show_memory_progress()

        # For simplicity and compatibility, run synchronously but with progress indication
        try:
            # Brief delay to let progress indicator show
            import time
            time.sleep(0.1)
            self.page.update()

            success, result = self.memory_manager.create_memory(target_date)

            self.app_ui.hide_memory_progress()

            if success:
                self.app_ui.update_memory_preview(result)
            else:
                self.app_ui.show_memory_error(result)

        except Exception as e:
            self.app_ui.hide_memory_progress()
            self.app_ui.show_memory_error(f"予期しないエラーが発生しました: {str(e)}")
            print(f"Exception in handle_create_memory: {e}")

    def handle_save_memory(self):
        """記憶を保存するハンドラ"""
        try:
            # Get the edited memory content and selected date from UI
            memory_content = self.app_ui.get_memory_edit_content()
            target_date = self.app_ui.get_selected_date()

            if not memory_content or not memory_content.strip():
                self.app_ui.show_memory_error("保存する記憶の内容が空です。")
                return

            # Construct memory file path
            import config
            memories_dir = getattr(config, 'MEMORIES_DIR', '')
            if not memories_dir:
                self.app_ui.show_memory_error("記憶保存ディレクトリが設定されていません。")
                return

            # Ensure memories directory exists
            os.makedirs(memories_dir, exist_ok=True)

            # Create filename in format memory-YY.MM.DD.md
            from datetime import datetime
            date_obj = datetime.strptime(target_date, "%Y-%m-%d")
            memory_filename = f"memory-{date_obj.strftime('%y.%m.%d')}.md"
            memory_file_path = os.path.join(memories_dir, memory_filename)

            # Use app_logic to save the file (for security and consistency)
            self.app_logic.save_file(memory_file_path, memory_content)

            # Show success message
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"記憶が保存されました: {memory_filename}"),
                bgcolor=ft.Colors.GREEN,
                duration=3000
            )
            self.page.snack_bar.open = True
            self.page.update()

            # Refresh file list to show the new memory file
            self.handle_refresh_files()

        except Exception as e:
            self.app_ui.show_memory_error(f"記憶の保存中にエラーが発生しました: {str(e)}")
            print(f"Error saving memory: {e}")