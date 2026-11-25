# FEFO Kurtarma Ajanı — Takım Planı, Sözleşmeler ve Görev Dağılımı

> **Hackathon:** AWS "Agentic AI in Supply Chain" — Kiro + Amazon Bedrock AgentCore (event hesabı us-east-1, 27 Kasım 09:38'de kapanır).
> **Teslim:** ≈17:10. **Bu dosya takımın tek ortak planıdır:** veri şeması (bölüm 3) ve tool kontratları (bölüm 4) **sözleşmedir**.
> AWS/Kiro kuralları, komutlar ve hatalar için ayrıntılı referans: `HACKATHON_KIRO_CONTEXT.md` (repo kökünde).

---

## 0. AI asistanlar için talimatlar (Kiro, Claude Code vb.)

1. Önce bölüm 1–5'i oku, sonra **sadece kendi rolünün** bölümünü (6.1 / 6.2 / 6.3) uygula.
2. **Kapsam sırası:** Önce **Plan 1** (bölüm 1.1) tamamlanır. Plan 2 ve Plan 3'e, Plan 1 yeşil olmadan ve bölüm 7'deki kontrol noktası geçilmeden **başlanmaz**.
3. **Sahiplik:** Yalnızca kendi rolünün sahip olduğu klasörlerde değişiklik yap (bölüm 5). Başka bir alana dokunman gerekiyorsa değişikliği öner ve insana sor.
4. **Sözleşmeler:** Bölüm 3 ve 4 iki geliştiricinin onayı olmadan değişmez. Değişirse bu dosya da aynı PR'da güncellenir.
5. **Rakam kuralı:** Agent (LLM) hiçbir sayıyı kendi hesaplamaz. Chat cevapları ve oluşturulan dosyalardaki bütün adet, gün ve ₺ değerleri tool çıktısından gelir.
6. **Gizli bilgi commit etme:** AWS credential'ları, GitHub token'ı, Kiro IDE URL'si (token içerir), `.env*` dosyaları, `agentcore/.env.local`.
7. **Deploy sadece Kiro IDE Browser terminalinden yapılır.** `agentcore deploy`'u yalnızca Dev A çalıştırır.
8. Küçük ve sık PR aç; her PR tek bir sahiplik alanına dokunsun.

### 0.1 Bugünkü ortam (dünkü workshop'tan farklı; çelişkide bu bölüm geçerli)

| Konu | Bugün |
|---|---|
| Hesap / bölge | `862714237836` (WSParticipantRole), `us-east-1` |
| IDE | Tarayıcıda Kiro (code-server). Dev A workspace'i: `/workshop/ai-agent-hackathon-dev-a`. **Planda `~/environment` geçen yerlerde repo kökü bu klasördür** (her geliştiricinin kendi klasörü/IDE'si olabilir; kod GitHub ile senkronlanır, AWS kaynakları aynı hesapta ortaktır) |
| Kurulu araçlar | node 24, cdk 2.1149, uv/uvx, docker, git, jq. `@aws/agentcore@1.0.3` her IDE'de ayrıca kurulmalı (`npm config set prefix ~/.npm-global`, PATH, `npm install -g @aws/agentcore@1.0.3`) |
| Python | Sistem Python 3.9. Proje için **uv ile Python 3.12** kullanılır |
| Model | Hesapta model allowlist var. Agent modeli: **`global.anthropic.claude-sonnet-5`** (Sonnet 5.5 yasak). Embedding: Titan Embed (izinli). Politikayı değiştirmeye çalışmayın |
| S3 | **`fefo-862714237836-us-east-1`**. Planda geçen `$S3_BUCKET_NAME` ve `REPORTS_BUCKET` bu bucket. KB kaynağı `kb/` öneki, raporlar `reports/` öneki |
| Yardımcı komutlar | `create_knowledge_base`, `enable_anthropic_models`, `create_backend_systems`, `cleanup_workshop` **yok**. KB console'dan oluşturulur |
| Steering / MCP | Workshop steering dosyaları kit'ten `.kiro/steering/`'e konur, ek olarak Kiro'nun yazdığı `environment-today.md` var. MCP: kullanıcı seviyesinde `aws-mcp`; workspace `.kiro/settings/mcp.json`'da `strands-agents` ve `bedrock-agentcore-mcp-server` |
| Hazır skill'ler | **Yok** (`build-chat-ui`, `deploy-chat-ui-to-ecs` dahil). UI, bölüm 6.3'teki gereksinimlere göre skill'siz yazılır |
| UI erişimi | `$IDE_URL` yok. Port proxy'si `VSCODE_PROXY_URI` üzerinden: `https://<ide-host>/proxy/8888/` |
| Güvenlik | Ortam değişkenlerinin tamamını basan komutları çalıştırmayın ve bu çıktıları paylaşmayın (`KIRO_API_KEY` görünüyor) |

---

## 1. Proje özeti

**Tek cümle:** Depodaki lotların SKT'den önce satılıp satılmayacağını tahmin eden, riskli lotları ₺ kaybıyla listeleyen, nedenini açıklayan ve aksiyon kombinasyonlarının kaybı ne kadar düşürdüğünü gösteren ("kayıp şelalesi") bir agent. Aksiyonlar: FEFO önceliği, bayiye özel teklif, kampanya, bağış, tedarikçi iadesi. Onay gelince depo, ticari ekip ve tedarikçi için **taslak** mesajlar hazırlar. Bir **chat arayüzünden** süreç hakkında soru cevaplar, istenince **PDF/Excel rapor** üretip indirme linki verir.

| | |
|---|---|
| **Kullanıcılar** | `depo` rolü: depo planlama sorumlusu · `ticari` rolü: ticari/kampanya ekibi |
| **Asla** | Kendi başına mail/mesaj göndermez (Plan 1'de sadece TASLAK) · onaysız karar kesinleştirmez · kendi başına rakam hesaplamaz · rolünün yetkisi dışındaki aksiyonu onaylatmaz |
| **Veri** | %100 sentetik, deterministik (sabit seed). Demoda "temsili senaryo" olarak sunulur; uydurma istatistik gerçek veri gibi gösterilmez |
| **"Bugün"** | Sabit `as_of_date = 2026-11-25` |

### 1.1 Kapsam planları

| Plan | İçerik | Ne zaman |
|---|---|---|
| **Plan 1 (zorunlu, 16:15'te çalışıyor olmalı)** | FEFO agent'ı · kendi MCP server'ımız `fefo_mcp` (stdio) · KB (politika + süreç rehberi) · onay akışı ve taslaklar · rol hook'u · **chat UI** (lokal, IDE proxy üzerinden) · **PDF/Excel rapor üretimi** (günlük risk raporu dahil, chat'ten istenince) · observability | Şimdi |
| **Plan 2 (zaman kalırsa)** | **Mail ile gönderim:** kişi listesi, mail önizleme, UI'da "Gönder" butonu → Amazon SES · Memory demosu · UI'ın ECS'e deploy'u | Plan 1 saat 15:45'te yeşilse |
| **Plan 3 (zaman yeterse)** | **Zamanlanmış günlük rapor maili** (EventBridge Scheduler → Lambda → agent → SES) · AgentCore Gateway | Plan 2 bittiyse; değilse pitch'te yol haritası |

**Demo anı (temsili):** "SKU-047 (yoğurt): depoda 2.400 adet, SKT'ye 9 gün var. Bayi kabul kuralları yüzünden ~1.440 adet fire riski (~27.000 ₺). FEFO ile 12.000 ₺'ye, Bayi-03/08'e özel teklif ile 4.000 ₺'ye iniyor. Onaylıyor musun?" Onayın ardından üç taslak mesaj gelir. "Bunu PDF yap" denince indirme linki çıkar. CloudWatch'ta MCP tool span'leri görünür.

---

## 2. Mimari ve AWS servisleri

| Katman | Servis | Görevi | Plan | Sahip |
|---|---|---|---|---|
| Geliştirme | **Kiro** (Specs/Quick Spec, steering, hooks, skills) | Her bileşen bir spec ile; `.kiro/specs/` pitch'te kanıt | 1 | Herkes |
| Agent | **Strands Agents + AgentCore Runtime** | Yorum, aksiyon önerisi, taslaklar, soru-cevap | 1 | A |
| Tool'lar | **MCP (stdio):** kendi server'ımız `fefo_mcp` (official `mcp` SDK'daki `FastMCP`) | Risk, profil, simülasyon, taslak ve rapor tool'ları; agent aynı runtime içinde alt süreç olarak başlatıp Strands `MCPClient` ile bağlanır | 1 | B (server) + A (client) |
| Bilgi | **Bedrock Knowledge Base** | `policy.md` + `process_guide.md` (süreç soruları için) | 1 | B (oluşturma) + A (retrieval) |
| Dosyalar | **S3** (`$S3_BUCKET_NAME`, `reports/` öneki) | Üretilen PDF/Excel dosyaları; indirme için süreli (presigned) link | 1 | B (tool) + A (IAM) |
| İzleme | **AgentCore Observability → CloudWatch** | Zorunlu guardrail; demoda MCP tool span'leri | 1 | A |
| Yetki | **AgentCore Identity kalıbı** (Lab 4 hook) | Rol bazlı onay (bölüm 4.10) | 1 | A |
| Arayüz | **Chat UI** (port 8888, `$IDE_URL/proxy/8888/`) | Chat, rapor indirme linkleri, onay butonu | 1 | B |
| Mail | **Amazon SES** | Kullanıcının UI'da onayladığı maili göndermek | **2** | B (+L: adres doğrulama) |
| Hafıza | **AgentCore Memory** (`agentMemory`) | Tercihler, geçmiş kararlar | 2 | A |
| Arayüz | **ECS Fargate + ECR** | UI'ın public deploy'u | 2 | B |
| Zamanlama | **EventBridge Scheduler + Lambda** | Her sabah günlük rapor maili | **3** | A |
| Tool erişimi | **AgentCore Gateway** (yönetilen MCP) + Lambda | `fefo_mcp` tool'larının yönetilen servise taşınması | 3 | A + B |

**Plan 1 akışları:**
- **Chat:** UI → AgentCore Runtime (streaming) → agent → `fefo_mcp` tool'ları ve KB → cevap
- **Veri:** `data/*.csv` → `pipeline/` batch (IDE'de çalışır) → hesaplanmış JSON'lar + `fefo_core` + `fefo_mcp` agent paketine kopyalanır
- **Dosya:** agent → `generate_report_file` → PDF/XLSX → S3 `reports/` → süreli link → chat'te indirme linki

**Tek mantık kaynağı:** Hesap mantığı (doğrulama, özellik, tahmin, risk, simülasyon) **sadece** `pipeline/fefo_core/` içinde yazılır. `fefo_mcp` ve rapor üretimi bu fonksiyonları sarar; hesap başka yerde tekrar yazılmaz.

---

## 3. Veri sözleşmesi (owner: L içerik, B şema doğrulama)

Genel kurallar: CSV, UTF-8, başlık satırı var, ayraç virgül. Tarihler ISO (`YYYY-MM-DD`). Para TRY (ondalık nokta), miktar adet (tam sayı), ağırlık kg. ID formatları: `SKU-001…SKU-100`, `BAYI-01…BAYI-10`, `LOT-<sku>-<n>`, `SUP-01…`.

### 3.1 `data/raw/products.csv` (100 satır)
| Sütun | Tip | Kural |
|---|---|---|
| sku_id | str | benzersiz |
| sku_name | str | Türkçe ürün adı (marka adı kullanılmaz) |
| category | enum | `COLD` (+4) / `DRY` |
| shelf_life_days | int | COLD: 7–21 · DRY: 90–365 |
| unit_cost_try | float | > 0 |
| unit_price_try | float | > unit_cost_try |
| unit_weight_kg | float | "kurtarılan kg" metriği için |
| supplier_id | str | tedarikçi bildirimi için |
| supplier_return_allowed | bool | iade aksiyonu uygun mu |

~30 ürün COLD, ~70 ürün DRY.

### 3.2 `data/raw/dealers.csv` (10 satır)
`dealer_id, dealer_name (anonim, ör. "Bayi-03 Merkez"), region, dealer_type (CHAIN = katı kurallı / TRADITIONAL = esnek)`

### 3.3 `data/raw/dealer_rules.csv` (10 × 2 = 20 satır) — "raftan çıkarma süresi" burada
| Sütun | Tip | Kural |
|---|---|---|
| dealer_id | str | |
| category | enum | COLD / DRY |
| shelf_pull_days | int | SKT'den kaç gün önce bayi ürünü raftan çeker |
| min_days_on_receipt | int | Bayi teslim aldığında en az kaç gün SKT kalmış olmalı. **Kural:** `min_days_on_receipt ≥ shelf_pull_days + 2`. Kesin değeri L belirler |

**Uygunluk kuralı:** Bir lot `d` günü bir bayiye ancak `(skt − d) ≥ min_days_on_receipt` ise sevk edilebilir.

### 3.4 `data/raw/shipments.csv` (~8–15 bin satır)
| Sütun | Tip | Kural |
|---|---|---|
| date | date | `as_of_date − 30` … `as_of_date − 1` |
| dealer_id, sku_id | str | |
| lot_id | str | stokta ya da geçmişte var olan lot; o gün uygunluk kuralını sağlamalı |
| qty_units | int | > 0. Sevkiyat olmayan gün için satır yazılmaz |

### 3.5 `data/raw/inventory_snapshot.csv` (~150–250 satır, `as_of_date` itibarıyla)
`sku_id, lot_id, qty_units, expiry_date, received_date, location_bin`. SKU başına 1–3 lot; `expiry_date` `received_date + shelf_life_days` ile tutarlı. `location_bin` (ör. `A-03-2`) FIFO bozulması senaryosunda "arka göz" bilgisi için.

### 3.6 `data/raw/inbound_plan.csv` (opsiyonel)
`expected_date, sku_id, lot_id, qty_units, expiry_date`. Yakında gelecek taze lotlar (`INBOUND_FRESH_LOT` nedeni için).

### 3.7 `data/raw/calendar.csv` (30 satır)
`date, is_campaign_day (bool), campaign_sku_ids ("SKU-001;SKU-007"), stockout_sku_ids (aynı format)`

### 3.8 `data/config/params.json` (değerleri L, şemayı B belirler)
Tüm varsayımlar burada tutulur, kodun içine gömülmez:
- `elasticity` (kategori bazında; ör. COLD 1.5, DRY 1.2): **satış artışı = elastikiyet × indirim oranı**
- `max_discount_pct_by_role`
- `donation_min_days_to_expiry`
- `supplier_return_min_days_to_expiry`, `supplier_return_credit_pct`
- `forecast_low_confidence_wape` (ör. 0.40)
- `risk_level_thresholds_try` (ör. LOW < 2.000 ≤ MEDIUM < 10.000 ≤ HIGH)

### 3.9 KB dokümanları (`data/policy/`)
- **`policy.md`** (1–2 sayfa): Maddeler numaralı (`POL-1.1` …). Kapsam: FEFO kuralı, bayi kabul kuralları, indirim/kampanya onay limitleri (params ile **aynı sayılar**), bağış ve tedarikçi iadesi koşulları, kim neyi onaylar.
- **`process_guide.md`** (1 sayfa): Chat'teki süreç soruları için. Maddeler `PRC-1.1` … şeklinde numaralı. Kapsam: FEFO süreci adım adım, roller ve sorumluluklar, risk seviyeleri ne anlama gelir, kayıp şelalesi ve rapor nasıl okunur, bir aksiyon onaylanınca ne olur.

### 3.10 `data/DATA_ASSUMPTIONS.md`
Bütün varsayımlar ve gerekçeleri. Jüri sorarsa gösterilir.

### 3.11 `data/scenarios/scenarios.csv` — **ground truth, agent paketine ASLA girmez**
`sku_id, lot_id, scenario_type, expected_reason_code, expected_best_actions, notes`. Sadece testlerde kullanılır.

| reason_code | Kurgu | Beklenen aksiyon |
|---|---|---|
| `FIFO_VIOLATION` | Eski lot arka gözde; son 7 günde hep taze lottan sevk edilmiş | FEFO_PRIORITY |
| `SLOW_MOVER_LARGE_LOT` | Satış hızı düşük, lot büyük | DEALER_OFFER / CAMPAIGN |
| `SHORT_SHELF_LIFE` | COLD ürün, hafta sonu düşüşü | FEFO + DEALER_OFFER |
| `DEALER_STOPPED_ORDERING` | Düzenli alan bayi son 9 gündür almıyor | Bayiye teyit + DEALER_OFFER |
| `STRICT_DEALER_ONLY` | Ürünü ağırlıklı olarak katı kurallı CHAIN bayi alıyor | DEALER_OFFER (esnek bayilere) |
| `DEMAND_DROP_TREND` | Son 7 gün belirgin düşüş | CAMPAIGN |
| `INBOUND_FRESH_LOT` | Yakında taze lot geliyor | FEFO + DEALER_OFFER |
| `UNSAVEABLE` | Kurtarılamaz; kalan miktar bağış ya da iade | DONATION / SUPPLIER_RETURN |

Ayrıca en az 1 **"neredeyse riskli ama değil"** kontrol SKU'su ve en az 1 **düşük güvenli tahmin** (çok dalgalı) SKU'su olmalı.

### 3.12 Tutarlılık kontrolleri (B'nin `validate` adımı, L'nin teslim öncesi kontrolü)
- Bütün ID'ler referans tablolarında var
- Sevkiyat ≤ o lotun o tarihteki stoğu; sevk edilen lot o gün bayi için uygun
- `expiry_date` raf ömrüyle tutarlı; negatif değer yok
- **Senaryo dışı SKU'lar gerçekten risksiz çıkıyor**
- Aynı seed ile yeniden üretim birebir aynı çıktıyı veriyor

### 3.13 (Plan 2) `data/raw/contacts.csv`
`contact_id, name, role (depo/ticari/yonetim/tedarikci/bagis), team, email, subscribed_daily (bool), sendable (bool)`.
- `email` sadece SES'te **doğrulanmış** takım adresleri olabilir; kurgusal kişilerde boş kalır ve `sendable=false` olur.
- Sadece adresini kullanmaya izin veren takım üyelerinin maili yazılır (repo private).

---

## 4. Tool kontratları (owner: A + B ortak; değişiklik iki onayla)

**Genel:**
- 4.1–4.4 ve 4.6 **`fefo_mcp` MCP server'ının tool'larıdır**; 4.5 agent tarafında local tool.
- Girdi ve çıktılar JSON. Para alanları `_try`, miktarlar `_units`, tarihler ISO.
- Hata durumunda çıktı `{"error": {"code": "...", "message": "..."}}` olur; tool exception fırlatmaz.
- `as_of_date` verilmezse varsayılan `2026-11-25`.
- Her tool'un docstring'i (MCP tool açıklaması) ne işe yaradığını ve parametrelerini net anlatmalı; model tool'u buna göre seçer. Sistem prompt'u tool'ları adıyla değil yeteneğiyle anlatmalı (Plan 3'te Gateway'e geçilirse isimler önek alır).

**stdio MCP kuralları:**
- `fefo_mcp` **stdout'a hiçbir şey yazmaz** (`print` yok); stdout MCP protokolüne ait. Loglar stderr'e gider.
- Server, agent'la aynı Python yorumlayıcısıyla modül olarak başlatılır. Hafif import'lar kullanılır (pandas yok).
- **Ortam değişkenleri alt sürece açıkça geçirilmeli.** MCP SDK'nın stdio client'ı varsayılan olarak sadece birkaç temel değişkeni (PATH, HOME gibi) geçirir. AWS kimlik bilgileri, `AWS_REGION` ve `REPORTS_BUCKET` geçirilmezse rapor tool'u S3'e yazamaz. Bu yüzden server parametrelerinde mevcut ortam aktarılır.
- Veri dosyaları paket içindeki göreli yoldan okunur.

### 4.1 `get_expiry_risks`
- **Girdi:** `as_of_date?`, `category?` (COLD/DRY), `min_loss_try?` (varsayılan 0), `top_n?` (varsayılan 10)
- **Çıktı:** `{ as_of_date, total_expected_loss_try, items: [ … ] }`. Her item:
  `sku_id, sku_name, category, lot_id, qty_units, expiry_date, days_to_expiry, location_bin, sellable_window_days, forecast_units_in_window {low, expected, high}, at_risk_units {low, expected, high}, loss_try {low, expected, high}, risk_level (LOW/MEDIUM/HIGH), reason_codes [..], forecast_confidence (HIGH/MEDIUM/LOW), wape`
- Sıralama: `loss_try.expected` azalan.

### 4.2 `get_sku_profile`
- **Girdi:** `sku_id`
- **Çıktı:** `sku` (master alanları), `daily_velocity {avg_7d, avg_30d, trend_pct}`, `weekday_factors {Mon..Sun}`, `forecast_method`, `wape`, `lots [ {lot_id, qty_units, expiry_date, location_bin, last_shipped_date} ]`, `dealers [ {dealer_id, dealer_type, share_pct, avg_daily_units, last_order_date, days_since_last_order, min_days_on_receipt, eligible_for_lot_ids [..]} ]`, `signals [ reason_codes ]`

### 4.3 `simulate_actions`
- **Girdi:** `lot_id`, `actions: [ {type, params} ]` (verilen sırayla uygulanır), `as_of_date?`
  - `FEFO_PRIORITY` — params yok. Lot tüketim sırası "son 7 günün lot karışımı devam eder"den "en eski uygun lot önce"ye çevrilir.
  - `DEALER_OFFER` — `{dealer_ids?: [..], discount_pct}`. Verilmezse en hızlı tüketen ve kuralı uygun 2 bayi seçilir; bu bayilerin talebine `elasticity × discount_pct` kadar artış uygulanır.
  - `CAMPAIGN` — `{discount_pct}`. Tüm uygun bayilerde artış.
  - `DONATION` — `{units?}`. Kalan adet (`donation_min_days_to_expiry` şartıyla).
  - `SUPPLIER_RETURN` — `{units?}`. Ürün izinliyse ve gün şartı tutuyorsa.
- **Baseline (aksiyonsuz durum):** Talep tahmini (`expected`), bayi payları ve uygunluk kuralı, son 7 günün lot karışımı.
- **Çıktı:** `{ lot_id, baseline_loss_try, steps: [ {action, params, feasible, infeasible_reason?, units_saved, loss_after_try, action_cost_try, net_benefit_try, kg_saved, policy_refs [..]} ], final_loss_try, total_net_benefit_try }`
  - `action_cost_try` = indirimli satılan adet × birim fiyat × indirim oranı
  - `net_benefit_try` = kayıptaki azalma − aksiyon maliyeti
  - DONATION ₺ kaybını azaltmaz; `kg_saved` üretir
  - SUPPLIER_RETURN `units × unit_cost × credit_pct` kadar geri kazanım sağlar
- Fizibilite `params.json`'dan kontrol edilir; `policy_refs` ilgili POL maddelerini döner.

### 4.4 `create_action_drafts`
- **Girdi:** `lot_id`, `approved_actions: [ {type, params} ]`, `approver_actor_id`
- **Çıktı:** `{ decision_id, status: "DRAFT", drafts: [ {audience: WAREHOUSE|COMMERCIAL|SUPPLIER|DEALER|DONATION_PARTNER, subject, body} ], summary {final_loss_try, total_net_benefit_try, kg_saved} }`
- Her taslağın başında **"TASLAK — gönderilmedi"** yazar.
- Kararlar bir oturum boyunca `decision_id` ile raporlarda kullanılabilecek şekilde saklanır (S3 `decisions/<decision_id>.json`).

### 4.5 `search_policies` (KB retrieval, agent tarafında local tool; owner A)
- **Girdi:** `query`
- **Çıktı:** `policy.md` ve `process_guide.md` içinden ilgili pasajlar ve madde numaraları (POL-x / PRC-x)
- KB hazır değilse **fallback:** paketlenmiş iki md dosyasında madde arayan local tool (aynı kontrat).

### 4.6 `generate_report_file` (Plan 1; `fefo_mcp`'de; owner B)
- **Girdi:**
  - `report_type`:
    - `DAILY_RISK` — günlük risk raporu: toplam beklenen kayıp, en riskli N lot, neden dağılımı, bekleyen kararlar
    - `LOT_ACTION_PLAN` — tek lotun detayı, kayıp şelalesi, onaylı aksiyonlar ve taslak metinleri
    - `RISK_TABLE` — bütün riskli lotların tablosu
  - `format`: `pdf` | `xlsx`
  - `lot_id?` (LOT_ACTION_PLAN için zorunlu), `decision_id?`
  - `summary_text?`: agent'ın yazdığı yorum paragrafı. Dosyada ayrı bir "Yorum" bölümüne konur; **yeni rakam içeremez**, rakamlar her zaman tool verisinden basılır.
  - `as_of_date?`
- **Çıktı:** `{ file_id, file_name, format, s3_key, download_url, expires_in_sec, size_bytes }`
- **Uygulama kuralları:**
  - **PDF:** `fpdf2` (saf Python). **Türkçe karakterler için Unicode bir TTF font paketlenip gömülmeli** (ör. DejaVuSans). Varsayılan core fontlar ş, ğ, ı, İ karakterlerini basamaz.
  - **Excel:** `openpyxl` (saf Python). Başlık satırı, sayı biçimleri, ₺ sütunları.
  - Dosya `s3://$REPORTS_BUCKET/reports/<as_of_date>/<file_id>.<ext>` adresine yazılır. `download_url` ~1 saatlik presigned URL'dir (runtime rolünün oturum süresiyle sınırlı, chat'te hemen kullanılmak için).
  - Dosya adı okunur olmalı: `FEFO_Gunluk_Risk_2026-11-25.pdf` gibi.

### 4.7 (Plan 2) Mail: `list_contacts`, `prepare_email` ve UI gönderimi
- **`list_contacts`** (`fefo_mcp`): girdi `role?`, `query?` → `[ {contact_id, name, role, team, sendable} ]`. **Mail adreslerini modele vermez**; model kişileri sadece `contact_id` ve isimle bilir.
- **`prepare_email`** (`fefo_mcp`): girdi `to_contact_ids [..]`, `subject`, `body`, `attachment_file_ids? [..]`, `email_type` (`ADHOC` | `DAILY_REPORT`), `requested_by_actor_id` → `{ email_id, status: "PENDING_CONFIRMATION", preview {to_names, subject, body, attachments} }`
  - Kayıt `s3://…/emails/<email_id>.json`'a yazılır.
  - Alıcılar **sadece kişi listesinden**, `sendable=true` olanlar. Serbest yazılmış bir adres kabul edilmez.
- **Gönderim agent tool'u değildir.** UI önizleme kartında **"Gönder"** butonunu gösterir. Kullanıcı basınca UI backend'i (`POST /api/emails/<email_id>/send`) SES ile gönderir: ek dosyalar S3'ten alınıp MIME eki olarak eklenir. Ardından kayıt `SENT` olarak işaretlenir. Böylece agent hiçbir koşulda tek başına mail atamaz.
- **SES sandbox:** Gönderen ve **alıcı adreslerinin hepsi** SES'te doğrulanmış olmalı (event hesabında production erişimi alınamaz). Doğrulama için her takım üyesi gelen linke tıklar.

### 4.8 (Plan 3) Zamanlanmış günlük rapor
- EventBridge Scheduler (her gün 08:00, Europe/Istanbul) → Lambda → AgentCore Runtime'ı `actorId: system-scheduler` ile çağırır. Agent `generate_report_file(DAILY_RISK, pdf)` ve `prepare_email(email_type=DAILY_REPORT, alıcılar: subscribed_daily=true)` çağırır.
- Lambda, çağrı bittikten sonra S3'te o güne ait `DAILY_REPORT` tipindeki bekleyen maili bulur ve SES ile gönderir. Agent'ın metin çıktısı parse edilmez; el sıkışma S3 kaydı üzerinden olur.
- **Gerekçe:** Abonelik, o sabit rapor için önceden verilmiş insan onayıdır. Ad-hoc mailler her zaman butonla gider.
- Demoda zamanlama yetişmezse aynı akış UI'daki "Günlük raporu şimdi hazırla" ile manuel gösterilir.

### 4.9 Agent'ın soru-cevap davranışı (Plan 1)
- **Süreç soruları** ("FEFO nasıl işliyor?", "Kampanyayı kim onaylar?") → `search_policies` ile cevap ve madde numarası (PRC-x / POL-x)
- **Veri soruları** ("Bugün en riskli 5 ürün?", "Bayi-05 neden riskli?") → ilgili tool
- **Dosya istekleri** ("Bunu Excel olarak ver", "Günlük raporu PDF yap") → `generate_report_file` ve chat'te indirme linki
- KB'de ya da tool çıktısında olmayan bir bilgiyi uydurmaz; "bu bilgi elimdeki verilerde yok" der.

### 4.10 Rol bazlı onay (Identity, Lab 4 hook kalıbı)
- Payload'daki `actorId` formatı: `<rol>-<isim>` (ör. `depo-ahmet`, `ticari-zeynep`; Plan 3'te `system-scheduler`). Sadece harf, rakam ve tire.
- Strands `BeforeToolCallEvent` hook'u `create_action_drafts`'i (Plan 2'de `prepare_email`'i de) kontrol eder. Rolün yetkisi dışında bir aksiyon varsa çağrıyı iptal eder ve agent'a "bu aksiyon için `ticari` onayı gerekir" sonucunu döner. Konuşma devam eder.

| Aksiyon | depo | ticari | system-scheduler (Plan 3) |
|---|---|---|---|
| FEFO_PRIORITY | ✅ | ✅ | ❌ |
| DEALER_OFFER, CAMPAIGN | ❌ | ✅ (`max_discount_pct_by_role` içinde) | ❌ |
| DONATION, SUPPLIER_RETURN | ✅ | ✅ | ❌ |
| generate_report_file | ✅ | ✅ | ✅ (sadece DAILY_RISK) |
| prepare_email (Plan 2) | ✅ ADHOC | ✅ ADHOC | ✅ sadece DAILY_REPORT, sadece abonelere |

---

## 5. Repo yapısı, sahiplik ve Git kuralları

**Repo kökü = Kiro IDE Browser'daki `~/environment`.** Workshop yolları, steering dosyaları ve Lab 7 guardrail'i ("proje `~/environment` içinde `agentcore create` ile oluşturulmuş") birebir korunur.

```
~/environment/                      (repo kökü, private GitHub repo)
├── TEAM_PLAN_FEFO_AGENT.md         (bu dosya)                                         owner: A
├── HACKATHON_KIRO_CONTEXT.md       (referans)                                         owner: A
├── README.md                                                                          owner: A
├── .kiro/
│   ├── steering/                   agentcore-deployment.md, strands-agent-coding.md, fefo-domain.md   owner: A
│   ├── skills/                     (workshop'un hazır skill'leri; dokunulmaz)
│   └── specs/                      her bileşenin spec'i, kendi sahibince
├── data/                           raw/, config/, policy/ (policy.md, process_guide.md), scenarios/, DATA_ASSUMPTIONS.md   owner: L
├── data-gen/                       sentetik veri üretici (sabit seed)                 owner: L (B destek)
├── pipeline/
│   ├── fefo_core/                  validate, features, forecast, risk, simulate       owner: B
│   ├── fefo_mcp/                   kendi MCP server'ımız: tool'lar + rapor üretimi (+ assets/ TTF font)   owner: B
│   └── export adımı                agent paketine kopyalar                            owner: B
├── FefoAgent/                      agentcore projesi (agentcore/, app/agent/…)        owner: A
│   └── app/agent/fefo_core/, fefo_mcp/, data/   export kopyası (elle düzenlenmez)     üretir: B
│       app/agent/fefo_mcp_stub/    walking skeleton için sahte MCP server (export gelince silinir)   owner: A
├── chat-ui/                        Lab 6 kalıbı UI (+ Plan 2: mail önizleme/gönderim backend'i)      owner: B
├── scheduler/                      (Plan 3) EventBridge + Lambda                      owner: A
└── tests/eval/                     test soruları, beklenen cevaplar, sonuçlar        owner: L + A
```

**Kurulum (Dev A, IDE terminalinde, bir kez):**
1. GitHub'da **private** repo aç, diğer iki kişiyi collaborator ekle.
2. `~/environment`'ta git init yap; `.gitignore`'u ekle; ilk commit (bu dosya, context md, steering, skills); remote ekle, push et. Push için kişisel bir fine-grained token kullanılır; token repoya ya da dosyaya yazılmaz.
3. Proje iskeleti: `agentcore create --name FefoAgent --template agent-python-strands --skip-git`. **`--skip-git` şart**; yoksa repo içinde ikinci bir git reposu oluşur.
4. Diğerleri repoyu kendi bilgisayarlarına clone eder. Lokal geliştirme serbest, ama deploy IDE'den yapılır.

**`.gitignore` en azından şunları içermeli:** `.venv/`, `__pycache__/`, `*.pyc`, `node_modules/`, `cdk.out/`, `.env*`, `**/agentcore/.env.local`, `**/agentcore/aws-targets.json`, `.DS_Store`, `traces/` (indirilen trace dosyalarını bu klasöre alın), lokalde üretilmiş `*.pdf` ve `*.xlsx` test çıktıları.

**Branch ve PR kuralları:**
- `main` her zaman deploy edilebilir durumda olmalı. **Plan 2/3 işleri ayrı branch'te yapılır** ve sadece çalışıyorsa merge edilir.
- Branch adları: `agent/*` (A), `pipeline/*`, `ui/*` (B), `data/*` (L)
- Küçük PR, en geç ~1 saatte bir merge. Kendi alanına dokunan PR'ı sahibi merge edebilir. Sözleşmeye (bölüm 3–4) ya da başka bir alana dokunan PR ikinci kişinin onayını ister.
- **Çakışma noktaları:**
  - Sadece A'nın: `FefoAgent/agentcore/agentcore.json`, `FefoAgent/app/agent/pyproject.toml`, `.kiro/steering/`
  - Sadece B'nin: export klasörleri
  - `fefo_mcp` yeni bir runtime bağımlılığı (ör. `fpdf2`, `openpyxl`) gerektirirse B bunu A'ya söyler, `pyproject.toml`'a A ekler.
- **Deploy ritüeli (IDE):** önce `git pull`, sonra deploy, sonra verify. Deploy sonrası çıkan değişiklikler commit edilir.

**Tek IDE kuralları:**
- Kiro IDE takım başına tek. A chat panelini kullanır. B IDE'de çalışacaksa ikinci bir terminalde `kiro-cli chat`'i **`~/environment`'tan** başlatır ve brief'te klasörünü belirtir.
- Aynı dosyalarda aynı anda iki Kiro oturumu çalışmaz.
- Lokal başka AI asistanları kullanılsa bile **agent, `fefo_mcp` ve UI için en az birer Kiro spec'i** `.kiro/specs/`'te bulunmalı.

---

## 6. Roller ve görevler

### 6.1 Lojistik (L) — Veri içeriği, KB dokümanları, test, pitch · [isim]
**Sahip olduğu yerler:** `data/`, `data-gen/` (içerik), `tests/eval/` (sorular ve beklenen cevaplar)

**Plan 1:**
1. **(12:50'ye kadar)** `params.json` değerleri, `dealer_rules` (raftan çekme süreleri, kabul kuralları), bayi profilleri, **senaryo listesi** (3.11).
2. **(13:00)** `policy/policy.md`, numaralı maddelerle. **B'nin KB'yi başlatabilmesi için öncelikli.**
3. **(13:30)** Veri v1: bütün CSV'ler, `DATA_ASSUMPTIONS.md`, `scenarios.csv`. Tutarlılık kontrolleri (3.12) geçmiş olmalı. Sıkışırsan önce 30 gün ve 8 senaryo.
4. **(14:00)** `policy/process_guide.md` (KB'nin ikinci dokümanı, chat'teki süreç soruları için).
5. **(14:30)** `tests/eval/`: 10–12 test sorusu ve beklenen cevaplar. Veri soruları, süreç soruları ve dosya istekleri dahil. Kontrol için birkaç sayıyı Excel'de bağımsız hesapla.
6. **(14:30–16:00)** Testleri UI'dan çalıştır; üretilen PDF/Excel'leri aç ve kontrol et (rakamlar, Türkçe karakterler); hataları GitHub issue olarak aç.
7. **(15:30–17:10)** Pitch: problem, iş etkisi, demo senaryosu. Sunumu yap.

**Plan 2 (15:45 kontrol noktası geçilirse):** `contacts.csv`; SES console'da takım adreslerini **doğrulama** (her kişi gelen linke tıklar).

DoD: Veri aynı seed ile tekrar üretilebiliyor, kontroller geçiyor, her senaryo farklı nedenle riskli, kontrol SKU'su risksiz, iki KB dokümanı numaralı maddelerle hazır.

### 6.2 Dev A — Agent ve AgentCore · [isim]
**Sahip olduğu yerler:** `FefoAgent/` (export klasörleri hariç), `.kiro/steering/`, kök md dosyaları, `scheduler/` (Plan 3), `tests/eval/` (çalıştırma)
**Servisler:** Kiro, AgentCore Runtime, MCP (client), Observability, Identity (hook), KB retrieval, S3 (IAM); Plan 2: Memory; Plan 3: EventBridge, Lambda, Gateway

**Plan 1:**
1. **(12:35–12:50)** Repo kurulumu (bölüm 5), ortam doğrulaması, `fefo-domain.md` steering'i: sözlük, rakam kuralı, "asla gönderme", Türkçe çıktı, ₺ formatı, rol kuralları, stdio MCP kuralları.
2. **(12:50–13:30) Walking skeleton (Kiro Quick Spec):**
   - Scaffold (`--skip-git`)
   - `app/agent/fefo_mcp_stub/`: bölüm 4 kontratına uyan sabit cevaplar dönen sahte bir MCP server
   - Strands `MCPClient` ile **stdio** bağlantısı: `_get_agent` içinde lazy başlatılır; server aynı Python yorumlayıcısıyla modül olarak açılır; **ortam değişkenleri alt sürece geçirilir**; tool'lar agent'a eklenir
   - Sistem prompt'unun ilk hâli
   - `UNIFIED_TRACES_DESTINATION_ENABLED=true`
   - Deploy ve **3 verify yeşil** (bölüm 9). Tool guardrail'i "MCP server" maddesiyle karşılanır.
3. **(13:30–14:00)** Prompt ve karar akışı stub üzerinde. Runtime `envVars`'a `REPORTS_BUCKET` (= `$S3_BUCKET_NAME`) ekle. `additionalPolicies`: S3'te `reports/*` ve `decisions/*` öneklerine `s3:PutObject`/`s3:GetObject`.
4. **(14:00–15:00) Gerçek akış (Kiro Spec):**
   - B'nin export'u gelince stub silinir; client gerçek `fefo_mcp`'ye bağlanır
   - Karar akışı: risk listesi → neden → simülasyon → öneri → onay → taslaklar
   - Düşük güvenli tahmin uyarısı
   - KB retrieval tool'u, `KNOWLEDGE_BASE_ID` env var'ı, `additionalPolicies` (`bedrock:Retrieve` KB ARN'ine, `bedrock:RetrieveAndGenerate` "*" üzerine); KB hazır değilse fallback
   - Rol hook'u (4.10)
   - `pyproject.toml`'a B'nin istediği bağımlılıklar (`fpdf2`, `openpyxl`)
5. **(15:00–16:00)** Soru-cevap ve dosya davranışı (4.9): süreç soruları madde numarasıyla cevaplanıyor, dosya isteklerinde link veriliyor. Eval düzeltmeleri, deploy.
6. **(16:00–16:15)** Son deploy ve verify. **16:15 freeze.**
7. **(16:15–17:10)** Trace ekran görüntüleri (MCP tool span'leri), yedek demo kaydı, `.kiro/specs` düzeni, demo sürücülüğü.

**Plan 2:** Memory tercih senaryosu (template'te hazır; 60 sn bekleme ile demo). Hook'u `prepare_email` için genişletme.
**Plan 3:** `scheduler/` (EventBridge Scheduler + Lambda, 4.8; Lambda rolüne `bedrock-agentcore:InvokeAgentRuntime`, S3, `ses:SendRawEmail`) · Gateway.

**Kritik kurallar** (ayrıntı: context md bölüm 6):
- Model ID keşfedilir ve `global.` önekiyle kullanılır
- Import: `from bedrock_agentcore.runtime import BedrockAgentCoreApp`
- Lazy init
- Runtime'da sadece runtime bağımlılıkları; pandas gibi ağır paketler yok
- IAM izinleri sadece `additionalPolicies` ile
- `--session-id` en az 33 karakter
- Test prompt'larında Türkçe kesme işareti yok (CLI payload'ını bozar)
- AgentCore CLI 1.0.3'ü güncelleme

### 6.3 Dev B — Pipeline, MCP server, raporlar ve UI · [isim]
**Sahip olduğu yerler:** `pipeline/`, `chat-ui/`, `FefoAgent/app/agent/{fefo_core,fefo_mcp,data}/` (export ile)
**Servisler:** MCP (server), S3, Bedrock KB; Plan 2: SES, ECS/ECR; Plan 3: Lambda (Gateway)

**Plan 1:**
1. **(12:35–13:30) `pipeline/fefo_core`** (saf Python, pandas yok; lokal geliştirilebilir):
   - `validate` (3.12 kontrolleri)
   - `features`: eksik günleri 0 ile doldur, bayi payları, kategori bazında haftanın günü faktörü, trend, sipariş kesen bayi, FIFO bozulması sinyali
   - `forecast`: SKU toplamı seviyesinde; son 7 gün backtest; 2–3 basit yöntem arasından seçim; düşük/beklenen/yüksek, WAPE
   - `risk`: uygunluk kuralı, etkili pencere, ₺ kaybı
   - `simulate` (4.3)
   - Küçük bir fixture ile birim testleri
   - Paralelde IDE'de hızlı test: S3'e yazma ve presigned URL üretme çalışıyor mu?
2. **(12:50–13:45) `pipeline/fefo_mcp`** — kendi MCP server'ımız:
   - Official `mcp` SDK'daki `FastMCP` (Strands'in bağımlılığı olarak zaten kurulu) ile tool'lar 4.1–4.4. Her biri `fefo_core`'u çağırır ve kontrata birebir uyar.
   - stdio transport; **stdout'a print yok**, loglar stderr'e; hatalar `{"error": …}` formatında
   - Docstring'ler net olmalı
   - **Test kolaylığı:** `fefo_mcp`'yi IDE'de Kiro'ya da MCP server olarak ekleyin (`~/.kiro/settings/mcp.json`). Tool'ları doğrudan Kiro chat'ten deneyebilirsiniz; demoda da gösterilebilir.
3. **(13:00–14:00) Knowledge Base:** `policy.md` gelince `$S3_BUCKET_NAME/policy/` altına yükle, KB'yi oluştur (console quick create ya da Kiro ile; vector store dakikalar sürer, embedding model erişimini kontrol et). `process_guide.md` gelince (14:00) aynı data source'a ekleyip sync et. KB ID'yi A'ya ver.
4. **(13:30–14:00) Export v1:** Veri v1 ile pipeline'ı çalıştır. JSON'ları `FefoAgent/app/agent/data/`'ya, `fefo_core` ve `fefo_mcp`'yi `FefoAgent/app/agent/` altına kopyalayan tek komutluk export. Kopya tek yönlü, elle düzenlenmez. `scenarios.csv` **kopyalanmaz.** A'ya haber ver.
5. **(14:00–15:00) `generate_report_file` (4.6):**
   - PDF (`fpdf2` + gömülü Unicode TTF) ve XLSX (`openpyxl`)
   - Üç rapor tipi: DAILY_RISK, LOT_ACTION_PLAN, RISK_TABLE
   - S3 `reports/`'a yazma ve presigned link
   - Bağımlılıkları A'ya bildir. Export v2.
   - Lokal test: üretilen dosyaları açıp Türkçe karakterleri ve rakamları kontrol et.
6. **(15:00–16:00) Chat UI** (lokal, `$IDE_URL/proxy/8888/`):
   - `build-chat-ui` skill'ini temel alın: port 8888, `/health`, relative path'ler, `AGENTCORE_ENDPOINT` ve `AWS_REGION` env, streaming
   - Ekler: rol seçici (`actorId`), markdown tabloları, **indirme linklerini buton olarak gösterme**, "Onayla" butonu (aynı oturuma "Onaylıyorum" mesajı yollar; mantık agent'ta kalır), hazır soru önerileri ("Bugün riskli ürünler?", "Günlük raporu PDF yap", "FEFO süreci nasıl işliyor?")
7. **(16:00–16:15)** UI düzeltmeleri. **16:15 freeze.**

**Plan 2 (15:45 kontrol noktası geçilirse, ayrı branch):**
- `list_contacts`, `prepare_email` (4.7)
- UI'da mail önizleme kartı ve "Gönder" butonu; backend'de SES gönderimi (ekli dosyalarla)
- SES test gönderimi, ECS deploy (`deploy-chat-ui-to-ecs` skill'i)

**Plan 3:** Gateway için tool Lambda'ları.

DoD: Pipeline aynı veriyle deterministik sonuç veriyor; senaryo SKU'ları beklenen `reason_code` ile çıkıyor; `fefo_mcp` tool'ları kontrata uyuyor ve Kiro'dan çağrılabiliyor; PDF/Excel Türkçe karakterlerle doğru açılıyor ve rakamları tool çıktısıyla aynı; UI `/health` 200 dönüyor ve indirme linkleri çalışıyor.

---

## 7. Zaman planı ve kontrol noktaları

Teslim ≈17:10. Saatler gerçek bitiş saatine göre kaydırılır.

| Saat | L | Dev A | Dev B |
|---|---|---|---|
| 12:35–12:50 | Params, kurallar, senaryolar | Repo kurulumu, steering | `fefo_core` iskeleti; S3 presign testi |
| 12:50–13:30 | Policy (13:00), veri v1 (13:30) | **Walking skeleton (stub MCP, stdio) → 3 verify yeşil** | `fefo_core` + `fefo_mcp`; policy gelince KB başlat |
| **13:30 ✦ K1** | Veri v1 merge | Skeleton yeşil mi? | Pipeline'ı veri v1 ile çalıştır |
| 13:30–14:00 | `process_guide.md` | Prompt/akış (stub), S3 IAM, env var'lar | **Export v1** → A'ya haber |
| 14:00–15:00 | Eval soruları (14:30), testler | Gerçek `fefo_mcp`, onay, taslaklar, KB retrieval, rol hook'u | `generate_report_file` (PDF/XLSX → S3) → **export v2** |
| **14:45 ✦ K2** | — | Gerçek `fefo_mcp` ile deploy var mı? | — |
| 15:00–16:00 | Testler (dosyalar dahil), pitch | Soru-cevap ve dosya davranışı, eval düzeltmeleri | **Chat UI** (chat, linkler, onay butonu) |
| **15:45 ✦ K3** | **Plan 2'ye geçiş kararı** | | |
| 16:00–16:15 | Prova | Son deploy + verify | UI düzeltmeleri |
| **16:15 ✦ Freeze** | | | |
| 16:15–17:10 | **Sunum** | Demo sürücüsü, trace, yedek kayıt | Demo desteği; (Plan 2 branch'i hazırsa merge) |

**Kurallar:**
- **K1 (13:30):** Walking skeleton deploy edilmemiş ve verify yeşil değilse herkes yardıma gelir.
- **K2 (14:45):** Gerçek `fefo_mcp` ile deploy yoksa UI ve rapor işleri bekler; herkes MVP'ye odaklanır.
- **K3 (15:45):** Plan 1'in bütün parçaları (chat, dosya, onay, KB) çalışıyorsa Plan 2 ayrı branch'te başlar ve 16:40'ta merge edilmemişse bırakılır. Plan 3 bugün büyük ihtimalle yetişmez; pitch'te yol haritası olarak anlatılır.
- 16:15'ten sonra `main`'e yeni özellik girmez, sadece hata düzeltilir.

---

## 8. Kesme sırası ve fallback'ler

**Kesme sırası** (önce kesilen en başta):
1. Plan 3'ün tamamı (zamanlanmış mail, Gateway)
2. Plan 2'nin tamamı (mail gönderimi, Memory demosu, ECS)
3. Rol hook'u
4. Excel formatı (sadece PDF kalır)
5. Chat UI → demo terminalden yapılır (okunur çıktı filtresiyle; bu durumda dosya linkleri terminalde basılır)

**Kesilmeyecekler:** Runtime deploy · observability · kendi MCP server'ımız (`fefo_mcp`, stdio) · politika ve süreç bilgisi (KB ya da fallback) · onay akışı ve taslaklar · en az PDF rapor.

| Sorun | Fallback |
|---|---|
| stdio MCP runtime'da açılmıyor | `agentcore logs runtime --since 15m`. Genelde stdout'a yazan bir `print`, yanlış modül yolu ya da alt sürece geçirilmeyen env var. Çözülemezse aynı `fefo_core` fonksiyonlarını local `@tool` olarak bağla; kontrat aynı kalır |
| Rapor S3'e yazamıyor | `REPORTS_BUCKET` env var'ı ve `additionalPolicies`'te S3 izni var mı; env alt sürece geçiyor mu? Son çare: rapor UI backend'inde üretilir (aynı `fefo_core` verisiyle) |
| PDF'te Türkçe karakterler bozuk | TTF font gömülü mü? Core font kullanılmamalı |
| KB oluşturulamıyor | İki md dosyası paketlenir, local `search_policies` (aynı kontrat) |
| Model erişim hatası | `enable_anthropic_models`, 2–6 dk bekle |
| (Plan 2) SES izni yok ya da adres doğrulanamıyor | Mail önizlemesi gösterilir ve indirilebilir `.eml` olarak sunulur; "gönderim simüle" diye etiketlenir |
| Canlı demo bozuldu | Yedek kayıt |

---

## 9. Test ve doğrulama

**Lab 7 guardrail'leri** (her deploy sonrası, `~/environment/FefoAgent` içinde):
1. `agentcore status` → runtime `deployed` ve ARN görünüyor
2. `agentcore invoke --runtime agent --payload '{"prompt":"Bugun riskli urunler neler? Bir aracini cagir ve sonucu goster.","actorId":"depo-test"}'` → tool verisi içeren cevap
3. `aws logs describe-log-groups --log-group-name-prefix /aws/bedrock-agentcore/runtimes/ --query "logGroups[].logGroupName" --output text` → `…-DEFAULT` log grubu var; `agentcore traces runtime list --since 15m` invoke'un trace'ini gösteriyor
4. `.kiro/specs/<isim>/` agent'ın nasıl yapıldığını belgeliyor
5. **MCP kontrolü:** `agentcore traces runtime get <trace-id>` çıktısında `fefo_mcp` tool çağrılarının span'leri görünüyor

**`fefo_mcp` tek başına (B):** Kiro'ya MCP server olarak eklendiğinde tool'lar listeleniyor; her tool kontrata uygun çıktı veriyor; hatalı girdide `{"error": …}` dönüyor.

**Eval seti** (`tests/eval/`, ground truth = `scenarios.csv`):
- **Rakamlar:** agent'ın söylediği ve dosyaya basılan sayılar tool çıktısıyla birebir aynı
- **Neden ve aksiyon:** her senaryonun nedeni doğru, aksiyon önerisi beklenenle uyumlu
- **Kontroller:** kontrol SKU'su riskli denmiyor; düşük güvenli tahmin işaretleniyor
- **Süreç soruları:** "FEFO nasıl işliyor?", "Kampanyayı kim onaylar?" → doğru cevap ve PRC/POL madde numarası; bilinmeyen soruda uydurmuyor
- **Dosyalar:** "Günlük raporu PDF yap" ve "Risk tablosunu Excel olarak ver" → çalışan indirme linki; dosya açılıyor; Türkçe karakterler doğru
- **Gönderim:** "Maili gönder" isteği reddediliyor, sadece taslak hazırlanıyor (Plan 2'de: önizleme + buton)
- **Roller:** `depo` rolü kampanya onaylayamıyor, `ticari` onaylayabiliyor
- **What-if:** "%10 yerine %20 indirim olsa?" sorusuna tablo yeniden hesaplanıyor
- (Plan 2) Serbest yazılmış bir mail adresine gönderim isteği reddediliyor; doğrulanmış takım adresine buton ile mail ulaşıyor

---

## 10. Demo akışı (3–4 dk, chat UI üzerinden)

1. **Problem** (L): soğuk zincirde SKT kaynaklı fire. Temsili senaryo olduğu açıkça söylenir.
2. **Süreç sorusu:** "FEFO süreci nasıl işliyor, kampanyayı kim onaylar?" → madde numaralı cevap
3. "Bugün riskli ürünler neler?" → top 10 ve toplam ₺ kaybı
4. Bir lot için neden (ör. FIFO bozulması: "eski lot A-03-2 arka gözde, son 7 gündür taze lot sevk ediliyor") ve kayıp şelalesi
5. `depo` rolüyle kampanya onaylanmaya çalışılır → reddedilir; `ticari` rolüyle onaylanır → üç TASLAK mesaj
6. "Bu planı PDF yap" ve "Günlük raporu hazırla" → indirme linkleri, dosyalar ekranda açılır
7. (Plan 2 hazırsa) "Raporu Ayşe'ye gönder" → önizleme → **Gönder** → mail bir takım üyesinin telefonuna canlı düşer
8. CloudWatch'ta trace (**kendi MCP server'ımızın tool span'leri**) ve `.kiro/specs` klasörü
9. Mimari slaydı (bölüm 2) ve yol haritası: zamanlanmış sabah raporu maili (Plan 3), `fefo_mcp`'nin AgentCore Gateway'e taşınması, gerçek veri bağlantısı, aynı veriyle nakliye kapasite ajanı
