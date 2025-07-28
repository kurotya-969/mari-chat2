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

# コアモジュールのインポート
from core_dialogue import DialogueGenerator
from core_sentiment import SentimentAnalyzer
from core_rate_limiter import RateLimiter
from core_scene_manager import SceneManager
from core_memory_manager import MemoryManager

# コンポーネントのインポート
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
        st.session_state.limiter_state = {"timestamps": [], "is_blocked": False}
        st.session_state.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        st.session_state.initialized = True
        logger.info(f"セッション状態を初期化しました。デバッグモード: {st.session_state.debug_mode}")

def inject_custom_css(file_path="streamlit_styles.css"):
    """外部CSSファイルを読み込んで注入する"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        logger.info(f"カスタムCSS ({file_path}) を注入しました。")
    except FileNotFoundError:
        logger.warning(f"警告: CSSファイルが見つかりません: {file_path}。")
    except Exception as e:
        logger.error(f"CSS注入中にエラーが発生しました: {e}")

# --- ▼▼▼ 【修正箇所 1】関数定義の変更 ▼▼▼ ---
def render_sidebar(background_manager, sentiment_analyzer):
    """サイドバーをレンダリングする（Expanderを使用して収納可能に）"""
    with st.sidebar:
        
        # --- ステータスセクション ---
        with st.expander("📊 ステータス", expanded=True):
            affection = st.session_state.get('affection', 30)
            
            st.metric(label="好感度", value=f"{affection} / 100")
            st.progress(affection)
            
            # --- ▼▼▼ 【修正箇所 2】呼び出し元の修正 ▼▼▼ ---
            stage_name = sentiment_analyzer.get_relationship_stage(affection)
            st.markdown(f"**関係性**: {stage_name}")
            
            theme_info = background_manager.get_current_theme_info()
            st.markdown(f"**現在のシーン**: {theme_info['description']}")

        # --- 設定セクション ---
        with st.expander("⚙️ 設定"):
            if st.button("📥 履歴をエクスポート", use_container_width=True):
                if 'chat_interface' in st.session_state:
                    export_data = st.session_state.chat_interface.export_chat_history()
                    st.download_button(
                        label="💾 ダウンロード",
                        data=export_data,
                        file_name=f"mari_chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
            
            if st.button("🔄 会話をリセット", type="secondary", use_container_width=True):
                st.session_state.messages = []
                st.session_state.affection = 30
                st.session_state.scene_params = {"theme": "default"}
                if 'memory_manager' in st.session_state:
                    st.session_state.memory_manager.clear_memory()
                st.success("会話をリセットしました")
                st.rerun()

        # --- デバッグセクション ---
        if st.session_state.get('debug_mode', False):
            with st.expander("🛠️ デバッグ情報"):
                st.write("**セッション状態**")
                st.json({
                    "messages_count": len(st.session_state.get('messages', [])),
                    "affection": st.session_state.get('affection', 30),
                    "current_theme": background_manager.get_current_theme_info()["theme"],
                    "limiter_blocked": st.session_state.limiter_state.get('is_blocked', False)
                })

        # --- フッター ---
        st.markdown(
            """
            <style>
                .sidebar-footer {
                    width: 100%; text-align: center; position: absolute;
                    bottom: 15px; font-size: 0.8em; color: rgba(255, 255, 255, 0.7);
                }
            </style>
            <div class="sidebar-footer">
                Made with Streamlit & Together AI
            </div>
            """,
            unsafe_allow_html=True
        )

def render_main_content(chat_interface, memory_manager):
    """メインコンテンツをレンダリングする"""
    st.title("💬 麻理チャット")
    st.markdown("*廃棄処分されたアンドロイド「麻理」との対話*")
    with st.expander("📝 このアプリについて（初めての方へ）"):
        st.markdown("""
        このアプリは、とっても不器用で臆病なアンドロイドの「麻理」と対話し、彼女との絆を育むチャットボットです。

        **遊び方:**
        - **会話する:** 下の入力欄から麻理に話しかけてみましょう。
        - **好感度を上げる:** あなたの言葉遣いや内容によって、麻理のあなたに対する**好感度**が変化します。
        - **変化を楽しむ:** 好感度が上がると、麻理の態度が少しずつ柔らかくなったり、会話の舞台（シーン）が変わったりすることがあります。

        サイドバーの「📊 ステータス」で現在の好感度やシーンを確認できます。
        あなただけの麻理との物語を紡いでみてください。
        """)
    st.markdown("---")
    
    messages = st.session_state.get('messages', [])
    chat_interface.render_chat_history(messages)

def process_message(message: str, dialogue_generator, sentiment_analyzer, 
                   rate_limiter, scene_manager, memory_manager) -> str:
    """メッセージを処理して応答を生成する"""
    try:
        if not rate_limiter.check_limiter(st.session_state.limiter_state):
            return "（…少し話すのが速すぎる。もう少し、ゆっくり話してくれないか？）"
        
        history = []
        messages = st.session_state.messages
        for i in range(0, len(messages) - 1, 2):
            if i + 1 < len(messages):
                history.append((messages[i]["content"], messages[i + 1]["content"]))
        
        history = history[-MAX_HISTORY_TURNS:]
        
        old_affection = st.session_state.affection
        conversation_context = st.session_state.messages[-10:] if st.session_state.messages else []
        
        new_affection, affection_change, change_reason = sentiment_analyzer.update_affection(
            message, old_affection, conversation_context
        )
        st.session_state.affection = new_affection
        
        if affection_change != 0 and 'status_display' in st.session_state:
            st.session_state.status_display.show_affection_change_notification(
                old_affection, new_affection, change_reason
            )
        
        stage_name = sentiment_analyzer.get_relationship_stage(new_affection)
        current_theme = st.session_state.scene_params.get("theme", "default")
        new_scene = scene_manager.detect_scene_change(history, dialogue_generator, current_theme)
        
        instruction = None
        if new_scene and new_scene != current_theme:
            st.session_state.scene_params = scene_manager.update_scene_params(
                st.session_state.scene_params, new_scene
            )
            instruction = f"ユーザーと一緒に「{new_scene}」に来た。周囲の様子を見て、最初の感想をぶっきらぼうに一言つぶやいてください。"
            st.session_state.scene_change_pending = {"new_theme": new_scene}
        
        memory_summary = memory_manager.get_memory_summary()
        response = dialogue_generator.generate_dialogue(
            history, message, new_affection, stage_name, 
            st.session_state.scene_params, instruction, memory_summary
        )
        return response if response else "…なんて言えばいいか分からない。"
        
    except Exception as e:
        logger.error(f"メッセージ処理エラー: {e}")
        return "（ごめん、システムに問題が起きたみたいだ。）"

def main():
    """メイン関数"""
    st.set_page_config(
        page_title="麻理チャット", page_icon="🤖",
        layout="centered", initial_sidebar_state="expanded"
    )
    
    initialize_session_state()
    
    # 依存モジュールの初期化
    if 'background_manager' not in st.session_state: st.session_state.background_manager = BackgroundManager()
    if 'dialogue_generator' not in st.session_state: st.session_state.dialogue_generator = DialogueGenerator()
    if 'sentiment_analyzer' not in st.session_state: st.session_state.sentiment_analyzer = SentimentAnalyzer()
    if 'rate_limiter' not in st.session_state: st.session_state.rate_limiter = RateLimiter()
    if 'scene_manager' not in st.session_state: st.session_state.scene_manager = SceneManager()
    if 'memory_manager' not in st.session_state: st.session_state.memory_manager = MemoryManager(history_threshold=10)
    if 'chat_interface' not in st.session_state: st.session_state.chat_interface = ChatInterface(max_input_length=MAX_INPUT_LENGTH)
    if 'status_display' not in st.session_state: st.session_state.status_display = StatusDisplay()

    inject_custom_css()
    st.session_state.background_manager.update_background(
        st.session_state.scene_params.get("theme", "default"),
        st.session_state.affection
    )
    
    if st.session_state.memory_manager.should_compress_history(st.session_state.messages):
        compressed_messages, keywords = st.session_state.memory_manager.compress_history(
            st.session_state.messages, st.session_state.dialogue_generator
        )
        st.session_state.messages = compressed_messages
        logger.info(f"履歴を圧縮しました。キーワード: {keywords}")

    # --- ▼▼▼ 【修正箇所 3】呼び出し時の引数を修正 ▼▼▼ ---
    render_sidebar(st.session_state.background_manager, st.session_state.sentiment_analyzer)
    render_main_content(st.session_state.chat_interface, st.session_state.memory_manager)
    
    if user_input := st.chat_input("麻理に話しかける..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("考え中..."):
                response = process_message(
                    user_input, st.session_state.dialogue_generator, st.session_state.sentiment_analyzer, 
                    st.session_state.rate_limiter, st.session_state.scene_manager, st.session_state.memory_manager
                )
            st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        if st.session_state.get('scene_change_pending'):
            del st.session_state.scene_change_pending
            st.rerun()

if __name__ == "__main__":
    main()