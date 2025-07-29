"""
麻理チャット＆手紙生成 統合アプリケーション
"""
import streamlit as st
import logging
import os
import asyncio
import sys
from datetime import datetime
from dotenv import load_dotenv

# --- 基本設定 ---
# 非同期処理の問題を解決 (Windows向け)
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# .envファイルから環境変数を読み込み
load_dotenv()

# ロガー設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# --- 必要なモジュールのインポート ---

# << 麻理チャット用モジュール >>
from core_dialogue import DialogueGenerator
from core_sentiment import SentimentAnalyzer
from core_rate_limiter import RateLimiter
from core_scene_manager import SceneManager  # 復元したモジュール
from core_memory_manager import MemoryManager
from components_chat_interface import ChatInterface
from components_status_display import StatusDisplay
# << 手紙生成用モジュール >>
from letter_config import Config
from letter_logger import setup_logger as setup_letter_logger
from letter_generator import LetterGenerator
from letter_request_manager import RequestManager
from letter_user_manager import UserManager
from async_storage_manager import AsyncStorageManager
from async_rate_limiter import AsyncRateLimitManager

# --- 定数 ---
MAX_INPUT_LENGTH = 200
MAX_HISTORY_TURNS = 50

def get_event_loop():
    """
    セッションごとに単一のイベントループを取得または作成する
    """
    try:
        # 既に実行中のループがあればそれを返す
        return asyncio.get_running_loop()
    except RuntimeError:
        # 実行中のループがなければ、新しく作成
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

def run_async(coro):
    """
    Streamlitのセッションで共有されたイベントループを使って非同期関数を実行する
    """
    try:
        # 既存のループがあるかチェック
        loop = asyncio.get_running_loop()
        # 既存のループがある場合は、新しいタスクとして実行
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # 実行中のループがない場合は、新しいループで実行
        return asyncio.run(coro)

def update_background(scene_manager: SceneManager, theme: str):
    """現在のテーマに基づいて背景画像を動的に設定するCSSを注入する"""
    try:
        # SceneManagerから画像のURLを取得
        image_url = scene_manager.get_theme_url(theme)
        if not image_url:
            logger.warning(f"Theme '{theme}' has no valid image URL.")
            return

        # 改善されたCSSを生成
        background_css = f"""
        <style>
        .stApp {{
            background-image: url('{image_url}');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            background-repeat: no-repeat;
            transition: background-image 1.5s ease-in-out;
        }}
        
        .stApp > div:first-child {{
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(5px);
            min-height: 100vh;
            transition: background 1.5s ease-in-out, backdrop-filter 1.5s ease-in-out;
        }}
        </style>
        """
        st.markdown(background_css, unsafe_allow_html=True)
        logger.info(f"背景を'{theme}'に変更しました")
        
    except Exception as e:
        logger.error(f"背景更新エラー: {e}")
        # フォールバック背景を適用
        fallback_css = """
        <style>
        .stApp {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .stApp > div:first-child {
            background: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(5px);
        }
        </style>
        """
        st.markdown(fallback_css, unsafe_allow_html=True)

def inject_custom_css(file_path="streamlit_styles.css"):
    """静的なCSSファイルを読み込む"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        logger.warning(f"CSSファイルが見つかりません: {file_path}")



# --- ▼▼▼ 1. 初期化処理の一元管理 ▼▼▼ ---

@st.cache_resource
def initialize_all_managers():
    """
    アプリケーション全体で共有する全ての管理クラスを初期化する
    Streamlitのキャッシュ機能により、シングルトンとして振る舞う
    """
    logger.info("Initializing all managers...")
    # --- 手紙機能の依存モジュール ---
    letter_storage = AsyncStorageManager(Config.STORAGE_PATH)
    letter_rate_limiter = AsyncRateLimitManager(letter_storage, max_requests=Config.MAX_DAILY_REQUESTS)
    user_manager = UserManager(letter_storage)
    letter_request_manager = RequestManager(letter_storage, letter_rate_limiter)
    letter_generator = LetterGenerator()

    request_manager = RequestManager(letter_storage, letter_rate_limiter)

    # --- チャット機能の依存モジュール ---
    dialogue_generator = DialogueGenerator()
    sentiment_analyzer = SentimentAnalyzer()
    rate_limiter = RateLimiter()
    scene_manager = SceneManager()
    # memory_manager は セッション単位で作成するため、ここでは作成しない
    chat_interface = ChatInterface(max_input_length=MAX_INPUT_LENGTH)
    status_display = StatusDisplay()

    logger.info("All managers initialized.")
    return {
        # 手紙用
        "user_manager": user_manager,
        "request_manager": request_manager,
        "letter_generator": letter_generator,
        # チャット用
        "dialogue_generator": dialogue_generator,
        "sentiment_analyzer": sentiment_analyzer,
        "rate_limiter": rate_limiter,
        "scene_manager": scene_manager,
        # memory_manager は セッション単位で作成
        "chat_interface": chat_interface,
        "status_display": status_display,
    }

def initialize_session_state(managers):
    """
    アプリケーション全体のセッションステートを初期化する
    """
    # 強制リセットフラグ（開発時用）
    force_reset = os.getenv("FORCE_SESSION_RESET", "false").lower() == "true"
    
    # 共通のユーザーIDを生成
    if 'user_id' not in st.session_state or force_reset:
        # 手紙機能はUUID形式のユーザーIDを想定しているため、それに合わせる
        st.session_state.user_id = managers["user_manager"].generate_user_id()
        logger.info(f"New user session created with shared User ID: {st.session_state.user_id}")

    # チャット機能用のセッション初期化
    if 'chat_initialized' not in st.session_state or force_reset:
        st.session_state.chat = {
            "messages": [{"role": "assistant", "content": "何の用？遊びに来たの？", "is_initial": True}],
            "affection": 30,
            "scene_params": {"theme": "default"},
            "limiter_state": managers["rate_limiter"].create_limiter_state(),
            "scene_change_pending": None
        }
        # 特別な記憶の通知用
        st.session_state.memory_notifications = []
        st.session_state.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        st.session_state.chat_initialized = True
        
        # セッション単位でMemoryManagerを作成
        st.session_state.memory_manager = MemoryManager(history_threshold=10)
        
        if force_reset:
            logger.info("Session force reset - all data cleared")
        else:
            logger.info("Chat session state initialized.")
    
    # MemoryManagerがセッション状態にない場合は作成
    if 'memory_manager' not in st.session_state:
        st.session_state.memory_manager = MemoryManager(history_threshold=10)
    
    # 特別な記憶の通知用リストが存在しない場合は作成
    if 'memory_notifications' not in st.session_state:
        st.session_state.memory_notifications = []

    # 手紙機能用のセッションは特に追加の初期化は不要
    # (各関数内で必要なデータは都度非同期で取得するため)


# --- ▼▼▼ 2. UIコンポーネントの関数化 ▼▼▼ ---

def inject_custom_css(file_path="streamlit_styles.css"):
    """外部CSSファイルを読み込んで注入する"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            css_content = f.read()
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
            logger.info(f"CSSファイルを読み込みました: {file_path}")
    except FileNotFoundError:
        logger.warning(f"CSSファイルが見つかりません: {file_path}")
        # フォールバック用の基本スタイルを適用
        apply_fallback_css()
    except Exception as e:
        logger.error(f"CSS読み込みエラー: {e}")
        apply_fallback_css()

def apply_fallback_css():
    """フォールバック用の基本CSSを適用"""
    fallback_css = """
    <style>
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    }
    .stApp > div:first-child {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(5px);
        min-height: 100vh;
    }
    .stChatMessage {
        background: rgba(255, 255, 255, 0.95) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        margin: 8px 0 !important;
    }
    </style>
    """
    st.markdown(fallback_css, unsafe_allow_html=True)
    logger.info("フォールバック用CSSを適用しました")

def show_memory_notification(message: str):
    """特別な記憶の通知をポップアップ風に表示する"""
    notification_css = """
    <style>
    .memory-notification {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 12px;
        border: 2px solid #ffffff40;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
        margin: 10px 0;
        animation: slideIn 0.5s ease-out;
        text-align: center;
        font-weight: 500;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .memory-notification .icon {
        font-size: 1.2em;
        margin-right: 8px;
    }
    </style>
    """
    
    notification_html = f"""
    <div class="memory-notification">
        <span class="icon">🧠✨</span>
        {message}
    </div>
    """
    
    st.markdown(notification_css + notification_html, unsafe_allow_html=True)

def render_custom_chat_history(messages):
    """カスタムチャット履歴表示エリア"""
    if not messages:
        st.info("まだメッセージがありません。下のチャット欄で麻理に話しかけてみてください。")
        return
    
    # Streamlitの標準チャット表示を使用（より安全）
    for message in messages:
        role = message.get('role', 'assistant')
        content = message.get('content', '')
        is_initial = message.get('is_initial', False)
        
        with st.chat_message(role):
            if is_initial:
                st.markdown(f"**{content}**")
            else:
                st.markdown(content)


# === チャットタブの描画関数 ===
def render_chat_tab(managers):
    """「麻理と話す」タブのUIを描画する"""

    # --- サイドバー ---
    with st.sidebar:
        with st.expander("📊 ステータス", expanded=True):
            affection = st.session_state.chat['affection']
            st.metric(label="好感度", value=f"{affection} / 100")
            st.progress(affection / 100.0)
            stage_name = managers['sentiment_analyzer'].get_relationship_stage(affection)
            st.markdown(f"**関係性**: {stage_name}")
            
            # SceneManagerから現在のテーマ名を取得
            current_theme_name = st.session_state.chat['scene_params'].get("theme", "default")
            st.markdown(f"**現在のシーン**: {current_theme_name}")

        with st.expander("⚙️ 設定"):
            # ... (エクスポートやリセットボタンのロジックは省略) ...
            if st.button("🔄 会話をリセット", type="secondary", use_container_width=True):
                # チャット履歴を完全にリセット
                st.session_state.chat['messages'] = [{"role": "assistant", "content": "何の用？遊びに来たの？", "is_initial": True}]
                st.session_state.chat['affection'] = 30
                st.session_state.chat['scene_params'] = {"theme": "default"}
                st.session_state.chat['limiter_state'] = managers['rate_limiter'].create_limiter_state()
                
                # メモリマネージャーをクリア
                st.session_state.memory_manager.clear_memory()
                
                # 新しいユーザーIDを生成（完全リセット）
                st.session_state.user_id = managers["user_manager"].generate_user_id()
                
                st.success("会話を完全にリセットしました（新しいセッションとして開始）")
                st.rerun()

        if st.session_state.debug_mode:
            with st.expander("🛠️ デバッグ情報"):
                st.json({
                    "affection": st.session_state.chat['affection'],
                    "theme": st.session_state.chat['scene_params']['theme'],
                    "limiter_state": st.session_state.chat.get('limiter_state', {}),
                    "messages_count": len(st.session_state.chat['messages']),
                    "user_id": st.session_state.user_id,
                    "session_keys": list(st.session_state.keys()),
                    "memory_cache_size": len(st.session_state.memory_manager.important_words_cache)
                })

    # --- メインコンテンツ ---
    st.title("💬 麻理チャット")
    st.markdown("*捨てられたアンドロイド「麻理」との対話*")
    
    # 特別な記憶の通知を表示
    if st.session_state.memory_notifications:
        for notification in st.session_state.memory_notifications:
            show_memory_notification(notification)
        # 通知を表示したらクリア
        st.session_state.memory_notifications = []
    
    # チュートリアル用のexpander（中央寄せ）
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.expander("📖 初めてチャットする人へ", expanded=False):
            st.markdown("""
            ### 🤖 麻理について
            麻理は感情を持つアンドロイドです。あなたとの会話を通じて関係性が変化していきます。
            
            ### 💝 好感度システム
            - **会話の内容**によって好感度が上下します
            - **優しい言葉**をかけると好感度が上がります
            - **冷たい態度**だと好感度が下がることも...
            - サイドバーで現在の好感度を確認できます
            
            ### 🎭 シーン変更機能
            特定の場所について話すと、背景が自動的に変わります：
            - 🏖️ **ビーチ**や**海**の話 → 夕日のビーチ
            - ⛩️ **神社**や**お参り**の話 → 神社の境内
            - ☕ **カフェ**や**コーヒー**の話 → 午後のカフェ
            - 🐠 **水族館**や**魚**の話 → 夜の水族館
            - 🎆 **お祭り**や**花火**の話 → 夜祭り
            
            ### 💬 会話のコツ
            1. **自然な会話**を心がけてください
            2. **質問**をすると麻理が詳しく答えてくれます
            3. **感情**を込めた言葉は特に反応が良いです
            4. **200文字以内**でメッセージを送ってください
            
            ### ⚙️ 便利な機能
            - **サイドバー**：好感度やシーン情報を確認
            - **会話履歴**：過去の会話を振り返り
            - **リセット機能**：新しい関係から始めたい時に
            
            ---
            **準備ができたら、下のチャット欄で麻理に話しかけてみてください！** 😊
            """)
    
    st.markdown("---")
    
    # カスタムチャット履歴表示エリア
    render_custom_chat_history(st.session_state.chat['messages'])

    # メッセージ処理ロジック
    def process_chat_message(message: str):
        try:
            # レート制限チェック
            if 'limiter_state' not in st.session_state.chat:
                st.session_state.chat['limiter_state'] = managers['rate_limiter'].create_limiter_state()
            
            limiter_state = st.session_state.chat['limiter_state']
            if not managers['rate_limiter'].check_limiter(limiter_state):
                st.session_state.chat['limiter_state'] = limiter_state
                return "（…少し話すのが速すぎる。もう少し、ゆっくり話してくれないか？）"
            
            st.session_state.chat['limiter_state'] = limiter_state

            # 会話履歴を正しく構築（現在のメッセージは含まない）
            # 注意: この時点では現在のユーザーメッセージはまだ履歴に追加されていない
            user_messages = [msg['content'] for msg in st.session_state.chat['messages'] if msg['role'] == 'user']
            assistant_messages = [msg['content'] for msg in st.session_state.chat['messages'] if msg['role'] == 'assistant']
            
            # 最新の数ターンの履歴を取得（最大5ターン）
            history = []
            max_turns = min(5, min(len(user_messages), len(assistant_messages)))
            for i in range(max_turns):
                if i < len(user_messages) and i < len(assistant_messages):
                    history.append((user_messages[-(i+1)], assistant_messages[-(i+1)]))
            history.reverse()  # 時系列順に並び替え

            # 好感度更新
            affection, change_amount, change_reason = managers['sentiment_analyzer'].update_affection(
                message, st.session_state.chat['affection'], st.session_state.chat['messages']
            )
            st.session_state.chat['affection'] = affection
            stage_name = managers['sentiment_analyzer'].get_relationship_stage(affection)
            
            # シーン変更検知
            current_theme = st.session_state.chat['scene_params']['theme']
            new_theme = managers['scene_manager'].detect_scene_change(history, current_theme=current_theme)
            
            instruction = None
            if new_theme:
                logger.info(f"Scene change detected! From '{current_theme}' to '{new_theme}'.")
                st.session_state.chat['scene_params'] = managers['scene_manager'].update_scene_params(st.session_state.chat['scene_params'], new_theme)
                instruction = managers['scene_manager'].get_scene_transition_message(current_theme, new_theme)
                st.session_state.scene_change_flag = True

            # メモリ圧縮とサマリー取得
            compressed_messages, important_words = st.session_state.memory_manager.compress_history(
                st.session_state.chat['messages']
            )
            memory_summary = st.session_state.memory_manager.get_memory_summary()
            
            # 応答生成
            response = managers['dialogue_generator'].generate_dialogue(
                history, message, affection, stage_name, st.session_state.chat['scene_params'], instruction, memory_summary
            )
            return response if response else "…なんて言えばいいか分からない。"
        except Exception as e:
            logger.error(f"チャットメッセージ処理エラー: {e}", exc_info=True)
            return "（ごめん、システムの調子が悪いみたいだ。）"

    # ユーザー入力処理
    if user_input := st.chat_input("麻理に話しかける..."):
        if len(user_input) > MAX_INPUT_LENGTH:
            st.error(f"⚠️ メッセージは{MAX_INPUT_LENGTH}文字以内で入力してください。")
        else:
            # 応答を生成（履歴追加前に実行）
            with st.spinner("考え中..."):
                response = process_chat_message(user_input)
            
            # 応答生成後に両方のメッセージを履歴に追加
            st.session_state.chat['messages'].append({"role": "user", "content": user_input})
            st.session_state.chat['messages'].append({"role": "assistant", "content": response})
            
            # シーン変更があった場合はフラグをクリア
            if st.session_state.get('scene_change_flag', False):
                del st.session_state['scene_change_flag']
            
            # チャット履歴を更新するためにページを再読み込み
            st.rerun()

# === 手紙タブの描画関数 ===
def render_letter_tab(managers):
    """「手紙を受け取る」タブのUIを描画する"""
    st.title("✉️ おやすみ前の、一通の手紙")
    st.write("今日の終わりに、あなたのためだけにAIが手紙を綴ります。伝えたいテーマと時間を選ぶと、あなたがログインした時に手紙が届きます。")
    
    # 手紙機能のチュートリアル
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.expander("📝 手紙機能の使い方", expanded=False):
            st.markdown("""
            ### ✉️ 手紙機能について
            麻理があなたのために、心を込めて手紙を書いてくれる特別な機能です。
            
            ### 📅 利用方法
            1. **好感度を上げる**：手紙をリクエストするには好感度40以上が必要です
            2. **テーマを入力**：手紙に書いてほしい内容やテーマを入力
            3. **時間を選択**：手紙を書いてほしい深夜の時間を選択
            4. **リクエスト送信**：「この内容でお願いする」ボタンを押す
            5. **手紙を受け取り**：指定した時間に手紙が生成されます
            6. **会話に反映**：手紙を読んだ後、「会話に反映」ボタンで麻理との会話で話題にできます
            
            ### 💡 テーマの例
            - 「今日見た美しい夕日について」
            - 「最近読んだ本の感想」
            - 「季節の変わり目の気持ち」
            - 「大切な人への想い」
            - 「将来への希望や不安」
            
            ### ⏰ 生成時間
            - **深夜2時〜4時**の間で選択可能
            - 静かな夜の時間に、ゆっくりと手紙を綴ります
            - **1日1通まで**リクエスト可能
            
            ### 💝 利用条件
            - **好感度40以上**が必要です
            - 麻理との会話を重ねて関係を深めてください
            
            ### 📖 手紙の確認
            - 生成された手紙は下の「あなたへの手紙」で確認できます
            - 過去の手紙も保存されているので、いつでも読み返せます
            
            ---
            **心に残るテーマを入力して、麻理からの特別な手紙を受け取ってみてください** 💌
            """)

    user_id = st.session_state.user_id
    user_manager = managers['user_manager']
    request_manager = managers['request_manager']

    st.divider()

    # --- 手紙のリクエストフォーム ---
    st.subheader("新しい手紙をリクエストする")
    
    # 現在の好感度を取得
    current_affection = st.session_state.chat['affection']
    required_affection = 40
    
    # 好感度制限チェック
    if current_affection < required_affection:
        st.warning(f"💔 手紙をリクエストするには好感度が{required_affection}以上必要です。現在の好感度: {current_affection}")
        st.info("麻理ともっと会話して、関係を深めてから手紙をお願いしてみてください。")
        return
    
    try:
        request_status = run_async(request_manager.get_user_request_status(user_id))
    except Exception as e:
        logger.error(f"リクエスト状況取得エラー: {e}")
        request_status = {"has_request": False}

    if request_status.get("has_request"):
        status = request_status.get('status', 'unknown')
        hour = request_status.get('generation_hour')
        if status == 'pending':
            st.info(f"本日分のリクエストは受付済みです。深夜{hour}時頃に手紙が生成されます。")
        else:
            st.success("本日分の手紙は処理済みです。下記の一覧からご確認ください。")
    else:
        # 好感度が十分な場合のみフォームを表示
        st.success(f"💝 好感度{current_affection}で手紙をリクエストできます！")
        
        with st.form("letter_request_form"):
            theme = st.text_input("手紙のテーマ", placeholder="例：最近見た美しい景色について")
            generation_hour = st.selectbox(
                "手紙を書いてほしい時間",
                options=Config.BATCH_SCHEDULE_HOURS,
                format_func=lambda h: f"深夜 {h}時"
            )
            submitted = st.form_submit_button("この内容でお願いする")

            if submitted:
                if not theme:
                    st.error("テーマを入力してください。")
                else:
                    with st.spinner("リクエストを送信中..."):
                        try:
                            # 好感度情報も一緒に送信
                            success, message = run_async(
                                request_manager.submit_request(user_id, theme, generation_hour, affection=current_affection)
                            )
                        except Exception as e:
                            logger.error(f"リクエスト送信エラー: {e}")
                            success, message = False, "リクエストの送信に失敗しました。しばらく後でお試しください。"
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

    st.divider()

    # --- 過去の手紙一覧 ---
    st.subheader("あなたへの手紙")
    with st.spinner("手紙の履歴を読み込んでいます..."):
        try:
            history = run_async(user_manager.get_user_letter_history(user_id, limit=10))
        except Exception as e:
            logger.error(f"手紙履歴取得エラー: {e}")
            history = []

    if not history:
        st.info("まだ手紙はありません。最初の手紙をリクエストしてみましょう。")
    else:
        for letter_info in history:
            date = letter_info.get("date")
            theme = letter_info.get("theme")
            status = letter_info.get("status", "unknown")

            with st.expander(f"{date} - テーマ: {theme} ({status})"):
                if status == "completed":
                    try:
                        user_data = run_async(user_manager.storage.get_user_data(user_id))
                        content = user_data.get("letters", {}).get(date, {}).get("content", "内容の取得に失敗しました。")
                        st.markdown(content.replace("\n", "\n\n"))
                        
                        # 手紙を会話に反映するボタン
                        col1, col2 = st.columns([3, 1])
                        with col2:
                            if st.button(f"💬 会話に反映", key=f"reflect_{date}", help="この手紙の内容を麻理との会話で話題にします"):
                                # 手紙の内容をメモリに追加
                                letter_summary = f"手紙のテーマ「{theme}」について麻理が書いた内容: {content[:200]}..."
                                memory_notification = st.session_state.memory_manager.add_important_memory("letter_content", letter_summary)
                                
                                # 手紙について話すメッセージを自動追加
                                letter_message = f"この前書いてくれた「{theme}」についての手紙、読ませてもらったよ。"
                                st.session_state.chat['messages'].append({"role": "user", "content": letter_message})
                                
                                # 麻理の応答を生成
                                response = f"あの手紙、読んでくれたんだ...。「{theme}」について書いたとき、あなたのことを思いながら一生懸命考えたんだ。どう思った？"
                                st.session_state.chat['messages'].append({"role": "assistant", "content": response})
                                
                                # 特別な記憶の通知をセッション状態に保存
                                st.session_state.memory_notifications.append(memory_notification)
                                st.success("手紙の内容が会話に反映されました！チャットタブで確認してください。")
                                st.rerun()
                                
                    except Exception as e:
                        logger.error(f"手紙内容取得エラー: {e}")
                        st.error("手紙の内容を読み込めませんでした。")
                elif status == "pending":
                    st.write("この手紙はまだ生成中です。")
                else:
                    st.write("この手紙は生成に失敗しました。")


# --- ▼▼▼ 3. メイン実行ブロック ▼▼▼ ---

def main():
    """メイン関数"""
    st.set_page_config(
        page_title="麻理プロジェクト", page_icon="🤖",
        layout="centered", initial_sidebar_state="auto"
    )

    # event loopの安全な設定
    try:
        # 既存のループがあるかチェック
        asyncio.get_running_loop()
    except RuntimeError:
        # 実行中のループがない場合のみ新しいループを設定
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # 全ての依存モジュールを初期化
    managers = initialize_all_managers()
    
    # セッションステートを初期化
    initialize_session_state(managers)

    # CSSを適用
    inject_custom_css()

    # 背景を更新
    update_background(managers['scene_manager'], st.session_state.chat['scene_params']['theme'])

    # タブを作成
    chat_tab, letter_tab = st.tabs(["💬 麻理と話す", "✉️ 手紙を受け取る"])

    with chat_tab:
        render_chat_tab(managers)

    with letter_tab:
        render_letter_tab(managers)

if __name__ == "__main__":
    if not Config.validate_config():
        logger.critical("手紙機能の設定にエラーがあります。アプリケーションを起動できません。")
    else:
        main()