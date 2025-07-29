---
title: 非同期手紙生成アプリ（麻理AI）
emoji: 💌
colorFrom: pink
colorTo: purple
sdk: streamlit
app_file: main_app.py
pinned: false
license: mit
---

# 非同期手紙生成アプリ（麻理AI）

Hugging Face Spaces用の非同期手紙生成・チャットボットアプリケーションです。

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

<svg width="1200" height="800" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
    
    <linearGradient id="cardGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:rgba(255,255,255,0.15);stop-opacity:1" />
      <stop offset="100%" style="stop-color:rgba(255,255,255,0.05);stop-opacity:1" />
    </linearGradient>
    
    <linearGradient id="titleGradient" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#ff6b6b;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#4ecdc4;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#45b7d1;stop-opacity:1" />
    </linearGradient>
    
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
      <feMerge> 
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  
  <!-- Background -->
  <rect width="1200" height="800" fill="url(#bgGradient)"/>
  
  <!-- Title -->
  <text x="600" y="60" font-family="Arial, sans-serif" font-size="36" font-weight="bold" text-anchor="middle" fill="url(#titleGradient)" filter="url(#glow)">🤖 麻理プロジェクト 技術スタック</text>
  <text x="600" y="90" font-family="Arial, sans-serif" font-size="18" text-anchor="middle" fill="rgba(255,255,255,0.8)">感情豊かなAI対話システムの技術構成</text>
  
  <!-- Frontend Card -->
  <rect x="50" y="120" width="350" height="200" rx="15" fill="url(#cardGradient)" stroke="rgba(255,255,255,0.3)" stroke-width="1"/>
  <text x="225" y="150" font-family="Arial, sans-serif" font-size="24" font-weight="bold" text-anchor="middle" fill="white">🌐 フロントエンド</text>
  <text x="70" y="175" font-family="Arial, sans-serif" font-size="16" fill="white">• Streamlit Framework</text>
  <text x="70" y="200" font-family="Arial, sans-serif" font-size="16" fill="white">• CSS3 + Animations</text>
  <text x="70" y="225" font-family="Arial, sans-serif" font-size="16" fill="white">• リアルタイム通知</text>
  <text x="70" y="250" font-family="Arial, sans-serif" font-size="16" fill="white">• レスポンシブデザイン</text>
  <text x="70" y="275" font-family="Arial, sans-serif" font-size="16" fill="white">• セッション状態管理</text>
  <text x="70" y="300" font-family="Arial, sans-serif" font-size="16" fill="white">• 動的背景変更</text>
  
  <!-- AI/ML Card -->
  <rect x="425" y="120" width="350" height="200" rx="15" fill="url(#cardGradient)" stroke="rgba(255,255,255,0.3)" stroke-width="1"/>
  <text x="600" y="150" font-family="Arial, sans-serif" font-size="24" font-weight="bold" text-anchor="middle" fill="white">🧠 AI・機械学習</text>
  <text x="445" y="175" font-family="Arial, sans-serif" font-size="16" fill="white">• Together.ai API</text>
  <text x="445" y="200" font-family="Arial, sans-serif" font-size="16" fill="white">• Groq API</text>
  <text x="445" y="225" font-family="Arial, sans-serif" font-size="16" fill="white">• Qwen3-235B Model</text>
  <text x="445" y="250" font-family="Arial, sans-serif" font-size="16" fill="white">• 感情分析アルゴリズム</text>
  <text x="445" y="275" font-family="Arial, sans-serif" font-size="16" fill="white">• シーン検知システム</text>
  <text x="445" y="300" font-family="Arial, sans-serif" font-size="16" fill="white">• 自然言語処理</text>
  
  <!-- Backend Card -->
  <rect x="800" y="120" width="350" height="200" rx="15" fill="url(#cardGradient)" stroke="rgba(255,255,255,0.3)" stroke-width="1"/>
  <text x="975" y="150" font-family="Arial, sans-serif" font-size="24" font-weight="bold" text-anchor="middle" fill="white">⚙️ バックエンド</text>
  <text x="820" y="175" font-family="Arial, sans-serif" font-size="16" fill="white">• Python 3.9+</text>
  <text x="820" y="200" font-family="Arial, sans-serif" font-size="16" fill="white">• 非同期処理 (asyncio)</text>
  <text x="820" y="225" font-family="Arial, sans-serif" font-size="16" fill="white">• OpenAI API Client</text>
  <text x="820" y="250" font-family="Arial, sans-serif" font-size="16" fill="white">• レート制限システム</text>
  <text x="820" y="275" font-family="Arial, sans-serif" font-size="16" fill="white">• エラーハンドリング</text>
  <text x="820" y="300" font-family="Arial, sans-serif" font-size="16" fill="white">• バッチ処理</text>
  
  <!-- Data Management Card -->
  <rect x="50" y="350" width="350" height="200" rx="15" fill="url(#cardGradient)" stroke="rgba(255,255,255,0.3)" stroke-width="1"/>
  <text x="225" y="380" font-family="Arial, sans-serif" font-size="24" font-weight="bold" text-anchor="middle" fill="white">💾 データ管理</text>
  <text x="70" y="405" font-family="Arial, sans-serif" font-size="16" fill="white">• JSON ファイルストレージ</text>
  <text x="70" y="430" font-family="Arial, sans-serif" font-size="16" fill="white">• メモリ圧縮アルゴリズム</text>
  <text x="70" y="455" font-family="Arial, sans-serif" font-size="16" fill="white">• キーワード抽出</text>
  <text x="70" y="480" font-family="Arial, sans-serif" font-size="16" fill="white">• 重要記憶管理</text>
  <text x="70" y="505" font-family="Arial, sans-serif" font-size="16" fill="white">• 履歴圧縮</text>
  <text x="70" y="530" font-family="Arial, sans-serif" font-size="16" fill="white">• データ整合性保証</text>
  
  <!-- System Skills Card -->
  <rect x="425" y="350" width="350" height="200" rx="15" fill="url(#cardGradient)" stroke="rgba(255,255,255,0.3)" stroke-width="1"/>
  <text x="600" y="380" font-family="Arial, sans-serif" font-size="24" font-weight="bold" text-anchor="middle" fill="white">🔧 システム技能</text>
  <text x="445" y="405" font-family="Arial, sans-serif" font-size="16" fill="#4ecdc4" font-weight="bold">• モジュラー設計</text>
  <text x="445" y="430" font-family="Arial, sans-serif" font-size="16" fill="#4ecdc4" font-weight="bold">• 非同期プログラミング</text>
  <text x="445" y="455" font-family="Arial, sans-serif" font-size="16" fill="#4ecdc4" font-weight="bold">• パフォーマンス最適化</text>
  <text x="445" y="480" font-family="Arial, sans-serif" font-size="16" fill="#4ecdc4" font-weight="bold">• セキュリティ対策</text>
  <text x="445" y="505" font-family="Arial, sans-serif" font-size="16" fill="#4ecdc4" font-weight="bold">• スケーラブル設計</text>
  <text x="445" y="530" font-family="Arial, sans-serif" font-size="16" fill="#4ecdc4" font-weight="bold">• テスト駆動開発</text>
  
  <!-- Deployment Card -->
  <rect x="800" y="350" width="350" height="200" rx="15" fill="url(#cardGradient)" stroke="rgba(255,255,255,0.3)" stroke-width="1"/>
  <text x="975" y="380" font-family="Arial, sans-serif" font-size="24" font-weight="bold" text-anchor="middle" fill="white">☁️ デプロイメント</text>
  <text x="820" y="405" font-family="Arial, sans-serif" font-size="16" fill="white">• Hugging Face Spaces</text>
  <text x="820" y="430" font-family="Arial, sans-serif" font-size="16" fill="white">• Docker コンテナ化</text>
  <text x="820" y="455" font-family="Arial, sans-serif" font-size="16" fill="white">• 環境変数管理</text>
  <text x="820" y="480" font-family="Arial, sans-serif" font-size="16" fill="white">• CI/CD パイプライン</text>
  <text x="820" y="505" font-family="Arial, sans-serif" font-size="16" fill="white">• 依存関係管理</text>
  <text x="820" y="530" font-family="Arial, sans-serif" font-size="16" fill="white">• モニタリング</text>
  
  <!-- Architecture Flow -->
  <rect x="100" y="580" width="1000" height="150" rx="15" fill="url(#cardGradient)" stroke="rgba(255,255,255,0.3)" stroke-width="1"/>
  <text x="600" y="610" font-family="Arial, sans-serif" font-size="24" font-weight="bold" text-anchor="middle" fill="white">🏗️ システムアーキテクチャフロー</text>
  
  <!-- Flow Boxes -->
  <rect x="150" y="640" width="150" height="60" rx="10" fill="rgba(102,126,234,0.8)" stroke="rgba(255,255,255,0.5)" stroke-width="1"/>
  <text x="225" y="660" font-family="Arial, sans-serif" font-size="14" font-weight="bold" text-anchor="middle" fill="white">📱 Streamlit UI</text>
  <text x="225" y="680" font-family="Arial, sans-serif" font-size="12" text-anchor="middle" fill="rgba(255,255,255,0.8)">ユーザーインターフェース</text>
  
  <text x="330" y="675" font-family="Arial, sans-serif" font-size="24" text-anchor="middle" fill="#4ecdc4">→</text>
  
  <rect x="370" y="640" width="150" height="60" rx="10" fill="rgba(102,126,234,0.8)" stroke="rgba(255,255,255,0.5)" stroke-width="1"/>
  <text x="445" y="660" font-family="Arial, sans-serif" font-size="14" font-weight="bold" text-anchor="middle" fill="white">🐍 Python Backend</text>
  <text x="445" y="680" font-family="Arial, sans-serif" font-size="12" text-anchor="middle" fill="rgba(255,255,255,0.8)">ビジネスロジック</text>
  
  <text x="550" y="675" font-family="Arial, sans-serif" font-size="24" text-anchor="middle" fill="#4ecdc4">→</text>
  
  <rect x="590" y="640" width="150" height="60" rx="10" fill="rgba(102,126,234,0.8)" stroke="rgba(255,255,255,0.5)" stroke-width="1"/>
  <text x="665" y="660" font-family="Arial, sans-serif" font-size="14" font-weight="bold" text-anchor="middle" fill="white">🤖 AI APIs</text>
  <text x="665" y="680" font-family="Arial, sans-serif" font-size="12" text-anchor="middle" fill="rgba(255,255,255,0.8)">Together.ai + Groq</text>
  
  <text x="770" y="675" font-family="Arial, sans-serif" font-size="24" text-anchor="middle" fill="#4ecdc4">→</text>
  
  <rect x="810" y="640" width="150" height="60" rx="10" fill="rgba(102,126,234,0.8)" stroke="rgba(255,255,255,0.5)" stroke-width="1"/>
  <text x="885" y="660" font-family="Arial, sans-serif" font-size="14" font-weight="bold" text-anchor="middle" fill="white">💾 JSON Storage</text>
  <text x="885" y="680" font-family="Arial, sans-serif" font-size="12" text-anchor="middle" fill="rgba(255,255,255,0.8)">データ永続化</text>
  
  <!-- Footer -->
  <text x="600" y="760" font-family="Arial, sans-serif" font-size="16" text-anchor="middle" fill="rgba(255,255,255,0.9)">💡 特徴的な技術力: AI API統合、非同期処理、リアルタイムUI、感情分析、シーン管理</text>
</svg>