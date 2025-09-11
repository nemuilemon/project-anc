# logic.py
import os
from tinydb import Query
import config
import ollama

class AppLogic:
    def __init__(self, db):
        self.db = db

    def get_file_list(self):
        return self.db.all()

    def read_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return None

    def save_file(self, path, content):
        """ファイル保存と、タグなしでのDB初期登録を行う"""
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            File = Query()
            title = os.path.basename(path)
            # upsertを使って、存在しなければtags:[]で新規作成、存在すれば何もしない
            self.db.upsert(
                {'title': title, 'path': path, 'tags': self.db.get(File.path == path).get('tags', [])},
                File.path == path
            )
            return True, title
        except Exception as e:
            print(f"Error saving file: {e}")
            return False, None

    # analyze_and_update_tags関数を新しく追加
    def analyze_and_update_tags(self, path, content):
        """指定されたファイルの内容を分析し、タグをDBに保存する"""
        try:
            tags = self._generate_tags_from_ollama(content)
            
            # タグ分析に失敗した場合は何もしない
            if not tags or "tag_error" in tags:
                 return False, "タグ分析に失敗しました。"

            File = Query()
            self.db.update({'tags': tags}, File.path == path)
            return True, "タグを更新しました。"
        except Exception as e:
            print(f"Error analyzing and updating tags: {e}")
            return False, "タグの更新中にエラーが発生しました。"


    def _generate_tags_from_ollama(self, content):
        """Ollamaに接続してコンテンツからタグを生成する（ガードレール付き）"""
        if not content.strip():
            return []
        try:
            prompt = f"""
            以下の文章の主要なキーワードを3つから5つ、コンマ区切りで単語のみ抽出してください。
            例: Python, Flet, データベース, AI

            文章:
            {content}

            キーワード:
            """
            response = ollama.generate(
                model=config.OLLAMA_MODEL,
                prompt=prompt
            )
            tags_string = response['response'].strip()

            MAX_TAGS_LENGTH = 100
            if len(tags_string) > MAX_TAGS_LENGTH:
                print(f"AIの応答が長すぎるため、タグ付けをスキップしました。({len(tags_string)}文字)")
                return []
            
            tags = [tag.strip() for tag in tags_string.split(',') if tag.strip()]
            print(f"AIが生成したタグ: {tags}")
            return tags
        except Exception as e:
            print(f"Ollamaへの接続エラー: {e}")
            return ["tag_error"]

    def search_files(self, keyword):
        if not keyword:
            return self.get_file_list()
        
        File = Query()
        results = self.db.search(
            (File.title.search(keyword)) | (File.tags.any(Query().search(keyword)))
        )
        return results