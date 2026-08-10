"""Environment-driven application settings (TRD §10)."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_ROOT.parent

# Resolved from this file's location, not the process working directory, so
# the same `.env` is found whether the backend is started from the project
# root or from `backend/` (the README's documented command).
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    # LLM (not required to be functional until Batch 2)
    llm_provider: str = "openai"
    llm_model: str = ""
    llm_api_key: str = ""

    # Database (default/sample dataset)
    database_url: str = "sqlite:///./data/ecommerce.db"

    # Database uploads
    database_upload_dir: str = "./data/uploads"
    database_upload_max_mb: int = 50

    # Query execution guards (04_AGENT_TOOLS.md Tool 2 §5/§8)
    hard_row_ceiling: int = 1000
    default_max_rows: int = 200
    query_timeout_seconds: int = 15

    # Backend
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_allowed_origins: str = "http://localhost:5173"

    # Frontend (unused by the backend itself, kept for parity with .env.example)
    vite_api_base_url: str = "http://localhost:8000"

    @property
    def default_database_path(self) -> Path:
        # DATABASE_URL is always a sqlite:/// URL for the default/sample dataset.
        raw_path = self.database_url.split("sqlite:///", 1)[-1]
        path = Path(raw_path)
        if not path.is_absolute():
            path = (BACKEND_ROOT / path).resolve()
        return path

    @property
    def upload_dir_path(self) -> Path:
        path = Path(self.database_upload_dir)
        if not path.is_absolute():
            path = (BACKEND_ROOT / path).resolve()
        return path

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


settings = Settings()
