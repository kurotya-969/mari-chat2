"""
Streamlit版麻理チャットアプリケーション
GradioからStreamlitに移行したメインアプリケーション
"""
import streamlit as st
import logging
import os
import asyncio
import sys
from datetime import datetime
from dotenv import load_dotenv

# 非同期処理の問題を解決
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Hugging Face Spaces用の環境変数設定
os.environ.setdefault("STREAMLIT_SERVER_PORT", "7860")
os.environ.setdefault("STREAMLIT_SERVER_ADDRESS", "0.0.0.0")
os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")

# コアモジュールのインポート（フラット構造用）
from core_dialogue import DialogueGenerator
from core_sentiment import SentimentAnalyzer
from core_rate_limiter import RateLimiter
from core_scene_manager import SceneManager
from core_memory_manager import MemoryManager

# コンポーネントのインポート（フラット構造用）
from components_chat_interface import ChatInterface
from components_background import BackgroundManager
from components_status_display import StatusDisplay

# 初期設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
load_dotenv()

# 定数
MAX_INPUT_LENGTH = 1000
MAX_HISTORY_TURNS = 50

def initialize_session_state():
    """Streamlit session stateを初期化する"""
    if 'initialized' not in st.session_state:
        st.session_state.messages = []
        st.session_state.affection = 30
        st.session_state.scene_params = {"theme": "default"}
        st.session_state.limiter_state = {
            "timestamps": [],
            "is_blocked": False
        }
        st.session_state.debug_mode = False
        st.session_state.initialized = True
        logger.info("セッション状態を初期化しました")

def inject_custom_css():
    """カスタムCSSを注入する"""
    try:
        # 基本的なスタイル設定（フォールバック用）
        fallback_css = """
        <style>
        /* フォールバック用基本スタイル */
        .main-container {
            padding: 20px;
            max-width: 1000px;
            margin: 0 auto;
        }
        
        .chat-message {
            padding: 12px;
            margin: 8px 0;
            border-radius: 12px;
            transition: all 0.3s ease;
        }
        
        .sidebar-content {
            padding: 15px;
        }
        
        .status-display {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 12px;
            margin: 10px 0;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
        }
        
        .affection-gauge {
            background: linear-gradient(90deg, #ff6b6b, #feca57, #48dbfb, #ff9ff3, #54a0ff);
            height: 20px;
            border-radius: 10px;
            margin: 10px 0;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
        }
        
        .error-message {
            color: #ff6b6b;
            background: rgba(255, 107, 107, 0.2);
            padding: 12px;
            border-radius: 8px;
            margin: 8px 0;
            border: 1px solid rgba(255, 107, 107, 0.4);
        }
        
        .success-message {
            color: #26de81;
            background: rgba(38, 222, 129, 0.2);
            padding: 12px;
            border-radius: 8px;
            margin: 8px 0;
            border: 1px solid rgba(38, 222, 129, 0.4);
        }
        
        .warning-message {
            color: #feca57;
            background: rgba(254, 202, 87, 0.2);
            padding: 12px;
            border-radius: 8px;
            margin: 8px 0;
            border: 1px solid rgba(254, 202, 87, 0.4);
        }
        
        .info-message {
            color: #54a0ff;
            background: rgba(84, 160, 255, 0.2);
            padding: 12px;
            border-radius: 8px;
            margin: 8px 0;
            border: 1px solid rgba(84, 160, 255, 0.4);
        }
        
        /* タイピングインジケーター */
        .typing-indicator {
            animation: pulse 1.5s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        </style>
        """
        
        st.markdown(fallback_css, unsafe_allow_html=True)
        logger.info("フォールバック用CSSを注入しました")
        
    except Exception as e:
        logger.error(f"CSS注入エラー: {e}")



def render_sidebar(background_manager, status_display):
    """サイドバーをレンダリングする"""
    with st.sidebar:
        st.header("🤖 麻理チャット")
        st.markdown("---")
        
        # ステータス表示
        st.subheader("📊 ステータス")
        
        # 拡張されたステータス表示を使用
        affection = st.session_state.get('affection', 30)
        status_display.render_enhanced_status_display(affection)
        
        # 現在のシーン表示
        theme_info = background_manager.get_current_theme_info()
        current_theme = theme_info["theme"]
        theme_description = theme_info["description"]
        
        st.write(f"🎭 **現在のシーン**: {theme_description}")
        
        # シーン選択（デバッグモード時）
        if st.session_state.get('debug_mode', False):
            st.subheader("🎨 シーン選択")
            available_themes = background_manager.get_available_themes()
            
            selected_theme = st.selectbox(
                "シーンを選択:",
                options=list(available_themes.keys()),
                index=list(available_themes.keys()).index(current_theme),
                format_func=lambda x: available_themes[x]
            )
            
            if selected_theme != current_theme:
                old_theme = current_theme
                st.session_state.scene_params["theme"] = selected_theme
                background_manager.apply_scene_transition_effect(old_theme, selected_theme)
                background_manager.show_scene_change_notification(selected_theme)
                st.rerun()
        
        st.markdown("---")
        
        # 設定セクション
        st.subheader("⚙️ 設定")
        
        # デバッグモード
        debug_mode = st.checkbox("デバッグモード", value=st.session_state.get('debug_mode', False))
        st.session_state.debug_mode = debug_mode
        if debug_mode:
            st.write("**セッション状態**")
            st.json({
                "messages_count": len(st.session_state.get('messages', [])),
                "affection": st.session_state.get('affection', 30),
                "current_theme": current_theme,
                "limiter_blocked": st.session_state.limiter_state.get('is_blocked', False)
            })
        
        # 統計情報表示（デバッグモード時）
        if debug_mode:
            if 'memory_manager' in st.session_state:
                memory_stats = st.session_state.memory_manager.get_memory_stats()
                st.write("**メモリ統計**")
                st.json(memory_stats)
            
            if 'chat_interface' in st.session_state:
                chat_stats = st.session_state.chat_interface.get_chat_stats()
                st.write("**チャット統計**")
                st.json(chat_stats)
            
            # 好感度統計表示
            affection_stats = status_display.get_affection_statistics()
            st.write("**好感度統計**")
            st.json(affection_stats)
            
            # 好感度履歴表示
            status_display.render_affection_history()
        
        # エクスポートボタン
        if st.button("📥 履歴をエクスポート", type="secondary"):
            if 'chat_interface' in st.session_state:
                export_data = st.session_state.chat_interface.export_chat_history()
                st.download_button(
                    label="💾 ダウンロード",
                    data=export_data,
                    file_name=f"mari_chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
        
        # リセットボタン
        if st.button("🔄 会話をリセット", type="secondary"):
            st.session_state.messages = []
            st.session_state.affection = 30
            st.session_state.scene_params = {"theme": "default"}
            st.session_state.limiter_state = {
                "timestamps": [],
                "is_blocked": False
            }
            # メモリマネージャーもリセット
            if 'memory_manager' in st.session_state:
                st.session_state.memory_manager.clear_memory()
            st.success("会話をリセットしました")
            st.rerun()
        
        st.markdown("---")
        st.markdown("*Made with Streamlit & Together AI*")

def render_main_content(chat_interface, memory_manager):
    """メインコンテンツをレンダリングする"""
    # ページタイトル
    st.title("💬 麻理チャット")
    st.markdown("*廃棄処分されたアンドロイド「麻理」との対話*")
    st.markdown("---")
    
    # メモリサマリーを取得
    memory_summary = memory_manager.get_memory_summary()
    
    # チャット履歴の表示
    messages = st.session_state.get('messages', [])
    chat_interface.render_chat_history(messages, memory_summary)



def process_message(message: str, dialogue_generator, sentiment_analyzer, 
                   rate_limiter, scene_manager, memory_manager) -> str:
    """メッセージを処理して応答を生成する"""
    try:
        # レート制限チェック
        if not rate_limiter.check_limiter(st.session_state.limiter_state):
            return "（…少し話すのが速すぎる。もう少し、ゆっくり話してくれないか？）"
        
        # 履歴を内部形式に変換
        history = []
        messages = st.session_state.messages
        for i in range(0, len(messages) - 1, 2):
            if i + 1 < len(messages):
                user_msg = messages[i]["content"]
                assistant_msg = messages[i + 1]["content"]
                history.append((user_msg, assistant_msg))
        
        # 履歴長制限
        if len(history) > MAX_HISTORY_TURNS:
            history = history[-MAX_HISTORY_TURNS:]
        
        # 好感度更新（拡張版を使用）
        old_affection = st.session_state.affection
        
        # 会話の文脈を取得
        conversation_context = st.session_state.messages[-10:] if st.session_state.messages else []
        
        new_affection, affection_change, change_reason = sentiment_analyzer.update_affection(
            message, old_affection, conversation_context
        )
        
        st.session_state.affection = new_affection
        
        # 好感度履歴を更新
        if 'status_display' in st.session_state:
            st.session_state.status_display.update_affection_history(
                old_affection, new_affection, message
            )
            
            # 好感度変化通知を表示
            if affection_change != 0:
                st.session_state.status_display.show_affection_change_notification(
                    old_affection, new_affection, change_reason
                )
        
        # デバッグモードの場合は変化を表示
        if st.session_state.get('debug_mode', False) and affection_change != 0:
            logger.info(f"好感度変化: {old_affection} -> {new_affection} ({affection_change:+d}) 理由: {change_reason}")
        
        stage_name = sentiment_analyzer.get_relationship_stage(
            st.session_state.affection
        )
        
        # シーン変更検出
        current_theme = st.session_state.scene_params.get("theme", "default")
        
        # デバッグモードの場合はシーン検出の詳細をログ出力
        if st.session_state.get('debug_mode', False):
            logger.info(f"シーン検出実行 - 現在のテーマ: {current_theme}, 履歴数: {len(history)}")
        
        new_scene = scene_manager.detect_scene_change(history, dialogue_generator, current_theme)
        
        # デバッグモードの場合は結果をログ出力
        if st.session_state.get('debug_mode', False):
            if new_scene:
                logger.info(f"シーン変更検出: {current_theme} → {new_scene}")
            else:
                logger.info("シーン変更なし")
        
        instruction = None
        scene_changed = False
        if new_scene and new_scene != current_theme:
            old_theme = current_theme
            st.session_state.scene_params = scene_manager.update_scene_params(
                st.session_state.scene_params, new_scene
            )
            scene_changed = True
            
            # シーン変更の指示を生成
            scene_transition_msg = scene_manager.get_scene_transition_message(old_theme, new_scene)
            instruction = f"ユーザーと一緒に「{new_scene}」に来た。周囲の様子を見て、最初の感想をぶっきらぼうに一言つぶやいてください。"
            
            # セッション状態にシーン変更フラグを設定
            st.session_state.scene_change_pending = {
                "old_theme": old_theme,
                "new_theme": new_scene,
                "message": scene_transition_msg
            }
        
        # メモリサマリーを取得
        memory_summary = memory_manager.get_memory_summary()
        
        # 対話生成
        response = dialogue_generator.generate_dialogue(
            history, message, st.session_state.affection, 
            stage_name, st.session_state.scene_params, instruction, memory_summary
        )
        
        return response if response else "…なんて言えばいいか分からない。"
        
    except Exception as e:
        logger.error(f"メッセージ処理エラー: {e}")
        return "（ごめん、システムに問題が起きたみたいだ。）"

def main():
    """メイン関数"""
    # ページ設定
    st.set_page_config(
        page_title="麻理チャット",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # セッション状態の初期化
    initialize_session_state()
    
    # 背景管理の初期化
    if 'background_manager' not in st.session_state:
        st.session_state.background_manager = BackgroundManager()
    background_manager = st.session_state.background_manager
    
    # カスタムCSSの注入
    inject_custom_css()
    background_manager.inject_base_styles()
    
    # 背景画像の更新
    current_theme = st.session_state.scene_params.get("theme", "default")
    current_affection = st.session_state.get('affection', 30)
    
    # シーン変更があった場合の処理
    if st.session_state.get('scene_change_pending'):
        scene_change_info = st.session_state.scene_change_pending
        background_manager.apply_scene_transition_effect(
            scene_change_info["old_theme"], 
            scene_change_info["new_theme"]
        )
        background_manager.show_scene_change_notification(scene_change_info["new_theme"])
        del st.session_state.scene_change_pending
    else:
        # 通常の背景更新（好感度情報を含む）
        background_manager.update_background(current_theme, affection=current_affection)
    
    # コアモジュールの初期化
    dialogue_generator = DialogueGenerator()
    sentiment_analyzer = SentimentAnalyzer()
    rate_limiter = RateLimiter()
    scene_manager = SceneManager()
    
    # メモリマネージャーとチャットインターフェース、ステータス表示の初期化
    if 'memory_manager' not in st.session_state:
        st.session_state.memory_manager = MemoryManager(history_threshold=10)
    memory_manager = st.session_state.memory_manager
    
    if 'chat_interface' not in st.session_state:
        st.session_state.chat_interface = ChatInterface(max_input_length=MAX_INPUT_LENGTH)
    chat_interface = st.session_state.chat_interface
    
    if 'status_display' not in st.session_state:
        st.session_state.status_display = StatusDisplay()
    status_display = st.session_state.status_display
    
    # 履歴圧縮の実行
    if memory_manager.should_compress_history(st.session_state.messages):
        compressed_messages, keywords = memory_manager.compress_history(
            st.session_state.messages, dialogue_generator
        )
        st.session_state.messages = compressed_messages
        logger.info(f"履歴を圧縮しました。保存されたキーワード: {keywords}")
    
    # UIレンダリング
    render_sidebar(background_manager, status_display)
    render_main_content(chat_interface, memory_manager)
    
    # ユーザー入力の処理
    user_input = chat_interface.render_input_area()
    if user_input:
        # ユーザーメッセージを追加
        chat_interface.add_message("user", user_input)
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # アシスタントの応答を生成
        with st.chat_message("assistant"):
            with chat_interface.show_typing_indicator("考え中..."):
                response = process_message(
                    user_input, dialogue_generator, sentiment_analyzer, 
                    rate_limiter, scene_manager, memory_manager
                )
            st.markdown(response)
        
        # アシスタントメッセージを追加
        chat_interface.add_message("assistant", response)
        
        # 背景を更新（シーンが変更された場合）
        new_theme = st.session_state.scene_params.get("theme", "default")
        if new_theme != current_theme:
            st.rerun()

if __name__ == "__main__":
    main()