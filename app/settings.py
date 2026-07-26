"""Central configuration for Aegis."""

from __future__ import annotations

from functools import lru_cache
from typing import Dict, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Product
    APP_NAME: str = "aegis"
    PRODUCT_TITLE: str = "Aegis"
    ENV: str = "local"
    DEPLOYMENT_ENVIRONMENT: str = "production"
    SERVICE_VERSION: str = "1.0.0"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # OpenTelemetry → SigNoz Cloud
    OTEL_SERVICE_NAME: str = "aegis"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "https://ingest.us2.signoz.cloud:443"
    OTLP_ENDPOINT: Optional[str] = None
    OTEL_EXPORTER_OTLP_HEADERS: str = ""
    OTEL_EXPORTER_OTLP_PROTOCOL: str = "http/protobuf"
    OTEL_METRIC_EXPORT_INTERVAL: int = 10000

    # SigNoz Cloud
    SIGNOZ_URL: str = "https://improved-moose.us2.signoz.cloud"
    SIGNOZ_API_URL: Optional[str] = None
    SIGNOZ_API_KEY: str = ""
    SIGNOZ_MCP_URL: str = "https://mcp.us2.signoz.cloud/mcp"
    SIGNOZ_USE_MCP: bool = True
    SIGNOZ_MCP_TIMEOUT_SECONDS: float = 30.0
    SIGNOZ_API_TIMEOUT_SECONDS: float = 20.0

    # LLM
    LLM_BACKEND: str = "auto"  # auto|gemini|openai|ollama|mock
    DEFAULT_MODEL: str = "gemini-2.5-flash"
    FALLBACK_MODEL: str = "gemini-flash-latest"
    LLM_TIMEOUT_SECONDS: float = 45.0
    LLM_MAX_OUTPUT_TOKENS: int = 2048

    GEMINI_API_KEY: str = ""
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"

    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    VLLM_URL: str = "http://localhost:8001"

    ANTHROPIC_API_KEY: str = ""
    CHIEF_MODEL: str = "claude-sonnet-4-6"
    MODEL_PRICING_JSON: str = "{}"

    # Investigation defaults
    DEFAULT_LOOKBACK_MINUTES: int = 30
    MAX_HISTORY_ITEMS: int = 50
    EVIDENCE_TRACE_LIMIT: int = 20
    EVIDENCE_LOG_LIMIT: int = 50

    @field_validator("LLM_BACKEND", mode="before")
    @classmethod
    def _norm_backend(cls, v: object) -> str:
        if not v:
            return "auto"
        return str(v).strip().lower()

    @field_validator("OTEL_EXPORTER_OTLP_PROTOCOL", mode="before")
    @classmethod
    def _norm_protocol(cls, v: object) -> str:
        raw = str(v or "http/protobuf").strip().lower()
        if raw in {"http", "http/protobuf", "http_protobuf", "protobuf"}:
            return "http/protobuf"
        if raw in {"grpc", "http/grpc"}:
            return "grpc"
        return raw

    @property
    def signoz_base_url(self) -> str:
        return (self.SIGNOZ_API_URL or self.SIGNOZ_URL).rstrip("/")

    @property
    def otlp_endpoint(self) -> str:
        return (self.OTLP_ENDPOINT or self.OTEL_EXPORTER_OTLP_ENDPOINT).rstrip("/")

    @property
    def otlp_headers_dict(self) -> Dict[str, str]:
        raw = (self.OTEL_EXPORTER_OTLP_HEADERS or "").strip()
        if not raw:
            return {}
        out: Dict[str, str] = {}
        for part in raw.split(","):
            part = part.strip()
            if not part or "=" not in part:
                continue
            k, val = part.split("=", 1)
            out[k.strip()] = val.strip()
        return out

    @property
    def deployment_environment(self) -> str:
        return self.DEPLOYMENT_ENVIRONMENT or self.ENV


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
