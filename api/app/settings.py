# api/app/settings.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Inference service
    inference_base_url: str = "http://localhost:8080"
    inference_model: str = "local-model"
    inference_timeout_seconds: int = 30

    # Application
    log_level: str = "INFO"
    debug: bool = False

    # n8n workflow automation
    n8n_webhook_url: str = ""
    n8n_enabled: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
