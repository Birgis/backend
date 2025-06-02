from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_name: str = "Flutter Multi-Platform API"
    debug: bool = True
    database_url: str = "sqlite:///./sql_app.db"
    allowed_origins: List[str] = ["*"]
    max_upload_size: int = 10 * 1024 * 1024
    supported_platforms: List[str] = ["web", "mobile", "desktop"]
    upload_dir: str = "uploads"

    class Config:
        env_file = ".env"


settings = Settings()
