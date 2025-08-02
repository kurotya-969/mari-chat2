---
---
title: 麻理チャット＆手紙生成 統合アプリ
emoji: 🐕
colorFrom: pink
colorTo: purple
sdk: streamlit
sdk_version: 1.28.0
app_file: main_app.py
pinned: false
---

# 🐕 麻理チャット＆手紙生成 統合アプリ

**麻理**という名前の感情豊かな少女型アンドロイドとの対話を楽しめる、高機能なAIチャットアプリケーションです。Together AIのAPIを使用し、リアルタイムチャットと非同期手紙生成の両方に対応しています。

## ✨ 主要機能

### 🐕 **ポチ機能（本音表示アシスタント）**
- 画面右下の犬のアシスタント「ポチ」が麻理の本音を察知
- ワンクリックで全メッセージの本音を一括表示/非表示
- ツンデレキャラクターの「デレ」部分を楽しめる
- レスポンシブ対応で様々な画面サイズに最適化

### 🔓 **セーフティ機能**
- 左サイドバーに統合されたセーフティ切り替えボタン
- 有効時は緑色、解除時は赤色で視覚的に分かりやすい表示
- より大胆で直接的な表現を有効にするモード
- 環境変数で独自のプロンプトを設定可能

### ✉️ **非同期手紙生成**
- 指定した時間に自動的に手紙を生成・配信
- テーマ選択機能（日常、恋愛、励まし、感謝など）
- バックグラウンド処理による効率的な生成

### 🎨 **高度なUI機能**
- **動的背景システム**: 会話内容に応じて背景が自動変化
- **好感度システム**: 関係性の進展を数値とステージで表示
- **メモリ管理**: 長期記憶と重要な会話の自動保存
- **セッション分離**: 複数ユーザー間での完全な独立性

### 🛡️ **堅牢なシステム**
- **レート制限**: API使用量の適切な制御
- **エラー回復**: 障害時の自動復旧機能
- **セッション管理**: 強化されたセッション分離とデータ整合性

## 🚀 セットアップ方法

### Hugging Face Spacesでの実行（推奨）

Hugging Face Spacesでは、セッション管理サーバーが自動的に起動されます。

#### 自動起動機能
- アプリケーション起動時にFastAPIサーバーが自動で起動
- セッション管理機能が完全に利用可能
- Cookie-based認証によるセキュアなセッション管理

#### 環境変数設定
Hugging Face Spacesの設定で以下の環境変数を設定してください：

```
TOGETHER_API_KEY=your_together_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

1. **リポジトリのインポート**
   - このリポジトリをHugging Face Spacesにインポート
   - または[デモサイト](https://huggingface.co/spaces/your-space-name)で直接体験

2. **Spaces設定**
   - **SDK**: Streamlit
   - **Python**: 3.10+
   - **Hardware**: CPU Basic（2GB RAM）以上推奨
   - **App File**: `spaces/main_app.py`

3. **必須環境変数**
   ```bash
   TOGETHER_API_KEY=your_together_api_key_here
   ```

4. **オプション環境変数**
   ```bash
   # 通常モード用カスタムプロンプト
   SYSTEM_PROMPT_MARI=your_custom_prompt_here
   
   # セーフティ解除モード用プロンプト
   SYSTEM_PROMPT_URA=your_ura_mode_prompt_here
   
   # デバッグモード有効化
   DEBUG_MODE=true
   
   # 手紙生成設定
   MAX_DAILY_REQUESTS=5
   BATCH_SCHEDULE_HOURS=2,3,4
   ```

#### APIキーの取得方法

1. [Together AI](https://api.together.xyz/)にアクセス
2. アカウント作成・ログイン
3. APIキーを生成
4. Hugging Face Spacesの「Settings」→「Variables and secrets」で設定

### ローカル環境での実行

1. **リポジトリをクローン**
   ```bash
   git clone <repository-url>
   cd mari-chat-app
   ```

2. **依存関係をインストール**
   ```bash
   pip install -r spaces/requirements.txt
   ```

3. **環境変数を設定**
   `spaces/.env`ファイルを作成：
   ```bash
   # 必須設定
   TOGETHER_API_KEY=your_together_api_key_here
   
   # オプション設定
   SYSTEM_PROMPT_MARI=your_custom_prompt_here
   SYSTEM_PROMPT_URA=your_ura_mode_prompt_here
   DEBUG_MODE=true
   
   # 手紙機能設定
   MAX_DAILY_REQUESTS=5
   STORAGE_PATH=/tmp/letters.json
   BATCH_SCHEDULE_HOURS=2,3,4
   ASYNC_LETTER_ENABLED=true
   ```

4. **アプリケーションを実行**
   ```bash
   cd spaces
   streamlit run main_app.py
   ```

5. **ブラウザでアクセス**
   - 自動的にブラウザが開きます
   - 手動の場合: `http://localhost:8501`

### Dockerでの実行

1. **Dockerイメージをビルド**
   ```bash
   docker build -t mari-chat-app .
   ```

2. **コンテナを実行**
   ```bash
   docker run -p 8501:8501 \
     -e TOGETHER_API_KEY=your_api_key_here \
     -e DEBUG_MODE=true \
     mari-chat-app
   ```

3. **docker-composeを使用**
   ```bash
   docker-compose up -d
   ```

4. **環境変数ファイルを使用**
   ```bash
   docker run -p 8501:8501 --env-file spaces/.env mari-chat-app
   ```

## 📖 使用方法

### 🎭 チャット機能

#### 基本的な使い方
1. **メッセージ入力**: 画面下部のテキスト入力欄にメッセージを入力
2. **送信**: 送信ボタンをクリック
3. **応答確認**: 麻理からの応答が表示されます
4. **本音表示**: 画面右下のポチ（🐕）をクリックして本音を確認

#### ポチ機能の使い方
- **🐕 ポチ**: 画面右下に固定配置された犬のアシスタント
- **ワンクリック**: ポチをクリックすると全メッセージの本音が一括表示
- **吹き出し**: 「ポチは麻理の本音を察知したようだ・・・」の可愛い吹き出し付き
- **背景色変化**: 本音表示時は暖色系の背景に変化
- **レスポンシブ**: 画面サイズに応じて適切にサイズ調整

#### セーフティ機能
- **🔒/🔓ボタン**: 左サイドバー最上部のセーフティ切り替えボタン
- **色分け表示**: 有効時は緑色、解除時は赤色で一目で分かる
- **表現変化**: より大胆で直接的な表現が有効になる
- **本音への影響**: セーフティ解除時はより踏み込んだ感情表現

### ✉️ 手紙機能

#### 手紙のリクエスト
1. **「手紙を受け取る」タブ**を選択
2. **テーマ選択**: 日常、恋愛、励まし、感謝、お疲れ様、おやすみから選択
3. **配信時間設定**: 希望する受け取り時間を指定
4. **リクエスト送信**: 「手紙をリクエスト」ボタンをクリック

#### 手紙の受け取り
- **自動生成**: 指定時間にバックグラウンドで生成
- **通知**: 新しい手紙が届くとチャットで通知
- **履歴確認**: 過去の手紙履歴を確認可能

### 🎛️ サイドバー機能

#### セーフティ機能（最上部）
- **🔒/🔓ボタン**: セーフティの有効/無効を色で表示
- **緑色**: セーフティ有効（通常モード）
- **赤色**: セーフティ解除（大胆モード）

#### ステータス表示
- **好感度**: 白色の文字で表示される好感度（0-100）とプログレスバー
- **関係性**: 警戒→困惑→信頼→親密の段階表示
- **現在のシーン**: 背景シーンの名前

#### 設定機能
- **🔄会話をリセット**: 大きな文字で表示される会話リセットボタン
- **🛠️デバッグ情報**: 詳細なシステム状態を表示（DEBUG_MODE=true時）

### 🎨 高度な機能

#### 自動シーン変更
- **キーワード検出**: 「水族館」「カフェ」「神社」などの場所を話題にすると自動変化
- **背景切り替え**: 会話内容に応じて背景画像が動的に変化
- **雰囲気演出**: シーンに合わせた色調とエフェクト

#### メモリ管理
- **長期記憶**: 重要な会話内容を自動的に記憶
- **要約機能**: 長い会話履歴を効率的に圧縮
- **特別な記憶**: 印象的な出来事を特別に保存

#### セッション分離
- **ユーザー独立**: 各ユーザーの会話は完全に分離
- **データ保護**: 他のユーザーの操作による影響なし
- **整合性チェック**: セッション状態の自動検証と復旧

## 🎨 シーン一覧

| シーン名 | 説明 | 背景画像 | トリガーワード |
|---------|------|----------|---------------|
| `default` | デフォルトの部屋 | 温かみのある室内 | 部屋、家 |
| `room_night` | 夜の部屋 | 夜景が見える室内 | 夜、寝る |
| `beach_sunset` | 夕暮れのビーチ | 美しい夕日のビーチ | ビーチ、海、夕日 |
| `festival_night` | 夜のお祭り | 賑やかな夜祭り | お祭り、花火、屋台 |
| `shrine_day` | 昼間の神社 | 静寂な神社の境内 | 神社、お参り、鳥居 |
| `cafe_afternoon` | 午後のカフェ | 落ち着いたカフェ | カフェ、コーヒー |
| `aquarium_night` | 夜の水族館 | 幻想的な水族館 | 水族館、魚、海洋 |

### シーン変更の仕組み
- **自動検出**: 会話内容から場所に関するキーワードを検出
- **スムーズ遷移**: 1.5秒のフェードイン・アウト効果
- **文脈適応**: 会話の流れに自然に溶け込む背景変化

## 🔧 技術仕様

### API情報
- **プロバイダー**: [Together AI](https://api.together.xyz/)
- **使用モデル**: `Qwen/Qwen3-235B-A22B-Instruct-2507-tput`（デフォルト）
- **レート制限**: 適応的制限により安定した動作
- **フォールバック**: API障害時は固定応答で継続動作

### システム要件
- **Python**: 3.8以上（3.10推奨）
- **メモリ**: 最小1GB、推奨2GB以上
- **ストレージ**: 100MB以上の空き容量
- **ネットワーク**: インターネット接続必須

### パフォーマンス
- **応答時間**: 通常2-5秒
- **同時接続**: 複数ユーザー対応
- **メモリ効率**: 自動圧縮により長期間の安定動作
- **セッション管理**: 強化された分離機能

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 🔑 APIキー関連
**問題**: APIキーエラーが発生する
**解決方法**:
- `TOGETHER_API_KEY`が正しく設定されているか確認
- [Together AI](https://api.together.xyz/)でAPIキーの有効性を確認
- 環境変数の再設定後、アプリを再起動

#### 🚀 起動・動作問題
**問題**: アプリが起動しない
**解決方法**:
- 依存関係の再インストール: `pip install -r spaces/requirements.txt`
- Pythonバージョン確認: `python --version`（3.8以上必須）
- ポート8501が使用中でないか確認

**問題**: 応答が生成されない
**解決方法**:
- インターネット接続を確認
- APIの利用制限状況を確認
- デバッグモードでエラーログを確認

#### 🐕 ポチ機能問題
**問題**: ポチが表示されない、または動作しない
**解決方法**:
- ブラウザのキャッシュをクリア
- 画面右下にポチが固定表示されているか確認
- 会話をリセットして再試行
- デバッグモードでHIDDEN形式の検出状況を確認

#### 💾 メモリ・セッション問題
**問題**: メモリエラーや会話履歴の問題
**解決方法**:
- サイドバーの「🔄会話をリセット」を実行
- ブラウザのキャッシュとCookieをクリア
- アプリの再起動

### 🛠️ デバッグ機能

#### デバッグモードの有効化
1. 環境変数で`DEBUG_MODE=true`を設定
2. または、サイドバーの「🛠️デバッグ情報」を展開

#### 確認できる情報
- **セッション分離状態**: ユーザー独立性の確認
- **メモリ統計**: 使用量と圧縮状況
- **API応答ログ**: リクエスト・レスポンスの詳細
- **ポチ機能統計**: HIDDEN形式の検出状況

#### ログファイルの場所
- **Streamlitログ**: コンソール出力
- **アプリケーションログ**: Python loggingモジュール
- **セッション情報**: デバッグモードで表示

## 👨‍💻 開発者向け情報

### プロジェクト構造

```
mari-chat-app/
├── spaces/                           # メインアプリケーション
│   ├── main_app.py                  # 統合メインアプリ
│   ├── components_chat_interface.py  # チャット機能（ポチ機能付き）
│   ├── components_dog_assistant.py  # ポチ（犬）アシスタント
│   ├── session_manager.py           # セッション分離管理
│   ├── core_dialogue.py             # 対話生成（HIDDEN形式対応）
│   ├── core_sentiment.py            # 感情分析・好感度システム
│   ├── core_scene_manager.py        # 動的背景システム
│   ├── core_memory_manager.py       # 長期記憶管理
│   ├── core_rate_limiter.py         # レート制限
│   ├── letter_*.py                  # 非同期手紙生成システム
│   ├── streamlit_styles.css         # カスタムCSS（ポチ機能含む）
│   ├── requirements.txt             # 依存関係
│   └── .env                         # 環境変数設定
├── .kiro/specs/                     # 機能仕様書
│   ├── ui-redesign/                 # UI再設計仕様
│   ├── async-letter-generation/     # 手紙機能仕様
│   └── session-isolation-fix/       # セッション分離仕様
├── test_*.py                        # テストスクリプト群
├── Dockerfile                       # Docker設定
├── docker-compose.yml              # Docker Compose設定
└── README.md                       # このファイル
```

### 🐕 ポチ機能の実装

#### 核となる仕組み
```python
# HIDDEN形式の検出
pattern = r'\[HIDDEN:(.*?)\](.*)'
has_hidden, visible, hidden = detect_hidden_content(message)

# 画面右下への固定配置
CSS: position: fixed; bottom: 20px; right: 20px; z-index: 1000;

# 全メッセージの一括制御
st.session_state.show_all_hidden = not st.session_state.show_all_hidden
```

#### カスタマイズポイント
- **プロンプト**: `SYSTEM_PROMPT_MARI`/`SYSTEM_PROMPT_URA`で隠された真実の生成を制御
- **レスポンシブ**: CSSメディアクエリで画面サイズ対応
- **検出ロジック**: `_detect_hidden_content()`で形式を変更可能
- **ポチの見た目**: `components_dog_assistant.py`でデザイン調整

### ✉️ 手紙機能の実装

#### 非同期処理アーキテクチャ
```python
# バックグラウンド生成
async def generate_letter_async(theme, user_id):
    # 非同期でAI生成
    
# スケジューラー
batch_scheduler.schedule_generation(user_id, theme, delivery_time)

# ストレージ管理
async_storage.save_letter(letter_data)
```

### 🛡️ セッション分離システム

#### 強化された分離機能
```python
class SessionManager:
    def __init__(self):
        self.session_id = id(st.session_state)
        self.user_id = None
        
    def validate_session_integrity(self):
        # セッション整合性チェック
```

### カスタマイズガイド

#### 新しいシーンの追加
1. `core_scene_manager.py`の`SCENE_CONFIGS`に追加
2. 背景画像URLを設定
3. トリガーワードを定義

#### プロンプトのカスタマイズ
```bash
# 通常モード
SYSTEM_PROMPT_MARI="あなたのカスタムプロンプト..."

# セーフティ解除モード  
SYSTEM_PROMPT_URA="より大胆なプロンプト..."
```

#### UIスタイルの変更
- `streamlit_styles.css`でカラーテーマ、アニメーション、レイアウトを調整
- CSS変数を使用した統一的なデザインシステム
- ポチの固定配置とレスポンシブ対応

### テスト機能

#### 提供されるテストスクリプト
- `test_mask_functionality.py`: ポチ機能の動作確認
- `test_multiple_hidden_fixed.py`: 複数HIDDEN形式の処理確認
- `test_hidden_format_issue.py`: HIDDEN形式の問題診断
- `debug_session_state.py`: セッション状態のデバッグ

#### テスト実行方法
```bash
python test_mask_functionality.py
python test_multiple_hidden_fixed.py
```

## 🤝 貢献・開発参加

### バグ報告・機能提案
- **Issues**: GitHubのIssuesでバグ報告や機能提案をお願いします
- **Discussion**: 新機能のアイデアや改善案の議論
- **Pull Request**: コード改善やバグ修正のPRを歓迎します

### 開発ガイドライン
1. **コードスタイル**: PEP 8に準拠
2. **テスト**: 新機能には対応するテストを追加
3. **ドキュメント**: 変更内容をREADMEに反映
4. **コミット**: 明確で説明的なコミットメッセージ

### 開発環境のセットアップ
```bash
# 開発用依存関係のインストール
pip install -r spaces/requirements.txt

# テストの実行
python -m pytest tests/

# コードフォーマット
black spaces/
flake8 spaces/
```

## 📄 ライセンス

このプロジェクトは**MITライセンス**の下で公開されています。

## 🙏 謝辞

- **Together AI**: 高品質なLLM APIの提供
- **Streamlit**: 直感的なWebアプリフレームワーク
- **コミュニティ**: バグ報告や機能提案をいただいた皆様

## 📞 サポート・連絡先

- **GitHub Issues**: バグ報告・機能提案
- **Discussions**: 一般的な質問・議論
- **Email**: 重要な問題やセキュリティ関連

## 🔄 更新履歴

### v2.1.0 (最新)
- 🐕 **ポチ機能**: 画面右下の犬アシスタントによる本音一括表示
- 🔓 **セーフティ統合**: 左サイドバーへの統合と色分け表示
- 📱 **レスポンシブ対応**: 様々な画面サイズに最適化
- 🎨 **UI簡素化**: 仮面ボタン削除によるシンプルな操作性
- ✉️ **非同期手紙生成**: バックグラウンド手紙生成
- 🛡️ **セッション分離強化**: マルチユーザー対応改善

### v2.0.0
- 🎭 **マスク機能**: 隠された真実の表示機能（現在はポチ機能に統合）
- 🔓 **セーフティ解除モード**: より大胆な表現モード
- ✉️ **非同期手紙生成**: バックグラウンド手紙生成
- 🛡️ **セッション分離強化**: マルチユーザー対応改善
- 🎨 **UI再設計**: モダンで直感的なインターフェース

### v1.0.0
- 基本的なチャット機能
- 好感度システム
- 動的背景変更
- メモリ管理機能

---

<div align="center">

**🐕 Made with ❤️ using Streamlit & Together AI 🐕**

*麻理とポチとの特別な時間をお楽しみください*

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Together AI](https://img.shields.io/badge/Together%20AI-000000?style=for-the-badge&logo=ai&logoColor=white)](https://together.ai/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)

</div>