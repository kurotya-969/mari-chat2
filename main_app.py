"""
麻理チャット＆手紙生成 統合アプリケーション
"""
import streamlit as st
import logging
import os
import asyncio
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from contextlib import contextmanager

# --- 基本設定 ---
# 非同期処理の問題を解決 (Windows向け)
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# .envファイルから環境変数を読み込み
load_dotenv()

# ロガー設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- セッション管理サーバー自動起動 ---
def start_session_server():
    """
    セッション管理サーバーを自動起動する
    Hugging Face Spacesでの実行時に必要
    """
    import subprocess
    import threading
    import requests
    import time
    
    def check_server_running(timeout=2):
        """サーバーが起動しているかチェック"""
        # Hugging Face Spacesでの実行を考慮してホストを動的に決定
        hosts_to_try = ["127.0.0.1", "localhost", "0.0.0.0"]
        port = 8000
        
        for host in hosts_to_try:
            try:
                response = requests.get(f"http://{host}:{port}/health", timeout=timeout)
                if response.status_code == 200:
                    logger.debug(f"サーバー接続成功: {host}:{port}")
                    return True
            except Exception:
                continue
        return False
    
    def run_server():
        """バックグラウンドでサーバーを起動"""
        try:
            logger.info("セッション管理サーバーをバックグラウンドで起動中...")
            
            # uvicornでサーバー起動（Hugging Face Spaces対応）
            import uvicorn
            
            # 実行環境に応じてホストを決定
            is_spaces = os.getenv("SPACE_ID") is not None
            host = "0.0.0.0" if is_spaces else "127.0.0.1"
            
            uvicorn.run(
                "session_api_server:app",
                host=host,
                port=8000,
                log_level="warning",  # ログレベルを下げてStreamlitログと混在を防ぐ
                access_log=False      # アクセスログを無効化
            )
        except Exception as e:
            logger.error(f"サーバー起動エラー: {e}")
    
    # 既にサーバーが起動しているかチェック
    if check_server_running():
        logger.info("✅ セッション管理サーバーは既に起動しています")
        return True
    
    try:
        # バックグラウンドでサーバー起動
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # サーバー起動待機（最大15秒、Hugging Face Spacesでは時間がかかる場合がある）
        max_wait = 15
        for i in range(max_wait):
            time.sleep(1)
            if check_server_running():
                logger.info(f"✅ セッション管理サーバー起動成功 ({i+1}秒)")
                return True
            if i < max_wait - 1:  # 最後の試行以外でログ出力
                logger.info(f"サーバー起動待機中... ({i+1}/{max_wait})")
        
        logger.warning("⚠️ セッション管理サーバー起動タイムアウト - フォールバックモードで継続")
        return False
        
    except Exception as e:
        logger.error(f"サーバー起動処理エラー: {e}")
        return False

# アプリケーション起動時にサーバーを自動起動
if 'server_started' not in st.session_state:
    st.session_state.server_started = start_session_server()
    if st.session_state.server_started:
        logger.info("🚀 セッション管理サーバー起動完了")
    else:
        logger.warning("⚠️ セッション管理サーバー起動失敗 - フォールバックモードで動作")


# --- 必要なモジュールのインポート ---

# << 麻理チャット用モジュール >>
from core_dialogue import DialogueGenerator
from core_sentiment import SentimentAnalyzer
from core_rate_limiter import RateLimiter
from core_scene_manager import SceneManager  # 復元したモジュール
from core_memory_manager import MemoryManager
from components_chat_interface import ChatInterface
from components_status_display import StatusDisplay
from components_dog_assistant import DogAssistant
from components_tutorial import TutorialManager
from session_manager import SessionManager, get_session_manager, validate_session_state, perform_detailed_session_validation
from session_api_client import SessionAPIClient
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
    """現在のテーマに基づいて背景画像を動的に設定するCSSを注入する（重複実行防止）"""
    # 現在のテーマと前回のテーマを比較
    last_theme = st.session_state.get('last_background_theme', '')
    if last_theme == theme:
        return  # 同じテーマの場合は更新しない
    
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
            background: rgba(250, 243, 224, 0.95);
            backdrop-filter: blur(5px);
            min-height: 100vh;
            transition: background 1.5s ease-in-out, backdrop-filter 1.5s ease-in-out;
        }}
        </style>
        """
        st.markdown(background_css, unsafe_allow_html=True)
        logger.info(f"背景を'{theme}'に変更しました")
        
        # 現在のテーマを記録
        st.session_state.last_background_theme = theme
        
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
        st.session_state.last_background_theme = theme

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
    dog_assistant = DogAssistant()
    tutorial_manager = TutorialManager()
    session_api_client = SessionAPIClient()

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
        "dog_assistant": dog_assistant,
        "tutorial_manager": tutorial_manager,
        "session_api_client": session_api_client,
    }

def initialize_session_state(managers, force_reset_override=False):
    """
    アプリケーション全体のセッションステートを初期化する
    SessionManagerを使用してセッション分離を強化
    
    Args:
        managers: 管理クラスの辞書
        force_reset_override: 強制リセットフラグ（フルリセット時に使用）
    """
    # 強制リセットフラグ（開発時用または明示的な指定）
    force_reset = force_reset_override or os.getenv("FORCE_SESSION_RESET", "false").lower() == "true"
    
    # 初回起動時はセッション検証をスキップ
    is_first_run = 'user_id' not in st.session_state
    
    # SessionManagerの初期化（セッション分離強化）
    session_manager = get_session_manager()
    
    # 初回起動時以外でセッション整合性チェックを実行
    if not is_first_run and not validate_session_state():
        logger.error("Session validation failed during initialization")
        # 復旧に失敗した場合は強制リセット
        force_reset = True
    
    # FastAPIセッション管理システムを使用してユーザーIDを取得
    session_api_client = managers["session_api_client"]
    
    # セッションIDを取得または生成（複数回呼び出し防止）
    if 'user_id' not in st.session_state or force_reset:
        session_id = session_api_client.get_or_create_session_id()
    else:
        session_id = st.session_state.user_id
        logger.debug(f"既存ユーザーID使用: {session_id[:8]}...")
    
    # ユーザーIDとしてセッションIDを使用
    session_changed = ('user_id' not in st.session_state or 
                      st.session_state.user_id != session_id or 
                      force_reset)
    
    if session_changed:
        st.session_state.user_id = session_id
        
        # SessionManagerにユーザーIDを設定
        session_manager.set_user_id(st.session_state.user_id)
        
        # セッション情報をログ出力
        session_info = {
            "user_id": st.session_state.user_id[:8] + "...",  # プライバシー保護のため一部のみ
            "session_id": id(st.session_state),
            "force_reset": force_reset,
            "session_changed": session_changed,
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"FastAPIセッション管理でユーザーセッション設定: {session_info}")
        
        # セッション固有の識別子を保存
        st.session_state._session_id = id(st.session_state)
    else:
        # 既存セッションの場合もSessionManagerにユーザーIDを設定
        if session_manager.user_id != st.session_state.user_id:
            session_manager.set_user_id(st.session_state.user_id)
        
        logger.debug(f"既存セッション継続使用: {st.session_state.user_id[:8]}...")

    # チャット機能用のセッション初期化
    if 'chat_initialized' not in st.session_state or force_reset:
        initial_message = "何の用？遊びに来たの？"
        st.session_state.chat = {
            "messages": [{"role": "assistant", "content": initial_message, "is_initial": True}],
            "affection": 30,
            "scene_params": {"theme": "default"},
            "limiter_state": managers["rate_limiter"].create_limiter_state(),
            "scene_change_pending": None,
            "ura_mode": False  # 裏モードフラグ
        }
        
        logger.info(f"チャット初期化完了 - 初期メッセージ: '{initial_message}'")
        # 特別な記憶の通知用
        st.session_state.memory_notifications = []
        # 好感度変化の通知用
        st.session_state.affection_notifications = []
        st.session_state.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        st.session_state.chat_initialized = True
        
        # セッション単位でMemoryManagerを作成
        st.session_state.memory_manager = MemoryManager(history_threshold=10)
        
        # Streamlitの内部チャット状態をクリア
        if 'messages' in st.session_state:
            del st.session_state.messages
        if 'last_sent_message' in st.session_state:
            del st.session_state.last_sent_message
        if 'user_message_input' in st.session_state:
            del st.session_state.user_message_input
        
        if force_reset:
            logger.info("Session force reset - all data cleared")
        else:
            logger.info("Chat session state initialized with SessionManager.")
    
    # MemoryManagerがセッション状態にない場合は作成
    if 'memory_manager' not in st.session_state:
        st.session_state.memory_manager = MemoryManager(history_threshold=10)
    
    # 特別な記憶の通知用リストが存在しない場合は作成
    if 'memory_notifications' not in st.session_state:
        st.session_state.memory_notifications = []
    
    # 好感度変化の通知用リストが存在しない場合は作成
    if 'affection_notifications' not in st.session_state:
        st.session_state.affection_notifications = []
    
    # 裏モードフラグが存在しない場合は作成
    if 'ura_mode' not in st.session_state.chat:
        st.session_state.chat['ura_mode'] = False
    
    # 最終的なセッション整合性チェック
    if not session_manager.validate_session_integrity():
        logger.warning("Session integrity check failed after initialization")
        session_manager.recover_session()

    # 初期化完了フラグを設定
    st.session_state._initialization_complete = True

    # 手紙機能用のセッションは特に追加の初期化は不要
    # (各関数内で必要なデータは都度非同期で取得するため)


# --- ▼▼▼ 2. UIコンポーネントの関数化 ▼▼▼ ---

def inject_custom_css(file_path="streamlit_styles.css"):
    """外部CSSファイルを読み込んで注入する（一度だけ実行）"""
    # CSS読み込み済みフラグをチェック
    if st.session_state.get('css_loaded', False):
        return
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            css_content = f.read()
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
            logger.info(f"CSSファイルを読み込みました: {file_path}")
            st.session_state.css_loaded = True
    except FileNotFoundError:
        logger.warning(f"CSSファイルが見つかりません: {file_path}")
        # フォールバック用の基本スタイルを適用
        apply_fallback_css()
        st.session_state.css_loaded = True
    except Exception as e:
        logger.error(f"CSS読み込みエラー: {e}")
        apply_fallback_css()
        st.session_state.css_loaded = True

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

def check_affection_milestone(old_affection: int, new_affection: int) -> str:
    """好感度のマイルストーンに到達したかチェックする"""
    milestones = {
        40: "🌸 麻理があなたに心を開き始めました！手紙をリクエストできるようになりました。",
        60: "💖 麻理があなたを信頼するようになりました！より深い会話ができるようになります。",
        80: "✨ 麻理があなたを大切な人だと思っています！特別な反応が増えるでしょう。",
        100: "🌟 麻理があなたを心から愛しています！最高の関係に到達しました！"
    }
    
    for milestone, message in milestones.items():
        if old_affection < milestone <= new_affection:
            return message
    
    return ""

def show_affection_notification(change_amount: int, change_reason: str, new_affection: int, is_milestone: bool = False):
    """好感度変化の通知を表示する（Streamlit標準コンポーネント使用）"""
    # 好感度変化がない場合は通知しない（マイルストーン以外）
    if change_amount == 0 and not is_milestone:
        return
    
    # マイルストーン通知の場合
    if is_milestone:
        st.balloons()  # 特別な演出
        st.success(f"🎉 **マイルストーン達成！** {change_reason} (現在の好感度: {new_affection}/100)")
    elif change_amount > 0:
        # 好感度上昇
        st.success(f"💕 **+{change_amount}** {change_reason} (現在の好感度: {new_affection}/100)")
    else:
        # 好感度下降
        st.info(f"💔 **{change_amount}** {change_reason} (現在の好感度: {new_affection}/100)")

def show_cute_thinking_animation():
    """かわいらしい考え中アニメーションを表示する"""
    thinking_css = """
    <style>
    .thinking-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 20px;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        border: 2px solid rgba(255, 182, 193, 0.6);
        box-shadow: 0 8px 32px rgba(255, 182, 193, 0.3);
        backdrop-filter: blur(10px);
        margin: 20px 0;
        animation: containerPulse 2s ease-in-out infinite;
    }
    
    .thinking-face {
        font-size: 3em;
        margin-bottom: 15px;
        animation: faceRotate 3s ease-in-out infinite;
        filter: drop-shadow(0 0 10px rgba(255, 105, 180, 0.5));
    }
    
    .thinking-text {
        font-size: 1.2em;
        color: #ff69b4;
        font-weight: 600;
        margin-bottom: 15px;
        animation: textGlow 1.5s ease-in-out infinite alternate;
    }
    
    .thinking-dots {
        display: flex;
        gap: 8px;
    }
    
    .thinking-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: linear-gradient(45deg, #ff69b4, #ff1493);
        animation: dotBounce 1.4s ease-in-out infinite;
    }
    
    .thinking-dot:nth-child(1) { animation-delay: 0s; }
    .thinking-dot:nth-child(2) { animation-delay: 0.2s; }
    .thinking-dot:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes containerPulse {
        0%, 100% { transform: scale(1); box-shadow: 0 8px 32px rgba(255, 182, 193, 0.3); }
        50% { transform: scale(1.02); box-shadow: 0 12px 40px rgba(255, 182, 193, 0.5); }
    }
    
    @keyframes faceRotate {
        0%, 100% { transform: rotate(0deg); }
        25% { transform: rotate(-5deg); }
        75% { transform: rotate(5deg); }
    }
    
    @keyframes textGlow {
        0% { text-shadow: 0 0 5px rgba(255, 105, 180, 0.5); }
        100% { text-shadow: 0 0 20px rgba(255, 105, 180, 0.8), 0 0 30px rgba(255, 105, 180, 0.6); }
    }
    
    @keyframes dotBounce {
        0%, 80%, 100% { transform: translateY(0); opacity: 0.7; }
        40% { transform: translateY(-15px); opacity: 1; }
    }
    
    .sound-wave {
        display: flex;
        gap: 3px;
        margin-top: 10px;
    }
    
    .sound-bar {
        width: 4px;
        height: 20px;
        background: linear-gradient(to top, #ff69b4, #ff1493);
        border-radius: 2px;
        animation: soundWave 1s ease-in-out infinite;
    }
    
    .sound-bar:nth-child(1) { animation-delay: 0s; }
    .sound-bar:nth-child(2) { animation-delay: 0.1s; }
    .sound-bar:nth-child(3) { animation-delay: 0.2s; }
    .sound-bar:nth-child(4) { animation-delay: 0.3s; }
    .sound-bar:nth-child(5) { animation-delay: 0.4s; }
    
    @keyframes soundWave {
        0%, 100% { height: 20px; }
        50% { height: 35px; }
    }
    </style>
    """
    
    thinking_html = """
    <div class="thinking-container">
        <div class="thinking-face">🤔</div>
        <div class="thinking-text">麻理が考え中...</div>
        <div class="thinking-dots">
            <div class="thinking-dot"></div>
            <div class="thinking-dot"></div>
            <div class="thinking-dot"></div>
        </div>
        <div class="sound-wave">
            <div class="sound-bar"></div>
            <div class="sound-bar"></div>
            <div class="sound-bar"></div>
            <div class="sound-bar"></div>
            <div class="sound-bar"></div>
        </div>
        <div style="margin-top: 10px; font-size: 0.9em; color: #ff69b4; opacity: 0.8;">
            💭 あんたのために一生懸命考えてるんだから...
        </div>
    </div>
    """
    
    # 音効果のJavaScript（Web Audio APIを使用した実際の音生成）
    sound_js = """
    <script>
    // Web Audio APIを使用した音効果生成
    function playThinkingSound() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // 柔らかい思考音を生成
            const oscillator1 = audioContext.createOscillator();
            const oscillator2 = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            // 周波数設定（優しい音色）
            oscillator1.frequency.setValueAtTime(220, audioContext.currentTime); // A3
            oscillator2.frequency.setValueAtTime(330, audioContext.currentTime); // E4
            
            // 波形設定（柔らかいサイン波）
            oscillator1.type = 'sine';
            oscillator2.type = 'sine';
            
            // 音量設定（控えめに）
            gainNode.gain.setValueAtTime(0, audioContext.currentTime);
            gainNode.gain.linearRampToValueAtTime(0.1, audioContext.currentTime + 0.1);
            gainNode.gain.linearRampToValueAtTime(0.05, audioContext.currentTime + 0.5);
            gainNode.gain.linearRampToValueAtTime(0, audioContext.currentTime + 1.0);
            
            // 接続
            oscillator1.connect(gainNode);
            oscillator2.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            // 再生
            oscillator1.start(audioContext.currentTime);
            oscillator2.start(audioContext.currentTime);
            oscillator1.stop(audioContext.currentTime + 1.0);
            oscillator2.stop(audioContext.currentTime + 1.0);
            
            console.log("🎵 麻理の思考音を再生中...");
            
        } catch (error) {
            console.log("音声再生はサポートされていません:", error);
        }
    }
    
    // 視覚的な音波エフェクトの強化
    setTimeout(() => {
        const soundBars = document.querySelectorAll('.sound-bar');
        soundBars.forEach((bar, index) => {
            bar.style.animationDuration = (0.8 + Math.random() * 0.4) + 's';
        });
        
        // 音効果を再生（ユーザーインタラクション後のみ）
        playThinkingSound();
    }, 100);
    
    // 定期的な音波効果
    setInterval(() => {
        const soundBars = document.querySelectorAll('.sound-bar');
        if (soundBars.length > 0) {
            soundBars.forEach((bar, index) => {
                const randomHeight = 15 + Math.random() * 25;
                bar.style.height = randomHeight + 'px';
            });
        }
    }, 200);
    </script>
    """
    
    return st.markdown(thinking_css + thinking_html + sound_js, unsafe_allow_html=True)

@contextmanager
def cute_thinking_spinner():
    """かわいらしい考え中アニメーション付きコンテキストマネージャー"""
    # アニメーション表示用のプレースホルダー
    placeholder = st.empty()
    
    try:
        # アニメーション開始
        with placeholder.container():
            show_cute_thinking_animation()
        
        yield
        
    finally:
        # アニメーション終了
        placeholder.empty()

def render_custom_chat_history(messages, chat_interface):
    """カスタムチャット履歴表示エリア（マスク機能付き）"""
    if not messages:
        st.info("まだメッセージがありません。下のチャット欄で麻理に話しかけてみてください。")
        return
    
    # デバッグ: 初期メッセージの存在確認
    initial_messages = [msg for msg in messages if msg.get('is_initial', False)]
    if initial_messages:
        logger.debug(f"初期メッセージ確認: {len(initial_messages)}件 - 内容: '{initial_messages[0].get('content', '')}'")
    else:
        logger.warning("初期メッセージが見つかりません")
    
    # 拡張されたチャットインターフェースを使用（マスク機能付き）
    chat_interface.render_chat_history(messages)


# === チャットタブの描画関数 ===
def render_chat_tab(managers):
    """「麻理と話す」タブのUIを描画する"""
    
    # チュートリアル機能の自動チェック
    tutorial_manager = managers['tutorial_manager']
    tutorial_manager.auto_check_completions()
    
    # チュートリアル案内をチャットタブに表示
    tutorial_manager.render_chat_tutorial_guide()

    # --- サイドバー ---
    with st.sidebar:
        # セーフティ機能を左サイドバーに統合
        current_mode = st.session_state.chat.get('ura_mode', False)
        safety_color = "#ff4757" if current_mode else "#2ed573"  # 赤：解除、緑：有効
        safety_text = "セーフティ解除" if current_mode else "セーフティ有効"
        safety_icon = "🔓" if current_mode else "🔒"
        
        # セーフティボタンのカスタムCSS
        safety_css = f"""
        <style>
        .safety-button {{
            background-color: {safety_color};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 15px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            margin-bottom: 15px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        .safety-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }}
        </style>
        """
        st.markdown(safety_css, unsafe_allow_html=True)
        
        if st.button(f"{safety_icon} {safety_text}", type="primary" if current_mode else "secondary", 
                    help="麻理のセーフティ機能を切り替えます", use_container_width=True):
            st.session_state.chat['ura_mode'] = not current_mode
            new_mode = st.session_state.chat['ura_mode']
            
            # チュートリアルステップ3を完了
            tutorial_manager.check_step_completion(3, True)
            
            if new_mode:
                st.success("🔓 セーフティ解除モードに切り替えました！")
            else:
                st.info("🔒 セーフティ有効モードに戻しました。")
            st.rerun()

        with st.expander("📊 ステータス", expanded=True):
            affection = st.session_state.chat['affection']
            
            # 好感度の文字を白くするためのCSS
            affection_css = """
            <style>
            .affection-label {
                color: white !important;
                font-weight: bold;
                font-size: 16px;
                margin-bottom: 10px;
            }
            </style>
            """
            st.markdown(affection_css, unsafe_allow_html=True)
            st.markdown('<div class="affection-label">好感度</div>', unsafe_allow_html=True)
            
            st.metric(label="", value=f"{affection} / 100")
            st.progress(affection / 100.0)
            stage_name = managers['sentiment_analyzer'].get_relationship_stage(affection)
            st.markdown(f"**関係性**: {stage_name}")
            
            # SceneManagerから現在のテーマ名を取得
            current_theme_name = st.session_state.chat['scene_params'].get("theme", "default")
            st.markdown(f"**現在のシーン**: {current_theme_name}")



        with st.expander("⚙️ 設定"):
            # 設定ボタン内の表示を大きくするCSS
            settings_css = """
            <style>
            .settings-content {
                font-size: 18px !important;
            }
            .settings-content .stButton > button {
                font-size: 18px !important;
                padding: 12px 20px !important;
                height: auto !important;
            }
            .settings-content .stButton > button div {
                font-size: 18px !important;
            }
            </style>
            """
            st.markdown(settings_css, unsafe_allow_html=True)
            
            # 設定コンテンツをラップ
            st.markdown('<div class="settings-content">', unsafe_allow_html=True)
            
            # ... (エクスポートやリセットボタンのロジックは省略) ...
            if st.button("🔄 会話をリセット", type="secondary", use_container_width=True, help="あなたの会話履歴のみをリセットします（他のユーザーには影響しません）"):
                # チャット履歴を完全にリセット
                st.session_state.chat['messages'] = [{"role": "assistant", "content": "何の用？遊びに来たの？", "is_initial": True}]
                st.session_state.chat['affection'] = 30
                st.session_state.chat['scene_params'] = {"theme": "default"}
                st.session_state.chat['limiter_state'] = managers['rate_limiter'].create_limiter_state()
                st.session_state.chat['ura_mode'] = False  # 裏モードもリセット
                
                # メモリマネージャーをクリア
                st.session_state.memory_manager.clear_memory()
                
                # Streamlitの内部チャット状態もクリア
                if 'messages' in st.session_state:
                    del st.session_state.messages
                if 'last_sent_message' in st.session_state:
                    del st.session_state.last_sent_message
                if 'user_message_input' in st.session_state:
                    del st.session_state.user_message_input
                if 'message_flip_states' in st.session_state:
                    del st.session_state.message_flip_states
                
                # 新しいセッションIDを生成（完全リセット）
                session_api_client = managers["session_api_client"]
                
                # セッションをリセット
                new_session_id = session_api_client.reset_session()
                st.session_state.user_id = new_session_id
                
                st.success("会話を完全にリセットしました（新しいセッションとして開始）")
                st.rerun()
            
            # フルリセットボタン（Cookie含む完全リセット）
            st.markdown("---")
            st.markdown("**⚠️ 危険な操作**")
            
            if st.button("🔥 フルリセット（Cookie含む）", 
                        type="secondary", 
                        use_container_width=True, 
                        help="Cookie含む全データを完全にリセットします（ブラウザセッションも新規作成）"):
                
                # 確認ダイアログ
                if 'full_reset_confirm' not in st.session_state:
                    st.session_state.full_reset_confirm = False
                
                if not st.session_state.full_reset_confirm:
                    st.session_state.full_reset_confirm = True
                    st.warning("⚠️ 本当にフルリセットしますか？この操作は取り消せません。")
                    st.info("Cookie削除→新規セッション作成を実行します。もう一度ボタンを押してください。")
                    st.rerun()
                else:
                    # フルリセット実行
                    session_api_client = managers["session_api_client"]
                    
                    try:
                        # プログレスバーで進行状況を表示
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        status_text.text("🔄 フルリセット開始...")
                        progress_bar.progress(10)
                        
                        # 1. フルリセット実行（Cookie削除→新規セッション作成）
                        status_text.text("🍪 Cookie削除中...")
                        progress_bar.progress(30)
                        
                        reset_result = session_api_client.full_reset_session()
                        
                        if reset_result['success']:
                            status_text.text("✅ Cookie削除完了、新規セッション作成中...")
                            progress_bar.progress(60)
                            
                            # 2. Streamlitセッション状態を完全クリア
                            keys_to_clear = list(st.session_state.keys())
                            for key in keys_to_clear:
                                if key not in ['_session_id', 'session_info']:  # 必要なキーは保持
                                    del st.session_state[key]
                            
                            # CSS読み込みフラグもリセット
                            st.session_state.css_loaded = False
                            st.session_state.last_background_theme = ''
                            st.session_state._initialization_complete = False
                            
                            # メッセージ処理キャッシュもクリア
                            cache_keys_to_clear = [key for key in st.session_state.keys() if key.startswith('processed_')]
                            for cache_key in cache_keys_to_clear:
                                del st.session_state[cache_key]
                            
                            status_text.text("🔄 セッション状態初期化中...")
                            progress_bar.progress(80)
                            
                            # 3. 新しいユーザーIDを設定
                            if reset_result.get('new_session_id'):
                                # 完全なセッションIDを取得（表示用は短縮版）
                                full_session_id = st.session_state.session_info.get('session_id')
                                st.session_state.user_id = full_session_id
                            
                            # 4. 初期状態を再構築（強制リセット）
                            initialize_session_state(managers, force_reset_override=True)
                            
                            # 5. MemoryManagerの完全クリア（念のため）
                            if hasattr(st.session_state, 'memory_manager'):
                                st.session_state.memory_manager.clear_memory()
                                logger.info("MemoryManager完全クリア実行")
                            
                            # 6. SessionManagerのデータもリセット
                            session_manager = get_session_manager()
                            session_manager.reset_session_data()
                            logger.info("SessionManagerデータリセット実行")
                            
                            status_text.text("🎉 フルリセット完了！")
                            progress_bar.progress(100)
                            
                            # 成功メッセージ
                            st.success(f"🔥 フルリセット完了！")
                            st.info(f"📊 Cookie削除: {'✅' if reset_result.get('cookie_reset') else '❌'}")
                            st.info(f"🆕 新規セッション: {'✅' if reset_result.get('session_created') else '❌'}")
                            st.info(f"🔄 旧→新: {reset_result.get('old_session_id')} → {reset_result.get('new_session_id')}")
                            
                            # 自動リロード
                            st.info("⏳ 3秒後に自動でページを再読み込みします...")
                            reload_js = """
                            <script>
                            setTimeout(function() {
                                window.location.reload();
                            }, 3000);
                            </script>
                            """
                            st.markdown(reload_js, unsafe_allow_html=True)
                            
                        else:
                            st.error(f"❌ フルリセット失敗: {reset_result.get('message', '不明なエラー')}")
                            st.info("通常のリセットを試すか、ページを手動で再読み込みしてください。")
                        
                    except Exception as e:
                        logger.error(f"フルリセットエラー: {e}")
                        st.error(f"❌ フルリセットに失敗しました: {str(e)}")
                        st.info("通常のリセットを試すか、ページを手動で再読み込みしてください。")
                    
                    # 確認フラグをリセット
                    st.session_state.full_reset_confirm = False
            
            # 設定コンテンツのHTMLタグを閉じる
            st.markdown('</div>', unsafe_allow_html=True)
        
        # チュートリアル案内をサイドバーに表示
        tutorial_manager.render_tutorial_sidebar()

        if st.session_state.debug_mode:
            with st.expander("🛠️ デバッグ情報", expanded=False):
                # SessionManagerから詳細情報を取得
                session_manager = get_session_manager()
                session_info = session_manager.get_session_info()
                isolation_status = session_manager.get_isolation_status()
                
                # 検証履歴と復旧履歴を取得
                validation_history = session_manager.get_validation_history(limit=10)
                recovery_history = session_manager.get_recovery_history(limit=10)
                
                # セッション分離詳細情報を構築
                session_isolation_details = {
                    "session_integrity": {
                        "status": "✅ 正常" if session_info["is_consistent"] else "❌ 不整合",
                        "session_id_match": session_info["session_id"] == session_info["current_session_id"],
                        "original_session_id": session_info["session_id"],
                        "current_session_id": session_info["current_session_id"],
                        "stored_session_id": session_info["stored_session_id"],
                        "user_id": session_info["user_id"],
                        "session_age_minutes": round(session_info["session_age_seconds"] / 60, 2),
                        "last_validated": session_info["last_validated"]
                    },
                    "validation_metrics": {
                        "total_validations": session_info["validation_count"],
                        "total_recoveries": session_info["recovery_count"],
                        "validation_history_size": session_info["validation_history_count"],
                        "recovery_history_size": session_info["recovery_history_count"],
                        "success_rate": round((session_info["validation_count"] - session_info["recovery_count"]) / max(session_info["validation_count"], 1) * 100, 2) if session_info["validation_count"] > 0 else 100
                    },
                    "component_isolation": isolation_status["component_isolation"],
                    "data_integrity": isolation_status["data_integrity"]
                }
                
                # FastAPIセッション状態を取得
                session_api_client = managers.get("session_api_client")
                api_session_status = session_api_client.get_session_status() if session_api_client else {}
                
                # Cookie状態を取得
                cookie_status = session_api_client.get_cookie_status() if session_api_client else {}
                
                # 拡張されたデバッグ情報
                enhanced_debug_info = {
                    "session_isolation_details": session_isolation_details,
                    "isolation_status": isolation_status,
                    "session_manager_info": {
                        "session_id": session_info["session_id"],
                        "current_session_id": session_info["current_session_id"],
                        "user_id": session_info["user_id"],
                        "is_consistent": session_info["is_consistent"],
                        "validation_count": session_info["validation_count"],
                        "recovery_count": session_info["recovery_count"],
                        "session_age_seconds": session_info["session_age_seconds"],
                        "created_at": session_info["created_at"],
                        "last_validated": session_info["last_validated"]
                    },
                    "fastapi_session_info": api_session_status,
                    "cookie_status": cookie_status,
                    "chat_state": {
                        "affection": st.session_state.chat['affection'],
                        "theme": st.session_state.chat['scene_params']['theme'],
                        "messages_count": len(st.session_state.chat['messages']),
                        "ura_mode": st.session_state.chat.get('ura_mode', False),
                        "limiter_state_present": 'limiter_state' in st.session_state.chat,
                        "scene_change_pending": st.session_state.chat.get('scene_change_pending')
                    },
                    "memory_state": {
                        "cache_size": len(st.session_state.memory_manager.important_words_cache),
                        "special_memories": len(st.session_state.memory_manager.special_memories),
                        "memory_manager_type": type(st.session_state.memory_manager).__name__,
                        "memory_manager_id": id(st.session_state.memory_manager)
                    },
                    "system_state": {
                        "session_keys": list(st.session_state.keys()),
                        "session_keys_count": len(st.session_state.keys()),
                        "notifications_pending": {
                            "affection": len(st.session_state.affection_notifications),
                            "memory": len(st.session_state.memory_notifications)
                        },
                        "streamlit_session_id": st.session_state.get('_session_id', 'unknown')
                    }
                }
                
                # タブ形式でデバッグ情報を整理（拡張版）
                debug_tab1, debug_tab2, debug_tab3, debug_tab4, debug_tab5, debug_tab6 = st.tabs([
                    "🔍 セッション分離", "📊 基本情報", "🍪 Cookie状態", "✅ 検証履歴", "🔧 復旧履歴", "⚙️ システム詳細"
                ])
                
                with debug_tab1:
                    st.markdown("### 🔒 セッション分離状態")
                    
                    # 手動検証ボタン
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    with col_btn1:
                        if st.button("🔍 手動検証実行", help="セッション整合性を手動で検証します"):
                            validation_result = validate_session_state()
                            if validation_result:
                                st.success("✅ セッション検証成功")
                            else:
                                st.error("❌ セッション検証失敗")
                            st.rerun()
                    
                    with col_btn2:
                        if st.button("📋 詳細検証実行", help="詳細なセッション検証を実行します"):
                            detailed_issues = perform_detailed_session_validation(session_manager)
                            if not detailed_issues:
                                st.success("✅ 詳細検証: 問題なし")
                            else:
                                st.warning(f"⚠️ 詳細検証: {len(detailed_issues)}件の問題を検出")
                                for issue in detailed_issues:
                                    severity_icon = "🔴" if issue['severity'] == 'critical' else "🟡"
                                    st.write(f"{severity_icon} **{issue['type']}**: {issue['description']}")
                    
                    with col_btn3:
                        if st.button("🔄 強制復旧実行", help="セッション状態を強制的に復旧します"):
                            session_manager.recover_session()
                            st.info("🔄 セッション復旧を実行しました")
                            st.rerun()
                    
                    st.markdown("---")
                    
                    # セッション整合性ステータス
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            "セッション整合性",
                            session_isolation_details["session_integrity"]["status"],
                            delta=None
                        )
                        st.metric(
                            "検証成功率",
                            f"{session_isolation_details['validation_metrics']['success_rate']}%",
                            delta=None
                        )
                    
                    with col2:
                        st.metric(
                            "総検証回数",
                            session_isolation_details["validation_metrics"]["total_validations"],
                            delta=None
                        )
                        st.metric(
                            "復旧実行回数",
                            session_isolation_details["validation_metrics"]["total_recoveries"],
                            delta=None
                        )
                    
                    # コンポーネント分離状態
                    st.markdown("#### 🧩 コンポーネント分離状態")
                    isolation_data = session_isolation_details["component_isolation"]
                    
                    for component, is_isolated in isolation_data.items():
                        status_icon = "✅" if is_isolated else "❌"
                        component_name = {
                            "chat_isolated": "チャット機能",
                            "memory_isolated": "メモリ管理",
                            "notifications_isolated": "通知システム",
                            "rate_limit_isolated": "レート制限"
                        }.get(component, component)
                        
                        st.write(f"{status_icon} **{component_name}**: {'分離済み' if is_isolated else '未分離'}")
                    
                    # データ整合性
                    st.markdown("#### 📋 データ整合性")
                    integrity_data = session_isolation_details["data_integrity"]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("チャットメッセージ数", integrity_data["chat_messages_count"])
                        st.metric("メモリキャッシュサイズ", integrity_data["memory_cache_size"])
                    
                    with col2:
                        st.metric("特別な記憶数", integrity_data["special_memories_count"])
                        pending_total = sum(integrity_data["pending_notifications"].values())
                        st.metric("保留中通知数", pending_total)
                    
                    # セッションID詳細
                    st.markdown("#### 🆔 セッションID詳細")
                    session_id_info = session_isolation_details["session_integrity"]
                    
                    st.code(f"""
セッション整合性: {session_id_info['status']}
オリジナルID: {session_id_info['original_session_id']}
現在のID: {session_id_info['current_session_id']}
保存されたID: {session_id_info['stored_session_id']}
ユーザーID: {session_id_info['user_id']}
セッション継続時間: {session_id_info['session_age_minutes']} 分
最終検証時刻: {session_id_info['last_validated'][:19]}
                    """)
                
                with debug_tab2:
                    st.markdown("### 📊 基本セッション情報")
                    st.json({
                        "session_manager": enhanced_debug_info["session_manager_info"],
                        "chat_state": enhanced_debug_info["chat_state"],
                        "memory_state": enhanced_debug_info["memory_state"]
                    })
                
                with debug_tab3:
                    st.markdown("### 🍪 Cookie状態")
                    
                    if cookie_status:
                        # Cookie概要
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Cookie数", cookie_status.get('count', 0))
                        with col2:
                            has_session = cookie_status.get('has_session_cookie', False)
                            st.metric("セッションCookie", "✅ あり" if has_session else "❌ なし")
                        with col3:
                            if st.button("🔄 Cookie状態更新", help="Cookie状態を再取得します"):
                                st.rerun()
                        
                        # Cookie詳細
                        if cookie_status.get('cookies'):
                            st.markdown("#### Cookie詳細")
                            for i, cookie in enumerate(cookie_status['cookies']):
                                with st.expander(f"Cookie {i+1}: {cookie.get('name', 'unknown')}"):
                                    st.json(cookie)
                        else:
                            st.info("現在Cookieは設定されていません")
                        
                        # Cookie操作ボタン
                        st.markdown("#### Cookie操作")
                        col_cookie1, col_cookie2 = st.columns(2)
                        with col_cookie1:
                            if st.button("🗑️ Cookie削除テスト", help="Cookieを削除してテストします"):
                                try:
                                    session_api_client.session.cookies.clear()
                                    st.success("Cookie削除完了")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Cookie削除エラー: {e}")
                        
                        with col_cookie2:
                            if st.button("🔥 フルリセットテスト", help="フルリセット機能をテストします"):
                                try:
                                    reset_result = session_api_client.full_reset_session()
                                    if reset_result['success']:
                                        st.success(f"フルリセット成功: {reset_result['message']}")
                                    else:
                                        st.error(f"フルリセット失敗: {reset_result['message']}")
                                    st.json(reset_result)
                                except Exception as e:
                                    st.error(f"フルリセットテストエラー: {e}")
                    else:
                        st.warning("Cookie状態を取得できませんでした")
                
                with debug_tab4:
                    st.markdown("### ✅ セッション検証履歴")
                    if validation_history:
                        st.write(f"**最新の検証履歴（最大10件）:** 総検証回数 {session_info['validation_count']} 回")
                        
                        # 検証履歴のサマリー
                        recent_validations = validation_history[-5:] if len(validation_history) >= 5 else validation_history
                        success_count = sum(1 for v in recent_validations if v['is_consistent'])
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("直近5回の成功率", f"{success_count}/{len(recent_validations)}")
                        with col2:
                            st.metric("最新検証結果", "✅ 成功" if validation_history[-1]['is_consistent'] else "❌ 失敗")
                        with col3:
                            st.metric("検証間隔", f"約{round((datetime.now() - datetime.fromisoformat(validation_history[-1]['timestamp'].replace('Z', '+00:00').replace('+00:00', ''))).total_seconds() / 60, 1)}分前")
                        
                        # 詳細な検証履歴
                        for i, record in enumerate(reversed(validation_history)):
                            status_icon = "✅" if record['is_consistent'] else "❌"
                            timestamp = record['timestamp'][:19].replace('T', ' ')
                            
                            with st.expander(f"{status_icon} 検証 #{record['validation_count']} - {timestamp}", expanded=(i==0)):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write("**基本情報:**")
                                    st.write(f"- 検証時刻: {timestamp}")
                                    st.write(f"- 検証回数: #{record['validation_count']}")
                                    st.write(f"- 結果: {'✅ 整合性OK' if record['is_consistent'] else '❌ 不整合検出'}")
                                    st.write(f"- ユーザーID: {record['user_id']}")
                                
                                with col2:
                                    st.write("**セッションID情報:**")
                                    st.write(f"- オリジナル: {record['original_session_id']}")
                                    st.write(f"- 現在: {record['current_session_id']}")
                                    st.write(f"- 保存済み: {record['stored_session_id']}")
                                    st.write(f"- セッションキー数: {record['session_keys_count']}")
                    else:
                        st.info("検証履歴がありません")
                
                with debug_tab4:
                    st.markdown("### 🔧 セッション復旧履歴")
                    if recovery_history:
                        st.write(f"**復旧履歴:** 総復旧回数 {session_info['recovery_count']} 回")
                        
                        # 復旧履歴のサマリー
                        if recovery_history:
                            last_recovery = recovery_history[-1]
                            time_since_recovery = (datetime.now() - datetime.fromisoformat(last_recovery['timestamp'].replace('Z', '+00:00').replace('+00:00', ''))).total_seconds() / 60
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("最新復旧", f"約{round(time_since_recovery, 1)}分前")
                            with col2:
                                st.metric("復旧タイプ", last_recovery.get('recovery_type', 'unknown'))
                        
                        # 詳細な復旧履歴
                        for record in reversed(recovery_history):
                            timestamp = record['timestamp'][:19].replace('T', ' ')
                            recovery_type = record.get('recovery_type', 'unknown')
                            
                            with st.expander(f"🔧 復旧 #{record['recovery_count']} - {timestamp} ({recovery_type})", expanded=True):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write("**復旧情報:**")
                                    st.write(f"- 復旧時刻: {timestamp}")
                                    st.write(f"- 復旧回数: #{record['recovery_count']}")
                                    st.write(f"- 復旧タイプ: {recovery_type}")
                                    st.write(f"- ユーザーID: {record['user_id']}")
                                
                                with col2:
                                    st.write("**セッションID変更:**")
                                    st.write(f"- 変更前: {record['old_session_id']}")
                                    st.write(f"- 変更後: {record['new_session_id']}")
                                    st.write(f"- セッションキー数: {record['session_keys_count']}")
                                    st.write(f"- 復旧時検証回数: {record['validation_count_at_recovery']}")
                    else:
                        st.success("復旧履歴がありません（正常な状態です）")
                
                with debug_tab5:
                    st.markdown("### 🔧 復旧履歴")
                    if recovery_history:
                        st.write(f"**復旧履歴（最大10件）:** 総復旧回数 {session_info['recovery_count']} 回")
                        
                        # 復旧履歴のサマリー
                        recent_recoveries = recovery_history[-5:] if len(recovery_history) >= 5 else recovery_history
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("直近の復旧回数", len(recent_recoveries))
                        with col2:
                            if recent_recoveries:
                                last_recovery = recent_recoveries[-1]
                                st.metric("最終復旧", last_recovery['timestamp'][:19])
                        
                        # 復旧履歴の詳細表示
                        for i, recovery in enumerate(reversed(recovery_history)):
                            with st.expander(f"復旧 #{len(recovery_history)-i}: {recovery['timestamp'][:19]}"):
                                st.json(recovery)
                    else:
                        st.success("復旧履歴がありません（正常な状態です）")
                
                with debug_tab6:
                    st.markdown("### ⚙️ システム詳細情報")
                    st.json(enhanced_debug_info["system_state"])
                    
                    
                    # ポチ機能の統計（本格実装）
                    st.markdown("---")
                    st.markdown("### 🐕 ポチ機能統計")
                    flip_states = st.session_state.get('message_flip_states', {})
                    st.markdown(f"**フリップ状態数**: {len(flip_states)}")
                    if flip_states:
                        st.json(flip_states)
                    
                    # 追加のシステム情報
                    st.markdown("#### 🔧 技術詳細")
                    st.code(f"""
Python オブジェクトID:
- st.session_state: {id(st.session_state)}
- SessionManager: {id(session_manager)}
- MemoryManager: {enhanced_debug_info['memory_state']['memory_manager_id']}

環境変数:
- DEBUG_MODE: {os.getenv('DEBUG_MODE', 'false')}
- FORCE_SESSION_RESET: {os.getenv('FORCE_SESSION_RESET', 'false')}

Streamlit情報:
- セッション状態キー数: {len(st.session_state.keys())}
- 内部セッションID: {st.session_state.get('_session_id', 'unknown')}
                    """)

    # --- メインコンテンツ ---
    st.title("💬 麻理チャット")
    st.markdown("*捨てられたアンドロイド「麻理」との対話*")
    
    # 好感度変化の通知を表示
    if st.session_state.affection_notifications:
        for notification in st.session_state.affection_notifications:
            show_affection_notification(
                notification["change_amount"],
                notification["change_reason"],
                notification["new_affection"],
                notification.get("is_milestone", False)
            )
        # 通知を表示したらクリア
        st.session_state.affection_notifications = []
    
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
            
            ### 🐕 本音表示機能
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
    
    # カスタムチャット履歴表示エリア（マスク機能付き）
    render_custom_chat_history(st.session_state.chat['messages'], managers['chat_interface'])

    # メッセージ処理ロジック
    def process_chat_message(message: str):
        try:
            # チュートリアルステップ1を完了（メッセージ送信）
            tutorial_manager.check_step_completion(1, True)
            
            # セッション検証を処理開始時に実行
            if not validate_session_state():
                logger.error("Session validation failed at message processing start")
                return "（申し訳ありません。システムに問題が発生しました。ページを再読み込みしてください。）"
            
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
            # 初期メッセージ（is_initial=True）を履歴から除外して会話ペアを構築
            non_initial_messages = [msg for msg in st.session_state.chat['messages'] 
                                  if not msg.get('is_initial', False)]
            
            # 会話ペアを時系列順に構築
            history = []
            user_msgs = []
            assistant_msgs = []
            
            for msg in non_initial_messages:
                if msg['role'] == 'user':
                    user_msgs.append(msg['content'])
                elif msg['role'] == 'assistant':
                    assistant_msgs.append(msg['content'])
            
            # ユーザーとアシスタントのメッセージをペアにする（最大5ターン）
            max_turns = min(5, min(len(user_msgs), len(assistant_msgs)))
            for i in range(max_turns):
                if i < len(user_msgs) and i < len(assistant_msgs):
                    history.append((user_msgs[i], assistant_msgs[i]))
            
            # 初回の場合は空の履歴になる（これが正しい動作）
            logger.info(f"📚 構築された履歴: {len(history)}ターン")
            if st.session_state.get('debug_mode', False):
                logger.info(f"🔍 全メッセージ数: {len(st.session_state.chat['messages'])}")
                logger.info(f"🔍 非初期メッセージ数: {len(non_initial_messages)}")
                logger.info(f"🔍 ユーザーメッセージ数: {len(user_msgs)}")
                logger.info(f"🔍 アシスタントメッセージ数: {len(assistant_msgs)}")

            # 好感度更新（初期メッセージを除外）
            old_affection = st.session_state.chat['affection']
            non_initial_messages = [msg for msg in st.session_state.chat['messages'] 
                                  if not msg.get('is_initial', False)]
            affection, change_amount, change_reason = managers['sentiment_analyzer'].update_affection(
                message, st.session_state.chat['affection'], non_initial_messages
            )
            st.session_state.chat['affection'] = affection
            stage_name = managers['sentiment_analyzer'].get_relationship_stage(affection)
            
            # 好感度変化があった場合は通知を追加
            if change_amount != 0:
                affection_notification = {
                    "change_amount": change_amount,
                    "change_reason": change_reason,
                    "new_affection": affection,
                    "old_affection": old_affection
                }
                st.session_state.affection_notifications.append(affection_notification)
                
                # 特定の好感度レベルに到達した時の特別な通知
                milestone_reached = check_affection_milestone(old_affection, affection)
                if milestone_reached:
                    milestone_notification = {
                        "change_amount": 0,  # マイルストーン通知は変化量0で特別扱い
                        "change_reason": milestone_reached,
                        "new_affection": affection,
                        "old_affection": old_affection,
                        "is_milestone": True
                    }
                    st.session_state.affection_notifications.append(milestone_notification)
            
            # シーン変更検知
            current_theme = st.session_state.chat['scene_params']['theme']
            new_theme = managers['scene_manager'].detect_scene_change(history, current_theme=current_theme)
            
            instruction = None
            if new_theme:
                logger.info(f"Scene change detected! From '{current_theme}' to '{new_theme}'.")
                st.session_state.chat['scene_params'] = managers['scene_manager'].update_scene_params(st.session_state.chat['scene_params'], new_theme)
                instruction = managers['scene_manager'].get_scene_transition_message(current_theme, new_theme)
                st.session_state.scene_change_flag = True

            # メモリ圧縮とサマリー取得（初期メッセージを除外）
            non_initial_messages = [msg for msg in st.session_state.chat['messages'] 
                                  if not msg.get('is_initial', False)]
            compressed_messages, important_words = st.session_state.memory_manager.compress_history(
                non_initial_messages
            )
            memory_summary = st.session_state.memory_manager.get_memory_summary()
            
            # デバッグ: メモリサマリーの内容をログ出力
            if memory_summary:
                logger.warning(f"🧠 メモリサマリーが存在: {memory_summary[:100]}...")
            else:
                logger.info("🧠 メモリサマリーは空です（初対面状態）")
            
            # 対話生成（隠された真実機能統合済み）
            response = managers['dialogue_generator'].generate_dialogue(
                history, message, affection, stage_name, st.session_state.chat['scene_params'], instruction, memory_summary, st.session_state.chat['ura_mode']
            )
            
            # デバッグ: AI応答の形式をチェック
            if response:
                logger.info(f"🤖 AI応答: '{response[:100]}...'")
                if '[HIDDEN:' in response:
                    logger.info("✅ HIDDEN形式を検出")
                else:
                    logger.warning("⚠️ HIDDEN形式が見つからない - フォールバック処理を実行")
                    # HIDDEN形式でない場合は、強制的にHIDDEN形式に変換
                    response = f"[HIDDEN:（本当の気持ちは...）]{response}"
                    logger.info(f"🔧 フォールバック後: '{response[:100]}...'")
            
            return response if response else "[HIDDEN:（言葉が出てこない...）]…なんて言えばいいか分からない。"
        except Exception as e:
            logger.error(f"チャットメッセージ処理エラー: {e}", exc_info=True)
            return "（ごめん、システムの調子が悪いみたいだ。）"

    # ユーザー入力処理（通常の入力フィールドを使用して二重表示を防止）
    with st.container():
        col_input, col_send = st.columns([0.85, 0.15])
        
        with col_input:
            user_input = st.text_input(
                "メッセージ", 
                placeholder="麻理に話しかける...",
                key="user_message_input",
                label_visibility="collapsed"
            )
        
        with col_send:
            send_button = st.button("送信", type="primary", use_container_width=True)
    
    # 送信ボタンでメッセージ送信（Enterキー送信は無効化して重複を防止）
    if send_button and user_input and user_input.strip():
        # 重複送信を防止
        if st.session_state.get("last_sent_message") == user_input:
            return
        st.session_state.last_sent_message = user_input
        
        if len(user_input) > MAX_INPUT_LENGTH:
            st.error(f"⚠️ メッセージは{MAX_INPUT_LENGTH}文字以内で入力してください。")
        else:
            # 応答を生成（履歴追加前に実行）
            with cute_thinking_spinner():
                response = process_chat_message(user_input)
            
            # 応答生成後に両方のメッセージを履歴に追加（メッセージIDを含む）
            user_message_id = f"user_{len(st.session_state.chat['messages'])}"
            assistant_message_id = f"assistant_{len(st.session_state.chat['messages']) + 1}"
            
            managers['chat_interface'].add_message("user", user_input, st.session_state.chat['messages'], user_message_id)
            managers['chat_interface'].add_message("assistant", response, st.session_state.chat['messages'], assistant_message_id)
            
            # 入力フィールドをクリア（次回の再実行時に反映）
            if 'user_message_input' in st.session_state:
                del st.session_state.user_message_input
            
            # シーン変更があった場合はフラグをクリア
            if st.session_state.get('scene_change_flag', False):
                del st.session_state['scene_change_flag']
            
            # st.rerun()を削除 - Streamlitは自動的に再描画される
    
    # DogAssistantの固定配置コンポーネントを描画（右下のみ）
    try:
        managers['dog_assistant'].render_dog_component(tutorial_manager)
    except Exception as e:
        logger.error(f"DogAssistant描画エラー: {e}")
        # フォールバック: シンプルなボタンを表示
        managers['dog_assistant'].render_with_streamlit_button()

# === 手紙タブの描画関数 ===
async def generate_tutorial_letter_async(theme: str, managers) -> str:
    """チュートリアル用の短縮版手紙を非同期で生成する（Groq + Qwen使用）"""
    try:
        # 現在の好感度と関係性を取得
        current_affection = st.session_state.chat.get('affection', 30)
        stage_name = managers['sentiment_analyzer'].get_relationship_stage(current_affection)
        user_id = st.session_state.user_id
        
        # チュートリアル用のユーザー履歴を構築
        tutorial_user_history = {
            'profile': {
                'total_letters': 0,
                'affection': current_affection,
                'stage': stage_name
            },
            'letters': {}
        }
        
        # 手紙生成器を使用（Groq + Qwen の2段階プロセス）
        letter_generator = managers.get('letter_generator')
        if not letter_generator:
            # フォールバック：直接生成
            return await generate_tutorial_letter_fallback(theme, current_affection, stage_name)
        
        # 通常の手紙生成システムを使用
        letter_result = await letter_generator.generate_letter(user_id, theme, tutorial_user_history)
        
        # 600文字以内に制限
        letter_content = letter_result['content']
        if len(letter_content) > 600:
            # 文の区切りで切り詰める
            sentences = letter_content.split('。')
            truncated_content = ""
            for sentence in sentences:
                if len(truncated_content + sentence + '。') <= 600:
                    truncated_content += sentence + '。'
                else:
                    break
            letter_content = truncated_content.rstrip('。') + '……'
        
        return letter_content
        
    except Exception as e:
        logger.error(f"チュートリアル手紙生成エラー: {e}")
        # フォールバック手紙
        return await generate_tutorial_letter_fallback(theme, current_affection, stage_name)

async def generate_tutorial_letter_fallback(theme: str, current_affection: int, stage_name: str) -> str:
    """チュートリアル手紙生成のフォールバック"""
    return f"""いつもありがとう。

{theme}のこと……書こうと思ったんだけど、なんか恥ずかしくて。
あんたと話してると、いつもと違う自分になれる気がするの。
それって、きっと特別なことよね。

私、まだまだ素直になれないけれど……
少しずつ、あんたのことを知りたいと思ってる。

……ま、忘れて。バカじゃないの。
でも、ありがとう。"""

def generate_tutorial_letter(theme: str, managers) -> str:
    """チュートリアル用手紙生成の同期ラッパー"""
    try:
        return run_async(generate_tutorial_letter_async(theme, managers))
    except Exception as e:
        logger.error(f"チュートリアル手紙生成同期ラッパーエラー: {e}")
        current_affection = st.session_state.chat.get('affection', 30)
        stage_name = managers['sentiment_analyzer'].get_relationship_stage(current_affection)
        return run_async(generate_tutorial_letter_fallback(theme, current_affection, stage_name))

def render_letter_tab(managers):
    """「手紙を受け取る」タブのUIを描画する"""
    st.title("✉️ おやすみ前の、一通の手紙")
    
    # チュートリアル案内（ステップ4の場合のみ）
    tutorial_manager = managers.get('tutorial_manager')
    if tutorial_manager and tutorial_manager.get_current_step() == 4:
        # 手紙タブに到達したことを祝福
        st.success("🎉 素晴らしい！手紙タブに到達しました！")
        tutorial_manager.render_chat_tutorial_guide()
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
    
    # チュートリアル状態をチェック
    tutorial_manager = managers.get('tutorial_manager')
    is_tutorial_step4 = (tutorial_manager and 
                        tutorial_manager.get_current_step() == 4 and 
                        not tutorial_manager.is_step_completed(4))
    
    # 好感度制限チェック（チュートリアル中は免除）
    if current_affection < required_affection and not is_tutorial_step4:
        st.warning(f"💔 手紙をリクエストするには好感度が{required_affection}以上必要です。現在の好感度: {current_affection}")
        st.info("麻理ともっと会話して、関係を深めてから手紙をお願いしてみてください。")
        return
    
    # チュートリアル中の特別案内
    if is_tutorial_step4:
        st.info("📘 **チュートリアル特典**: 初回のみ好感度に関係なく手紙をリクエストできます！")
    
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
        # 好感度が十分な場合またはチュートリアル中のフォーム表示
        if not is_tutorial_step4:
            st.success(f"💝 好感度{current_affection}で手紙をリクエストできます！")
        
        with st.form("letter_request_form"):
            if is_tutorial_step4:
                # チュートリアル用のデフォルトテーマ
                theme = st.text_input("手紙のテーマ", 
                                    value="初めての出会いについて", 
                                    placeholder="例：最近見た美しい景色について")
                st.caption("📘 チュートリアル用にテーマを設定済みです。変更も可能です。")
                
                # チュートリアル用は即時生成
                st.info("🚀 チュートリアル特典：即座に手紙を生成します！")
                submitted = st.form_submit_button("📘 チュートリアル用手紙を生成")
            else:
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
                    if is_tutorial_step4:
                        # チュートリアル用即時生成
                        with st.spinner("チュートリアル用手紙を生成中..."):
                            try:
                                # 短縮版手紙を即時生成（Groq + Qwen使用）
                                tutorial_letter = generate_tutorial_letter(theme, managers)
                                
                                # チュートリアル手紙生成フラグを設定
                                st.session_state.tutorial_letter_generated = True
                                
                                # チュートリアルステップ4を完了
                                tutorial_manager.check_step_completion(4, True)
                                
                                # 手紙を表示
                                st.success("✉️ 麻理からの手紙が届きました！")
                                
                                with st.container():
                                    st.markdown("---")
                                    
                                    # 手紙のスタイル付きコンテナ
                                    letter_css = """
                                    <style>
                                    .tutorial-letter {
                                        background: linear-gradient(135deg, #fff8e1 0%, #f3e5f5 100%);
                                        border: 2px solid #e1bee7;
                                        border-radius: 15px;
                                        padding: 25px;
                                        margin: 20px 0;
                                        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                                        font-family: 'Georgia', serif;
                                        line-height: 1.8;
                                        position: relative;
                                    }
                                    
                                    .tutorial-letter::before {
                                        content: '💌';
                                        position: absolute;
                                        top: -10px;
                                        left: 20px;
                                        background: white;
                                        padding: 5px 10px;
                                        border-radius: 50%;
                                        font-size: 20px;
                                    }
                                    
                                    .tutorial-letter h3 {
                                        color: #7b1fa2;
                                        text-align: center;
                                        margin-bottom: 20px;
                                        font-size: 24px;
                                    }
                                    
                                    .tutorial-notice {
                                        background: rgba(255, 193, 7, 0.1);
                                        border-left: 4px solid #ffc107;
                                        padding: 10px 15px;
                                        margin: 15px 0;
                                        border-radius: 0 8px 8px 0;
                                        font-size: 14px;
                                        color: #856404;
                                    }
                                    </style>
                                    """
                                    
                                    st.markdown(letter_css, unsafe_allow_html=True)
                                    
                                    # 手紙の内容を美しく表示
                                    letter_html = f"""
                                    <div class="tutorial-letter">
                                        <h3>麻理からの手紙</h3>
                                        <div style="white-space: pre-line; color: #424242;">
                                            {tutorial_letter}
                                        </div>
                                    </div>
                                    """
                                    
                                    st.markdown(letter_html, unsafe_allow_html=True)
                                    
                                    # チュートリアル用の注意書き
                                    notice_html = """
                                    <div class="tutorial-notice">
                                        📘 これはチュートリアル用の短縮版です。好感度を上げると、もっと長い手紙も……？
                                    </div>
                                    """
                                    st.markdown(notice_html, unsafe_allow_html=True)
                                    
                                    # 会話に反映ボタン
                                    if st.button("💬 この手紙の内容を会話に反映", key="tutorial_letter_reflect"):
                                        # メモリに手紙の内容を追加
                                        memory_notification = f"手紙の内容「{theme}」について話題にしました"
                                        st.session_state.memory_notifications.append(memory_notification)
                                        st.success("手紙の内容が会話に反映されました！チャットタブで確認してください。")
                                        st.rerun()
                                
                            except Exception as e:
                                logger.error(f"チュートリアル手紙生成エラー: {e}")
                                st.error("手紙の生成に失敗しました。しばらく後でお試しください。")
                    else:
                        # 通常の手紙リクエスト処理
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

    # チュートリアル機能の初期化
    tutorial_manager = managers['tutorial_manager']
    
    # 初回訪問時のウェルカムダイアログ
    if tutorial_manager.should_show_tutorial():
        tutorial_manager.render_welcome_dialog()
        tutorial_manager.mark_tutorial_shown()
    
    # チュートリアル開始/スキップの処理
    if st.session_state.get('tutorial_start_requested', False):
        st.session_state.tutorial_start_requested = False
        # チュートリアル開始の案内
        st.success("📘 チュートリアルを開始しました！青い案内ボックスに従って進めてください。")
    
    if st.session_state.get('tutorial_skip_requested', False):
        st.session_state.tutorial_skip_requested = False
        st.success("⏭️ チュートリアルをスキップしました。麻理との会話をお楽しみください！")
    
    # チュートリアルステップ4の場合、手紙タブを強調表示
    tutorial_manager = managers['tutorial_manager']
    current_step = tutorial_manager.get_current_step()
    
    # タブ名を動的に設定
    if current_step == 4 and not tutorial_manager.is_step_completed(4):
        # ステップ4の場合、手紙タブを強調
        letter_tab_name = "👉 ✉️ 手紙を受け取る ← ここをクリック！"
        
        # 手紙タブ強調のCSS
        tab_highlight_css = """
        <style>
        /* 手紙タブの強調表示 */
        .stTabs [data-baseweb="tab-list"] button:nth-child(2) {
            background: linear-gradient(45deg, #ff6b6b, #feca57) !important;
            color: white !important;
            font-weight: bold !important;
            animation: tabPulse 2s ease-in-out infinite !important;
            border: 2px solid #ff6b6b !important;
            border-radius: 10px !important;
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4) !important;
        }
        
        .stTabs [data-baseweb="tab-list"] button:nth-child(2):hover {
            transform: scale(1.05) !important;
            box-shadow: 0 6px 20px rgba(255, 107, 107, 0.6) !important;
        }
        
        @keyframes tabPulse {
            0%, 100% { 
                transform: scale(1);
                box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
            }
            50% { 
                transform: scale(1.02);
                box-shadow: 0 6px 25px rgba(255, 107, 107, 0.7);
            }
        }
        
        /* 矢印アニメーション */
        .tutorial-arrow {
            position: fixed;
            top: 60px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
            font-size: 30px;
            color: #ff6b6b;
            animation: arrowBounce 1.5s ease-in-out infinite;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        @keyframes arrowBounce {
            0%, 100% { transform: translateX(-50%) translateY(0px); }
            50% { transform: translateX(-50%) translateY(-10px); }
        }
        
        @media (max-width: 768px) {
            .tutorial-arrow {
                top: 50px;
                font-size: 24px;
            }
        }
        </style>
        """
        
        st.markdown(tab_highlight_css, unsafe_allow_html=True)
        
        # 矢印の表示
        arrow_html = """
        <div class="tutorial-arrow">
            ↓ 手紙タブをクリック！ ↓
        </div>
        """
        
        st.markdown(arrow_html, unsafe_allow_html=True)
    else:
        letter_tab_name = "✉️ 手紙を受け取る"
    
    # タブを作成
    chat_tab, letter_tab, tutorial_tab = st.tabs(["💬 麻理と話す", letter_tab_name, "📘 チュートリアル"])

    with chat_tab:
        render_chat_tab(managers)

    with letter_tab:
        render_letter_tab(managers)
    
    with tutorial_tab:
        tutorial_manager.render_tutorial_tab()

if __name__ == "__main__":
    if not Config.validate_config():
        logger.critical("手紙機能の設定にエラーがあります。アプリケーションを起動できません。")
    else:
        main()