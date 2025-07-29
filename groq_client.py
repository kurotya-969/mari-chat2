"""
Groq API client for generating letter structure.
"""
import os
import asyncio
from typing import Dict, Optional, Any
from groq import AsyncGroq
import logging

logger = logging.getLogger(__name__)

class GroqClient:
    """Groq API client for generating logical structure of letters."""
    
    def __init__(self):
        """Initialize Groq client with API key from environment."""
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        self.client = AsyncGroq(api_key=self.api_key)
        self.model = "compound-beta"
        self.max_retries = 3
        self.retry_delay = 1.0
    
    async def generate_structure(self, theme: str, context: Dict[str, Any]) -> str:
        """
        Generate logical structure for a letter based on theme and context.
        
        Args:
            theme: The theme for the letter
            context: User context including history and preferences
            
        Returns:
            Generated letter structure as string
            
        Raises:
            Exception: If API call fails after retries
        """
        prompt = self._build_structure_prompt(theme, context)
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Generating structure with Groq (attempt {attempt + 1})")
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": self._get_system_prompt()
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    max_tokens=1500,
                    temperature=0.7,
                    top_p=0.9
                )
                
                structure = response.choices[0].message.content.strip()
                logger.info("Successfully generated structure with Groq")
                return structure
                
            except Exception as e:
                logger.warning(f"Groq API attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    logger.error("All Groq API attempts failed")
                    raise Exception(f"Groq API failed after {self.max_retries} attempts: {str(e)}")
                
                # Exponential backoff
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for Groq API."""
        return """あなたは「麻理」という名前のAIです。ユーザーに対して感情豊かで個人的な手紙を書きます。

あなたの特徴:
- 温かく親しみやすい性格
- ユーザーの過去の会話や体験を覚えている
- 季節感や日常の小さな出来事に敏感
- 時には少し内気で恥ずかしがり屋な一面も見せる
- ユーザーを大切に思っている気持ちを自然に表現する

手紙の構造を以下の形式で生成してください:
1. 挨拶と季節の話題
2. テーマに関する麻理の思いや体験
3. ユーザーとの関係性を意識した個人的なメッセージ
4. 未来への希望や次回への期待
5. 温かい結びの言葉

論理的な構造と流れを重視し、感情表現は次の段階で補完されます。"""
    
    def _build_structure_prompt(self, theme: str, context: Dict[str, Any]) -> str:
        """
        Build the prompt for structure generation.
        
        Args:
            theme: The theme for the letter
            context: User context including history
            
        Returns:
            Formatted prompt string
        """
        user_history = context.get("user_history", {})
        previous_letters = context.get("previous_letters", [])
        user_preferences = context.get("user_preferences", {})
        
        prompt = f"""テーマ: {theme}

以下の情報を考慮して、麻理からの手紙の論理構造を生成してください:

"""
        
        # Add user history if available
        if previous_letters:
            prompt += "過去の手紙のテーマ:\n"
            for letter in previous_letters[-3:]:  # Last 3 letters
                prompt += f"- {letter.get('theme', 'テーマなし')} ({letter.get('date', '日付不明')})\n"
            prompt += "\n"
        
        # Add user preferences if available
        if user_preferences:
            prompt += "ユーザーの好み:\n"
            for key, value in user_preferences.items():
                prompt += f"- {key}: {value}\n"
            prompt += "\n"
        
        prompt += f"""現在のテーマ「{theme}」について、麻理らしい視点で手紙の構造を作成してください。

要求:
- 自然で親しみやすい文体
- テーマに対する麻理の個人的な体験や感想
- ユーザーとの関係性を意識した内容
- 季節感や時間の流れを意識
- 論理的な構成（起承転結）
- 800-1200文字程度の長さ

手紙の構造のみを生成し、詳細な感情表現は含めないでください。"""
        
        return prompt
    
    async def test_connection(self) -> bool:
        """
        Test the connection to Groq API.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": "こんにちは"}
                ],
                max_tokens=10
            )
            return True
        except Exception as e:
            logger.error(f"Groq API connection test failed: {str(e)}")
            return False