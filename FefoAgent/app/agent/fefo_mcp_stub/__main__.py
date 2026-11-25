"""Stub MCP stdio sunucusu. stdout yalnızca MCP protokolüne aittir; loglar stderr'e gider."""
import logging
import sys

from mcp.server.fastmcp import FastMCP

from . import tools

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

mcp = FastMCP("fefo_mcp_stub")


@mcp.tool()
def get_expiry_risks(as_of_date: str | None = None, category: str | None = None,
                     min_loss_try: float = 0, top_n: int = 10) -> dict:
    """SKT riski taşıyan lotları beklenen ₺ kaybına göre azalan sırada listeler."""
    return tools.get_expiry_risks(as_of_date, category, min_loss_try, top_n)


@mcp.tool()
def get_sku_profile(sku_id: str, as_of_date: str | None = None) -> dict:
    """Bir ürünün satış hızı, lotları ve bayi bilgilerini getirir."""
    return tools.get_sku_profile(sku_id, as_of_date)


@mcp.tool()
def simulate_actions(lot_id: str, actions: list[dict], as_of_date: str | None = None) -> dict:
    """Bir lot için aksiyonları verilen sırayla uygulayıp kayıp şelalesini hesaplar."""
    return tools.simulate_actions(lot_id, actions, as_of_date)


@mcp.tool()
def create_action_drafts(lot_id: str, approved_actions: list[dict],
                         approver_actor_id: str) -> dict:
    """Onaylanan aksiyonlar için TASLAK mesajlar hazırlar. Hiçbir şey göndermez."""
    return tools.create_action_drafts(lot_id, approved_actions, approver_actor_id)


@mcp.tool()
def generate_report_file(report_type: str, format: str, lot_id: str | None = None,
                         decision_id: str | None = None, summary_text: str | None = None,
                         as_of_date: str | None = None) -> dict:
    """PDF veya Excel rapor dosyası üretir ve indirme linki döner."""
    return tools.generate_report_file(report_type, format, lot_id, decision_id,
                                      summary_text, as_of_date)


if __name__ == "__main__":
    mcp.run(transport="stdio")
