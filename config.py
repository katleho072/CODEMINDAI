# backend/app/core/config.py
from typing import Optional
from pydantic_settings import BaseSettings  # Changed from pydantic.v1
import os
from pathlib import Path

# Get base directory
BASE_DIR = Path(__file__).parent.parent.parent  # Points to backend/

class Settings(BaseSettings):
    # API Configuration
    PROJECT_NAME: str = "DevMate AI"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # DeepSeek Configuration - make optional for development
    DEEPSEEK_API_KEY: Optional[str] = None  # Fixed syntax
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-coder"

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 30

    # File limits
    MAX_FILE_SIZE_MB: int = 10
    MAX_TOTAL_FILES: int = 50
    ALLOWED_EXTENSIONS: list = [".py", ".js", ".ts", ".java", ".cpp", ".go", ".rs", ".rb", ".kt"]

    # Context
    MAX_CONTEXT_TOKENS: int = 4000
    ENABLE_VECTOR_STORE: bool = True

    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/devmate.db"

    # Development
    DEBUG: bool = True

    class Config:
        env_file = BASE_DIR / ".env"  # Points to backend/.env
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create the settings instance
settings = Settings()

# Optional: Print debug info
if __name__ == "__main__":
    print(f"🔧 Settings loaded:")
    print(f"   Project: {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"   API Key: {'Set' if settings.DEEPSEEK_API_KEY else 'NOT SET'}")
    print(f"   Database: {settings.DATABASE_URL}")
    print(f"   Env file: {BASE_DIR / '.env'}")
