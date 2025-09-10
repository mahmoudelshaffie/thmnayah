from typing import List, Optional
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "CMS FastAPI"
    VERSION: str = "1.0.0"

    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    SERVER_NAME: str = os.getenv("SERVER_NAME", "localhost")
    SERVER_HOST: AnyHttpUrl = os.getenv("SERVER_HOST", "http://localhost:8000")

    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")

    # Email settings
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "True").lower() in ("true", "1", "t")
    SMTP_PORT: Optional[int] = os.getenv("SMTP_PORT", 587)
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST", "smtp.example.com")
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER", "smtp_user")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD", "smtp_password")
    EMAILS_FROM_EMAIL: Optional[str] = os.getenv("EMAILS_FROM_EMAIL", "EMAILS_FROM_EMAIL")
    EMAILS_FROM_NAME: Optional[str] = os.getenv("EMAILS_FROM_NAME", "CMS System")

    # File upload settings
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "gif", "pdf", "doc", "docx"]


settings = Settings()