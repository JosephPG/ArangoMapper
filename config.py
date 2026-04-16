from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env"), env_file_encoding="utf-8")

    ARANGO_HOST: str = "http://localhost:8529"
    ARANGO_DB: str = "_system"
    ARANGO_USERNAME: str = ""
    ARANGO_PASSWORD: str = ""


settings = Settings()
