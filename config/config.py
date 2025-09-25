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
ALICE_SYSTEM_PROMPT_PATH = os.path.join(NOTES_DIR, "0-怪文書.md")

# Alice Chat ログディレクトリ
CHAT_LOGS_DIR = os.path.join(PROJECT_ROOT, "data", "chat_logs")

# Alice Chat 設定
ALICE_CHAT_CONFIG = {
    "model": "gemini-2.5-pro",  # デフォルトのGeminiモデル
    "max_history_length": 500,  # 保持する会話履歴の最大件数
    "auto_save_interval": 30,  # 自動保存間隔（秒）
}