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

# Sentiment Compass専用モデル設定
# Growth Analysis（感情コンパス）で使用するモデル
SENTIMENT_COMPASS_MODEL = "gemma3:4b"

# 利用可能なモデル候補（コメント）
# gemma3:27b  - 高精度だがメモリ使用量大
# gemma3:4b   - バランス型（推奨）
# gpt-oss:20b - 中程度の精度とパフォーマンス
# llama3.2    - Llama系モデル（もし利用可能な場合）

# モデル設定の説明
MODEL_DESCRIPTIONS = {
    "gemma3:4b": "バランス型 - 適度な精度と速度（推奨）",
    "gemma3:27b": "高精度型 - 最高品質だがメモリ使用量大",
    "llama3.2": "Llama系 - 汎用的な性能",
    "auto": "自動選択 - 利用可能な最初のモデルを使用"
}

# =================== Alice Chat 設定 ===================

# Gemini API Key - 環境変数から読み込み（セキュリティのため）
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

# Aliceシステムプロンプトファイルのパス
ALICE_SYSTEM_PROMPT_PATH = os.path.join(NOTES_DIR, "0-System-Prompt.md")

# Alice 長期記憶ファイルのパス
ALICE_MEMORY_FILE_PATH = os.path.join(NOTES_DIR, "0-Memory.md")

# 記憶ファイルを保存するディレクトリ
MEMORIES_DIR = os.path.join(PROJECT_ROOT, "data", "memories")

# 日報ファイルを保存するディレクトリ
NIPPO_DIR = os.path.join(PROJECT_ROOT, "data", "nippo")

# プロンプトファイルを保存するディレクトリ
PROMPTS_DIR = os.path.join(PROJECT_ROOT, "prompts")

# 記憶生成用プロンプトファイルのパス
CREATE_MEMORY_PROMPT_PATH = os.path.join(PROMPTS_DIR, "create_memory_prompt.md")

# 日報生成用プロンプトファイルのパス
CREATE_NIPPO_PROMPT_PATH = os.path.join(PROMPTS_DIR, "create_nippo_prompt.md")

# Alice Chat ログディレクトリ
CHAT_LOGS_DIR = os.path.join(PROJECT_ROOT, "data", "chat_logs")

# Compass API 設定
# 過去の関連会話履歴を検索するためのAPIエンドポイント
COMPASS_API_URL = "http://127.0.0.1:8000/search"

# Compass API リクエスト設定
COMPASS_API_CONFIG = {"target": "summary", "limit": 5, "compress": False, "search_mode": "latest"}

# Alice Chat 設定
ALICE_CHAT_CONFIG = {
    "model": "gemini-2.5-pro",  # デフォルトのGeminiモデル
    "max_history_length": 500,  # 保持する会話履歴の最大件数
    "auto_save_interval": 30,  # 自動保存間隔（秒）
    "history_char_limit": 4000,  # 過去のログから読み込む文字数制限
}