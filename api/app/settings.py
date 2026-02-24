# api/app/settings.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Groq inference
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.3-70b-versatile"
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
