---
title: 非同期手紙生成アプリ（麻理AI）
emoji: 💌
colorFrom: pink
colorTo: purple
sdk: streamlit
pinned: false
license: mit
---

# 非同期手紙生成アプリ（麻理AI）

Hugging Face Spaces用の非同期手紙生成アプリケーションです。

## 🚀 機能

- **非同期手紙生成**: GroqとGemini APIを使用した手紙の自動生成
- **バッチ処理**: 指定時刻での自動処理
- **ストレージ管理**: JSONベースのデータ永続化
- **ログ機能**: 詳細なログ出力
- **Streamlitインターフェース**: ユーザーフレンドリーなWeb UI

## 📁 ファイル構成

### コア機能
- `letter_app.py` - メインアプリケーション
- `letter_config.py` - 設定管理
- `letter_logger.py` - ログ機能
- `letter_storage.py` - ストレージ管理
- `letter_models.py` - データモデル
- `letter_manager.py` - 手紙管理

### UI
- `streamlit_app.py` - Streamlitメインアプリ
- `streamlit_styles.css` - スタイル定義

### 設定
- `requirements.txt` - 依存関係
- `.env` - 環境変数（開発用）

## 🔧 環境変数

Hugging Face Spacesの設定画面で以下を設定してください：

| 変数名 | 説明 | 必須 | デフォルト値 |
|--------|------|------|-------------|
| `GROQ_API_KEY` | Groq APIキー | ✅ | - |
| `GEMINI_API_KEY` | Gemini APIキー | ✅ | - |
| `DEBUG_MODE` | デバッグモード | ❌ | false |
| `BATCH_SCHEDULE_HOURS` | バッチ処理時刻 | ❌ | 2,3,4 |
| `MAX_DAILY_REQUESTS` | 最大日次リクエスト数 | ❌ | 1 |
| `STORAGE_PATH` | ストレージパス | ❌ | /tmp/letters.json |
| `BACKUP_PATH` | バックアップパス | ❌ | /tmp/backup |
| `LOG_LEVEL` | ログレベル | ❌ | INFO |
| `STREAMLIT_PORT` | Streamlitポート | ❌ | 7860 |
| `SESSION_TIMEOUT` | セッションタイムアウト | ❌ | 3600 |

## 🚀 デプロイメント

### Hugging Face Spacesでのデプロイ

1. このディレクトリの全ファイルをHugging Face Spacesリポジトリにアップロード
2. Space設定で以下を設定:
   - **SDK**: "Streamlit"
   - **Hardware**: CPU basic（推奨）
3. 環境変数を設定（Settings > Variables and secrets）
4. 自動的にアプリケーションが起動します

### ローカル実行

```bash
# 依存関係をインストール
pip install -r requirements.txt

# アプリケーションを起動
streamlit run streamlit_app.py
```

## 📋 使用方法

1. Webインターフェースにアクセス
2. ユーザーIDを入力
3. 手紙生成をリクエスト
4. バッチ処理で自動生成される手紙を確認

## 🧪 開発

テスト実行：

```bash
python tests/test_config_setup.py
```

## 📞 サポート

問題が発生した場合は、ログを確認してください。デバッグモードを有効にすると詳細な情報が表示されます。