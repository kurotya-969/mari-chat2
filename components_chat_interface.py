"""
チャットインターフェースコンポーネント
Streamlitのチャット機能を使用したメッセージ表示と入力処理
"""
import streamlit as st
import logging
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
        チャット履歴を表示する
        
        Args:
            messages: チャットメッセージのリスト
            memory_summary: メモリサマリー（重要単語から生成）
        """
        try:
            # メモリサマリーがある場合は表示
            if memory_summary:
                with st.expander("💭 過去の会話の記憶", expanded=False):
                    st.info(memory_summary)
            
            # 初回メッセージ
            if not messages:
                with st.chat_message("assistant"):
                    st.markdown("何の用？遊びに来たの？")
                return
            
            # 既存のメッセージを表示
            for message in messages:
                role = message.get("role", "user")
                content = message.get("content", "")
                timestamp = message.get("timestamp")
                
                with st.chat_message(role):
                    st.markdown(content)
                    
                    # デバッグモードの場合はタイムスタンプを表示
                    if st.session_state.get("debug_mode", False) and timestamp:
                        st.caption(f"送信時刻: {timestamp}")
                        
        except Exception as e:
            logger.error(f"チャット履歴表示エラー: {e}")
            st.error("チャット履歴の表示中にエラーが発生しました。")
    
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
                   messages: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
        """
        メッセージをリストに追加する
        
        Args:
            role: メッセージの役割 ('user' or 'assistant')
            content: メッセージ内容
            messages: メッセージリスト（Noneの場合はsession_stateから取得）
            
        Returns:
            更新されたメッセージリスト
        """
        try:
            if messages is None:
                messages = st.session_state.get('messages', [])
            
            # メッセージオブジェクトを作成
            message = {
                "role": role,
                "content": self.sanitize_message(content),
                "timestamp": datetime.now().isoformat()
            }
            
            messages.append(message)
            
            # セッション状態を更新
            st.session_state.messages = messages
            
            logger.info(f"メッセージを追加: {role} - {len(content)}文字")
            return messages
            
        except Exception as e:
            logger.error(f"メッセージ追加エラー: {e}")
            return messages or []
    
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