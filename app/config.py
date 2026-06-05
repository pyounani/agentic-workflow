from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "agentic_workflow"
    APP_ENV: str = "development"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    AI_SERVER_URL: str = "http://localhost:8001"


settings = Settings()
