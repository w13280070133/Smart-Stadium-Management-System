import os
import warnings
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Gym Management System V2"
    SECRET_KEY: str = ""  # 必须在 .env 中配置
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 天

    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""  # 必须在 .env 中配置
    DB_NAME: str = "gym_v2"
    
    # 数据库连接池配置
    DB_POOL_SIZE: int = 10
    DB_POOL_NAME: str = "gym_pool"
    
    # AI Agent 配置
    DEEPSEEK_API_KEY: str = ""  # DeepSeek API Key

    class Config:
        env_file = ".env"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 安全检查：生产环境必须配置 SECRET_KEY
        if not self.SECRET_KEY or self.SECRET_KEY == "CHANGE_THIS_TO_RANDOM_SECRET":
            # 开发环境允许使用默认值，但会发出警告
            if os.getenv("ENV", "development") == "production":
                raise ValueError(
                    "SECRET_KEY 未配置或使用了不安全的默认值！"
                    "请在 .env 文件中设置一个强随机密钥。"
                )
            else:
                warnings.warn(
                    "SECRET_KEY 未配置，使用开发环境默认值。生产环境请务必配置！",
                    UserWarning
                )
                self.SECRET_KEY = "DEV_SECRET_KEY_DO_NOT_USE_IN_PRODUCTION"
        
        # 数据库密码检查
        if not self.DB_PASSWORD:
            if os.getenv("ENV", "development") == "production":
                raise ValueError("DB_PASSWORD 未配置！请在 .env 文件中设置数据库密码。")
            else:
                warnings.warn(
                    "DB_PASSWORD 未配置，使用开发环境默认值 '123456'。",
                    UserWarning
                )
                self.DB_PASSWORD = "123456"


settings = Settings()
