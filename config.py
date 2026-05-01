from pydantic_settings import BaseSettings, SettingsConfigDict

MIGRATE_MODELS: list[str] = ["app.collections", "example.models"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env"), env_file_encoding="utf-8")

    ARANGO_HOST: str = "http://localhost"
    ARANGO_PORT: str = "8529"
    ARANGO_DB: str = "_system"
    ARANGO_USERNAME: str = ""
    ARANGO_PASSWORD: str = ""


settings = Settings()
