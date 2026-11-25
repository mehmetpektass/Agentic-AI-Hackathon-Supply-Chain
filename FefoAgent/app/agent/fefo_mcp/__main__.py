"""FEFO MCP stdio sunucusu (fefo_core üzerinde). stdout yalnızca MCP protokolüne aittir; loglar stderr'e gider."""
import logging
import sys
from typing import Literal

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger("fefo_mcp")

try:
    from . import tools  # import anında _SNAPSHOT bir kez kurulur
except Exception as exc:  # doğrulama/yükleme hatası: stderr'e logla, mcp.run() öncesi çık
    issues = getattr(exc, "issues", None)
    if issues:
        for i in issues:
            logger.error("veri doğrulama hatası: %s satır %s kural %s", i.file, i.row, i.rule)
    else:
        logger.error("başlangıç yüklemesi başarısız: %s: %s", type(exc).__name__, exc)
    sys.exit(1)

mcp = FastMCP("fefo_mcp")


class ActionSpec(BaseModel):
    """Bir aksiyon: type ve params. discount_pct yalnızca DEALER_OFFER ve CAMPAIGN için gerekir."""
    type: Literal["FEFO_PRIORITY", "DEALER_OFFER", "CAMPAIGN", "DONATION", "SUPPLIER_RETURN"]
    params: dict = Field(default_factory=dict, description=(
        "FEFO_PRIORITY: {}. DEALER_OFFER: {dealer_ids?, discount_pct}. CAMPAIGN: {discount_pct}. "
        "DONATION: {units?}. SUPPLIER_RETURN: {units?}"))


@mcp.tool()
def get_expiry_risks(as_of_date: str | None = None, category: Literal["COLD", "DRY"] | None = None,
                     min_loss_try: float = 0, top_n: int = 10) -> dict:
    """SKT riski taşıyan lotları beklenen ₺ kaybına göre azalan sırada listeler."""
    return tools.get_expiry_risks(as_of_date, category, min_loss_try, top_n)


@mcp.tool()
def get_sku_profile(sku_id: str, as_of_date: str | None = None) -> dict:
    """Bir ürünün satış hızı, lotları ve bayi bilgilerini getirir."""
    return tools.get_sku_profile(sku_id, as_of_date)


@mcp.tool()
def simulate_actions(lot_id: str, actions: list[ActionSpec], as_of_date: str | None = None) -> dict:
    """Bir lot için aksiyonları verilen sırayla uygulayıp kayıp şelalesini hesaplar."""
    return tools.simulate_actions(lot_id, [a.model_dump() for a in actions], as_of_date)


@mcp.tool()
def create_action_drafts(lot_id: str, approved_actions: list[ActionSpec],
                         approver_actor_id: str) -> dict:
    """Onaylanan aksiyonlar için TASLAK mesajlar hazırlar. Hiçbir şey göndermez."""
    return tools.create_action_drafts(lot_id, [a.model_dump() for a in approved_actions],
                                      approver_actor_id)


@mcp.tool()
def generate_report_file(report_type: Literal["DAILY_RISK", "LOT_ACTION_PLAN", "RISK_TABLE"],
                         format: Literal["pdf", "xlsx"], lot_id: str | None = None,
                         decision_id: str | None = None, summary_text: str | None = None,
                         as_of_date: str | None = None) -> dict:
    """PDF veya Excel rapor dosyası üretir ve indirme linki döner. DAILY_RISK günlük risk raporu,
    RISK_TABLE risk tablosu, LOT_ACTION_PLAN tek lot için aksiyon planıdır (lot_id gerekir)."""
    return tools.generate_report_file(report_type, format, lot_id, decision_id,
                                      summary_text, as_of_date)


if __name__ == "__main__":
    mcp.run(transport="stdio")
