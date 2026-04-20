from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings"""

    # Phase 1: OpenAI API settings
    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"
    openai_timeout: float = 60.0  # seconds
    max_file_size_bytes: int = 10 * 1024 * 1024  # 10MB
    allowed_content_types: tuple[str, ...] = (
        "image/jpeg",
        "image/png",
        "image/webp",
    )

    # Phase 2: Ollama settings
    ollama_base_url: str = ""
    ollama_ocr_model: str = ""  # Recommended: Qwen3.6-35B-A3B
    ollama_summary_model: str = ""  # Recommended: Qwen3.6-35B-A3B
    ollama_timeout_seconds: float = 60.0

    # Phase 2: NDLOCR-Lite settings
    ndlocr_lite_path: str = ""
    ndlocr_timeout_seconds: float = 60.0
    ndlocr_temp_dir: str = ""  # OS default temp if empty

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
