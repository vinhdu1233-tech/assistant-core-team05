"""Read and validate assistant configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, model_validator

from assistant_core.errors import ConfigError
from assistant_core.rag.index import DEFAULT_MIN_SCORES


class Settings(BaseModel):
    data_dir: Path = Path("data")
    llm_provider: str = "stub"
    llm_api_key: str | None = Field(default=None, repr=False)
    llm_timeout_s: float = Field(default=5.0, gt=0)
    llm_model: str = "llama3.2"
    llm_base_url: str | None = None
    kb_dir: Path = Path("data/kb")
    retrieval_kind: str = "bm25"
    retrieval_min_score: float = Field(default=2.0, ge=0, allow_inf_nan=False)
    prompt_version: str = "answer_v1"
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
    database_url: str = "sqlite:///assistant.db"
    session_salt: str = Field(default="dev-salt", repr=False)


    @model_validator(mode="before")
    @classmethod
    def choose_retrieval_min_score(cls, data):
        if isinstance(data, dict) and "retrieval_min_score" not in data:
            kind = data.get("retrieval_kind", "bm25")
            if isinstance(kind, str) and kind in DEFAULT_MIN_SCORES:
                return {**data, "retrieval_min_score": DEFAULT_MIN_SCORES[kind]}
        return data

    @model_validator(mode="after")
    def validate_retrieval_scale(self):
        if self.retrieval_kind in {"tfidf", "hybrid"} and self.retrieval_min_score > 1.0:
            raise ValueError("TF-IDF and hybrid retrieval thresholds must be between 0 and 1")
        return self


def load_settings(env_file: str | None = ".env") -> Settings:
    """Load environment settings without exposing credentials."""
    if env_file is not None:
        load_dotenv(env_file, override=False)

    try:
        threshold = os.getenv("RETRIEVAL_MIN_SCORE", "").strip()
        overrides = {"retrieval_min_score": float(threshold)} if threshold else {}
        settings = Settings(
            data_dir=Path(os.getenv("ASSISTANT_DATA_DIR", "data")),
            llm_provider=os.getenv("LLM_PROVIDER", "stub"),
            llm_api_key=os.getenv("LLM_API_KEY") or None,
            llm_timeout_s=float(os.getenv("LLM_TIMEOUT_S", "5")),
            llm_model=os.getenv("LLM_MODEL", "llama3.2"),
            llm_base_url=os.getenv("LLM_BASE_URL") or None,
            kb_dir=Path(os.getenv("KB_DIR", "data/kb")),
            retrieval_kind=os.getenv("RETRIEVAL_KIND", "bm25"),
            **overrides,
            prompt_version=os.getenv("PROMPT_VERSION", "answer_v1"),
            credit_rate_vnd=int(os.getenv("CREDIT_RATE_VND", "450000")),
            retake_multiplier=float(os.getenv("RETAKE_MULTIPLIER", "1.5")),
            max_credits=int(os.getenv("MAX_CREDITS", "30")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            api_admin_key=os.getenv("API_ADMIN_KEY") or None,
            weather_url=os.getenv(
                "WEATHER_URL",
                "https://api.open-meteo.com/v1/forecast",
            ),
            weather_timeout_s=float(os.getenv("WEATHER_TIMEOUT_S", "3")),
            campus_lat=float(os.getenv("CAMPUS_LAT", "10.7626")),
            campus_lon=float(os.getenv("CAMPUS_LON", "106.6822")),
            rate_limit_per_min=int(os.getenv("RATE_LIMIT_PER_MIN", "30")),
            database_url=os.getenv("DATABASE_URL", "sqlite:///assistant.db"),
            session_salt=os.getenv("SESSION_SALT", "dev-salt"),
        )
    except (ValueError, ValidationError):
        raise ConfigError("Invalid environment configuration") from None

    # Preserve the legacy "remote" configuration accepted by Lab 05 tests.
    # The application does not instantiate a remote adapter without an explicit provider.
    if settings.llm_provider not in {"stub", "template", "ollama", "openai", "remote"}:
        raise ConfigError("Unsupported LLM provider")
    if settings.llm_provider in {"openai", "remote"} and not settings.llm_api_key:
        raise ConfigError("LLM_API_KEY is required for the remote/openai provider")
    if settings.retrieval_kind not in {"bm25", "tfidf", "hybrid"}:
        raise ConfigError("Invalid retrieval index kind")

    return settings
