
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    tavily_api_key: str = ""
    chroma_path: str = "data/chroma"
    collection_name: str = "research_documents"

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def chroma_directory(self) -> str:
        path = Path(self.chroma_path)

        if not path.is_absolute():
            path = PROJECT_ROOT / path

        return str(path)


settings = Settings()
