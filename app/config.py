"""
配置中心模块

统一管理所有配置项，从环境变量读取。
其他模块通过 `from app.config import config` 导入使用。
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    配置类，所有配置项作为类属性
    """
    # llm config
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "")

    # Redis Config
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    MAX_HISTORY_ROUNDS: int = int(os.getenv("MAX_HISTORY_ROUNDS", "10"))

    # Application Config
    APP_NAME: str = "AutoBizMind-Agent"
    APP_VERSION: str = "0.1.0"

    # 验证必填项
    @classmethod
    def validate(cls) -> None:
        if not cls.OPENAI_API_KEY:
            raise ValueError(
                "Not Found OPENAI_API_KEY!\n"
                "需在.env 文件中配置：\n"
            )

config = Config()

# 启动时自动验证
config.validate()