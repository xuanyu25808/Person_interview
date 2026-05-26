from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Interview Twin API"
    api_prefix: str = "/api"
    allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    interview_model: str = "placeholder"
    interview_mode: str = "text"
    ark_api_key: str = ""
    ark_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    ark_endpoint_id: str = ""
    kb_api_key: str = ""
    kb_project_name: str = "default"
    kb_collection_name: str = "dw_ai"
    kb_domain: str = "api-knowledgebase.mlp.cn-beijing.volces.com"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
