# logic.py
import os
from tinydb import Query
import config
import ollama

class AppLogic:
    def __init__(self, db):
        self.db = db
        self.sync_database()

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
            ファイルが存在しない、アクセス権限がない等の場合はNoneを返し、
            エラー内容はコンソールに出力される。
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
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
            新しいファイルの場合は自動的にDBレコードを作成し、
            既存ファイルの場合は既存の情報（タグ、ステータス等）を保持する。
        """
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            File = Query()
            title = os.path.basename(path)
            
            # 既存のドキュメントを取得
            doc = self.db.get(File.path == path)
            # 既存の値があればそれを使い、なければデフォルト値を使う
            existing_tags = doc.get('tags', []) if doc else []
            existing_status = doc.get('status', 'active') if doc else 'active'
            existing_order_index = doc.get('order_index', 0) if doc else 0
            
            # 新しいファイルの場合は order_index を設定
            if not doc:
                all_records = self.db.all()
                if all_records:
                    existing_order_index = max([d.get('order_index', 0) for d in all_records]) + 1
                else:
                    existing_order_index = 1
            
            # upsertを使って、ドキュメントを更新または新規作成する
            self.db.upsert(
                {'title': title, 'path': path, 'tags': existing_tags, 'status': existing_status, 'order_index': existing_order_index},
                File.path == path
            )
            return True, title
        except Exception as e:
            print(f"Error saving file: {e}")
            return False, None

    # analyze_and_update_tags関数を新しく追加
    def analyze_and_update_tags(self, path, content, cancel_event=None):
        """AI（Ollama）を使用してファイル内容を分析し、自動的にタグを生成・更新する。
        
        Args:
            path (str): 分析対象ファイルの絶対パス
            content (str): 分析するテキスト内容
            cancel_event (threading.Event, optional): 処理をキャンセルするためのイベント
        
        Returns:
            tuple: (成功フラグ, メッセージ)
                - bool: 分析・更新が成功した場合True
                - str: 結果メッセージ（成功/失敗/キャンセル）
        
        Note:
            非同期処理で実行され、cancel_eventによりキャンセル可能。
            Ollamaサーバーへの接続エラーやタイムアウトも適切に処理される。
        """
        try:
            tags = self._generate_tags_from_ollama(content, cancel_event)
            
            if "tag_cancelled" in tags:
                return False, "分析を中止しました。"

            if not tags or "tag_error" in tags:
                 return False, "タグ分析に失敗しました。"
            
            File = Query()
            self.db.update({'tags': tags}, File.path == path)
            return True, "タグを更新しました。"
        except Exception as e:
            print(f"Error analyzing and updating tags: {e}")
            return False, "タグの更新中にエラーが発生しました。"


    def _generate_tags_from_ollama(self, content, cancel_event=None):
        """Ollama AIモデルを使用してコンテンツからタグを生成する。
        
        Args:
            content (str): タグ生成の対象となるテキスト内容
            cancel_event (threading.Event, optional): 処理キャンセル用イベント
        
        Returns:
            list: 生成されたタグのリスト。エラー時は["tag_error"]、
                  キャンセル時は["tag_cancelled"]を返す。
        
        Note:
            AIの応答が長すぎる場合（100文字超）は最大3回まで自動再試行する。
            各試行の開始時にキャンセルチェックを行う。
        """
        if not content.strip():
            return []

        # 1. 定数の設定
        MAX_TAGS_LENGTH = 100  # 許容する最大文字数
        MAX_RETRIES = 3        # 最大試行回数
        current_content = content # 繰り返し処理で利用する現在のテキスト

        for attempt in range(MAX_RETRIES):
            #ループの開始時にキャンセルされていないかチェック
            if cancel_event and cancel_event.is_set():
                print("Cancellation detected. Stopping tag generation.")
                return ["tag_cancelled"]
            
            print(f"--- タグ生成試行: {attempt + 1}回目 ---")
            try:
                prompt = f"""
                以下の文章の主要なキーワードを5つから8つ、コンマ区切りで単語のみ抽出してください。
                出力例: "Python, Flet, データベース, AI"
                文章:「{current_content}」
                """
                response = ollama.generate(
                    model=config.OLLAMA_MODEL,
                    prompt=prompt
                )
                tags_string = response['response'].strip()

                # 2. 成功条件のチェック
                if len(tags_string) <= MAX_TAGS_LENGTH:
                    tags = [tag.strip() for tag in tags_string.split(',') if tag.strip()]
                    print(f"AIが生成したタグ (成功): {tags}")
                    return tags # 成功したので、結果を返して処理を終了

                # 3. 失敗（長文応答）時の処理
                print(f"AIの応答が長すぎます ({len(tags_string)}文字)。応答内容を元に再試行します。")
                current_content = tags_string # 帰ってきた長文を次の入力にする

            except Exception as e:
                print(f"Ollamaへの接続エラー: {e}")
                return ["tag_error"]

        # 4. 最大試行回数を超えた場合の処理
        print(f"最大試行回数({MAX_RETRIES}回)を超えました。タグ付けをスキップします。")
        return []

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
            作成されたファイルは自動的に最後の順序（最大order_index + 1）で
            データベースに登録される。
        """
        # 1. ファイル名の検証と正規化
        if not filename.strip():
            return False, "ファイル名を入力してください。"
        
        if not filename.endswith('.md'):
            filename += '.md'
        
        # 2. フルパスを生成
        full_path = os.path.join(config.NOTES_DIR, filename)
        
        # 3. ファイル名の衝突チェック
        if os.path.exists(full_path):
            return False, "同じ名前のファイルが既に存在します。"
        
        try:
            # 4. 空のファイルを作成
            with open(full_path, "w", encoding="utf-8") as f:
                f.write("")
            
            # 5. データベースにレコードを追加（order_indexは最大値+1）
            existing_max_order = 0
            all_records = self.db.all()
            if all_records:
                existing_max_order = max([doc.get('order_index', 0) for doc in all_records])
            
            order_index = existing_max_order + 1
            self.db.insert({
                'title': filename,
                'path': full_path,
                'tags': [],
                'status': 'active',
                'order_index': order_index
            })
            
            return True, f"新しいファイル「{filename}」を作成しました。"
        except Exception as e:
            print(f"Error creating file: {e}")
            return False, "ファイルの作成中にエラーが発生しました。"

    def rename_file(self, old_path, new_name):
        """ファイル名を変更し、DBのレコードも更新する"""
        # 1. 新しいファイル名の検証
        if not new_name.endswith('.md'):
            new_name += '.md'
        
        # 新しいフルパスを生成
        new_path = os.path.join(os.path.dirname(old_path), new_name)

        # 2. ファイル名の衝突チェック
        if os.path.exists(new_path):
            return False, "同じ名前のファイルが既に存在します。", None, None

        try:
            # 3. ファイルシステム上で名前を変更
            os.rename(old_path, new_path)

            # 4. データベースのレコードを更新
            File = Query()
            new_title = os.path.basename(new_path)
            self.db.update(
                {'title': new_title, 'path': new_path},
                File.path == old_path
            )
            
            return True, f"ファイル名を「{new_title}」に変更しました。", old_path, new_path
        except Exception as e:
            print(f"Error renaming file: {e}")
            # もしDB更新前にエラーが起きた場合、ファイル名を元に戻す試み
            if os.path.exists(new_path):
                os.rename(new_path, old_path)
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

    # 4. 指揮系統の整理：使わなくなった検索機能を一旦コメントアウト
    # def search_files(self, keyword):
    #     if not keyword:
    #         return self.get_file_list()
        
    #     File = Query()
    #     results = self.db.search(
    #         (File.title.search(keyword)) | (File.tags.any(Query().search(keyword)))
    #     )
    #     return results