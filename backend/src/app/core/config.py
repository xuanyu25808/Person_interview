from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Interview Twin API"
    api_prefix: str = "/api"
    allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    interview_model: str = "placeholder"
    interview_mode: str = "text"
    volcengine_app_id: str = ""
    volcengine_access_key: str = ""
    volcengine_secret_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
