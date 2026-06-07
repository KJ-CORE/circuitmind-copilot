import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "CircuitMind API"
    environment: str = "development"

    database_url: str = "postgresql://postgres:postgres@localhost:5432/circuitmind"

    qdrant_host: str = ":memory:"
    qdrant_port: int = 6333
    qdrant_api_key: Optional[str] = None
    qdrant_collection_name: str = "datasheets"

    openai_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "nvidia/nemotron-3-nano-30b-a3b"

    jwt_secret: str = "circuitmind_super_secret_key_change_me_in_production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
