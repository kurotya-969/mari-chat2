"""
背景管理コンポーネント
動的背景画像の切り替えとCSS管理
"""
import streamlit as st
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class BackgroundManager:
    """背景画像の管理を担当するクラス"""
    
    def __init__(self):
        """背景管理クラスを初期化する"""
        self.theme_urls = {
            "default": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=1200&h=800&fit=crop",
            "room_night": "https://images.unsplash.com/photo-1505142468610-359e7d316be0?w=1200&h=800&fit=crop",
            "beach_sunset": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200&h=800&fit=crop",
            "festival_night": "https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3?w=1200&h=800&fit=crop",
            "shrine_day": "https://images.unsplash.com/photo-1545569341-9eb8b30979d9?w=1200&h=800&fit=crop",
            "cafe_afternoon": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=1200&h=800&fit=crop",
            "aquarium_night": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=1200&h=800&fit=crop"
        }
        
        self.theme_descriptions = {
            "default": "デフォルトの部屋",
            "room_night": "夜の部屋",
            "beach_sunset": "夕日のビーチ",
            "festival_night": "夜祭り",
            "shrine_day": "昼間の神社",
            "cafe_afternoon": "午後のカフェ",
            "aquarium_night": "夜の水族館"
        }
    
    def get_theme_url(self, theme: str) -> str:
        """
        テーマに対応するURLを取得する
        
        Args:
            theme: テーマ名
            
        Returns:
            背景画像のURL
        """
        return self.theme_urls.get(theme, self.theme_urls["default"])
    
    def get_theme_description(self, theme: str) -> str:
        """
        テーマの説明を取得する
        
        Args:
            theme: テーマ名
            
        Returns:
            テーマの説明
        """
        return self.theme_descriptions.get(theme, "不明なシーン")
    
    def get_available_themes(self) -> Dict[str, str]:
        """
        利用可能なテーマとその説明を取得する
        
        Returns:
            テーマ名と説明の辞書
        """
        return self.theme_descriptions.copy()
    
    def update_background(self, theme: str, opacity: float = 0.7, 
                         blur_strength: int = 5, affection: int = 30) -> None:
        """
        背景画像を動的に変更する
        
        Args:
            theme: 適用するテーマ名
            opacity: オーバーレイの透明度 (0.0-1.0)
            blur_strength: ブラー効果の強度 (0-20)
            affection: 現在の好感度（動的スタイル用）
        """
        try:
            background_url = self.get_theme_url(theme)
            
            # 基本的な背景画像のCSS
            background_css = f"""
            <style>
            .stApp {{
                background-image: url('{background_url}');
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
                background-repeat: no-repeat;
                transition: background-image 1.5s ease-in-out;
            }}
            
            .stApp > div:first-child {{
                backdrop-filter: blur({blur_strength}px);
                min-height: 100vh;
                transition: background 1.5s ease-in-out, backdrop-filter 1.5s ease-in-out;
            }}
            </style>
            """
            
            st.markdown(background_css, unsafe_allow_html=True)
            
            # テーマ固有のスタイルを適用
            self.apply_theme_specific_styles(theme)
            
            # 好感度に基づく動的スタイルを適用
            self.apply_dynamic_styles(affection)
            
            # アクセシビリティスタイルを適用
            self.apply_accessibility_styles()
            
            logger.info(f"背景を'{theme}'に変更しました（好感度: {affection}）")
            
        except Exception as e:
            logger.error(f"背景更新エラー: {e}")
            # フォールバック：デフォルト背景を適用
            self._apply_fallback_background()
    
    def _apply_fallback_background(self) -> None:
        """フォールバック用のデフォルト背景を適用する"""
        try:
            default_css = """
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
            st.markdown(default_css, unsafe_allow_html=True)
            logger.info("フォールバック背景を適用しました")
            
        except Exception as e:
            logger.error(f"フォールバック背景適用エラー: {e}")
    
    def apply_theme_specific_styles(self, theme: str) -> None:
        """
        テーマ固有のスタイルを適用する
        
        Args:
            theme: 適用するテーマ名
        """
        try:
            theme_styles = {
                "default": {
                    "overlay_color": "rgba(0, 0, 0, 0.7)",
                    "text_shadow": "1px 1px 2px rgba(0, 0, 0, 0.7)",
                    "accent_color": "rgba(255, 255, 255, 0.2)"
                },
                "room_night": {
                    "overlay_color": "rgba(0, 0, 50, 0.8)",
                    "text_shadow": "2px 2px 4px rgba(0, 0, 0, 0.9)",
                    "accent_color": "rgba(100, 149, 237, 0.3)"
                },
                "beach_sunset": {
                    "overlay_color": "rgba(255, 100, 0, 0.3)",
                    "text_shadow": "1px 1px 3px rgba(0, 0, 0, 0.8)",
                    "accent_color": "rgba(255, 165, 0, 0.4)"
                },
                "festival_night": {
                    "overlay_color": "rgba(50, 0, 100, 0.7)",
                    "text_shadow": "2px 2px 4px rgba(0, 0, 0, 0.9)",
                    "accent_color": "rgba(255, 20, 147, 0.4)"
                },
                "shrine_day": {
                    "overlay_color": "rgba(0, 50, 0, 0.5)",
                    "text_shadow": "1px 1px 2px rgba(0, 0, 0, 0.6)",
                    "accent_color": "rgba(34, 139, 34, 0.3)"
                },
                "cafe_afternoon": {
                    "overlay_color": "rgba(139, 69, 19, 0.6)",
                    "text_shadow": "1px 1px 2px rgba(0, 0, 0, 0.7)",
                    "accent_color": "rgba(210, 180, 140, 0.4)"
                },
                "aquarium_night": {
                    "overlay_color": "rgba(0, 0, 139, 0.8)",
                    "text_shadow": "2px 2px 4px rgba(0, 0, 0, 0.9)",
                    "accent_color": "rgba(0, 191, 255, 0.3)"
                }
            }
            
            style_config = theme_styles.get(theme, theme_styles["default"])
            
            theme_css = f"""
            <style>
            .stApp > div:first-child {{
                background: {style_config["overlay_color"]} !important;
            }}
            
            .stMarkdown, .stText {{
                text-shadow: {style_config["text_shadow"]} !important;
            }}
            
            .stChatMessage:hover {{
                background: {style_config["accent_color"]} !important;
            }}
            
            .stButton > button:hover {{
                background: {style_config["accent_color"]} !important;
            }}
            
            .theme-accent {{
                background: {style_config["accent_color"]} !important;
                border: 1px solid {style_config["accent_color"]} !important;
            }}
            </style>
            """
            
            st.markdown(theme_css, unsafe_allow_html=True)
            logger.info(f"テーマ固有スタイルを適用: {theme}")
            
        except Exception as e:
            logger.error(f"テーマ固有スタイル適用エラー: {e}")
    
    def apply_dynamic_styles(self, affection: int) -> None:
        """
        好感度に基づく動的スタイルを適用する
        
        Args:
            affection: 現在の好感度
        """
        try:
            # 好感度に基づく色の変化
            if affection >= 80:
                accent_color = "rgba(255, 20, 147, 0.4)"  # ピンク（高好感度）
                glow_color = "rgba(255, 20, 147, 0.6)"
            elif affection >= 60:
                accent_color = "rgba(255, 165, 0, 0.4)"   # オレンジ（中高好感度）
                glow_color = "rgba(255, 165, 0, 0.6)"
            elif affection >= 40:
                accent_color = "rgba(255, 255, 0, 0.4)"   # 黄色（中好感度）
                glow_color = "rgba(255, 255, 0, 0.6)"
            elif affection >= 20:
                accent_color = "rgba(135, 206, 235, 0.4)" # 水色（低中好感度）
                glow_color = "rgba(135, 206, 235, 0.6)"
            else:
                accent_color = "rgba(128, 128, 128, 0.4)" # グレー（低好感度）
                glow_color = "rgba(128, 128, 128, 0.6)"
            
            dynamic_css = f"""
            <style>
            .affection-glow {{
                box-shadow: 0 0 20px {glow_color} !important;
                border: 2px solid {accent_color} !important;
            }}
            
            .affection-accent {{
                background: {accent_color} !important;
                border: 1px solid {accent_color} !important;
            }}
            
            .stProgress > div > div > div {{
                box-shadow: 0 0 15px {glow_color} !important;
            }}
            </style>
            """
            
            st.markdown(dynamic_css, unsafe_allow_html=True)
            logger.debug(f"動的スタイルを適用: 好感度{affection}")
            
        except Exception as e:
            logger.error(f"動的スタイル適用エラー: {e}")
    
    def apply_accessibility_styles(self) -> None:
        """
        アクセシビリティ向上のためのスタイルを適用する
        """
        try:
            accessibility_css = """
            <style>
            /* ハイコントラストモード対応 */
            @media (prefers-contrast: high) {
                .stApp > div:first-child {
                    background: rgba(0, 0, 0, 0.9) !important;
                }
                
                .stChatMessage {
                    background: rgba(255, 255, 255, 0.2) !important;
                    border: 2px solid rgba(255, 255, 255, 0.5) !important;
                }
                
                .stButton > button {
                    background: rgba(255, 255, 255, 0.2) !important;
                    border: 2px solid rgba(255, 255, 255, 0.6) !important;
                }
            }
            
            /* 動きを減らす設定 */
            @media (prefers-reduced-motion: reduce) {
                .stApp, .stApp > div:first-child, .stChatMessage {
                    transition: none !important;
                    animation: none !important;
                }
            }
            
            /* フォーカス表示の改善 */
            .stButton > button:focus,
            .stTextInput > div > div > input:focus,
            .stSelectbox > div > div:focus {
                outline: 3px solid rgba(255, 255, 255, 0.8) !important;
                outline-offset: 2px !important;
            }
            
            /* 大きなテキスト設定対応 */
            @media (min-resolution: 2dppx) {
                .stMarkdown, .stText {
                    font-size: 1.1em !important;
                    line-height: 1.6 !important;
                }
            }
            </style>
            """
            
            st.markdown(accessibility_css, unsafe_allow_html=True)
            logger.info("アクセシビリティスタイルを適用しました")
            
        except Exception as e:
            logger.error(f"アクセシビリティスタイル適用エラー: {e}")
    
    def get_style_config(self) -> Dict[str, any]:
        """
        現在のスタイル設定を取得する
        
        Returns:
            スタイル設定の辞書
        """
        try:
            # session_stateから現在の設定を取得
            current_theme = "default"
            current_affection = 30
            
            if hasattr(st, 'session_state'):
                if hasattr(st.session_state, 'scene_params'):
                    scene_params = st.session_state.scene_params
                    if isinstance(scene_params, dict):
                        current_theme = scene_params.get("theme", "default")
                
                if hasattr(st.session_state, 'affection'):
                    current_affection = st.session_state.affection
            
            return {
                "current_theme": current_theme,
                "current_affection": current_affection,
                "theme_url": self.get_theme_url(current_theme),
                "theme_description": self.get_theme_description(current_theme),
                "available_themes": self.get_available_themes(),
                "css_file_loaded": True
            }
            
        except Exception as e:
            logger.error(f"スタイル設定取得エラー: {e}")
            return {
                "current_theme": "default",
                "current_affection": 30,
                "theme_url": self.get_theme_url("default"),
                "theme_description": "デフォルトの部屋",
                "available_themes": self.get_available_themes(),
                "css_file_loaded": False
            }
    
    def apply_scene_transition_effect(self, old_theme: str, new_theme: str) -> None:
        """
        シーン変更時のトランジション効果を適用する
        
        Args:
            old_theme: 変更前のテーマ
            new_theme: 変更後のテーマ
        """
        try:
            # トランジション効果のCSS
            transition_css = """
            <style>
            .stApp {
                transition: background-image 1.5s ease-in-out;
            }
            
            .stApp > div:first-child {
                transition: background 1.5s ease-in-out, backdrop-filter 1.5s ease-in-out;
            }
            
            /* フェードイン効果 */
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            .scene-transition {
                animation: fadeIn 2s ease-in-out;
            }
            </style>
            """
            
            st.markdown(transition_css, unsafe_allow_html=True)
            
            # 新しい背景を適用
            self.update_background(new_theme)
            
            logger.info(f"シーン変更: {old_theme} → {new_theme}")
            
        except Exception as e:
            logger.error(f"シーン変更効果エラー: {e}")
            # エラー時は通常の背景更新を実行
            self.update_background(new_theme)
    
    def show_scene_change_notification(self, new_theme: str) -> None:
        """
        シーン変更の通知を表示する
        
        Args:
            new_theme: 新しいテーマ名
        """
        try:
            theme_description = self.get_theme_description(new_theme)
            
            # 通知メッセージを表示
            st.success(f"🎭 シーンが変更されました: {theme_description}")
            
            # 短時間後に自動で消える通知（JavaScript使用）
            notification_js = f"""
            <script>
            setTimeout(function() {{
                const notifications = document.querySelectorAll('.stAlert');
                notifications.forEach(function(notification) {{
                    if (notification.textContent.includes('シーンが変更されました')) {{
                        notification.style.transition = 'opacity 0.5s ease-out';
                        notification.style.opacity = '0';
                        setTimeout(function() {{
                            notification.remove();
                        }}, 500);
                    }}
                }});
            }}, 3000);
            </script>
            """
            
            st.markdown(notification_js, unsafe_allow_html=True)
            
        except Exception as e:
            logger.error(f"シーン変更通知エラー: {e}")
    
    def get_current_theme_info(self) -> Dict[str, str]:
        """
        現在のテーマ情報を取得する
        
        Returns:
            現在のテーマ情報の辞書
        """
        try:
            # session_stateが存在し、scene_paramsが存在するかチェック
            if hasattr(st, 'session_state') and hasattr(st.session_state, 'scene_params'):
                scene_params = st.session_state.scene_params
                if isinstance(scene_params, dict):
                    current_theme = scene_params.get("theme", "default")
                else:
                    current_theme = "default"
            else:
                current_theme = "default"
            
            return {
                "theme": current_theme,
                "description": self.get_theme_description(current_theme),
                "url": self.get_theme_url(current_theme)
            }
            
        except Exception as e:
            logger.error(f"テーマ情報取得エラー: {e}")
            return {
                "theme": "default",
                "description": "デフォルトの部屋",
                "url": self.get_theme_url("default")
            }
    
    def validate_theme(self, theme: str) -> bool:
        """
        テーマが有効かどうかを検証する
        
        Args:
            theme: 検証するテーマ名
            
        Returns:
            テーマが有効かどうか
        """
        return theme in self.theme_urls
    
    def inject_base_styles(self) -> None:
        """
        基本的なスタイルを注入する
        """
        try:
            # 外部CSSファイルを読み込み
            css_file_path = "streamlit_styles.css"
            try:
                with open(css_file_path, 'r', encoding='utf-8') as f:
                    css_content = f.read()
                st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
                logger.info("外部CSSファイルを読み込みました")
            except FileNotFoundError:
                logger.warning(f"CSSファイルが見つかりません: {css_file_path}")
                self._apply_fallback_styles()
            
        except Exception as e:
            logger.error(f"基本スタイル注入エラー: {e}")
            self._apply_fallback_styles()
    
    def _apply_fallback_styles(self) -> None:
        """フォールバック用の基本スタイルを適用する"""
        try:
            fallback_css = """
            <style>
            /* フォールバック用基本スタイル */
            .stApp {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            
            .stApp > div:first-child {
                background: rgba(0, 0, 0, 0.7);
                backdrop-filter: blur(5px);
                min-height: 100vh;
            }
            
            .stChatMessage {
                background: rgba(255, 255, 255, 0.1) !important;
                backdrop-filter: blur(10px);
                border-radius: 12px !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
            }
            
            .css-1d391kg, .css-1cypcdb {
                background: rgba(0, 0, 0, 0.8) !important;
                backdrop-filter: blur(15px) !important;
            }
            
            .stButton > button {
                background: rgba(255, 255, 255, 0.1) !important;
                color: white !important;
                border: 1px solid rgba(255, 255, 255, 0.3) !important;
                backdrop-filter: blur(5px);
            }
            
            .stTextInput > div > div > input {
                background: rgba(255, 255, 255, 0.1) !important;
                color: white !important;
                border: 1px solid rgba(255, 255, 255, 0.3) !important;
            }
            </style>
            """
            
            st.markdown(fallback_css, unsafe_allow_html=True)
            logger.info("フォールバック基本スタイルを適用しました")
            
        except Exception as e:
            logger.error(f"フォールバック基本スタイル適用エラー: {e}")