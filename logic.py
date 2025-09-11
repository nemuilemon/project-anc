# logic.py
import os
from tinydb import Query
import config

class AppLogic:
    def __init__(self, db):
        self.db = db

    def get_file_list(self):
        """notesディレクトリ内のマークダウンファイル一覧を返す"""
        return [f for f in os.listdir(config.NOTES_DIR) if f.endswith(".md")]

    def read_file(self, path):
        """指定されたファイルの内容を返す"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return None

    def save_file(self, path, content):
        """ファイルに内容を保存し、DBにメタデータを記録する"""
        try:
            # 1. ファイルシステムに書き込む
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            # 2. データベースにメタデータを保存
            File = Query()
            title = os.path.basename(path)
            self.db.upsert(
                {'title': title, 'path': path},
                File.path == path
            )
            return True, title # 成功したことを伝える
        except Exception as e:
            print(f"Error saving file: {e}")
            return False, None