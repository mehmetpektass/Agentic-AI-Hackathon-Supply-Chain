"""Tek yapılandırma noktası. Değerler ortam değişkenlerinden okunur."""
import os

DEFAULT_MODEL_ID = "global.anthropic.claude-sonnet-5"
DEFAULT_AS_OF_DATE = "2026-11-25"


def get_model_id() -> str:
    model_id = os.environ.get("MODEL_ID", DEFAULT_MODEL_ID)
    if not model_id.startswith("global."):
        raise ValueError("MODEL_ID 'global.' önekiyle başlamalı")
    return model_id


def get_mcp_backend() -> str:
    backend = os.environ.get("MCP_BACKEND", "stub")
    if backend not in ("stub", "fefo_mcp"):
        raise ValueError("MCP_BACKEND 'stub' veya 'fefo_mcp' olmalı")
    return backend


def get_reports_bucket() -> str | None:
    return os.environ.get("REPORTS_BUCKET") or None


def get_knowledge_base_id() -> str | None:
    return os.environ.get("KNOWLEDGE_BASE_ID") or None
