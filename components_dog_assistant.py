"""
ポチ（犬）アシスタントコンポーネント
画面右下に固定配置され、本音表示機能を提供する
"""
import streamlit as st
import logging

logger = logging.getLogger(__name__)

class DogAssistant:
    """ポチ（犬）アシスタントクラス"""
    
    def __init__(self):
        """初期化"""
        self.default_message = "ポチは麻理の本音を察知したようだ・・・"
        self.active_message = "ワンワン！本音が見えてるワン！"
    
    def render_dog_component(self):
        """画面右下に固定配置される犬のコンポーネントを描画"""
        try:
            # 犬のコンポーネントのCSS（レスポンシブ対応）
            dog_css = """
            <style>
            .dog-assistant-container {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 1000;
                display: flex;
                flex-direction: column;
                align-items: flex-end;
                pointer-events: none;
            }
            
            .dog-speech-bubble {
                background-color: rgba(255, 255, 255, 0.95);
                color: #333;
                padding: 10px 15px;
                border-radius: 20px;
                font-size: 13px;
                margin-bottom: 10px;
                position: relative;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(0,0,0,0.1);
                max-width: 200px;
                word-wrap: break-word;
                animation: bubbleFloat 3s ease-in-out infinite;
                pointer-events: auto;
            }
            
            .dog-speech-bubble::after {
                content: '';
                position: absolute;
                bottom: -8px;
                right: 20px;
                width: 0;
                height: 0;
                border-left: 8px solid transparent;
                border-right: 8px solid transparent;
                border-top: 8px solid rgba(255, 255, 255, 0.95);
            }
            
            .dog-button {
                background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%);
                border: none;
                border-radius: 50%;
                width: 70px;
                height: 70px;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(255, 154, 158, 0.4);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 35px;
                pointer-events: auto;
                animation: dogBounce 2s ease-in-out infinite;
            }
            
            .dog-button:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 20px rgba(255, 154, 158, 0.6);
                background: linear-gradient(135deg, #ff6b6b 0%, #feca57 50%, #ff9ff3 100%);
            }
            
            .dog-button:active {
                transform: scale(0.95);
            }
            
            .dog-button.active {
                background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
                animation: dogActive 1s ease-in-out infinite;
            }
            
            @keyframes bubbleFloat {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-5px); }
            }
            
            @keyframes dogBounce {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-3px); }
            }
            
            @keyframes dogActive {
                0%, 100% { transform: scale(1) rotate(0deg); }
                25% { transform: scale(1.05) rotate(-2deg); }
                75% { transform: scale(1.05) rotate(2deg); }
            }
            
            /* レスポンシブ対応 */
            @media (max-width: 768px) {
                .dog-assistant-container {
                    bottom: 15px;
                    right: 15px;
                }
                
                .dog-speech-bubble {
                    max-width: 150px;
                    font-size: 12px;
                    padding: 8px 12px;
                }
                
                .dog-button {
                    width: 60px;
                    height: 60px;
                    font-size: 30px;
                }
            }
            
            @media (max-width: 480px) {
                .dog-assistant-container {
                    bottom: 10px;
                    right: 10px;
                }
                
                .dog-speech-bubble {
                    max-width: 120px;
                    font-size: 11px;
                    padding: 6px 10px;
                }
                
                .dog-button {
                    width: 50px;
                    height: 50px;
                    font-size: 25px;
                }
            }
            
            /* 画面が非常に小さい場合は吹き出しを非表示 */
            @media (max-width: 320px) {
                .dog-speech-bubble {
                    display: none;
                }
            }
            </style>
            """
            
            # 現在の状態を取得
            is_active = st.session_state.get('show_all_hidden', False)
            bubble_text = self.active_message if is_active else self.default_message
            button_class = "dog-button active" if is_active else "dog-button"
            
            # JavaScriptでクリックイベントを処理
            dog_js = f"""
            <script>
            function toggleDogMode() {{
                // Streamlitのセッション状態を更新するためのトリガー
                const event = new CustomEvent('dogButtonClick', {{
                    detail: {{ active: {str(is_active).lower()} }}
                }});
                window.dispatchEvent(event);
                
                // ボタンの状態を即座に更新
                const button = document.querySelector('.dog-button');
                const bubble = document.querySelector('.dog-speech-bubble');
                
                if (button && bubble) {{
                    if ({str(is_active).lower()}) {{
                        button.classList.remove('active');
                        bubble.textContent = '{self.default_message}';
                    }} else {{
                        button.classList.add('active');
                        bubble.textContent = '{self.active_message}';
                    }}
                }}
            }}
            
            // ページ読み込み時にイベントリスナーを設定
            document.addEventListener('DOMContentLoaded', function() {{
                const button = document.querySelector('.dog-button');
                if (button) {{
                    button.addEventListener('click', toggleDogMode);
                }}
            }});
            
            // Streamlitの再描画後にもイベントリスナーを再設定
            setTimeout(function() {{
                const button = document.querySelector('.dog-button');
                if (button) {{
                    button.addEventListener('click', toggleDogMode);
                }}
            }}, 100);
            </script>
            """
            
            # HTMLコンポーネント
            dog_html = f"""
            <div class="dog-assistant-container">
                <div class="dog-speech-bubble">
                    {bubble_text}
                </div>
                <button class="{button_class}" title="ポチが麻理の本音を察知します" onclick="toggleDogMode()">
                    🐕
                </button>
            </div>
            """
            
            # CSSとJavaScriptとHTMLを結合して表示
            st.markdown(dog_css + dog_js + dog_html, unsafe_allow_html=True)
            
            logger.debug(f"犬のコンポーネントを描画しました (active: {is_active})")
            
        except Exception as e:
            logger.error(f"犬のコンポーネント描画エラー: {e}")
    
    def handle_dog_button_click(self):
        """犬のボタンクリック処理"""
        try:
            # 本音表示機能のトリガー
            if 'show_all_hidden' not in st.session_state:
                st.session_state.show_all_hidden = False
            
            # 新しい状態を設定
            new_state = not st.session_state.show_all_hidden
            st.session_state.show_all_hidden = new_state
            

            
            # 全メッセージのフリップ状態を即座に更新
            if 'message_flip_states' not in st.session_state:
                st.session_state.message_flip_states = {}
            
            # 現在のメッセージに対してフリップ状態を設定
            if 'chat' in st.session_state and 'messages' in st.session_state.chat:
                for i, message in enumerate(st.session_state.chat['messages']):
                    if message['role'] == 'assistant':
                        message_id = f"msg_{i}"
                        st.session_state.message_flip_states[message_id] = new_state
            
            # 通知メッセージ
            if new_state:
                st.success("🐕 ポチが麻理の本音を察知しました！")
            else:
                st.info("🐕 ポチが通常モードに戻りました。")
            
            logger.info(f"犬のボタンがクリックされました (new state: {new_state})")
            
        except Exception as e:
            logger.error(f"犬のボタンクリック処理エラー: {e}")
    
    def render_with_streamlit_button(self):
        """Streamlitのボタンを使用した代替実装（フォールバック用）"""
        try:
            # 固定位置のCSS
            fallback_css = """
            <style>
            .dog-fallback-container {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 1000;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 15px;
                padding: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                backdrop-filter: blur(10px);
            }
            
            @media (max-width: 768px) {
                .dog-fallback-container {
                    bottom: 15px;
                    right: 15px;
                    padding: 8px;
                }
            }
            </style>
            """
            
            st.markdown(fallback_css, unsafe_allow_html=True)
            
            # コンテナの開始
            st.markdown('<div class="dog-fallback-container">', unsafe_allow_html=True)
            
            # 状態表示
            is_active = st.session_state.get('show_all_hidden', False)
            status_text = "本音モード中" if is_active else "通常モード"
            st.caption(f"🐕 {status_text}")
            
            # ボタン
            button_text = "🔄 戻す" if is_active else "🐕 本音を見る"
            if st.button(button_text, key="dog_assistant_btn"):
                self.handle_dog_button_click()
                st.rerun()
            
            # コンテナの終了
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            logger.error(f"犬のフォールバック描画エラー: {e}")
    
    def get_current_state(self):
        """現在の犬の状態を取得"""
        return {
            'is_active': st.session_state.get('show_all_hidden', False),
            'message': self.active_message if st.session_state.get('show_all_hidden', False) else self.default_message
        }