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
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# .env ファイルを自動的に読み込む
try:
    from dotenv import load_dotenv
    env_file = Path(PROJECT_ROOT) / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"[Config] .env file loaded from: {env_file}")
    else:
        print(f"[Config] .env file not found at: {env_file}")
except ImportError:
    print("[Config] python-dotenv not installed. Environment variables must be set manually.")
except Exception as e:
    print(f"[Config] Error loading .env file: {e}")

# データファイルを保存するメインディレクトリ
DATA_DIR = os.path.join(PROJECT_ROOT, os.getenv('DATA_DIR_NAME', 'data'))

# メモを保存するメインディレクトリ
NOTES_DIR = os.path.join(DATA_DIR, os.getenv('NOTES_DIR_NAME', 'notes'))

# アーカイブファイルを保存するディレクトリ
# アーカイブされたファイルはここに移動される
ARCHIVE_DIR = os.path.join(NOTES_DIR, os.getenv('ARCHIVE_DIR_NAME', '.archive'))

# TinyDBデータベースファイル名とパス
# ファイルのメタデータ（タグ、ステータス、順序等）を格納
DB_FILE = os.path.join(DATA_DIR, os.getenv('DB_FILE_NAME', 'anc_db.json'))

# Ollama AIモデル名
# タグ自動生成で使用するローカルLLMモデル
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'gemma3:4b')

# Sentiment Compass専用モデル設定
# Growth Analysis（感情コンパス）で使用するモデル
SENTIMENT_COMPASS_MODEL = os.getenv('SENTIMENT_COMPASS_MODEL', 'gemma3:4b')

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

# API Provider - "google" または "openai" を指定
CHAT_API_PROVIDER = os.environ.get('CHAT_API_PROVIDER', 'google')

# Gemini API Key - 環境変数から読み込み（セキュリティのため）
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

# OpenAI API Key - 環境変数から読み込み（セキュリティのため）
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Aliceシステムプロンプトファイルのパス
ALICE_SYSTEM_PROMPT_PATH = os.path.join(DATA_DIR, os.getenv('ALICE_SYSTEM_PROMPT_FILE', '0-System-Prompt.md'))

# Alice 長期記憶ファイルのパス
ALICE_MEMORY_FILE_PATH = os.path.join(DATA_DIR, os.getenv('ALICE_MEMORY_FILE', '0-Memory.md'))

# 記憶ファイルを保存するディレクトリ
MEMORIES_DIR = os.path.join(DATA_DIR, os.getenv('MEMORIES_DIR_NAME', 'memories'))

# 日報ファイルを保存するディレクトリ
NIPPO_DIR = os.path.join(DATA_DIR, os.getenv('NIPPO_DIR_NAME', 'nippo'))

# プロンプトファイルを保存するディレクトリ
PROMPTS_DIR = os.path.join(DATA_DIR, os.getenv('PROMPTS_DIR_NAME', 'prompts'))

# 記憶生成用プロンプトファイルのパス
CREATE_MEMORY_PROMPT_PATH = os.path.join(PROMPTS_DIR, os.getenv('CREATE_MEMORY_PROMPT_FILE', 'create_memory_prompt.md'))

# 日報生成用プロンプトファイルのパス
CREATE_NIPPO_PROMPT_PATH = os.path.join(PROMPTS_DIR, os.getenv('CREATE_NIPPO_PROMPT_FILE', 'create_nippo_prompt.md'))

# Alice Chat ログディレクトリ
CHAT_LOGS_DIR = os.path.join(DATA_DIR, os.getenv('CHAT_LOGS_DIR_NAME', 'chat_logs'))

# Compass API 設定
# 過去の関連会話履歴を検索するためのAPIベースURL（エンドポイントパスを含まない）
COMPASS_API_BASE_URL = os.environ.get('COMPASS_API_BASE_URL', 'http://127.0.0.1:8000')

# Compass API エンドポイントタイプ: "search" または "graph_search"
COMPASS_API_ENDPOINT = os.environ.get('COMPASS_API_ENDPOINT', 'search')

# Compass API リクエスト設定
COMPASS_API_CONFIG = {
    "target": os.environ.get('COMPASS_API_TARGET', 'content'),
    "limit": int(os.environ.get('COMPASS_API_LIMIT', '0')),
    "related_limit": int(os.environ.get('COMPASS_API_RELATED_LIMIT', '0')),  # graph_search用
    "compress": os.environ.get('COMPASS_API_COMPRESS', 'False').lower() in ('true', '1', 'yes'),
    "search_mode": os.environ.get('COMPASS_API_SEARCH_MODE', 'latest'),
    "endpoint": os.environ.get('COMPASS_API_ENDPOINT', 'search')
}

# Chat API Base URL (for API client migration)
CHAT_API_BASE_URL = os.environ.get('CHAT_API_BASE_URL', 'http://localhost:8000')

# Chat API Key (for authentication)
COMPASS_API_KEY = os.environ.get('COMPASS_API_KEY', None)

# Alice Chat 設定
ALICE_CHAT_CONFIG = {
    "gemini_model": os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),  # Google Geminiモデル
    "openai_model": os.getenv('OPENAI_MODEL_NAME', 'gpt-5'),  # OpenAIモデル
    "max_history_length": int(os.getenv('MAX_HISTORY_LENGTH', '500')),  # 保持する会話履歴の最大件数
    "auto_save_interval": int(os.getenv('AUTO_SAVE_INTERVAL', '30')),  # 自動保存間隔（秒）
    "history_char_limit": int(os.environ.get('ALICE_HISTORY_CHAR_LIMIT', '4000')),  # 過去のログから読み込む文字数制限
    "temperature": float(os.getenv('ALICE_TEMPERATURE', '1.0')),  # 温度パラメータ
}