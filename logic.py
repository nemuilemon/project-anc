# logic.py
import os
import time
from tinydb import Query
import config
from security import sanitize_filename, validate_file_path, safe_file_operation, create_safe_directory, SecurityError
from async_operations import async_manager, ProgressTracker, run_with_progress

# Import new AI analysis system
from ai_analysis import AIAnalysisManager, TaggingPlugin, SummarizationPlugin, SentimentPlugin

class AppLogic:
    def __init__(self, db):
        self.db = db
        # Define allowed directories for security validation
        self.allowed_dirs = [config.NOTES_DIR, config.ARCHIVE_DIR]
        
        # Initialize AI analysis system
        self.ai_manager = AIAnalysisManager()
        self._setup_ai_plugins()
        
        self.sync_database()
    
    def _setup_ai_plugins(self):
        """Initialize and register AI analysis plugins."""
        try:
            # Register core analysis plugins
            self.ai_manager.register_plugin(TaggingPlugin())
            self.ai_manager.register_plugin(SummarizationPlugin())
            self.ai_manager.register_plugin(SentimentPlugin())
            
            print(f"Registered {len(self.ai_manager.get_available_plugins())} AI analysis plugins")
        except Exception as e:
            print(f"Error setting up AI plugins: {e}")

    def get_file_list(self, show_archived=False):
        """ファイルリストを取得する。
        
        Args:
            show_archived (bool): Trueの場合、アーカイブされたファイルも含める。
                                 デフォルトはFalse（アクティブなファイルのみ）。
        
        Returns:
            list: ファイル情報の辞書のリスト。各辞書は以下のキーを含む：
                - title (str): ファイル名
                - path (str): ファイルの絶対パス
                - tags (list): タグのリスト
                - status (str): ファイル状態 ('active' または 'archived')
                - order_index (int): 表示順序（昇順でソート）
        
        Note:
            レガシーファイルでstatusやorder_indexが未設定の場合、
            それぞれ'active'と0として扱われる。
        """
        if show_archived:
            # すべてのファイルを返す
            files = self.db.all()
        else:
            # アクティブなファイルのみ返す
            File = Query()
            # statusフィールドがないレガシーファイルはアクティブとして扱う
            files = self.db.search((File.status == 'active') | (~File.status.exists()))
        
        # order_indexでソート（order_indexがないファイルは0として扱う）
        files.sort(key=lambda x: x.get('order_index', 0))
        return files

    # 2. データベース同期機能：フォルダとDBを同期する新機能
    def sync_database(self):
        """ファイルシステムとデータベースを同期する。
        
        NOTES_DIR内の.mdファイルをスキャンし、データベースに登録されていない
        新しいファイルを自動的に追加する。既存のDBレコードは変更しない。
        
        Raises:
            FileNotFoundError: NOTES_DIRが存在しない場合は処理をスキップ
        
        Note:
            新しいファイルのorder_indexは、既存の最大値+1が設定される。
        """
        # フォルダにある実際のファイル一覧を取得
        try:
            actual_files = {os.path.join(config.NOTES_DIR, f) for f in os.listdir(config.NOTES_DIR) if f.endswith('.md')}
        except FileNotFoundError:
            # NOTES_DIRが存在しない場合は何もしない
            return
            
        # データベースに登録されているファイル一覧を取得
        db_files = {doc['path'] for doc in self.db.all()}
        
        # フォルダにはあるけど、DBにないファイル（＝新しいファイル）を見つける
        new_files = actual_files - db_files
        
        # 新しいファイルをDBに初期登録する（order_indexは最大値+1）
        existing_max_order = 0
        all_records = self.db.all()
        if all_records:
            existing_max_order = max([doc.get('order_index', 0) for doc in all_records])
        
        for i, path in enumerate(new_files):
            title = os.path.basename(path)
            order_index = existing_max_order + i + 1
            self.db.insert({'title': title, 'path': path, 'tags': [], 'status': 'active', 'order_index': order_index})
            print(f"New file found and added to DB: {title} (order: {order_index})")

    # 3. 手動タグ更新機能：タグ情報を更新する新機能
    def update_tags(self, path, tags):
        """指定されたファイルのタグを手動で更新する。
        
        Args:
            path (str): 更新対象ファイルの絶対パス
            tags (list): 新しいタグのリスト
        
        Returns:
            tuple: (成功フラグ, メッセージ)
                - bool: 更新が成功した場合True
                - str: 結果メッセージ（成功/失敗）
        """
        try:
            File = Query()
            self.db.update({'tags': tags}, File.path == path)
            return True, "タグを更新しました。"
        except Exception as e:
            print(f"Error updating tags: {e}")
            return False, "タグの更新中にエラーが発生しました。"

    def read_file(self, path):
        """ファイルの内容を読み取る。
        
        Args:
            path (str): 読み取り対象ファイルの絶対パス
        
        Returns:
            str or None: ファイルの内容（UTF-8）。エラーの場合はNone。
        
        Note:
            セキュリティ検証を行い、許可されたディレクトリ内のファイルのみ読み取る。
            ファイルが存在しない、アクセス権限がない等の場合はNoneを返し、
            エラー内容はコンソールに出力される。
        """
        try:
            success, message, content = safe_file_operation('read', path, allowed_dirs=self.allowed_dirs)
            if success:
                return content
            else:
                print(f"Error reading file: {message}")
                return None
        except Exception as e:
            print(f"Unexpected error reading file: {e}")
            return None

    def save_file(self, path, content):
        """ファイル内容をディスクに保存し、データベースレコードを更新する。
        
        Args:
            path (str): 保存先ファイルの絶対パス
            content (str): 保存するテキスト内容
        
        Returns:
            tuple: (成功フラグ, ファイル名またはNone)
                - bool: 保存が成功した場合True
                - str or None: 成功時はファイル名、失敗時はNone
        
        Note:
            セキュリティ検証を行い、トランザクション的な操作でファイル保存とDB更新を実行する。
            新しいファイルの場合は自動的にDBレコードを作成し、
            既存ファイルの場合は既存の情報（タグ、ステータス等）を保持する。
        """
        # Transaction state tracking
        file_created = False
        db_updated = False
        
        try:
            # Security validation
            success, message, validated_path = validate_file_path(path, self.allowed_dirs)
            if not success:
                print(f"Security validation failed: {message}")
                return False, None
            
            path = validated_path
            title = os.path.basename(path)
            
            # Get existing document before making changes
            File = Query()
            doc = self.db.get(File.path == path)
            existing_tags = doc.get('tags', []) if doc else []
            existing_status = doc.get('status', 'active') if doc else 'active'
            existing_order_index = doc.get('order_index', 0) if doc else 0
            
            # Set order_index for new files
            if not doc:
                all_records = self.db.all()
                if all_records:
                    existing_order_index = max([d.get('order_index', 0) for d in all_records]) + 1
                else:
                    existing_order_index = 1
            
            # Create backup of existing file if it exists
            backup_content = None
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        backup_content = f.read()
                except:
                    pass
            
            # Perform file write
            success, write_message, _ = safe_file_operation('write', path, content, self.allowed_dirs)
            if not success:
                print(f"File write failed: {write_message}")
                return False, None
            
            file_created = True
            
            # Update database
            try:
                self.db.upsert(
                    {'title': title, 'path': path, 'tags': existing_tags, 'status': existing_status, 'order_index': existing_order_index},
                    File.path == path
                )
                db_updated = True
                return True, title
                
            except Exception as db_error:
                # Rollback file write if database update fails
                if backup_content is not None:
                    try:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(backup_content)
                    except:
                        pass
                else:
                    try:
                        os.remove(path)
                    except:
                        pass
                
                print(f"Database update failed, file rolled back: {db_error}")
                return False, None
                
        except Exception as e:
            # Attempt rollback if something went wrong
            if file_created and not db_updated:
                try:
                    os.remove(path)
                except:
                    pass
            
            print(f"Error saving file: {e}")
            return False, None

    # analyze_and_update_tags関数を新しいAI分析システムで置き換え
    def analyze_and_update_tags(self, path, content, cancel_event=None):
        """AI分析システムを使用してファイル内容を分析し、自動的にタグを生成・更新する。
        
        Args:
            path (str): 分析対象ファイルの絶対パス
            content (str): 分析するテキスト内容
            cancel_event (threading.Event, optional): 処理をキャンセルするためのイベント
        
        Returns:
            tuple: (成功フラグ, メッセージ)
                - bool: 分析・更新が成功した場合True
                - str: 結果メッセージ（成功/失敗/キャンセル）
        
        Note:
            新しいモジュラーAI分析システムを使用し、プラグインベースでタグ分析を実行。
        """
        try:
            # Use new AI analysis system
            result = self.ai_manager.analyze(content, "tagging")
            
            if not result.success:
                return False, result.message
            
            # Extract tags from result
            tags = result.data.get("tags", [])
            
            # Update database with new tags
            File = Query()
            self.db.update({'tags': tags}, File.path == path)
            return True, result.message
            
        except Exception as e:
            print(f"Error analyzing and updating tags: {e}")
            return False, "タグの更新中にエラーが発生しました。"


    def run_ai_analysis(self, content: str, analysis_type: str, **kwargs) -> dict:
        """新しいAI分析システムを使用してコンテンツを分析する。
        
        Args:
            content (str): 分析対象のテキスト内容
            analysis_type (str): 分析タイプ ("tagging", "summarization", "sentiment")
            **kwargs: 分析タイプ固有のパラメータ
        
        Returns:
            dict: 分析結果の辞書 (success, data, message, processing_time等)
        
        Note:
            新しいモジュラーAI分析システムのエントリーポイント。
            各種AI分析プラグインへの統一インターフェースを提供。
        """
        try:
            result = self.ai_manager.analyze(content, analysis_type, **kwargs)
            return {
                "success": result.success,
                "data": result.data,
                "message": result.message,
                "processing_time": result.processing_time,
                "plugin_name": result.plugin_name,
                "metadata": result.metadata
            }
        except Exception as e:
            from log_utils import log_error
            log_error(f"AI analysis failed for analysis_type '{analysis_type}': {e}")
            print(f"Error in AI analysis: {e}")
            return {
                "success": False,
                "data": {},
                "message": f"分析中にエラーが発生しました: {str(e)}",
                "processing_time": 0,
                "plugin_name": analysis_type,
                "metadata": {"error": str(e)}
            }
    
    def get_available_ai_functions(self) -> list:
        """利用可能なAI分析機能の一覧を取得する。
        
        Returns:
            list: AI分析プラグインの情報リスト
        """
        functions = []
        for plugin_name in self.ai_manager.get_available_plugins():
            plugin_info = self.ai_manager.get_plugin_info(plugin_name)
            if plugin_info:
                functions.append(plugin_info)
        return functions

    def create_new_file(self, filename):
        """新しい空のMarkdownファイルを作成し、データベースに登録する。
        
        Args:
            filename (str): 作成するファイル名。拡張子(.md)は自動付与される。
        
        Returns:
            tuple: (成功フラグ, メッセージ)
                - bool: 作成が成功した場合True
                - str: 結果メッセージ（成功/失敗理由）
        
        Raises:
            既存ファイルと同名の場合は失敗を返す（上書きしない）
        
        Note:
            セキュリティ検証とファイル名のサニタイゼーションを行い、
            作成されたファイルは自動的に最後の順序（最大order_index + 1）で
            データベースに登録される。
        """
        # Transaction state tracking
        file_created = False
        
        try:
            # 1. ファイル名の検証とサニタイゼーション
            if not filename or not filename.strip():
                return False, "ファイル名を入力してください。"
            
            try:
                sanitized_filename = sanitize_filename(filename.strip())
            except SecurityError as e:
                return False, f"ファイル名が無効です: {str(e)}"
            
            # 2. 拡張子の確認・付与
            if not sanitized_filename.endswith('.md'):
                sanitized_filename += '.md'
            
            # 3. フルパスを生成
            full_path = os.path.join(config.NOTES_DIR, sanitized_filename)
            
            # 4. パス検証
            success, message, validated_path = validate_file_path(full_path, self.allowed_dirs)
            if not success:
                return False, f"パス検証失敗: {message}"
            
            full_path = validated_path
            
            # 5. ディレクトリ作成
            dir_success, dir_message = create_safe_directory(config.NOTES_DIR)
            if not dir_success:
                return False, f"ディレクトリ作成失敗: {dir_message}"
            
            # 6. ファイル名の衝突チェック
            if os.path.exists(full_path):
                return False, "同じ名前のファイルが既に存在します。"
            
            # 7. データベースの状態を事前に確認
            existing_max_order = 0
            all_records = self.db.all()
            if all_records:
                existing_max_order = max([doc.get('order_index', 0) for doc in all_records])
            
            order_index = existing_max_order + 1
            
            # 8. ファイル作成
            success, write_message, _ = safe_file_operation('write', full_path, "", self.allowed_dirs)
            if not success:
                return False, f"ファイル作成失敗: {write_message}"
            
            file_created = True
            
            # 9. データベースにレコードを追加
            try:
                self.db.insert({
                    'title': sanitized_filename,
                    'path': full_path,
                    'tags': [],
                    'status': 'active',
                    'order_index': order_index
                })
                
                return True, f"新しいファイル「{sanitized_filename}」を作成しました。"
                
            except Exception as db_error:
                # データベース挿入失敗時のファイル削除
                if file_created:
                    try:
                        os.remove(full_path)
                    except:
                        pass
                
                print(f"Database insertion failed: {db_error}")
                return False, "データベースへの登録中にエラーが発生しました。"
            
        except Exception as e:
            # 一般的なエラー時のクリーンアップ
            if file_created:
                try:
                    os.remove(full_path)
                except:
                    pass
            
            print(f"Error creating file: {e}")
            return False, "ファイルの作成中にエラーが発生しました。"

    def rename_file(self, old_path, new_name):
        """ファイル名を変更し、DBのレコードも更新する"""
        # Transaction state tracking
        file_renamed = False
        
        try:
            # 1. 入力検証とサニタイゼーション
            if not new_name or not new_name.strip():
                return False, "新しいファイル名を入力してください。", None, None
            
            try:
                sanitized_name = sanitize_filename(new_name.strip())
            except SecurityError as e:
                return False, f"ファイル名が無効です: {str(e)}", None, None
            
            # 2. 拡張子の確認・付与
            if not sanitized_name.endswith('.md'):
                sanitized_name += '.md'
            
            # 3. パスの検証
            success, message, validated_old_path = validate_file_path(old_path, self.allowed_dirs)
            if not success:
                return False, f"元ファイルのパス検証失敗: {message}", None, None
            
            old_path = validated_old_path
            
            # 4. 新しいフルパスを生成
            new_path = os.path.join(os.path.dirname(old_path), sanitized_name)
            
            # 5. 新しいパスの検証
            success, message, validated_new_path = validate_file_path(new_path, self.allowed_dirs)
            if not success:
                return False, f"新ファイルのパス検証失敗: {message}", None, None
            
            new_path = validated_new_path
            
            # 6. ファイル存在確認
            if not os.path.exists(old_path):
                return False, "変更対象のファイルが見つかりません。", None, None
            
            # 7. ファイル名の衝突チェック
            if os.path.exists(new_path):
                return False, "同じ名前のファイルが既に存在します。", None, None
            
            # 8. データベースの事前確認
            File = Query()
            existing_record = self.db.get(File.path == old_path)
            if not existing_record:
                return False, "データベースにファイル記録が見つかりません。", None, None
            
            # 9. ファイルシステム上で名前を変更
            try:
                os.rename(old_path, new_path)
                file_renamed = True
            except PermissionError:
                return False, "ファイルの変更権限がありません。", None, None
            except OSError as e:
                return False, f"ファイル名変更エラー: {str(e)}", None, None
            
            # 10. データベースのレコードを更新
            try:
                new_title = os.path.basename(new_path)
                updated_count = self.db.update(
                    {'title': new_title, 'path': new_path},
                    File.path == old_path
                )
                
                if updated_count == 0:
                    # データベース更新失敗時のロールバック
                    os.rename(new_path, old_path)
                    return False, "データベースの更新に失敗しました。", None, None
                
                return True, f"ファイル名を「{new_title}」に変更しました。", old_path, new_path
                
            except Exception as db_error:
                # データベース更新失敗時のロールバック
                if file_renamed:
                    try:
                        os.rename(new_path, old_path)
                    except:
                        pass
                
                print(f"Database update failed during rename: {db_error}")
                return False, "データベース更新中にエラーが発生しました。", None, None
                
        except Exception as e:
            # 一般的なエラー時のロールバック
            if file_renamed:
                try:
                    os.rename(new_path, old_path)
                except:
                    pass
            
            print(f"Error renaming file: {e}")
            return False, "ファイル名の変更中にエラーが発生しました。", None, None

    def archive_file(self, file_path):
        """ファイルをアーカイブフォルダに移動し、DBのレコードを更新する"""
        try:
            # 1. アーカイブディレクトリが存在しない場合は作成
            if not os.path.exists(config.ARCHIVE_DIR):
                os.makedirs(config.ARCHIVE_DIR)
            
            # 2. 新しいアーカイブパスを生成
            filename = os.path.basename(file_path)
            archive_path = os.path.join(config.ARCHIVE_DIR, filename)
            
            # 3. アーカイブフォルダに同名ファイルがある場合の処理
            if os.path.exists(archive_path):
                return False, "アーカイブフォルダに同じ名前のファイルが既に存在します。"
            
            # 4. ファイルをアーカイブフォルダに移動
            os.rename(file_path, archive_path)
            
            # 5. データベースのレコードを更新
            File = Query()
            self.db.update(
                {'path': archive_path, 'status': 'archived'},
                File.path == file_path
            )
            
            return True, f"ファイル「{filename}」をアーカイブしました。"
        except Exception as e:
            print(f"Error archiving file: {e}")
            # ファイル移動が失敗した場合、元に戻す試み
            if os.path.exists(archive_path):
                os.rename(archive_path, file_path)
            return False, "ファイルのアーカイブ中にエラーが発生しました。"

    def unarchive_file(self, file_path):
        """アーカイブされたファイルを元のフォルダに戻す"""
        try:
            # 1. 元のフォルダでの新しいパスを生成
            filename = os.path.basename(file_path)
            active_path = os.path.join(config.NOTES_DIR, filename)
            
            # 2. 元のフォルダに同名ファイルがある場合の処理
            if os.path.exists(active_path):
                return False, "アクティブフォルダに同じ名前のファイルが既に存在します。"
            
            # 3. ファイルを元のフォルダに移動
            os.rename(file_path, active_path)
            
            # 4. データベースのレコードを更新
            File = Query()
            self.db.update(
                {'path': active_path, 'status': 'active'},
                File.path == file_path
            )
            
            return True, f"ファイル「{filename}」をアクティブに戻しました。"
        except Exception as e:
            print(f"Error unarchiving file: {e}")
            # ファイル移動が失敗した場合、元に戻す試み
            if os.path.exists(active_path):
                os.rename(active_path, file_path)
            return False, "ファイルのアーカイブ解除中にエラーが発生しました。"

    def update_file_order(self, ordered_paths):
        """ファイルの新しい順番を受け取り、order_indexをデータベースで更新する"""
        try:
            print(f"Updating file order for {len(ordered_paths)} files")  # Debug
            File = Query()
            
            # 各パスに対して新しい order_index を設定
            for new_index, path in enumerate(ordered_paths, start=1):
                print(f"Setting order_index {new_index} for {path}")  # Debug
                # パスに対応するファイルの order_index を更新
                updated_count = self.db.update(
                    {'order_index': new_index},
                    File.path == path
                )
                
                if updated_count == 0:
                    print(f"Warning: File not found in DB for path: {path}")
                else:
                    print(f"Updated {updated_count} records for {path}")  # Debug
            
            print("File order update completed successfully")  # Debug
            return True, "ファイルの順番を更新しました。"
        except Exception as e:
            print(f"Error updating file order: {e}")
            return False, "ファイル順番の更新中にエラーが発生しました。"

    def delete_file(self, file_path):
        """ファイルを完全に削除し、データベースからもレコードを削除する。
        
        Args:
            file_path (str): 削除対象ファイルの絶対パス
        
        Returns:
            tuple: (成功フラグ, メッセージ)
                - bool: 削除が成功した場合True
                - str: 結果メッセージ（成功/失敗理由）
        
        Note:
            セキュリティ検証を行い、ファイルシステムとデータベースの両方から
            安全に削除する。バックアップは作成されないため、操作は不可逆的。
        """
        # Transaction state tracking
        file_deleted = False
        db_updated = False
        backup_content = None
        
        try:
            # 1. セキュリティ検証
            success, message, validated_path = validate_file_path(file_path, self.allowed_dirs)
            if not success:
                return False, f"セキュリティ検証失敗: {message}"
            
            file_path = validated_path
            filename = os.path.basename(file_path)
            
            # 2. ファイル存在確認
            if not os.path.exists(file_path):
                return False, "削除対象のファイルが見つかりません。"
            
            # 3. データベースレコード存在確認
            File = Query()
            existing_record = self.db.get(File.path == file_path)
            if not existing_record:
                return False, "データベースにファイル記録が見つかりません。"
            
            # 4. バックアップ作成（エラー時のロールバック用）
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    backup_content = f.read()
            except Exception as e:
                print(f"Warning: Could not create backup for {filename}: {e}")
            
            # 5. データベースからレコードを削除
            try:
                removed_count = self.db.remove(File.path == file_path)
                if removed_count == 0:
                    return False, "データベースからのファイル削除に失敗しました。"
                
                db_updated = True
                
            except Exception as db_error:
                print(f"Database deletion failed: {db_error}")
                return False, "データベース操作中にエラーが発生しました。"
            
            # 6. ファイルシステムからファイルを削除
            try:
                success, delete_message, _ = safe_file_operation('delete', file_path, allowed_dirs=self.allowed_dirs)
                if not success:
                    # データベースから削除済みなので、ロールバック
                    if backup_content is not None:
                        try:
                            self.db.insert(existing_record)
                        except:
                            pass
                    
                    return False, f"ファイル削除失敗: {delete_message}"
                
                file_deleted = True
                return True, f"ファイル「{filename}」を完全に削除しました。"
                
            except Exception as file_error:
                # ファイル削除失敗時のデータベースロールバック
                if db_updated and backup_content is not None:
                    try:
                        self.db.insert(existing_record)
                    except:
                        pass
                
                print(f"File deletion failed: {file_error}")
                return False, "ファイル削除中にエラーが発生しました。"
                
        except Exception as e:
            # 一般的なエラー時のクリーンアップ
            if db_updated and not file_deleted and backup_content is not None:
                try:
                    self.db.insert(existing_record)
                except:
                    pass
            
            print(f"Error deleting file: {e}")
            return False, "ファイル削除処理中にエラーが発生しました。"

    def read_file_async(self, path: str, progress_callback=None, completion_callback=None, error_callback=None) -> str:
        """ファイルを非同期で読み取る（大きなファイルでのUI凍結を防止）。
        
        Args:
            path (str): 読み取り対象ファイルの絶対パス
            progress_callback (Callable, optional): 進捗更新コールバック
            completion_callback (Callable, optional): 完了時コールバック
            error_callback (Callable, optional): エラー時コールバック
        
        Returns:
            str: 操作ID（非同期操作の追跡用）
        """
        def _async_read():
            try:
                # Security validation
                success, message, validated_path = validate_file_path(path, self.allowed_dirs)
                if not success:
                    raise SecurityError(f"Security validation failed: {message}")
                
                # Check file size for progress tracking
                file_size = os.path.getsize(validated_path)
                
                if file_size > 1024 * 1024:  # Files larger than 1MB get chunked reading
                    content = ""
                    chunk_size = 8192
                    bytes_read = 0
                    
                    with open(validated_path, 'r', encoding='utf-8') as f:
                        while True:
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            
                            content += chunk
                            bytes_read += len(chunk.encode('utf-8'))
                            
                            # Update progress
                            if progress_callback and file_size > 0:
                                progress = min(100, int((bytes_read / file_size) * 100))
                                progress_callback(progress)
                            
                            # Small delay for UI responsiveness
                            import time
                            time.sleep(0.001)
                    
                    return content
                else:
                    # Small files read directly
                    with open(validated_path, 'r', encoding='utf-8') as f:
                        return f.read()
                    
            except Exception as e:
                raise Exception(f"Error reading file: {str(e)}")
        
        return run_with_progress(
            _async_read,
            progress_callback=progress_callback
        )
    
    def save_file_async(self, path: str, content: str, progress_callback=None, completion_callback=None, error_callback=None) -> str:
        """ファイルを非同期で保存する（大きなファイルでのUI凍結を防止）。
        
        Args:
            path (str): 保存先ファイルの絶対パス
            content (str): 保存するテキスト内容
            progress_callback (Callable, optional): 進捗更新コールバック
            completion_callback (Callable, optional): 完了時コールバック
            error_callback (Callable, optional): エラー時コールバック
        
        Returns:
            str: 操作ID（非同期操作の追跡用）
        """
        def _async_save():
            # Use the existing synchronous save_file method with async wrapper
            return self.save_file(path, content)
        
        return async_manager.run_async_operation(
            _async_save,
            progress_callback=progress_callback,
            completion_callback=completion_callback,
            error_callback=error_callback
        )

    def analyze_and_update_tags_async(self, path: str, content: str, progress_callback=None, completion_callback=None, error_callback=None, cancel_event=None) -> str:
        """AI分析を非同期で実行する（UI凍結防止）- 新AI分析システム使用。
        
        Args:
            path (str): 分析対象ファイルの絶対パス
            content (str): 分析するテキスト内容
            progress_callback (Callable, optional): 進捗更新コールバック
            completion_callback (Callable, optional): 完了時コールバック
            error_callback (Callable, optional): エラー時コールバック
            cancel_event (threading.Event, optional): キャンセル用イベント
        
        Returns:
            str: 操作ID（非同期操作の追跡用）
        """
        def _async_analyze():
            if progress_callback:
                progress_callback(10)  # Starting analysis
            
            try:
                # Use new AI analysis system with async support
                result = self.ai_manager.analyze_async(
                    content, 
                    "tagging", 
                    progress_callback=progress_callback,
                    cancel_event=cancel_event
                )
                
                if not result.success:
                    return False, result.message
                
                # Extract tags from result
                tags = result.data.get("tags", [])
                
                if progress_callback:
                    progress_callback(90)  # Analysis complete, updating DB
                
                # Update database with new tags
                File = Query()
                self.db.update({'tags': tags}, File.path == path)
                
                if progress_callback:
                    progress_callback(100)  # Complete
                
                return True, result.message
                
            except Exception as e:
                print(f"Error analyzing and updating tags: {e}")
                return False, "タグの更新中にエラーが発生しました。"
        
        return async_manager.run_async_operation(
            _async_analyze,
            progress_callback=progress_callback,
            completion_callback=completion_callback,
            error_callback=error_callback
        )
    
    def run_ai_analysis_async(self, path: str, content: str, analysis_type: str, 
                             progress_callback=None, completion_callback=None, 
                             error_callback=None, cancel_event=None, **kwargs) -> str:
        """任意のAI分析を非同期で実行し、結果をデータベースに保存する。
        
        Args:
            path (str): 分析対象ファイルの絶対パス
            content (str): 分析するテキスト内容
            analysis_type (str): 分析タイプ ("tagging", "summarization", "sentiment")
            progress_callback (Callable, optional): 進捗更新コールバック
            completion_callback (Callable, optional): 完了時コールバック
            error_callback (Callable, optional): エラー時コールバック
            cancel_event (threading.Event, optional): キャンセル用イベント
            **kwargs: 分析タイプ固有のパラメータ
        
        Returns:
            str: 操作ID（非同期操作の追跡用）
        """
        def _async_analyze():
            if progress_callback:
                progress_callback(10)
            
            try:
                result = self.ai_manager.analyze_async(
                    content,
                    analysis_type,
                    progress_callback=progress_callback,
                    cancel_event=cancel_event,
                    **kwargs
                )
                
                if progress_callback:
                    progress_callback(90)
                
                # Store analysis results in database metadata
                if result.success and analysis_type != "tagging":
                    File = Query()
                    doc = self.db.get(File.path == path)
                    if doc:
                        # Add analysis results to document metadata
                        analysis_data = doc.get("ai_analysis", {})
                        analysis_data[analysis_type] = {
                            "data": result.data,
                            "timestamp": time.time(),
                            "processing_time": result.processing_time
                        }
                        self.db.update({"ai_analysis": analysis_data}, File.path == path)
                
                if progress_callback:
                    progress_callback(100)
                
                return result.success, result.message
                
            except Exception as e:
                print(f"Error in async AI analysis: {e}")
                return False, f"分析中にエラーが発生しました: {str(e)}"
        
        return async_manager.run_async_operation(
            _async_analyze,
            progress_callback=progress_callback,
            completion_callback=completion_callback,
            error_callback=error_callback
        )

    # 4. 指揮系統の整理：使わなくなった検索機能を一旦コメントアウト
    # def search_files(self, keyword):
    #     if not keyword:
    #         return self.get_file_list()
        
    #     File = Query()
    #     results = self.db.search(
    #         (File.title.search(keyword)) | (File.tags.any(Query().search(keyword)))
    #     )
    #     return results