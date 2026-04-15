from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env"), env_file_encoding="utf-8")

    arango_host: str = "http://localhost:8529"
    arango_db: str = "_system"
    arango_username: str = ""
    arango_password: str = ""


settings = Settings()
