from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file.

    NOTE: pydantic-settings automatically maps an environment variable to a
    field when the variable name matches the field name (case-insensitive
    by default), so no extra `env=` kwarg is required on `Field()`. The old
    `Field(..., env="X")` syntax is a pydantic v1 pattern that pydantic v2
    silently deprecates -- it was removed here to eliminate startup warnings.
    """

    APP_NAME: str = Field(default='AI Healthcare Care Coordinator')
    APP_HOST: str = Field(default='0.0.0.0')
    APP_PORT: int = Field(default=8000)

    SECRET_KEY: str = Field(default='dev-secret-key-change-me')
    ALGORITHM: str = Field(default='HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)

    DATABASE_URL: str = Field(default='sqlite:///./healthcare_ai.db')

    GOOGLE_APPLICATION_CREDENTIALS: str | None = Field(default=None)
    GOOGLE_API_KEY: str | None = Field(default=None)
    GEMINI_MODEL_NAME: str = Field(default='gemini-3.5-flash')

    EMAIL_SMTP_SERVER: str | None = Field(default=None)
    EMAIL_SMTP_PORT: int | None = Field(default=None)
    EMAIL_USERNAME: str | None = Field(default=None)
    EMAIL_PASSWORD: str | None = Field(default=None)

    # Base URL the frontend (Streamlit) uses to reach the FastAPI backend.
    API_BASE_URL: str = Field(default='https://ai-healthcare-backend-r99g.onrender.com')

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / '.env'),
        env_file_encoding='utf-8',
        extra='ignore',
    )


settings = Settings()
