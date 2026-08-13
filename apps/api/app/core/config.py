"""Application settings loaded from environment."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "test", "staging", "production"] = "development"
    app_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/enterprise_ai"
    )

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "enterprise_ai_chunks"

    upstash_redis_rest_url: str = ""
    upstash_redis_rest_token: str = ""

    r2_endpoint: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = "enterprise-ai-docs"
    object_storage_backend: Literal["filesystem", "r2", "s3", "firebase"] = "filesystem"
    object_storage_path: str = "./data/storage"
    firebase_storage_bucket: str = ""
    firebase_storage_root: str = "resolve-ai"
    firebase_credentials_path: str = ""
    firebase_credentials_json: str = ""

    oidc_issuer: str = "https://example.auth0.com/"
    oidc_audience: str = "https://api.enterprise-ai-support.local"
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    dev_auth_enabled: bool = True
    dev_auth_secret: str = "dev-only-change-me-in-local"
    allow_dev_auth_in_production: bool = False
    registration_enabled: bool = True
    embedded_mocks_enabled: bool = False
    run_migrations_on_startup: bool = True

    llm_primary_provider: str = "groq"
    llm_primary_model: str = "openai/gpt-oss-20b"
    groq_api_key: str = ""

    llm_fallback_provider: str = "gemini"
    llm_fallback_model: str = ""
    gemini_api_key: str = ""

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    internal_job_secret: str = "change-me-job-secret"
    internal_job_hmac_key: str = "change-me-hmac-key-32bytes-min!!"

    max_anonymous_messages_per_day: int = 5
    max_authenticated_messages_per_day: int = 20
    max_global_model_calls_per_day: int = 700
    max_model_calls_per_turn: int = 4
    max_graph_steps: int = 8
    max_output_tokens: int = 600

    crm_base_url: str = "http://localhost:8101"
    erp_base_url: str = "http://localhost:8102"
    carrier_base_url: str = "http://localhost:8103"
    ticketing_base_url: str = "http://localhost:8104"
    mock_service_token: str = "mock-service-dev-token"

    sentry_dsn: str = ""
    git_sha: str = "local"
    graph_version: str = "v1"
    cors_origins: str = "http://localhost:3000"

    brevo_api_key: str = ""
    brevo_sender_email: str = ""
    brevo_sender_name: str = "ResolveAI"
    email_enabled: bool = True
    email_fallback_recipient: str = ""

    @field_validator("firebase_credentials_path")
    @classmethod
    def resolve_firebase_credentials_path(cls, value: str) -> str:
        if not value:
            return value
        path = Path(value).expanduser()
        if path.is_file():
            return str(path.resolve())
        repo_root = Path(__file__).resolve().parents[4]
        candidate = repo_root / value
        if candidate.is_file():
            return str(candidate.resolve())
        return value

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("sqlite"):
            return value
        if value.startswith("postgresql://"):
            value = value.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif value.startswith("postgres://"):
            value = value.replace("postgres://", "postgresql+asyncpg://", 1)

        # Strip libpq-only params; SSL is applied via connect_args in session/alembic.
        if "://" in value:
            from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

            parsed = urlparse(value)
            query = dict(parse_qsl(parsed.query, keep_blank_values=True))
            for key in ("sslmode", "ssl", "channel_binding"):
                query.pop(key, None)
            value = urlunparse(parsed._replace(query=urlencode(query)))
        return value

    @property
    def database_requires_ssl(self) -> bool:
        host = ""
        try:
            from urllib.parse import urlparse

            host = urlparse(self.database_url).hostname or ""
        except Exception:  # noqa: BLE001
            host = ""
        return "neon.tech" in host or self.app_env == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def validate_runtime(self) -> None:
        if (
            self.is_production
            and self.dev_auth_enabled
            and not self.allow_dev_auth_in_production
        ):
            raise ValueError(
                "DEV_AUTH_ENABLED must be false in production unless "
                "ALLOW_DEV_AUTH_IN_PRODUCTION=true"
            )
        if self.is_production and self.dev_auth_secret.startswith("dev-only"):
            if not self.dev_auth_enabled:
                pass
            elif not self.allow_dev_auth_in_production:
                raise ValueError("DEV_AUTH_SECRET must be rotated in production")
        if len(self.internal_job_hmac_key) < 16:
            raise ValueError("INTERNAL_JOB_HMAC_KEY must be at least 16 characters")

    def service_base_urls(self) -> dict[str, str]:
        """Resolve integration URLs; embedded mocks run inside this API on cloud."""
        if not self.embedded_mocks_enabled:
            return {
                "crm": self.crm_base_url.rstrip("/"),
                "erp": self.erp_base_url.rstrip("/"),
                "carrier": self.carrier_base_url.rstrip("/"),
                "ticketing": self.ticketing_base_url.rstrip("/"),
            }
        base = self.api_url.rstrip("/")
        return {
            "crm": f"{base}/mocks/crm",
            "erp": f"{base}/mocks/erp",
            "carrier": f"{base}/mocks/carrier",
            "ticketing": f"{base}/mocks/ticketing",
        }


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_runtime()
    return settings
