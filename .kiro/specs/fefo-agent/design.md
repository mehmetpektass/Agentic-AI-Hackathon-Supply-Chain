# Design Document

## Overview

FEFO_Agent, Strands Agents çatısı ile yazılan ve Amazon Bedrock AgentCore_Runtime üzerinde çalışan bir Python 3.12 uygulamasıdır. Agent kendisi hiçbir sayısal hesap yapmaz; tüm adet, gün ve ₺ değerlerini `Stub_MCP` veya `Fefo_MCP` adlı bir stdio MCP sunucusundan alınan tool çıktılarından okur. Agent ayrıca yerel bir `search_policies` tool'u ile Knowledge_Base'den (veya KB_Fallback ile paketlenmiş Policy_Docs'tan) politika/süreç bilgisi getirir.

Bu tasarım Plan 1 (Dev A) kapsamını kapsar: repo/steering kurulumu, AgentCore iskeleti, MCP_Adapter (Stub_MCP ↔ Fefo_MCP geçişi), Tool_Contract'a bağlı tool çağırma mantığı, Role_Hook, soru-cevap davranışı ve deploy/doğrulama belgelendirmesi (komutlar Kullanıcı tarafından veya Kullanıcı'nın bu oturumda açıkça yetkilendirdiği asistan tarafından çalıştırılır).

Tasarım dili: yapısal sözde kod (Türkçe anahtar kelimelerle: EĞER/İSE, DEĞİLSE, İÇİN, DÖNDÜR, FONKSİYON) ve gerekli yerlerde Python 3.12 imza örnekleri. Gerçek kod Dev A tarafından uygulama sırasında yazılacaktır; burada sözleşmeler ve akışlar netleştirilir.

### Kapsam Dışı

- `pipeline/fefo_core` hesap mantığı (Dev B sahipliği).
- `fefo_mcp` ve `chat-ui` implementasyonu (Dev B sahipliği) — bu tasarım yalnızca Tool_Contract'a uyan arayüzü varsayar.
- Plan 2 ve Plan 3 özellikleri.
- Plan 2 ve Plan 3 dışındaki kapsam: `agentcore deploy`, `invoke`, `status`, `logs` komutlarını Kullanıcı çalıştırır. Kullanıcı bu oturumda asistanın çalıştırmasını açıkça yetkilendirmiştir ve asistan yalnızca bu yetkiyle çalıştırır (PATH'te `~/.npm-global/bin` olmalıdır).

## Architecture

```
                     ┌─────────────────────────────────────────────┐
                     │           AgentCore_Runtime (us-east-1)      │
                     │                                               │
  İstek (prompt,     │   ┌───────────────────────────────────────┐ │
  actorId) ──────────┼──▶│  BedrockAgentCoreApp giriş noktası     │ │
                     │   │  (app/agent/main.py)                   │ │
                     │   └───────────────┬───────────────────────┘ │
                     │                   │ _get_agent() (lazy init)│
                     │                   ▼                         │
                     │   ┌───────────────────────────────────────┐ │
                     │   │  Strands Agent                        │ │
                     │   │  - Sistem prompt (yetenek bazlı)       │ │
                     │   │  - Model_ID (config, global.* )        │ │
                     │   │  - Role_Hook (BeforeToolCallEvent)     │ │
                     │   │  - search_policies (yerel @tool)       │ │
                     │   │  - MCP tool'ları (MCP_Adapter üzerinden)│ │
                     │   └───────┬───────────────────┬────────────┘ │
                     │           │                   │              │
                     │           ▼                   ▼              │
                     │  ┌─────────────────┐  ┌──────────────────┐  │
                     │  │ MCP_Adapter      │  │ Knowledge_Base    │  │
                     │  │ (stdio subprocess)│  │ veya KB_Fallback  │  │
                     │  └────────┬─────────┘  └──────────────────┘  │
                     │           │                                  │
                     │           ▼                                  │
                     │  ┌─────────────────────┐                    │
                     │  │ Stub_MCP  veya        │                    │
                     │  │ Fefo_MCP (Dev B)      │                    │
                     │  └──────────┬────────────┘                   │
                     │             │ S3 PutObject/GetObject          │
                     └─────────────┼──────────────────────────────┘
                                   ▼
                          S3 ($REPORTS_BUCKET)
                          reports/* , decisions/*

  AgentCore Observability (tool span'leri) ──▶ CloudWatch Logs / Traces
```

### Katmanlar

1. **Giriş noktası (`app/agent/main.py`)**: `BedrockAgentCoreApp` örneğini oluşturur, gelen `{"prompt", "actorId"}` yükünü `_get_agent()` ile elde edilen agent'a iletir, yanıtı stream eder.
2. **Agent katmanı**: Strands `Agent` nesnesi, sistem promptu, Role_Hook, yerel `search_policies` tool'u ve MCP_Adapter'dan gelen uzak tool'ları birleştirir.
3. **MCP_Adapter katmanı**: Yapılandırma değerine (`MCP_BACKEND` ortam değişkeni: `stub` | `fefo_mcp`) göre `fefo_mcp_stub` veya `fefo_mcp` modülünü, agent'ı çalıştıran aynı Python yorumlayıcısıyla (`sys.executable -m <modül>`) alt süreç olarak başlatır; `MCPClient` ile stdio bağlanır.
4. **Policy katmanı**: `search_policies` yerel tool'u, `KNOWLEDGE_BASE_ID` ortam değişkeni tanımlıysa Bedrock Knowledge Base'i sorgular; tanımlı değilse veya erişim hatası alırsa KB_Fallback'e (paketlenmiş `policy.md`/`process_guide.md` içinde arama) geçer.
5. **Yapılandırma katmanı**: Model_ID, MCP_BACKEND, REPORTS_BUCKET, KNOWLEDGE_BASE_ID, Max_Discount_Pct_By_Role gibi değerler ortam değişkenlerinden veya bir yapılandırma dosyasından okunur; hiçbiri koda gömülmez.

## Components and Interfaces

### 1. Giriş Noktası — `app/agent/main.py`

**Sorumluluk**: AgentCore_Runtime isteklerini kabul etmek, lazy-init agent'ı çağırmak, yanıtı dönmek.

```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()
_agent_singleton = None  # modül yüklenirken OLUŞTURULMAZ

def _get_agent():
    global _agent_singleton
    if _agent_singleton is None:
        _agent_singleton = _build_agent()  # MCP_Client, Role_Hook, tool'lar burada kurulur
    return _agent_singleton

@app.entrypoint
def invoke(payload: dict) -> dict:
    prompt = payload.get("prompt", "")
    actor_id = payload.get("actorId", "")
    agent = _get_agent()
    return agent.run(prompt=prompt, actor_id=actor_id)
```

Yapısal sözde kod:

```
FONKSİYON invoke(payload):
    istem = payload["prompt"]
    aktor_id = payload["actorId"]
    agent = _get_agent()   // yalnızca ilk çağrıda inşa eder
    DÖNDÜR agent.çalıştır(istem, aktor_id)
```

### 2. Yapılandırma — `app/agent/config.py`

**Sorumluluk**: Tüm dışsal değerleri ortam değişkenlerinden/yapılandırma dosyasından okumak, doğrulamak, varsayılanları uygulamak.

| Alan | Kaynak | Varsayılan | Doğrulama |
|---|---|---|---|
| `MODEL_ID` | env `MODEL_ID` | `global.anthropic.claude-sonnet-5` (`agentcore.json` envVars ile verilir) | `global.` ile başlamalı (Req 5.3); yoksa başlatma reddedilir. `sonnet-5-5` hesapta yasaktır |
| `MCP_BACKEND` | env `MCP_BACKEND` | `stub` | `stub` \| `fefo_mcp` |
| `REPORTS_BUCKET` | env `REPORTS_BUCKET` | `fefo-862714237836-us-east-1` (`S3_BUCKET_NAME` env yok, ad doğrudan kullanılır) | boş olamaz |
| `KNOWLEDGE_BASE_ID` | env `KNOWLEDGE_BASE_ID` | yok (opsiyonel, KB ID henüz yok) | tanımlı değilse KB_Fallback. ID gelince `agentcore.json` içine eklenir |
| `MAX_DISCOUNT_PCT_BY_ROLE` | `app/agent/data/params.json` içindeki `max_discount_pct_by_role` alanı | dosya veya alan yoksa `config.py` içindeki tek varsayılan: `ticari` → `DEALER_OFFER` 20, `CAMPAIGN` 25; `depo` → indirimli aksiyon yok | rol adı → aksiyon tipi → sayı (0-100) eşlemesi |

> **Not — Max_Discount_Pct_By_Role kaynağı**: Sınırlar `app/agent/data/params.json` içindeki `max_discount_pct_by_role` alanından okunur (`role_policy.json` kullanılmaz). `data/` klasörü Dev B export'una aittir ve elle düzenlenmez. Dosya veya alan yoksa Role_Hook, `config.py` içinde tek noktada tanımlı varsayılana düşer. Varsayılan sayılar yalnızca `config.py` içinde bulunur, başka hiçbir yerde tekrarlanmaz. Yapılandırma okunamıyorsa (bozuk JSON) varsayılan kullanılır ve uyarı stderr'e loglanır.

`params.json` içindeki beklenen alan biçimi (Dev B export'u; hook dosya yoksa varsayılana düşer):

```json
{
  "max_discount_pct_by_role": {
    "ticari": { "DEALER_OFFER": 20, "CAMPAIGN": 25 }
  }
}
```

Yapısal sözde kod — yapılandırma yükleme:

```
FONKSİYON max_indirim_yükle():
    yol = paket_içi("data/params.json")
    EĞER dosya(yol) mevcut DEĞİLSE VEYA "max_discount_pct_by_role" alanı YOKSA:
        DÖNDÜR VARSAYILAN_MAX_İNDİRİM   // config.py içindeki tek nokta: {"ticari": {"DEALER_OFFER": 20, "CAMPAIGN": 25}}
    içerik = json_oku(yol)
    DÖNDÜR içerik["max_discount_pct_by_role"]  // { rol: { aksiyon_tipi: yüzde } }

FONKSİYON izinli_mi(rol, aksiyon_tipi, istenen_yüzde, harita):
    EĞER rol harita İÇİNDE DEĞİLSE: DÖNDÜR YANLIŞ
    EĞER aksiyon_tipi harita[rol] İÇİNDE DEĞİLSE: DÖNDÜR YANLIŞ
    sınır = harita[rol][aksiyon_tipi]
    DÖNDÜR istenen_yüzde <= sınır
```

### 3. MCP_Adapter — `app/agent/mcp_adapter.py`

**Sorumluluk**: `MCP_BACKEND` değerine göre doğru stdio MCP modülünü başlatmak, ortam değişkenlerini açıkça geçirmek, `MCPClient` bağlantısını kurmak, tool listesini agent'a sunmak.

```python
import os
import sys
from strands.tools.mcp import MCPClient
from mcp.client.stdio import StdioServerParameters

def build_mcp_client() -> MCPClient:
    backend = os.environ.get("MCP_BACKEND", "stub")
    module = "app.agent.fefo_mcp_stub" if backend == "stub" else "fefo_mcp"

    child_env = dict(os.environ)  # mevcut ortamı aktar
    # AWS kimlik bilgileri zaten os.environ içinde; ayrıca açıkça listelenen anahtarlar:
    for key in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN",
                "AWS_REGION", "REPORTS_BUCKET"):
        if key in os.environ:
            child_env[key] = os.environ[key]

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", module],
        env=child_env,
    )
    try:
        return MCPClient(lambda: stdio_client(params))
    except ImportError as exc:
        # Req 6.9: Fefo_MCP içe aktarılamıyorsa stderr'e logla, başlatmayı durdur
        print(f"MCP_Adapter: {module} içe aktarılamadı: {exc}", file=sys.stderr)
        raise
```

Yapısal sözde kod:

```
FONKSİYON mcp_istemcisi_oluştur():
    backend = ortam["MCP_BACKEND"] VEYA "stub"
    modül = EĞER backend == "stub" İSE "fefo_mcp_stub" DEĞİLSE "fefo_mcp"
    alt_süreç_ortamı = mevcut_ortamın_kopyası()
    // AWS kimlik bilgileri, AWS_REGION, REPORTS_BUCKET açıkça geçirilir (zaten kopya içinde,
    // burada varlığı doğrulanır)
    EĞER modül içe_aktarılamıyorsa:
        stderr_log("MCP modülü başlatılamadı: " + modül)
        İPTAL_ET  // başlatmayı durdur
    parametreler = StdioParametreleri(komut=python_yorumlayıcısı, args=["-m", modül], ortam=alt_süreç_ortamı)
    DÖNDÜR MCPİstemcisi(parametreler)  // aynı Python yorumlayıcısı, modül olarak başlatılır
```

Backend değişimi (Req 6.10) sadece `MCP_BACKEND` değerinin `stub` → `fefo_mcp` olarak güncellenmesi ve `fefo_mcp_stub/` klasörünün silinmesiyle yapılır; agent kodunda başka değişiklik gerekmez (Req 6.8).

### 4. Stub_MCP — `app/agent/fefo_mcp_stub/`

**Sorumluluk**: Tool_Contract'a (bölüm 4) uyan, sabit/deterministik yanıtlar dönen sahte stdio MCP sunucusu. stdout'a yalnızca MCP protokol mesajları yazılır; hiçbir `print()` kullanılmaz, loglar `logging` ile stderr'e yönlendirilir.

Modül yapısı:

```
app/agent/fefo_mcp_stub/
  __init__.py
  __main__.py         # stdio server başlatıcı (python -m app.agent.fefo_mcp_stub)
  tools.py             # get_expiry_risks, get_sku_profile, simulate_actions,
                       # create_action_drafts, generate_report_file
  fixtures/            # sabit örnek veri (JSON)
```

Her tool fonksiyonu Tool_Contract'taki şemayı birebir uygular ve varsayılan `as_of_date = "2026-11-25"` (Default_As_Of_Date) kullanır (Req 8.4).

Yapısal sözde kod (örnek: `get_expiry_risks`):

```
FONKSİYON get_expiry_risks(as_of_date=YOK, category=YOK, min_loss_try=0, top_n=10):
    EĞER as_of_date == YOK: as_of_date = "2026-11-25"
    öğeler = sabit_fixture_oku("expiry_risks.json")
    EĞER category VERİLDİYSE: öğeler = öğeler.filtrele(category)
    öğeler = öğeler.filtrele(loss_try.expected >= min_loss_try)
    öğeler = öğeler.azalan_sırala(loss_try.expected)
    öğeler = öğeler[:top_n]
    DÖNDÜR { "as_of_date": as_of_date,
             "total_expected_loss_try": toplam(öğeler.loss_try.expected),
             "items": öğeler }
```

Hata durumunda (Req 8.1): exception fırlatılmaz, `{"error": {"code": "...", "message": "..."}}` dönülür.

### 5. Fefo_MCP Bağlantısı (Dev B — yalnızca arayüz varsayımı)

Dev A, `fefo_mcp` modülünü **elle düzenlemez** (Req 6.12). MCP_Adapter, `MCP_BACKEND=fefo_mcp` iken aynı stdio başlatma mekanizmasını kullanır; Tool_Contract'ın korunduğu, Stub_MCP ile aynı testlerin (Req 6.11, 18.3) geçmesi beklenir.

### 6. Role_Hook — `app/agent/role_hook.py`

**Not (modül adları)**: `role_hook.py`, `config.py`, `mcp_adapter.py`, `policy_tool.py`, `schemas.py` adları ve `app/agent/` altındaki yerleşim bu tasarımdaki varsayımdır. Scaffold sonrası gerçek yapı (`main.py`, `parse.py`, `model/load.py`, `memory/session.py`) incelenir ve modül adları ile import yolları ona göre uyarlanır.

**Sorumluluk**: `BeforeToolCallEvent` üzerinde `create_action_drafts` çağrısını denetlemek, Actor_Id biçimini doğrulamak, Role_Action_Matrix ve Max_Discount_Pct_By_Role'e göre izin/ret vermek, kararı loglamak.

Role_Action_Matrix (Req 9.4, 9.5):

| Aksiyon | depo | ticari |
|---|---|---|
| FEFO_PRIORITY | izinli | izinli |
| DEALER_OFFER | yasak | izinli (Max_Discount_Pct_By_Role sınırı içinde) |
| CAMPAIGN | yasak | izinli (Max_Discount_Pct_By_Role sınırı içinde) |
| DONATION | izinli | izinli |
| SUPPLIER_RETURN | izinli | izinli |
| generate_report_file | izinli | izinli |

```python
import re
import logging

ACTOR_ID_RE = re.compile(r"^[a-z]+-[a-zA-Z0-9-]+$")
DISCOUNT_ACTIONS = {"DEALER_OFFER", "CAMPAIGN"}
ALWAYS_ALLOWED = {"FEFO_PRIORITY", "DONATION", "SUPPLIER_RETURN"}
VALID_ROLES = {"depo", "ticari"}

logger = logging.getLogger("fefo_agent.role_hook")

def on_before_tool_call(event):
    if event.tool_name != "create_action_drafts":
        return  # yalnızca create_action_drafts denetlenir

    actor_id = event.arguments.get("approver_actor_id", "")
    if not ACTOR_ID_RE.match(actor_id):
        logger.info("ret: actorId_biçimsiz actor_id=%s", actor_id)
        event.cancel("rol belirlenemedi: actorId biçimi geçersiz")
        return

    role = actor_id.split("-", 1)[0]
    if role not in VALID_ROLES:
        logger.info("ret: bilinmeyen_rol role=%s actor_id=%s", role, actor_id)
        event.cancel("rol belirlenemedi: bilinmeyen rol")
        return
    discount_limits = load_max_discount_pct_by_role()  # config.py

    for action in event.arguments.get("approved_actions", []):
        action_type = action["type"]
        if action_type in ALWAYS_ALLOWED or action_type == "generate_report_file":
            continue
        if action_type in DISCOUNT_ACTIONS:
            if role != "ticari":
                logger.info("ret: rol_yetkisiz role=%s action=%s", role, action_type)
                event.cancel("bu aksiyon için ticari onayı gerekir")
                return
            requested_pct = action.get("params", {}).get("discount_pct")
            if not is_valid_pct(requested_pct):  # eksik, sayısal değil veya 0-100 dışı
                logger.info("ret: discount_pct_gecersiz role=%s action=%s", role, action_type)
                event.cancel("indirim yüzdesi eksik veya geçersiz")
                return
            if not is_allowed(role, action_type, requested_pct, discount_limits):
                logger.info("ret: indirim_siniri_asimi role=%s action=%s pct=%s",
                            role, action_type, requested_pct)
                event.cancel("bu aksiyon için ticari onayı gerekir")
                return

    logger.info("izin: role=%s actor_id=%s actions=%s", role, actor_id,
                [a["type"] for a in event.arguments.get("approved_actions", [])])
```

Yapısal sözde kod:

```
FONKSİYON rol_hook(olay):
    EĞER olay.tool_adı != "create_action_drafts": DÖNÜŞ

    actor_id = olay.argümanlar["approver_actor_id"]
    EĞER actor_id ACTOR_ID_BİÇİMİNE_UYMUYORSA:
        logla("ret", "actorId_biçimsiz", actor_id)
        olay.iptal_et("rol belirlenemedi")
        DÖNÜŞ

    rol = actor_id.split("-")[0]
    EĞER rol NOT IN {"depo", "ticari"}:
        logla("ret", "bilinmeyen_rol", rol, actor_id)
        olay.iptal_et("rol belirlenemedi: bilinmeyen rol")
        DÖNÜŞ
    indirim_sınırları = max_indirim_yükle()

    İÇİN her aksiyon IN olay.argümanlar["approved_actions"]:
        EĞER aksiyon.tipi HER_ZAMAN_İZİNLİ_KÜMESİNDE: DEVAM_ET
        EĞER aksiyon.tipi İNDİRİM_AKSİYONLARI_KÜMESİNDE:
            EĞER rol != "ticari":
                logla("ret", "rol_yetkisiz", rol, aksiyon.tipi)
                olay.iptal_et("bu aksiyon için ticari onayı gerekir")
                DÖNÜŞ
            istenen = aksiyon.params["discount_pct"]
            EĞER istenen EKSİK VEYA SAYISAL_DEĞİL VEYA istenen < 0 VEYA istenen > 100:
                logla("ret", "discount_pct_gecersiz", rol, aksiyon.tipi)
                olay.iptal_et("indirim yüzdesi eksik veya geçersiz")
                DÖNÜŞ
            EĞER DEĞİL izinli_mi(rol, aksiyon.tipi, istenen, indirim_sınırları):
                // sınır haritasında rol veya aksiyon yoksa izinli_mi YANLIŞ döner → ret
                logla("ret", "indirim_siniri_asimi_veya_tanimsiz", rol, aksiyon.tipi, istenen)
                olay.iptal_et("bu aksiyon için ticari onayı gerekir")
                DÖNÜŞ

    logla("izin", rol, actor_id, aksiyon_tipleri)
```

İptal edilen çağrıdan sonra agent konuşmayı sonlandırmaz (Req 9.8); üst katmandaki Strands agent döngüsü `event.cancel(...)` mesajını bir tool hata yanıtı gibi işler ve kullanıcıya iletip beklemeye devam eder.

### 7. search_policies — `app/agent/policy_tool.py`

**Sorumluluk**: Yerel `@tool` olarak çalışmak (Fefo_MCP üzerinden sunulmaz, Req 7.15), `query` girdisini kabul edip Policy_Docs'tan ilgili pasajları ve madde numaralarını (`POL-x`/`PRC-x`) dönmek.

```
FONKSİYON search_policies(query):
    EĞER ortam["KNOWLEDGE_BASE_ID"] TANIMLIYSA:
        DENE:
            sonuçlar = bedrock_kb_sorgula(ortam["KNOWLEDGE_BASE_ID"], query)
            DÖNDÜR madde_numaralı_pasajlar(sonuçlar)
        YAKALA erişim_hatası:
            logla("KB erişilemedi, KB_Fallback'e geçiliyor")
            // devam et, aşağıdaki fallback'e düş
    // KB_Fallback
    pasajlar = paketlenmiş_md_dosyalarında_ara("policy.md", "process_guide.md", query)
    DÖNDÜR { "pasajlar": pasajlar, "kb_kullanılamadı": DOĞRU }
```

Fallback çıktısı da ana yol çıktısıyla aynı şemayı korur (Req 14.4): `{"pasajlar": [{"madde_no": "POL-3", "metin": "..."}], "kb_kullanılamadı": bool}`.

### 8. Sistem Prompt Tasarımı

Sistem prompt, tool'ları **isim** değil **yetenek** olarak tanıtır (Req 5.9). Örnek çerçeve (Türkçe):

```
Sen FEFO Kurtarma Ajanısın. Depo lotlarının SKT'den önce satılıp satılmayacağını
tahmin eden, riskli lotları ₺ kaybıyla gösteren ve aksiyon kombinasyonlarının
etkisini simüle eden bir asistansın.

Kurallar:
- Hiçbir adet, gün veya ₺ değerini kendin hesaplama; yalnızca ilgili yeteneği
  çağırıp sonucu oku.
- Mail veya mesaj asla kendi başına gönderilmez; onay sonrası yalnızca TASLAK
  üretilir.
- Süreç sorularında ilgili politika/süreç bilgisini ara ve madde numarasını belirt.
- Veriler sentetiktir, "temsili senaryo" olarak sun.
- forecast_confidence değeri LOW olan öğeler için düşük güvenli tahmin uyarısı ver.
- Karar akışı sırası: risk listesi → neden → simülasyon → öneri → onay → taslaklar.
- Elindeki bilgide olmayan bir şeyi uydurma; "bu bilgi elimdeki verilerde yok" de.
```

## Data Models

Tüm veri modelleri Tool_Contract (requirements.md Glossary ve Requirement 7) ile birebir uyumludur; burada yalnızca Python `TypedDict`/`dataclass` biçiminde referans gösterilir (gerçek implementasyon JSON şema doğrulamasıyla da desteklenebilir).

```python
from typing import TypedDict, Literal, Optional

class Range(TypedDict):
    low: float
    expected: float
    high: float

class ExpiryRiskItem(TypedDict):
    sku_id: str
    sku_name: str
    category: Literal["COLD", "DRY"]
    lot_id: str
    qty_units: int
    expiry_date: str          # ISO
    days_to_expiry: int
    location_bin: str
    sellable_window_days: int
    forecast_units_in_window: Range
    at_risk_units: Range
    loss_try: Range
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    reason_codes: list[str]
    forecast_confidence: Literal["HIGH", "MEDIUM", "LOW"]
    wape: float

class ExpiryRisksResponse(TypedDict):
    as_of_date: str
    total_expected_loss_try: float
    items: list[ExpiryRiskItem]

class ToolError(TypedDict):
    error: "ToolErrorBody"

class ToolErrorBody(TypedDict):
    code: str
    message: str

class ActionDraft(TypedDict):
    audience: Literal["WAREHOUSE", "COMMERCIAL", "SUPPLIER", "DEALER", "DONATION_PARTNER"]
    subject: str
    body: str  # Draft_Header ile başlamalı: "TASLAK — gönderilmedi"

class CreateActionDraftsResponse(TypedDict):
    decision_id: str
    status: Literal["DRAFT"]
    drafts: list[ActionDraft]
    summary: "DraftSummary"

class DraftSummary(TypedDict):
    final_loss_try: float
    total_net_benefit_try: float
    kg_saved: float
```

`simulate_actions`, `get_sku_profile`, `generate_report_file` için de aynı şekilde Tool_Contract alanlarını birebir yansıtan `TypedDict` tanımları `app/agent/schemas.py` içinde tutulur ve hem Stub_MCP hem Fefo_MCP yanıtlarının şema doğrulaması (Req 8.6) bu tanımlara karşı yapılır.

### Max_Discount_Pct_By_Role Yapılandırma Şeması

```python
MaxDiscountPctByRole = dict[str, dict[str, float]]
# Örnek: {"ticari": {"DEALER_OFFER": 15, "CAMPAIGN": 20}}
# Dosya/değer yoksa: {} (boş harita) → tüm indirimli aksiyonlar reddedilir.
```

## Error Handling

| Durum | Davranış |
|---|---|
| Tool çağrısı hata döner (Tool_Error) | Agent hata kodunu kullanıcıya bildirir, uydurma veri eklemez (Req 8.3) |
| Tool yanıtı şemaya uymuyor | Agent şema ihlalini loglar, kullanıcıya "tool yanıtı geçersiz" bildirir (Req 8.6) |
| `MCP_BACKEND=fefo_mcp` ama modül içe aktarılamıyor | MCP_Adapter stderr'e nedeni loglar, başlatmayı durdurur (Req 6.9) |
| Knowledge_Base erişilemiyor/tanımsız | `search_policies` KB_Fallback'e geçer, yanıtta KB kullanılamadığını belirtir (Req 14.3, 14.6) |
| `actorId` eksik/biçimsiz | Role_Hook isteği reddeder, "rol belirlenemedi" döner (Req 9.10) |
| Rol yetkisi dışı aksiyon veya indirim sınırı aşımı (ya da sınır tanımsız) | Role_Hook çağrıyı iptal eder, "bu aksiyon için ticari onayı gerekir" döner, konuşma sürer (Req 9.7, 9.8, 9.9) |
| Kullanıcı "maili gönder" gibi gönderim ister | Agent isteği reddeder, yalnızca taslak üretebileceğini söyler (Req 12.2) |
| Soru yanıtı KB'de veya tool çıktısında yok | Agent "bu bilgi elimdeki verilerde yok" der (Req 10.4) |
| `generate_report_file` S3'e yazamıyor | Fefo_MCP Tool_Error döner, agent hata kodunu bildirir (Req 13.6) |
| `report_type=LOT_ACTION_PLAN` ve `lot_id` yok | `generate_report_file` Tool_Error döner (Req 13.2) |

Genel ilke: hiçbir katman exception fırlatarak süreci kesmez; her hata `{"error": {"code", "message"}}` biçiminde yukarı taşınır ve agent bunu kullanıcıya Türkçe, uydurma içermeyen bir mesaja çevirir.

## Agentcore_Config (`FefoAgent/agentcore/agentcore.json`) Tasarımı

```json
{
  "name": "FefoAgent",
  "region": "us-east-1",
  "envVars": {
    "MODEL_ID": "global.anthropic.claude-sonnet-5",
    "MCP_BACKEND": "stub",
    "REPORTS_BUCKET": "fefo-862714237836-us-east-1",
    "UNIFIED_TRACES_DESTINATION_ENABLED": "true"
  },
  "additionalPolicies": [
    {
      "effect": "Allow",
      "actions": ["s3:PutObject", "s3:GetObject"],
      "resources": [
        "arn:aws:s3:::fefo-862714237836-us-east-1/reports/*",
        "arn:aws:s3:::fefo-862714237836-us-east-1/decisions/*"
      ]
    },
    {
      "effect": "Allow",
      "actions": ["bedrock:Retrieve"],
      "resources": ["<Knowledge_Base ARN, yalnızca KNOWLEDGE_BASE_ID tanımlıysa>"]
    },
    {
      "effect": "Allow",
      "actions": ["bedrock:RetrieveAndGenerate"],
      "resources": ["*"]
    }
  ]
}
```

`REPORTS_BUCKET` değeri `fefo-862714237836-us-east-1` olarak yazılır. Knowledge_Base ID henüz yoktur: `KNOWLEDGE_BASE_ID` envVar'ı ve `bedrock:Retrieve` / `bedrock:RetrieveAndGenerate` politika girdileri şimdilik eklenmez ve `search_policies` KB_Fallback modunda çalışır. ID gelince hepsi `agentcore.json` içine eklenir. Yukarıdaki JSON örnektir, gerçek şema scaffold'un ürettiği `agentcore.json` dosyasına göre uyarlanır (runtime adı `agent`, politikalar runtime `additionalPolicies` listesinde).

## Deploy ve Doğrulama Akışı (Kullanıcı Yetkisiyle Asistan Çalıştırabilir)

Aşağıdaki komutlar Project_Setup tarafından belgelenir. Kullanıcı (Dev A) bu oturumda asistanın `agentcore deploy`, `invoke`, `status` ve `logs` komutlarını çalıştırmasını açıkça yetkilendirmiştir (Req 16.1). Yetki dışındaki AWS değişiklikleri için ayrıca onay istenir. Komutlardan önce `~/.npm-global/bin` PATH'te olmalıdır. Alt sürece mevcut ortamın kopyası geçirilir ve ortam (`env`, `printenv`) hiçbir zaman ekrana veya loga basılmaz.

```
1. agentcore status
   Beklenen: runtime "deployed" durumunda, ARN görünür.

2. agentcore invoke --runtime agent --session-id <33+ karakter> \
   --payload '{"prompt":"Bugun riskli urunler neler? Bir aracini cagir ve sonucu goster.","actorId":"depo-test"}'
   Beklenen: yanıt tool verisi (ör. lot_id, loss_try) içerir.

3. aws logs describe-log-groups --log-group-name-prefix /aws/bedrock-agentcore/runtimes/ \
   --query "logGroups[].logGroupName" --output text
   Beklenen: "...-DEFAULT" log grubu listede.
   agentcore traces runtime list --since 15m
   Beklenen: son invoke'un trace'i listede.

4. ls .kiro/specs/fefo-agent/
   Beklenen: requirements.md, design.md, tasks.md mevcut.

5. agentcore traces runtime get <trace-id>
   Beklenen: fefo_mcp tool span'leri (get_expiry_risks, simulate_actions, vb.) görünür.
```

Deploy ritüeli: `git pull` → `agentcore deploy` (Kullanıcı) → Verification_Set (Kullanıcı) → deploy sonrası değişiklikleri commit (Kullanıcı, Project_Setup bu adımı belgeler).

## Testing Strategy

### Test Kapsamı Kararı
Bu oturumda yalnızca Tool kontrat testleri (Stub_MCP kontrat doğrulaması) aktiftir. Diğer tüm testler (Role_Hook, MCP_Adapter, search_policies, yapılandırma birim testleri, property-based testler ve eval testleri) **şimdilik atlandı**. Aşağıdaki maddeler atlanan testlerin tasarımını korur.

### Birim Testleri
- **Aktif**: Stub_MCP'nin her tool'u için Tool_Contract şema doğrulaması (Req 18.1).
- (şimdilik atlandı) Role_Hook karar yolları: izin, ret (rol yetkisiz), ret (actorId biçimsiz veya bilinmeyen rol), ret (discount_pct eksik veya geçersiz), ret (indirim sınırı aşımı) (Req 18.2).
- (şimdilik atlandı) MCP_Adapter'ın `stub` ve `fefo_mcp` seçim mantığı (Req 18.3).
- `generate_report_file` girdi doğrulaması: `LOT_ACTION_PLAN` + `lot_id` eksik → Tool_Error.
- (şimdilik atlandı) `params.json` veya alanı yokken `config.py` varsayılanının (ticari: `DEALER_OFFER` 20, `CAMPAIGN` 25; depo: yok) uygulandığının doğrulanması.

### Property-Based Testler (şimdilik atlandı)
Aşağıdaki "Correctness Properties" bölümünde tanımlanan özellikler, her biri ilgili fonksiyon/modül için ayrı bir property test olarak uygulanır (örn. `hypothesis` kütüphanesi ile, minimum 100 iterasyon).

### Entegrasyon / Eval Testleri (şimdilik atlandı)
- Eval_Set senaryoları (requirements.md Req 18.4-18.8): rakam birebir eşleşmesi, madde numaralı süreç yanıtı, "maili gönder" reddi, rol bazlı onay, what-if yeniden hesaplama — Stub_MCP üzerinde `tests/eval/` içinde örnek bazlı senaryolarla doğrulanır (bunlar PBT değildir, çünkü spesifik senaryo/transkript doğrulamasıdır).

## Correctness Properties

*Not: Bu özelliklere karşılık gelen property testleri şimdilik atlandı; özellikler tasarım referansı olarak korunur.*

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Risk listesi azalan sıralı ve Tool_Contract alanlarını içerir

For any `get_expiry_risks` response generated by Stub_MCP with arbitrary valid inputs (`as_of_date`, `category`, `min_loss_try`, `top_n`), the returned `items` list SHALL be sorted in non-increasing order of `loss_try.expected`, and every item SHALL contain all required fields (`sku_id`, `sku_name`, `category`, `lot_id`, `qty_units`, `expiry_date`, `days_to_expiry`, `location_bin`, `sellable_window_days`, `forecast_units_in_window`, `at_risk_units`, `loss_try`, `risk_level`, `reason_codes`, `forecast_confidence`, `wape`).

**Validates: Requirements 7.3, 7.4**

### Property 2: min_loss_try filtresi tüm sonuçlarda korunur

For any `get_expiry_risks` call with a given `min_loss_try` threshold, every returned item's `loss_try.expected` SHALL be greater than or equal to `min_loss_try`.

**Validates: Requirements 7.2**

### Property 3: as_of_date verilmezse varsayılan uygulanır

For any tool call among `get_expiry_risks`, `get_sku_profile`, `simulate_actions`, `generate_report_file` made without an `as_of_date` argument, the response's effective `as_of_date` SHALL equal Default_As_Of_Date (`2026-11-25`).

**Validates: Requirements 8.4, 8.5**

### Property 4: simulate_actions adımları girdi sırasını korur ve kaybı tutarlı günceller

For any `lot_id` and any ordered list of actions passed to `simulate_actions`, the returned `steps` list SHALL have the same length and the same order of `action` types as the input `actions` list, and for every step the `loss_after_try` of a feasible step SHALL be less than or equal to the `loss_after_try` (or `baseline_loss_try` for the first step) of the preceding step.

**Validates: Requirements 7.7, 7.8, 7.9**

### Property 5: Taslak başlığı her zaman mevcuttur

For any successful `create_action_drafts` response, every draft in the `drafts` list SHALL have a `body` field that starts with the Draft_Header string `"TASLAK — gönderilmedi"`.

**Validates: Requirements 12.3**

### Property 6: audience alanı izinli kümeden seçilir

For any successful `create_action_drafts` response, every draft's `audience` field SHALL be one of `WAREHOUSE`, `COMMERCIAL`, `SUPPLIER`, `DEALER`, `DONATION_PARTNER`.

**Validates: Requirements 7.12**

### Property 7: Role_Hook — izinli aksiyonlar her rolde geçer

For any `approver_actor_id` with a valid role prefix (`depo` or `ticari`) and any `approved_actions` list consisting only of `FEFO_PRIORITY`, `DONATION`, `SUPPLIER_RETURN`, or `generate_report_file`, the Role_Hook SHALL allow the `create_action_drafts` call (no cancellation).

**Validates: Requirements 9.4**

### Property 8: Role_Hook — depo rolü indirimli aksiyonları her zaman reddeder

For any `approved_actions` list containing a `DEALER_OFFER` or `CAMPAIGN` action and any `approver_actor_id` whose role is `depo`, the Role_Hook SHALL cancel the `create_action_drafts` call with a message indicating commercial approval is required.

**Validates: Requirements 9.5, 9.7**

### Property 9: Role_Hook — indirim sınırı aşımı, geçersiz discount_pct veya sınırsız aksiyon reddedilir

For any `ticari` actor and any `DEALER_OFFER` or `CAMPAIGN` action whose `discount_pct` exceeds the configured Max_Discount_Pct_By_Role limit for that action (including a missing, non-numeric or out-of-range `discount_pct`, and an action type with no configured limit), the Role_Hook SHALL cancel the `create_action_drafts` call.

**Validates: Requirements 9.9**

### Property 10: Role_Hook — indirim sınırı içindeki ticari istekler geçer

For any `ticari` actor, any `DEALER_OFFER` or `CAMPAIGN` action whose `discount_pct` is less than or equal to a configured Max_Discount_Pct_By_Role limit for that action, the Role_Hook SHALL allow the `create_action_drafts` call.

**Validates: Requirements 9.5**

### Property 11: Geçersiz actorId her zaman reddedilir

For any string that does not match the `<rol>-<isim>` pattern (letters, digits, and hyphens only, with at least one hyphen separating a role prefix), using it as `approver_actor_id` SHALL cause the Role_Hook to cancel the call with a "rol belirlenemedi" message.

**Validates: Requirements 9.2, 9.10**

### Property 12: MCP_Adapter modül seçimi yapılandırmayla tutarlıdır

For any value of `MCP_BACKEND` in `{"stub", "fefo_mcp"}`, the MCP_Adapter SHALL start the subprocess using the module path corresponding to that value (`fefo_mcp_stub` for `"stub"`, `fefo_mcp` for `"fefo_mcp"`), and no other module.

**Validates: Requirements 6.2, 6.8**

### Property 13: Alt sürece geçirilen ortam değişkenleri korunur

For any parent process environment containing `AWS_REGION` and `REPORTS_BUCKET`, the subprocess environment constructed by MCP_Adapter SHALL contain the same key-value pairs for `AWS_REGION` and `REPORTS_BUCKET`.

**Validates: Requirements 6.4**

### Property 14: search_policies her zaman madde numarası döner (KB veya fallback)

For any non-empty `query` string, the response from `search_policies` SHALL contain at least one passage annotated with a reference matching the pattern `POL-\d+` or `PRC-\d+`, regardless of whether Knowledge_Base or KB_Fallback was used.

**Validates: Requirements 7.14, 14.4**

### Property 15: KB_Fallback kontrat eşdeğerliği

For any `query`, the output schema returned when `KNOWLEDGE_BASE_ID` is undefined (KB_Fallback path) SHALL be identical in shape (same keys) to the output schema returned when `KNOWLEDGE_BASE_ID` is defined and reachable.

**Validates: Requirements 14.4**

### Property 16: Tool hatası asla exception olarak dışarı taşmaz

For any tool invocation (on Stub_MCP) with malformed or out-of-range input that the tool is designed to reject, the tool SHALL return a JSON object matching the Tool_Error shape (`{"error": {"code", "message"}}`) rather than raising an exception.

**Validates: Requirements 8.1**

### Property 17: generate_report_file girdi doğrulaması

For any call to `generate_report_file` with `report_type="LOT_ACTION_PLAN"` and no `lot_id` provided, the response SHALL be a Tool_Error.

**Validates: Requirements 13.2**

### Property 18: Rapor dosya anahtarı kalıbı

For any successful `generate_report_file` response, the `s3_key` field SHALL match the pattern `reports/<as_of_date>/<file_id>.<format>` where `format` is either `pdf` or `xlsx` matching the request's `format` input.

**Validates: Requirements 13.3, 13.4**

### Property 19: Model_ID öneki doğrulaması

For any configured `MODEL_ID` value, the agent's startup validation SHALL accept the value if and only if it starts with the literal prefix `global.`.

**Validates: Requirements 5.2, 5.3**
