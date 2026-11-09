from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    database_url: str = 'sqlite:///./data/quoteclear.db'
    storage_dir: Path = Path('./data/uploads')
    allowed_origins: str = 'http://localhost:8080,http://localhost:5173'
    cookie_secure: bool = False
    session_days: int = 7
    allow_registration: bool = True
    max_upload_bytes: int = 10 * 1024 * 1024
    @property
    def origins(self) -> list[str]:
        return [v.strip().rstrip('/') for v in self.allowed_origins.split(',') if v.strip()]

@lru_cache
def settings() -> Settings:
    return Settings()
