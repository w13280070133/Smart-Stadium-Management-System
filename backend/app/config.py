from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Gym Management System V2"
    SECRET_KEY: str = "CHANGE_THIS_TO_RANDOM_SECRET"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 天

    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "123456"  # 这里改成你真实的 MySQL 密码
    DB_NAME: str = "gym_v2"

    class Config:
        env_file = ".env"


settings = Settings()
