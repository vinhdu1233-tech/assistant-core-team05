"""Read and validate assistant configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

from assistant_core.errors import ConfigError


class Settings(BaseModel):
    data_dir: Path = Path("data")
    llm_provider: str = "stub"
    llm_api_key: str | None = Field(default=None, repr=False)
    credit_rate_vnd: int = Field(default=450_000, gt=0)
    retake_multiplier: float = Field(default=1.5, gt=0)
    max_credits: int = Field(default=30, gt=0)
    log_level: str = "INFO"
    api_admin_key: str | None = Field(default=None, repr=False)
    weather_url: str = "https://api.open-meteo.com/v1/forecast"
    weather_timeout_s: float = Field(default=3.0, gt=0)
    campus_lat: float = 10.7626
    campus_lon: float = 106.6822
    rate_limit_per_min: int = Field(default=30, gt=0)


def load_settings(env_file: str | None = ".env") -> Settings:
    """Load environment settings without exposing credentials."""
    if env_file is not None:
        load_dotenv(env_file, override=False)

    try:
        settings = Settings(
            data_dir=Path(os.getenv("ASSISTANT_DATA_DIR", "data")),
            llm_provider=os.getenv("LLM_PROVIDER", "stub"),
            llm_api_key=os.getenv("LLM_API_KEY") or None,
            credit_rate_vnd=int(os.getenv("CREDIT_RATE_VND", "450000")),
            retake_multiplier=float(os.getenv("RETAKE_MULTIPLIER", "1.5")),
            max_credits=int(os.getenv("MAX_CREDITS", "30")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            api_admin_key=os.getenv("API_ADMIN_KEY") or None,
            weather_url=os.getenv("WEATHER_URL", "https://api.open-meteo.com/v1/forecast"),
            weather_timeout_s=float(os.getenv("WEATHER_TIMEOUT_S", "3")),
            campus_lat=float(os.getenv("CAMPUS_LAT", "10.7626")),
            campus_lon=float(os.getenv("CAMPUS_LON", "106.6822")),
            rate_limit_per_min=int(os.getenv("RATE_LIMIT_PER_MIN", "30")),
        )
    except (ValueError, ValidationError):
        raise ConfigError("Invalid environment configuration") from None

    if settings.llm_provider != "stub" and not settings.llm_api_key:
        raise ConfigError("LLM_API_KEY is required for a non-stub provider")

    return settings
