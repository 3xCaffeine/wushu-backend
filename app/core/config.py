from pydantic_settings import BaseSettings, SettingsConfigDict
import os

DOTENV = os.path.join(os.path.abspath(os.path.dirname(__name__)), "..", ".env")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=DOTENV,
        env_file_encoding='utf-8',
        extra='ignore'
    )

    DATABASE_URI: str
    S3_BUCKET: str
    REGION: str = "ap-south-1"

settings = Settings()