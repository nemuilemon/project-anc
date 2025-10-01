# Alice Chat Setup Guide

## 🌸 ありすとの対話機能セットアップガイド

このガイドでは、Project A.N.C.に新しく追加された「ありす」との対話機能の設定方法を説明します。

## 前提条件

- Google AI Studioアカウント
- Gemini API キー

## セットアップ手順

### 1. Gemini APIキーの取得

1. [Google AI Studio](https://makersuite.google.com/app/apikey) にアクセス
2. Googleアカウントでログイン
3. 「Create API Key」をクリック
4. 新しいプロジェクトを作成するか、既存のプロジェクトを選択
5. 生成されたAPIキーをコピー

### 2. 環境変数の設定

#### Windows (コマンドプロンプト)
```cmd
set GEMINI_API_KEY=your_api_key_here
```

#### Windows (PowerShell)
```powershell
$env:GEMINI_API_KEY = "your_api_key_here"
```

#### Linux/macOS
```bash
export GEMINI_API_KEY="your_api_key_here"
```

### 3. .envファイルでの設定（推奨）

プロジェクトルートに `.env` ファイルを作成し、以下を追加：

```
GEMINI_API_KEY=your_api_key_here
```

### 4. 動作確認

1. Project A.N.C.を起動
```bash
python app/main.py
```

2. サイドバーの「ありすと対話」ボタンをクリック
3. メッセージを入力して送信ボタンをクリック
4. ありすからの応答を確認

## 機能概要

### 💫 追加された機能

1. **チャットインターフェース**
   - スクロール可能なチャット履歴
   - リアルタイムメッセージ送受信
   - タイピングインディケーター

2. **会話履歴管理**
   - 会話履歴の自動保存
   - セッション間での履歴保持
   - 履歴クリア機能

3. **ログ機能**
   - 日別チャットログ（Markdown形式）
   - 保存場所: `data/chat_logs/YYYY-MM-DD.md`
   - システムログとの統合

4. **AIモデル設定**
   - デフォルトモデル: gemini-2.0-flash-exp
   - 設定可能な会話履歴長
   - システムプロンプト（0-怪文書.md）の自動読み込み

## トラブルシューティング

### APIキーエラー
- エラーメッセージ: "ありすとの接続が利用できません"
- 解決方法: GEMINI_API_KEYが正しく設定されているか確認

### システムプロンプトエラー
- ファイル: `data/notes/0-怪文書.md` が存在するか確認
- ファイルが読み取り可能か確認

### ログファイルエラー
- `data/chat_logs` ディレクトリの書き込み権限を確認
- ディスク容量を確認

## ファイル構成

```
project-anc/
├── config/
│   └── config.py                  # Gemini API設定追加
├── app/
│   ├── alice_chat_manager.py      # 新規作成
│   ├── ui.py                      # チャット機能統合
│   ├── handlers.py               # チャットハンドラー追加
│   ├── logger.py                 # チャットロガー追加
│   └── main.py                   # チャット機能有効化
├── data/
│   ├── notes/
│   │   └── 0-怪文書.md           # システムプロンプト
│   └── chat_logs/                # チャットログ（自動作成）
└── logs/
    └── alice_chat.log            # システムログ（自動作成）
```

## 使用方法

1. アプリケーション起動後、サイドバーの「ありすと対話」をクリック
2. チャット画面が表示されます
3. メッセージを入力し、Enterまたは送信ボタンで送信
4. ありすからの応答をお待ちください
5. 「クリア」ボタンで会話履歴をリセット可能

---

**注意**: APIキーは機密情報です。第三者に共有しないよう注意してください。