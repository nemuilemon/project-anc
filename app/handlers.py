"""Event handlers for Project A.N.C.

This module contains all event handler functions that were previously
in main.py, implementing separation of concerns and improving code
organization.
"""

import flet as ft
import os
from threading import Thread, Event
from logic import AppLogic


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

    def handle_save_file(self, path: str, content: str):
        """ファイル保存処理のハンドラ"""
        try:
            # For large files, use async saving
            content_size = len(content.encode('utf-8'))
            if content_size > 1024 * 1024:  # 1MB+
                self.app_ui.show_progress_indicators("Saving file...")
                
                def progress_callback(progress):
                    self.app_ui.update_progress(progress, f"Saving file... {progress}%")
                
                def completion_callback(result):
                    self.app_ui.hide_progress_indicators()
                    success, title = result
                    if success:
                        self.page.snack_bar = ft.SnackBar(content=ft.Text(f"『{title}』を保存しました。"))
                        self.page.snack_bar.open = True
                        
                        try:
                            all_files = self.app_logic.get_file_list()
                            self.app_ui.update_file_list(all_files)
                        except Exception as list_error:
                            print(f"Error updating file list after save: {list_error}")
                        
                        self.page.update()
                    else:
                        self.page.snack_bar = ft.SnackBar(content=ft.Text("ファイルの保存に失敗しました。"))
                        self.page.snack_bar.open = True
                        self.page.update()
                
                def error_callback(error):
                    self.app_ui.hide_progress_indicators()
                    print(f"Error in async file save: {error}")
                    self.page.snack_bar = ft.SnackBar(content=ft.Text(f"保存エラー: {str(error)}"))
                    self.page.snack_bar.open = True
                    self.page.update()
                
                # Use async file saving for large files
                self.app_logic.save_file_async(
                    path, 
                    content,
                    progress_callback=progress_callback,
                    completion_callback=completion_callback,
                    error_callback=error_callback
                )
            else:
                # Small files save synchronously
                success, title = self.app_logic.save_file(path, content)
                if success:
                    self.page.snack_bar = ft.SnackBar(content=ft.Text(f"『{title}』を保存しました。"))
                    self.page.snack_bar.open = True
                    
                    try:
                        all_files = self.app_logic.get_file_list()
                        self.app_ui.update_file_list(all_files)
                    except Exception as list_error:
                        print(f"Error updating file list after save: {list_error}")
                    
                    self.page.update()
                else:
                    self.page.snack_bar = ft.SnackBar(content=ft.Text("ファイルの保存に失敗しました。"))
                    self.page.snack_bar.open = True
                    self.page.update()
                    
        except Exception as e:
            print(f"Error in handle_save_file: {e}")
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"保存処理エラー: {str(e)}"))
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