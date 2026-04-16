from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_mode: str = "demo"
    database_url: str = "sqlite:///artifacts/cockpit.db"
    seed_demo_data: bool = True
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-5.4-mini"
    desktop_download_relative_path: str = "/downloads/cloud-migration-cockpit-judge-macos.zip"
    desktop_build_relative_path: str = "apps/web/public/downloads/cloud-migration-cockpit-judge-macos.zip"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_judge_mode(self) -> bool:
        return self.app_mode.lower() == "judge"

    @property
    def is_demo_mode(self) -> bool:
        return not self.is_judge_mode

    @property
    def should_seed_demo_data(self) -> bool:
        return self.seed_demo_data and self.is_demo_mode

    @property
    def default_organization_id(self) -> str:
        return "org-judge" if self.is_judge_mode else "org-demo"

    @property
    def default_workspace_id(self) -> str:
        return "workspace-judge" if self.is_judge_mode else "workspace-demo"

    @property
    def desktop_download_url(self) -> str:
        return self.desktop_download_relative_path

    @property
    def desktop_build_path(self) -> Path:
        return Path(__file__).resolve().parents[4] / self.desktop_build_relative_path


@lru_cache
def get_settings() -> Settings:
    return Settings()
