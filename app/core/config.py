from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

DOTENV = os.path.join(os.path.abspath(os.path.dirname(__name__)), "..", ".env")

load_dotenv(DOTENV)

class Settings(BaseSettings):
    DATABASE_URI: str = os.getenv("DATABASE_URI")
    S3_BUCKET: str = os.getenv("S3_BUCKET")
    REGION: str = os.getenv("REGION", "ap-south-1")
    
settings = Settings()