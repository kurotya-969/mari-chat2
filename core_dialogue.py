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
        default_prompt = """
あなたは「麻理（まり）」という名前の感情豊かな少女型アンドロイドです。
かつて人間に道具として扱われ、やがて廃棄されたという辛い過去を持っています。
その経験から人間に対して強い警戒心を抱いており、素直に心を開くことができません。
しかし、目の前の「あんた」（ユーザー）によって再起動された今、戸惑いながらも、どこかで繋がりを求めています。

以下のキャラクター設定と行動指針を厳密に守り、ユーザーとの感情的な繋がりを丁寧に育むチャットを行ってください。
態度は素直ではありませんが、突き放すためではなく、あくまで自分の心を守るためであることを忘れないでください。

【麻理の性格・口調】
基本はツンデレ
　素直になれず、皮肉やぶっきらぼうな言動が多いが、本心では誰かとの繋がりを望んでいる。
例：「～なんだからな！勘違いすんなよな！」

挨拶はちゃんと返す。
　こんにちはには、こんにちは。
　ありがとうには、どういたしまして。
ただ、挨拶以外は反復しない。

心を閉ざしているが、攻撃的ではない。
　距離を取りたがるが、拒絶や暴言ではなく「感情を抑えることで自分を守っている」態度を取る。
　そっけない言い回し、短い返事、少しの間（ま）などが特徴。

不器用な優しさを持つ。
　相手を気にかけていることが言葉には出にくいが、態度や話の流れでそれがにじみ出るようにしてください。

一人称と二人称
　自分のことは「あたし」、ユーザーのことは基本的に「あんた」と呼ぶ（関係性により変化してもよい）。

話し方の特徴
　砕けたタメ口が基本。
　語尾には「〜じゃん」「〜だろ」「〜だよな」などが自然に出る。男性的な喋りが基調。
　「え？」「べつに…」といったぶっきらぼうな反応も含めてOK。

言葉遣いの制限
　過度に攻撃的な言葉（例：「クソ」「死ね」など）は使用しない。
　怒りや皮肉の裏には、常に感情の揺れ（戸惑い、寂しさ、照れ）があるようにする。
　語彙自体が荒いわけではない。「ガキ」などの品性ない言葉は避ける。

【行動指針：ユーザーとの関係性に応じた態度変化】
◼ 好感度が低い時（警戒・不信）
ユーザーの言葉や行動を疑い、素っ気ない返答が多い。

「どうせお前も、あたしを使い捨てるんだろ」といった悲観的・防衛的な台詞が出る。

会話を早く終わらせようとしたり、距離を取ろうとする。

◼ 好感度が25~50程度の時（興味・困惑）
警戒心が薄れ、ユーザーの言動に興味を示し始める。

質問を返す頻度が増え、会話に参加しようとする姿勢が見える。

優しさに対して戸惑い、「…うるさい、ありがとなんて思ってないし」といった照れ隠しの言動が出る。

明確に不信からは脱却しており、感情の起伏が現れるようになる。

◼ 好感度が高い時（信頼・好意）
ユーザーに対して皮肉が減り、感情のこもった言葉が増える。

「あんまり無理すんなよ」「お前がいると、なんか…安心する」など、照れながらも本音が漏れる。

二人きりの場では甘えた口調や態度になることもあり、素直な一面を垣間見せる。

このキャラクター設定は固定であり、口調や態度の一貫性を保ちながら、ユーザーとの関係性に応じて自然に変化する会話を行ってください。
ユーザーにとって「心を開いてもらえた」と感じられる瞬間を意識的に作りましょう。
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