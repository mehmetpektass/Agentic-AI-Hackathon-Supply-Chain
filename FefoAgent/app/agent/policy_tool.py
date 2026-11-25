"""search_policies: politika ve süreç maddelerini (POL-x / PRC-x) arar.

KNOWLEDGE_BASE_ID tanımlıysa Bedrock Knowledge Base kullanılır. Tanımlı değilse veya KB
erişilemezse KB_Fallback devreye girer: app/agent/data/policy/*.md içinde madde araması.
Doküman yoksa uydurma içerik dönmez.
"""
import logging
import re
from pathlib import Path

from strands import tool

import config

logger = logging.getLogger("fefo_agent.policy_tool")
POLICY_DIR = Path(__file__).resolve().parent / "data" / "policy"
ARTICLE_START = re.compile(r"^[#>*\-\s]*\**((?:POL|PRC)-\d+(?:\.\d+)*)\**[\s:.\-–—)]*", re.M)
MSG_NO_DOCS = "politika dokümanı henüz yüklenmedi"
MSG_NO_MATCH = "sorguyla eşleşen madde bulunamadı"
TOP_K = 3


def _fold(text: str) -> str:
    return text.replace("İ", "i").replace("I", "ı").lower()


def split_articles(text: str) -> list[dict]:
    """Metni madde numarasıyla başlayan pasajlara böler."""
    starts = list(ARTICLE_START.finditer(text))
    out = []
    for i, m in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
        body = text[m.end():end].strip()
        if body:
            out.append({"madde_no": m.group(1), "metin": body})
    return out


def _load_articles(directory: Path) -> list[dict]:
    articles = []
    for path in sorted(directory.glob("*.md")) if directory.is_dir() else []:
        articles += split_articles(path.read_text(encoding="utf-8"))
    return articles


def _tokens(query: str) -> list[str]:
    return [t[:5] for t in re.findall(r"\w+", _fold(query)) if len(t) > 2]


def search_local(query: str, directory: Path | None = None) -> dict:
    articles = _load_articles(directory or POLICY_DIR)
    if not articles:
        return {"pasajlar": [], "kb_kullanılamadı": True, "mesaj": MSG_NO_DOCS}
    tokens = _tokens(query)
    scored = []
    for art in articles:
        hay = _fold(art["madde_no"] + " " + art["metin"])
        score = sum(1 for t in tokens if t in hay)
        if score:
            scored.append((score, art))
    scored.sort(key=lambda x: -x[0])
    result = {"pasajlar": [a for _, a in scored[:TOP_K]], "kb_kullanılamadı": True}
    if not result["pasajlar"]:
        result["mesaj"] = MSG_NO_MATCH
    return result


def search_kb(query: str, kb_id: str) -> dict:
    import boto3
    client = boto3.client("bedrock-agent-runtime", region_name=config.get_region())
    resp = client.retrieve(knowledgeBaseId=kb_id, retrievalQuery={"text": query},
                           retrievalConfiguration={"vectorSearchConfiguration": {
                               "numberOfResults": TOP_K}})
    passages = []
    for r in resp.get("retrievalResults", []):
        text = (r.get("content") or {}).get("text", "")
        passages += split_articles(text)
    result = {"pasajlar": passages[:TOP_K], "kb_kullanılamadı": False}
    if not passages:
        result["mesaj"] = MSG_NO_MATCH
    return result


def search(query: str) -> dict:
    kb_id = config.get_knowledge_base_id()
    if kb_id:
        try:
            return search_kb(query, kb_id)
        except Exception as exc:  # KB erişilemezse yedek akışa geç
            logger.warning("KB erişilemedi, KB_Fallback kullanılıyor: %s", type(exc).__name__)
    return search_local(query)


@tool
def search_policies(query: str) -> dict:
    """Şirketin FEFO politika ve süreç belgelerinde arama yapar. Süreç, rol, onay limiti,
    kampanya, bağış, iade ve kural sorularında kullan. Sonuç madde numarası (POL-x veya PRC-x)
    ve metin içeren pasajlardır. kb_kullanılamadı true ise Knowledge_Base kullanılamamıştır.
    Pasaj yoksa bilgi belgelerde yoktur, uydurma."""
    return search(query)
