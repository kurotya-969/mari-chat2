"""
チャットインターフェースコンポーネント
Streamlitのチャット機能を使用したメッセージ表示と入力処理
マスクアイコンとフリップアニメーション機能を含む
"""
import streamlit as st
import logging
import re
import uuid
from typing import List, Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class ChatInterface:
    """チャットインターフェースを管理するクラス"""
    
    def __init__(self, max_input_length: int = 1000):
        """
        Args:
            max_input_length: 入力メッセージの最大長
        """
        self.max_input_length = max_input_length
    
    def render_chat_history(self, messages: List[Dict[str, str]], 
                          memory_summary: str = "") -> None:
        """
        チャット履歴を表示する（マスク機能付き）
        
        Args:
            messages: チャットメッセージのリスト
            memory_summary: メモリサマリー（重要単語から生成）
        """
        try:
            # メモリサマリーがある場合は表示
            if memory_summary:
                with st.expander("💭 過去の会話の記憶", expanded=False):
                    st.info(memory_summary)
            
            # 既存のメッセージを表示
            for i, message in enumerate(messages):
                role = message.get("role", "user")
                content = message.get("content", "")
                timestamp = message.get("timestamp")
                is_initial = message.get("is_initial", False)
                message_id = message.get("message_id", f"msg_{i}")
                
                with st.chat_message(role):
                    if role == "assistant":
                        # 麻理のメッセージの場合、隠された真実をチェック
                        self._render_mari_message_with_mask(message_id, content, is_initial)
                    else:
                        # ユーザーメッセージは通常通り表示
                        if is_initial:
                            st.markdown(f'<div class="mari-initial-message">{content}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(content)
                    
                    # デバッグモードの場合はタイムスタンプを表示
                    if st.session_state.get("debug_mode", False) and timestamp:
                        st.caption(f"送信時刻: {timestamp}")
                        
        except Exception as e:
            logger.error(f"チャット履歴表示エラー: {e}")
            st.error("チャット履歴の表示中にエラーが発生しました。")
    
    def _render_mari_message_with_mask(self, message_id: str, content: str, is_initial: bool = False) -> None:
        """
        麻理のメッセージをマスク機能付きで表示する
        
        Args:
            message_id: メッセージの一意ID
            content: メッセージ内容
            is_initial: 初期メッセージかどうか
        """
        try:
            # 隠された真実を検出
            has_hidden_content, visible_content, hidden_content = self._detect_hidden_content(content)
            
            # 隠された真実が検出されない場合のフォールバック処理
            if not has_hidden_content:
                logger.warning(f"隠された真実が検出されませんでした: '{content[:50]}...'")
                # AIが[HIDDEN:...]形式で応答していない場合は通常表示
            
            # セッション状態でフリップ状態を管理
            if 'message_flip_states' not in st.session_state:
                st.session_state.message_flip_states = {}
            
            is_flipped = st.session_state.message_flip_states.get(message_id, False)
            
            if has_hidden_content:
                # マスクアイコン付きメッセージを表示
                self._render_message_with_flip_animation(
                    message_id, visible_content, hidden_content, is_flipped, is_initial
                )
            else:
                # 通常のメッセージ表示
                if is_initial:
                    st.markdown(f'<div class="mari-initial-message">{content}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(content)
                    
        except Exception as e:
            logger.error(f"マスク付きメッセージ表示エラー: {e}")
            # フォールバック: 通常のメッセージ表示
            st.markdown(content)
    
    def _detect_hidden_content(self, content: str) -> Tuple[bool, str, str]:
        """
        メッセージから隠された真実を検出する
        
        Args:
            content: メッセージ内容
            
        Returns:
            (隠された内容があるか, 表示用内容, 隠された内容)
        """
        try:
            # デバッグ用ログ
            logger.info(f"🔍 隠された内容検出中: '{content[:50]}...'")
            
            # 隠された真実のマーカーを検索
            # 形式: [HIDDEN:隠された内容]表示される内容
            hidden_pattern = r'\[HIDDEN:(.*?)\](.*)'
            match = re.search(hidden_pattern, content)
            
            if match:
                hidden_content = match.group(1).strip()
                visible_content = match.group(2).strip()
                
                # 複数HIDDENをチェック
                additional_hidden = re.findall(r'\[HIDDEN:(.*?)\]', visible_content)
                if additional_hidden:
                    logger.warning(f"⚠️ 複数HIDDEN検出: {len(additional_hidden) + 1}個のHIDDENが見つかりました")
                    # 2番目以降のHIDDENを表示内容から除去
                    visible_content = re.sub(r'\[HIDDEN:.*?\]', '', visible_content).strip()
                    logger.info(f"🔧 複数HIDDEN除去後: 表示='{visible_content}'")
                
                logger.info(f"🐕 隠された真実を検出: 表示='{visible_content}', 隠し='{hidden_content}'")
                return True, visible_content, hidden_content
            
            # マーカーがない場合は通常のメッセージ
            logger.info(f"📝 通常メッセージ: '{content[:30]}...'")
            return False, content, ""
            
        except Exception as e:
            logger.error(f"隠された内容検出エラー: {e}")
            return False, content, ""
    
    def _render_message_with_flip_animation(self, message_id: str, visible_content: str, 
                                          hidden_content: str, is_flipped: bool, is_initial: bool = False) -> None:
        """
        フリップアニメーション付きメッセージを表示する
        
        Args:
            message_id: メッセージID
            visible_content: 表示用内容
            hidden_content: 隠された内容
            is_flipped: 現在フリップされているか
            is_initial: 初期メッセージかどうか
        """
        try:
            logger.info(f"🐕 ポチモード付きメッセージを表示: ID={message_id}, フリップ={is_flipped}")
            # フリップアニメーション用CSS
            flip_css = f"""
            <style>
            .message-container-{message_id} {{
                position: relative;
                perspective: 1000px;
                margin: 10px 0;
            }}
            
            .message-flip-{message_id} {{
                position: relative;
                width: 100%;
                height: auto;
                min-height: 60px;
                transform-style: preserve-3d;
                transition: transform 0.4s ease-in-out;
                transform: {'rotateY(180deg)' if is_flipped else 'rotateY(0deg)'};
            }}
            
            .message-side-{message_id} {{
                position: absolute;
                width: 100%;
                backface-visibility: hidden;
                padding: 15px 45px 15px 15px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                font-family: var(--mari-font);
                line-height: 1.7;
                min-height: 50px;
            }}
            
            .message-front-{message_id} {{
                background: var(--mari-bubble-bg);
                border: 1px solid rgba(0, 0, 0, 0.1);
                color: var(--text-color);
                transform: rotateY(0deg);
            }}
            
            .message-back-{message_id} {{
                background: var(--hidden-bubble-bg);
                border: 1px solid rgba(255, 248, 225, 0.7);
                color: var(--text-color);
                transform: rotateY(180deg);
                box-shadow: 0 2px 8px rgba(255, 248, 225, 0.3);
            }}
            
            .mask-icon-{message_id} {{
                position: absolute;
                bottom: 12px;
                right: 12px;
                font-size: 20px;
                cursor: pointer;
                padding: 6px;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.9);
                transition: all 0.3s ease;
                z-index: 10;
                user-select: none;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
            }}
            
            .mask-icon-{message_id}:hover {{
                background: rgba(255, 255, 255, 1);
                transform: scale(1.1);
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            }}
            
            .mask-icon-{message_id}:active {{
                transform: scale(0.95);
            }}
            
            .tutorial-pulse-{message_id} {{
                animation: tutorialPulse 2s ease-in-out infinite;
            }}
            
            @keyframes tutorialPulse {{
                0%, 100% {{ 
                    transform: scale(1);
                    box-shadow: 0 0 0 0 rgba(255, 105, 180, 0.7);
                }}
                50% {{ 
                    transform: scale(1.1);
                    box-shadow: 0 0 0 10px rgba(255, 105, 180, 0);
                }}
            }}
            </style>
            """
            
            # 犬のボタンの状態を事前にチェックして即座に反映
            show_all_hidden = st.session_state.get('show_all_hidden', False)
            
            # 犬のボタンの状態に従って表示を切り替え
            if show_all_hidden != is_flipped:
                st.session_state.message_flip_states[message_id] = show_all_hidden
                is_flipped = show_all_hidden
            
            # 現在表示するコンテンツを決定
            current_content = hidden_content if is_flipped else visible_content
            initial_class = "mari-initial-message" if is_initial else ""
            
            # メッセージを全幅で表示（ボタンは削除）
            # 背景色を動的に設定
            bg_color = "#FFF8E1" if is_flipped else "#F5F5F5"
            message_style = f"""
            <div style="
                padding: 15px; 
                background: {bg_color}; 
                border-radius: 12px; 
                border: 1px solid rgba(0,0,0,0.1); 
                min-height: 50px;
                font-family: var(--mari-font);
                line-height: 1.7;
                margin: 8px 0;
            ">
                <div class="{initial_class}">{current_content}</div>
            </div>
            """
            st.markdown(message_style, unsafe_allow_html=True)
            
            # 本音表示機能の状態表示（開発用）
            if st.session_state.get("debug_mode", False):
                st.caption(f"🐕 Dog Mode: ID={message_id}, Hidden={len(hidden_content)>0}, Showing={is_flipped}")
                
        except Exception as e:
            logger.error(f"フリップアニメーション表示エラー: {e}")
            # フォールバック: 通常のメッセージ表示
            st.markdown(visible_content)
    
    def _is_tutorial_message(self, message_id: str) -> bool:
        """
        チュートリアル用のメッセージかどうかを判定する
        
        Args:
            message_id: メッセージID
            
        Returns:
            チュートリアルメッセージかどうか
        """
        # 初回のマスク付きメッセージの場合はチュートリアル扱い
        tutorial_completed = st.session_state.get('mask_tutorial_completed', False)
        return not tutorial_completed and message_id == "msg_0"
    
    def validate_input(self, message: str) -> Tuple[bool, str]:
        """
        入力メッセージの検証
        
        Args:
            message: 入力メッセージ
            
        Returns:
            (検証結果, エラーメッセージ)
        """
        if not message or not message.strip():
            return False, "メッセージが空です。"
        
        if len(message) > self.max_input_length:
            return False, f"メッセージが長すぎます。{self.max_input_length}文字以内で入力してください。"
        
        # 不正な文字のチェック
        if any(ord(char) < 32 and char not in ['\n', '\r', '\t'] for char in message):
            return False, "不正な文字が含まれています。"
        
        return True, ""
    
    def sanitize_message(self, message: str) -> str:
        """
        メッセージをサニタイズする
        
        Args:
            message: 入力メッセージ
            
        Returns:
            サニタイズされたメッセージ
        """
        try:
            # 基本的なサニタイズ
            sanitized = message.strip()
            
            # HTMLエスケープ（Streamlitが自動で行うが念のため）
            sanitized = sanitized.replace("<", "&lt;").replace(">", "&gt;")
            
            # 連続する空白を単一の空白に変換
            import re
            sanitized = re.sub(r'\s+', ' ', sanitized)
            
            return sanitized
            
        except Exception as e:
            logger.error(f"メッセージサニタイズエラー: {e}")
            return message
    
    def add_message(self, role: str, content: str, 
                   messages: Optional[List[Dict[str, str]]] = None, 
                   message_id: Optional[str] = None) -> List[Dict[str, str]]:
        """
        メッセージをリストに追加する（マスク機能対応）
        
        Args:
            role: メッセージの役割 ('user' or 'assistant')
            content: メッセージ内容
            messages: メッセージリスト（Noneの場合はsession_stateから取得）
            message_id: メッセージの一意ID（Noneの場合は自動生成）
            
        Returns:
            更新されたメッセージリスト
        """
        try:
            if messages is None:
                messages = st.session_state.get('messages', [])
            
            # メッセージIDを生成または使用
            if message_id is None:
                message_id = f"msg_{len(messages)}_{uuid.uuid4().hex[:8]}"
            
            # メッセージオブジェクトを作成
            message = {
                "role": role,
                "content": self.sanitize_message(content),
                "timestamp": datetime.now().isoformat(),
                "message_id": message_id
            }
            
            messages.append(message)
            
            # セッション状態を更新
            st.session_state.messages = messages
            
            logger.info(f"メッセージを追加: {role} - {len(content)}文字 (ID: {message_id})")
            return messages
            
        except Exception as e:
            logger.error(f"メッセージ追加エラー: {e}")
            return messages or []
    
    def create_hidden_content_message(self, visible_content: str, hidden_content: str) -> str:
        """
        隠された真実を含むメッセージを作成する
        
        Args:
            visible_content: 表示される内容
            hidden_content: 隠された内容
            
        Returns:
            マーカー付きメッセージ
        """
        return f"[HIDDEN:{hidden_content}]{visible_content}"
    
    def generate_mock_hidden_content(self, visible_content: str) -> str:
        """
        テスト用のモック隠された内容を生成する
        
        Args:
            visible_content: 表示される内容
            
        Returns:
            隠された内容
        """
        # 簡単なモック生成ロジック
        mock_patterns = {
            "何の用？": "（本当は嬉しいけど...素直になれない）",
            "別に": "（実はすごく気になってる）",
            "そうね": "（もっと話していたい）",
            "まあまあ": "（とても楽しい！）",
            "普通": "（特別な時間だと思ってる）",
            "いいんじゃない": "（すごく良いと思う！）",
            "そんなことない": "（本当はそう思ってる）"
        }
        
        for pattern, hidden in mock_patterns.items():
            if pattern in visible_content:
                return hidden
        
        # デフォルトの隠された内容
        return "（本当の気持ちは...）"
    
    def render_input_area(self, placeholder: str = "メッセージを入力してください...") -> Optional[str]:
        """
        入力エリアをレンダリングし、入力を取得する
        
        Args:
            placeholder: 入力フィールドのプレースホルダー
            
        Returns:
            入力されたメッセージ（入力がない場合はNone）
        """
        try:
            # レート制限チェック
            if st.session_state.get('limiter_state', {}).get('is_blocked', False):
                st.warning("⏰ レート制限中です。しばらくお待ちください。")
                st.chat_input(placeholder, disabled=True)
                return None
            
            # 通常の入力フィールド
            user_input = st.chat_input(placeholder)
            
            if user_input:
                # 入力検証
                is_valid, error_msg = self.validate_input(user_input)
                if not is_valid:
                    st.error(error_msg)
                    return None
                
                return user_input
            
            return None
            
        except Exception as e:
            logger.error(f"入力エリア表示エラー: {e}")
            st.error("入力エリアの表示中にエラーが発生しました。")
            return None
    
    def show_typing_indicator(self, message: str = "考え中...") -> None:
        """
        タイピングインジケーターを表示する
        
        Args:
            message: 表示するメッセージ
        """
        return st.spinner(message)
    
    def clear_chat_history(self) -> None:
        """チャット履歴をクリアする"""
        try:
            st.session_state.messages = []
            logger.info("チャット履歴をクリアしました")
            
        except Exception as e:
            logger.error(f"チャット履歴クリアエラー: {e}")
    
    def get_chat_stats(self) -> Dict[str, int]:
        """
        チャットの統計情報を取得する
        
        Returns:
            統計情報の辞書
        """
        try:
            messages = st.session_state.get('messages', [])
            
            user_messages = [msg for msg in messages if msg.get("role") == "user"]
            assistant_messages = [msg for msg in messages if msg.get("role") == "assistant"]
            
            total_chars = sum(len(msg.get("content", "")) for msg in messages)
            
            return {
                "total_messages": len(messages),
                "user_messages": len(user_messages),
                "assistant_messages": len(assistant_messages),
                "total_characters": total_chars,
                "average_message_length": total_chars // len(messages) if messages else 0
            }
            
        except Exception as e:
            logger.error(f"統計情報取得エラー: {e}")
            return {
                "total_messages": 0,
                "user_messages": 0,
                "assistant_messages": 0,
                "total_characters": 0,
                "average_message_length": 0
            }
    
    def export_chat_history(self) -> str:
        """
        チャット履歴をエクスポート用の文字列として取得する
        
        Returns:
            エクスポート用の文字列
        """
        try:
            messages = st.session_state.get('messages', [])
            
            if not messages:
                return "チャット履歴がありません。"
            
            export_lines = []
            export_lines.append("=== 麻理チャット履歴 ===")
            export_lines.append(f"エクスポート日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            export_lines.append("")
            
            for i, message in enumerate(messages, 1):
                role = "ユーザー" if message.get("role") == "user" else "麻理"
                content = message.get("content", "")
                timestamp = message.get("timestamp", "")
                
                export_lines.append(f"[{i}] {role}: {content}")
                if timestamp:
                    export_lines.append(f"    時刻: {timestamp}")
                export_lines.append("")
            
            return "\n".join(export_lines)
            
        except Exception as e:
            logger.error(f"履歴エクスポートエラー: {e}")
            return "エクスポート中にエラーが発生しました。"