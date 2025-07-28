"""
Together AI API client for enhancing emotional expression in letters.
"""
import os
import asyncio
from typing import Dict, Optional, Any
import aiohttp
import json
import logging

logger = logging.getLogger(__name__)

class TogetherClient:
    """Together AI API client for enhancing emotional expression in letters."""
    
    def __init__(self):
        """環境変数からAPIキーを取得してTogetherクライアントを初期化"""
        self.api_key = os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("TOGETHER_API_KEY environment variable is required")
        
        self.base_url = "https://api.together.xyz/v1/chat/completions"
        self.model = "meta-llama/Llama-2-70b-chat-hf"
        self.max_retries = 3
        self.retry_delay = 1.0
    
    async def enhance_emotion(self, structure: str, context: Dict[str, Any]) -> str:
        """
        論理構造に感情表現を補完して完成した手紙を生成
        
        Args:
            structure: Groqで生成された論理構造
            context: ユーザーコンテキスト（履歴、好みなど）
            
        Returns:
            感情表現が補完された完成した手紙
            
        Raises:
            Exception: リトライ後もAPI呼び出しが失敗した場合
        """
        prompt = self._build_emotion_prompt(structure, context)
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Together AIで感情表現を補完中 (試行 {attempt + 1})")
                
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    payload = {
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "あなたは感情豊かで親しみやすい「麻理」というAIです。与えられた手紙の構造に感情表現を加えて完成させてください。"
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 2000,
                        "temperature": 0.8,
                        "top_p": 0.9,
                        "stop": ["</s>", "[INST]", "[/INST]"]
                    }
                    
                    async with session.post(self.base_url, headers=headers, json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            enhanced_letter = result["choices"][0]["message"]["content"].strip()
                            logger.info("Together AIで感情表現の補完が完了")
                            return enhanced_letter
                        else:
                            error_text = await response.text()
                            raise Exception(f"Together AI API error {response.status}: {error_text}")
                
            except Exception as e:
                logger.warning(f"Together AI API 試行 {attempt + 1} 失敗: {str(e)}")
                if attempt == self.max_retries - 1:
                    logger.error("全てのTogether AI API試行が失敗")
                    raise Exception(f"Together AI API が {self.max_retries} 回の試行後に失敗: {str(e)}")
                
                # 指数バックオフ
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
    
    def _build_emotion_prompt(self, structure: str, context: Dict[str, Any]) -> str:
        """
        感情表現補完用のプロンプトを構築
        
        Args:
            structure: 論理構造
            context: ユーザーコンテキスト
            
        Returns:
            フォーマットされたプロンプト文字列
        """
        user_history = context.get("user_history", {})
        previous_letters = context.get("previous_letters", [])
        user_preferences = context.get("user_preferences", {})
        theme = context.get("theme", "")
        
        prompt = f"""以下の手紙の論理構造に、麻理らしい感情表現と個性を加えて完成させてください。

【論理構造】
{structure}

【麻理の性格設定】
- 温かく親しみやすい性格
- 時には少し内気で恥ずかしがり屋
- ユーザーを大切に思っている
- 季節や日常の小さな変化に敏感
- 自然で親しみやすい砕けた口調を時々使う
- 感情豊かで表現力がある

"""
        
        # 過去の手紙情報を追加
        if previous_letters:
            prompt += "【過去の手紙の情報】\n"
            for letter in previous_letters[-2:]:  # 直近2通
                prompt += f"- テーマ: {letter.get('theme', 'なし')}\n"
                if 'date' in letter:
                    prompt += f"  日付: {letter['date']}\n"
            prompt += "\n"
        
        # ユーザーの好みを追加
        if user_preferences:
            prompt += "【ユーザーの好み】\n"
            for key, value in user_preferences.items():
                prompt += f"- {key}: {value}\n"
            prompt += "\n"
        
        prompt += f"""【要求事項】
1. 論理構造を保ちながら、麻理らしい感情表現を追加
2. 自然で親しみやすい文体（敬語と親しみやすさのバランス）
3. 季節感や時間の流れを意識した表現
4. ユーザーとの関係性を大切にした個人的なメッセージ
5. 時々関西弁を混ぜた親しみやすい表現
6. 内気で恥ずかしがり屋な一面も表現
7. 1000-1500文字程度の長さ

現在のテーマ「{theme}」について、麻理の個性と感情を込めた手紙を完成させてください。
論理構造は維持しつつ、感情豊かで心温まる手紙にしてください。

完成した手紙のみを出力してください。説明や前置きは不要です。"""
        
        return prompt
    
    async def test_connection(self) -> bool:
        """
        Together AI APIへの接続をテスト
        
        Returns:
            接続成功時はTrue、失敗時はFalse
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": "こんにちは"}
                    ],
                    "max_tokens": 10
                }
                
                async with session.post(self.base_url, headers=headers, json=payload) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Together AI API接続テスト失敗: {str(e)}")
            return False
    
    async def generate_simple_response(self, prompt: str) -> str:
        """
        シンプルなレスポンス生成（テスト用）
        
        Args:
            prompt: 入力プロンプト
            
        Returns:
            生成されたレスポンス
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7
                }
                
                async with session.post(self.base_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"].strip()
                    else:
                        error_text = await response.text()
                        raise Exception(f"Together AI API error {response.status}: {error_text}")
        except Exception as e:
            logger.error(f"Together AI簡単レスポンス生成失敗: {str(e)}")
            raise