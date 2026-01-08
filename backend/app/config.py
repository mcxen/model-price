from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    data_dir: Path = Path(__file__).parent.parent.parent.parent / "data"
    host: str = "0.0.0.0"
    port: int = 3001
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_prefix="APP_")


settings = Settings()
