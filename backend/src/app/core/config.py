from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Interview Twin API"
    api_prefix: str = "/api"
    allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    interview_model: str = "placeholder"
    interview_mode: str = "text"
    ark_api_key: str = Field(default="", validation_alias=AliasChoices("ARK_API_KEY"))
    ark_base_url: str = Field(
        default="https://ark.cn-beijing.volces.com/api/v3",
        validation_alias=AliasChoices("ARK_BASE_URL"),
    )
    ark_endpoint_id: str = Field(default="", validation_alias=AliasChoices("ARK_ENDPOINT_ID"))
    kb_api_key: str = Field(default="", validation_alias=AliasChoices("KB_API_KEY", "VOLC_API_KEY"))
    kb_project_name: str = Field(default="default", validation_alias=AliasChoices("KB_PROJECT_NAME"))
    kb_collection_name: str = Field(default="dw_ai", validation_alias=AliasChoices("KB_COLLECTION_NAME"))
    kb_domain: str = Field(
        default="api-knowledgebase.mlp.cn-beijing.volces.com",
        validation_alias=AliasChoices("KB_DOMAIN"),
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
