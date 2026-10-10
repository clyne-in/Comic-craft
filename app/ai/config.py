from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "ComicCraft"
    app_env: str = "development"

    # mock = no API calls
    # live = Gemini + Hugging Face
    app_mode: str = "live"

    # API keys
    gemini_api_key: str = "AQ.Ab8RN6J4JhLLk9__IiX7Ot9zeHL2FSQfHVYCBKcqdldK4SE9FA"
    hf_token: str = "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"

    # Gemini models
    gemini_outline_model: str = "gemini-2.5-flash"
    gemini_story_model: str = "gemini-2.5-pro"

    # Hugging Face image model
    hf_image_model: str = (
        "stabilityai/stable-diffusion-3-medium-diffusers"
    )

    hf_provider: str = "hf-inference"

    # Image settings
    image_width: int = 768
    image_height: int = 512
    image_steps: int = 28
    image_guidance: float = 7.0

    max_prompt_length: int = 2000

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()