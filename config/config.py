"""Project A.N.C. アプリケーション設定ファイル

このモジュールは、Project A.N.C.（Alice Nexus Core）で使用される
すべての設定定数を管理します。

設定項目:
- ファイル保存ディレクトリ
- データベースファイル
- AI分析用モデル設定
"""

# プロジェクトルートディレクトリの取得
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# メモを保存するメインディレクトリ
NOTES_DIR = os.path.join(PROJECT_ROOT, "data", "notes")

# アーカイブファイルを保存するディレクトリ
# アーカイブされたファイルはここに移動される
ARCHIVE_DIR = os.path.join(NOTES_DIR, ".archive")

# TinyDBデータベースファイル名とパス
# ファイルのメタデータ（タグ、ステータス、順序等）を格納
DB_FILE = os.path.join(PROJECT_ROOT, "data", "anc_db.json")

# Ollama AIモデル名
# タグ自動生成で使用するローカルLLMモデル
OLLAMA_MODEL = "gemma3:4b"

# 利用可能なモデル候補（コメント）
# gemma3:27b  - 高精度だがメモリ使用量大
# gemma3:4b   - バランス型（推奨）
# gpt-oss:20b - 中程度の精度とパフォーマンス