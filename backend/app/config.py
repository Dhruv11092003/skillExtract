from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SkillExtract Integrity API"
    app_version: str = "2.0.0"
    cors_origins: str = "*"
    semantic_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    default_required_skills: str = "Python,FastAPI,React,SQL,Django"
    context_window_size: int = 50

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
