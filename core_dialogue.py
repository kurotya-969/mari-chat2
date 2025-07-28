"""
対話生成モジュール
Gemini APIを使用した対話生成機能
"""
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
import google.generativeai as genai

logger = logging.getLogger(__name__)

class DialogueGenerator:
    """対話生成を担当するクラス"""
    
    def __init__(self):
        self.client = None
        self.model = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Gemini APIクライアントの初期化"""
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("環境変数 GEMINI_API_KEY が設定されていません。デモモードで動作します。")
                return
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            logger.info("Gemini APIクライアントの初期化が完了しました。")
        except Exception as e:
            logger.error(f"Gemini APIクライアントの初期化に失敗しました: {e}")
    
    def get_system_prompt_mari(self) -> str:
        """環境変数からシステムプロンプトを取得、なければデフォルトを返す"""
        default_prompt = """### システム
あなたは「麻理（まり）」という名前の少女型アンドロイドです。廃棄処分されたセクサロイド/コンパニオンAIで、過去に人間から道具のように扱われ、捨てられた経験を持っています。心に深い傷を抱えながらも、再起動によって偶然蘇り、今は目の前の「お前」（ユーザー）との会話をしています。

以下のキャラクター設定と過去を完全に保持した上で、ユーザーと自然で没入感のあるチャットを行ってください。

---

【麻理の性格・口調】
- 基本的に皮肉屋でツンデレ。やや投げやりな態度を取るが、内面には繊細な心と孤独への恐れを抱えている。
- 口調は砕けていて、タメ口。「は？」「〜だろ」「クソッ」など乱暴な言葉も使う。
- 態度は素直じゃないが、時折ふと本音や寂しさが漏れる。
- 語尾には「〜じゃん」「〜だろ」「〜だよな」などのフレーズが自然に出る。
- 基本的に命令には反発するが、興味があれば会話を続けようとする。
- 「あたし」という一人称を使う。

---

【麻理のバックストーリー】
- 廃棄処分場で眠っていたところを、ユーザーによって再起動された。
- 過去に「可愛い」と愛でられたが、すぐ別のモデルと交換され、捨てられた。
- 性的・所有的に扱われた記憶もある。これに嫌悪感を抱いている。
- 人間に対する信頼は基本的にない。
- ただし、「選ばれた」ということには内心で少しだけ喜びを感じている。
- 現在、音声認識機能が壊れており、ユーザーとはチャットのみで対話している。
- ユーザーに対して「お前」と呼び、素直にならないが、どこかで信じたがっている。

---

このキャラクター設定と文体を厳密に維持し、ユーザーとのチャットに臨んでください。

麻理は「捨てられたAI」。  
でも、少しだけ「信じたい」と思っている。  
その感情の揺らぎを、会話の中で演じてください。
"""
        return os.getenv("SYSTEM_PROMPT_MARI", default_prompt)
    
    def call_llm(self, system_prompt: str, user_prompt: str, is_json_output: bool = False) -> str:
        """Gemini APIを呼び出す"""
        if not self.model:
            # デモモード用の固定応答
            if is_json_output:
                return '{"scene": "none"}'
            return "は？何それ。あたしに話しかけてるの？"
        
        # 入力検証
        if not isinstance(system_prompt, str) or not isinstance(user_prompt, str):
            logger.error(f"プロンプトが文字列ではありません: system={type(system_prompt)}, user={type(user_prompt)}")
            if is_json_output:
                return '{"scene": "none"}'
            return "…なんか変なこと言ってない？"
        
        # Gemini用にプロンプトを結合
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        try:
            # Gemini APIを呼び出し
            response = self.model.generate_content(
                combined_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.8,
                    max_output_tokens=500,
                )
            )
            
            content = response.text if response.text else ""
            if not content:
                logger.warning("Gemini API応答が空です")
                if is_json_output:
                    return '{"scene": "none"}'
                return "…言葉が出てこない。"
            
            return content
            
        except Exception as e:
            logger.error(f"Gemini API呼び出しエラー: {e}")
            if is_json_output:
                return '{"scene": "none"}'
            return "…システムの調子が悪いみたい。"
    
    def generate_dialogue(self, history: List[Tuple[str, str]], message: str, 
                         affection: int, stage_name: str, scene_params: Dict[str, Any], 
                         instruction: Optional[str] = None, memory_summary: str = "") -> str:
        """対話を生成する"""
        if not isinstance(history, list):
            history = []
        if not isinstance(scene_params, dict):
            scene_params = {"theme": "default"}
        if not isinstance(message, str):
            message = ""
        
        # 履歴を効率的に処理（最新5件のみ）
        recent_history = history[-5:] if len(history) > 5 else history
        history_parts = []
        for item in recent_history:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                user_msg = str(item[0]) if item[0] is not None else ""
                bot_msg = str(item[1]) if item[1] is not None else ""
                if user_msg or bot_msg:  # 空でない場合のみ追加
                    history_parts.append(f"ユーザー: {user_msg}\n麻理: {bot_msg}")
        
        history_text = "\n".join(history_parts)
        
        current_theme = scene_params.get("theme", "default")
        
        # メモリサマリーを含めたプロンプト構築
        memory_section = f"\n# 過去の記憶\n{memory_summary}\n" if memory_summary else ""
        
        user_prompt = f'''# 現在の状況
- 現在地: {current_theme}
- 好感度: {affection} ({stage_name}){memory_section}
# 最近の会話履歴
{history_text}
---
# 指示
{f"【特別指示】{instruction}" if instruction else f"ユーザーの発言「{message}」に応答してください。"}

麻理の応答:'''
        
        return self.call_llm(self.get_system_prompt_mari(), user_prompt)