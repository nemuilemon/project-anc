# logic.py
import os
from tinydb import Query
import config
import ollama

class AppLogic:
    def __init__(self, db):
        self.db = db
        self.sync_database()

    def get_file_list(self):
        return self.db.all()

    # 2. データベース同期機能：フォルダとDBを同期する新機能
    def sync_database(self):
        """NOTES_DIRにあるmdファイルとDBを同期する"""
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
        
        # 新しいファイルをDBに初期登録する
        for path in new_files:
            title = os.path.basename(path)
            self.db.insert({'title': title, 'path': path, 'tags': []})
            print(f"New file found and added to DB: {title}")

    # 3. 手動タグ更新機能：タグ情報を更新する新機能
    def update_tags(self, path, tags):
        """指定されたファイルのタグを更新する"""
        try:
            File = Query()
            self.db.update({'tags': tags}, File.path == path)
            return True, "タグを更新しました。"
        except Exception as e:
            print(f"Error updating tags: {e}")
            return False, "タグの更新中にエラーが発生しました。"

    def read_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return None

    def save_file(self, path, content):
        """ファイル保存と、DBレコードの更新/作成を行う"""
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            File = Query()
            title = os.path.basename(path)
            
            # 既存のドキュメントを取得
            doc = self.db.get(File.path == path)
            # 既存のタグがあればそれを使い、なければ空のリストを使う
            existing_tags = doc.get('tags', []) if doc else []
            
            # upsertを使って、ドキュメントを更新または新規作成する
            self.db.upsert(
                {'title': title, 'path': path, 'tags': existing_tags},
                File.path == path
            )
            return True, title
        except Exception as e:
            print(f"Error saving file: {e}")
            return False, None

    # analyze_and_update_tags関数を新しく追加
    def analyze_and_update_tags(self, path, content, cancel_event=None):
        """指定されたファイルの内容を分析し、タグをDBに保存する"""
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


    def _generate_tags_from_ollama(self,content, cancel_event=None):
        """Ollamaに接続してコンテンツからタグを生成する（長文応答時に再試行するガードレール付き）"""
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
        """新しい空の.mdファイルを作成し、DBにレコードを追加する"""
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
            
            # 5. データベースにレコードを追加
            self.db.insert({
                'title': filename,
                'path': full_path,
                'tags': []
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

    # 4. 指揮系統の整理：使わなくなった検索機能を一旦コメントアウト
    # def search_files(self, keyword):
    #     if not keyword:
    #         return self.get_file_list()
        
    #     File = Query()
    #     results = self.db.search(
    #         (File.title.search(keyword)) | (File.tags.any(Query().search(keyword)))
    #     )
    #     return results