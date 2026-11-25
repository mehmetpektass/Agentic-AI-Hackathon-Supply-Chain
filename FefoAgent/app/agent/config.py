"""Tek yapılandırma noktası. Değerler ortam değişkenlerinden okunur."""
import json
import logging
import os
from pathlib import Path

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


# --- Max_Discount_Pct_By_Role: tek varsayılan noktası -------------------------------------
# Kaynak: app/agent/data/params.json -> "max_discount_pct_by_role". Dosya veya alan yoksa
# aşağıdaki varsayılan kullanılır. depo rolü için indirimli aksiyon tanımlı değildir.
DEFAULT_MAX_DISCOUNT_PCT_BY_ROLE: dict[str, dict[str, float]] = {
    "ticari": {"DEALER_OFFER": 20, "CAMPAIGN": 25},
}
PARAMS_PATH = Path(__file__).resolve().parent / "data" / "params.json"


def load_max_discount_pct_by_role(path: Path | None = None) -> dict[str, dict[str, float]]:
    path = path or PARAMS_PATH
    try:
        if not path.is_file():
            return DEFAULT_MAX_DISCOUNT_PCT_BY_ROLE
        value = json.loads(path.read_text(encoding="utf-8")).get("max_discount_pct_by_role")
        return value if isinstance(value, dict) else DEFAULT_MAX_DISCOUNT_PCT_BY_ROLE
    except (OSError, ValueError) as exc:
        logging.getLogger("fefo_agent.config").warning(
            "params.json okunamadı, varsayılan kullanılıyor: %s", type(exc).__name__)
        return DEFAULT_MAX_DISCOUNT_PCT_BY_ROLE


def get_region() -> str:
    return os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
