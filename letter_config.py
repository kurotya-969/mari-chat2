"""
設定管理モジュール
Configuration management module
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

class Config:
    """アプリケーション設定クラス"""
    
    # API設定
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    
    # デバッグモード
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    
    # バッチ処理設定
    BATCH_SCHEDULE_HOURS: list = [
        int(h.strip()) for h in os.getenv("BATCH_SCHEDULE_HOURS", "2,3,4").split(",")
    ]
    
    # レート制限設定
    MAX_DAILY_REQUESTS: int = int(os.getenv("MAX_DAILY_REQUESTS", "1"))
    
    # ストレージ設定（Hugging Face Spaces用パス）
    STORAGE_PATH: str = os.getenv("STORAGE_PATH", "/tmp/letters.json")
    BACKUP_PATH: str = os.getenv("BACKUP_PATH", "/tmp/backup")
    
    # ログ設定
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Streamlit設定（Spaces用ポート）
    STREAMLIT_PORT: int = int(os.getenv("STREAMLIT_PORT", "7860"))
    
    # セキュリティ設定
    SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1時間
    
    # 非同期手紙生成設定
    ASYNC_LETTER_ENABLED: bool = os.getenv("ASYNC_LETTER_ENABLED", "true").lower() == "true"
    GENERATION_TIMEOUT: int = int(os.getenv("GENERATION_TIMEOUT", "300"))  # 5分
    MAX_CONCURRENT_GENERATIONS: int = int(os.getenv("MAX_CONCURRENT_GENERATIONS", "3"))
    
    # AI モデル設定
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-pro")
    
    # テーマ設定
    AVAILABLE_THEMES: list = [
        "春の思い出", "夏の夜空", "秋の風景", "冬の静寂",
        "友情", "家族", "恋愛", "仕事", "趣味", "旅行"
    ]
    
    @classmethod
    def validate_config(cls) -> bool:
        """設定の妥当性をチェック"""
        errors = []
        
        if not cls.GROQ_API_KEY:
            errors.append("GROQ_API_KEY is required")
        
        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is required")
        
        if not all(h in [2, 3, 4] for h in cls.BATCH_SCHEDULE_HOURS):
            errors.append("BATCH_SCHEDULE_HOURS must contain only 2, 3, or 4")
        
        if cls.MAX_CONCURRENT_GENERATIONS < 1:
            errors.append("MAX_CONCURRENT_GENERATIONS must be at least 1")
        
        if cls.GENERATION_TIMEOUT < 60:
            errors.append("GENERATION_TIMEOUT must be at least 60 seconds")
        
        if errors:
            for error in errors:
                logging.error(f"Configuration error: {error}")
            return False
        
        return True
    
    @classmethod
    def get_log_level(cls) -> int:
        """ログレベルを取得"""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return level_map.get(cls.LOG_LEVEL.upper(), logging.INFO)