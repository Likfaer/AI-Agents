"""
Application configuration via environment variables.
Uses pydantic-settings for validation and .env support.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LM Studio
    LM_STUDIO_BASE_URL: str = "http://localhost:1234/v1"
    LM_STUDIO_API_KEY: str = "lm-studio"
    LM_STUDIO_TIMEOUT: float = 120.0
    DEFAULT_MODEL: str = "local-model"
    MAX_RETRIES: int = 3

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Memory
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    MEMORY_DIR: str = "./data/memory"

    # Tools
    WORKSPACE_DIR: str = "./workspace"
    ALLOWED_COMMANDS: list[str] = [
        "python", "pip", "npm", "node", "git", "ls", "cat",
        "echo", "mkdir", "touch", "cp", "mv", "find", "grep",
        "curl", "docker", "uvicorn", "pytest",
    ]
    COMMAND_TIMEOUT: int = 30
    MAX_FILE_SIZE_MB: int = 10

    # Web Search
    SEARCH_MAX_RESULTS: int = 5
    SEARCH_TIMEOUT: int = 10

    # VSCode
    VSCODE_EXECUTABLE: str = "code"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/platform.log"

    # Security
    SECRET_KEY: str = Field(default="change-me-in-production-please")
    ENABLE_SANDBOX: bool = True


settings = Settings()
