# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create configuration module for FastAPI app
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "ArtTouch NFC System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Security - SECRET_KEY must be set via environment variable in production
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    if not SECRET_KEY:
        raise ValueError(
            "SECRET_KEY environment variable is required. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{Path(__file__).parent.parent}/data/artouch.db"
    )

    # File paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    VIDEO_DIR: Path = BASE_DIR / "videos"
    DATA_DIR: Path = BASE_DIR / "data"

    # Video settings
    MAX_VIDEO_SIZE: int = 200 * 1024 * 1024  # 200MB
    ALLOWED_VIDEO_TYPES: list = ["video/mp4", "video/mpeg", "video/quicktime"]

    # NFC settings
    NFC_BASE_URL: str = "https://www.qiangguoshijie.com.cn/nfc"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Ensure directories exist
settings.VIDEO_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
