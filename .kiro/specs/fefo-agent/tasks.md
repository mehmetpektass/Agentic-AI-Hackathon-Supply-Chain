# Implementation Plan: FEFO Agent (Dev A, Plan 1)

## Overview

Bu plan yalnızca Dev A Plan 1 kapsamını uygular. Plan 2 ve Plan 3 kapsam dışıdır ve görevi yoktur (Requirement 18.9, 18.10).

Uygulama dili Python 3.12'dir (`.python-version`, uv ile kurulu) ve tasarımın dili ile aynıdır. Dil sorusu sorulmaz. `pytest` yalnızca `[dependency-groups] dev` içinde tutulur ve runtime bağımlılıklarına girmez (Requirement 5.7).

Bu oturumda yalnızca **walking skeleton** uygulanır: 1.1, 1.2, 3.1, 3.2, 4.1, 4.2, 4.3, 4.4, 5.1 (Tool kontrat testleri) ve 11.1, ayrıca 4.4 içinde minimum sistem prompt. Diğer görevler sonraki oturumlara kalır ve açık durur.

Genel kurallar:

- Kullanıcı (Dev A) bu oturumda `agentcore deploy`, `invoke`, `status` ve `logs` komutlarının asistan tarafından çalıştırılmasını açıkça yetkilendirmiştir. Asistan bu komutları yalnızca bu yetkiyle çalıştırır. Komutlardan önce `~/.npm-global/bin` PATH'te olmalıdır (Requirement 16.1).
- Alt sürece (Stub_MCP stdio) mevcut ortamın kopyası geçirilir (AWS kimlik değişkenleri, `AWS_REGION`, `REPORTS_BUCKET` dahil). Ortam hiçbir zaman ekrana veya loga basılmaz. `env`, `printenv`, `set` çalıştırılmaz (Requirement 6.4).
- `.kiro/steering/` altındaki mevcut orijinal dosyalar değiştirilmez (Requirement 3.6).
- `FefoAgent/app/agent/fefo_core`, `fefo_mcp` ve `data` klasörleri elle düzenlenmez (Requirement 6.12).
- Tool_Contract iki geliştirici onayı olmadan değişmez (Requirement 7.17).
- Dev A sahiplik alanı dışındaki bir dosya gerekirse dosya değiştirilmez, öneri Kullanıcı'ya iletilir (Requirement 1.7).
- AWS kimlik bilgisi, GitHub token'ı ve Kiro IDE URL'si hiçbir izlenen dosyaya yazılmaz (Requirement 1.4).
- AgentCore_CLI 1.0.3 güncellenmez (Requirement 2.6).
- Modül adları (`config.py`, `role_hook.py`, `mcp_adapter.py` vb.) tasarımdaki varsayımdır. Scaffold sonrası gerçek yapıya (`main.py`, `parse.py`, `model/load.py`, `memory/session.py`) göre uyarlanır.

## Test Kapsamı Kararı

- **Aktif**: yalnızca Tool kontrat testleri: görev 5.1 (zorunlu) ve Stub_MCP kontrat doğrulaması. Fefo_MCP geçişinde aynı kontrat testleri görev 15.4 ile koşar.
- **Şimdilik atlandı**: tüm opsiyonel (`*`) testler, tüm property-based test görevleri ve eval testleri (13.x). Bu görevlerde onay kutusu işaretlenmez, satırda "(şimdilik atlandı)" yazar. Gereksinimler geçerliliğini korur, testler bu aşamada yazılmaz.

## Kesin Değerler ve Bekleyen Girdiler

| Değer | Karar |
|---|---|
| Workspace/repo kökü | `/workshop/ai-agent-hackathon-dev-a`. Scaffold bu kökte `FefoAgent/` olarak oluşur: `agentcore create --name FefoAgent --template agent-python-strands --skip-git` |
| Model_ID | `global.anthropic.claude-sonnet-5` (hesapta allowlist var, `sonnet-5-5` yasak). Görev 3.2 bu değeri converse ile doğrular, başka model seçmez |
| `REPORTS_BUCKET` | `fefo-862714237836-us-east-1` (`S3_BUCKET_NAME` env yok, bu ad kullanılır) |
| Python | 3.12 (`.python-version`) |
| agentcore.json envVars | `UNIFIED_TRACES_DESTINATION_ENABLED=true`, `REPORTS_BUCKET`, `MODEL_ID`, `MCP_BACKEND=stub` |
| Max_Discount_Pct_By_Role | `app/agent/data/params.json` içindeki `max_discount_pct_by_role`. Dosya veya alan yoksa `config.py` varsayılanı: `ticari` → `DEALER_OFFER` 20, `CAMPAIGN` 25; `depo` → indirimli aksiyon yok. Artık bekleyen girdi değildir |

| Bekleyen girdi | İlgili görev | Değer gelene kadar davranış |
|---|---|---|
| Remote_Repo URL'si (GitHub repo henüz yok) | 1.3 | `git init` yapılır, `origin` sonra eklenir (Requirement 1.2) |
| Knowledge_Base ID | 11.2 | `search_policies` KB_Fallback ile çalışır. ID gelince `agentcore.json` içine eklenir (Requirement 14.7) |
| Dev B `fefo_mcp`, `fefo_core`, `data` export'u ve bağımlılık talebi (`fpdf2`, `openpyxl`) | 15.1 - 15.5 | Agent `MCP_BACKEND=stub` ile çalışır |

## Tasks

- [ ] 1. Repo, git ve ortam doğrulaması
  - [x] 1.1 Ortam önkoşullarını doğrula **[BU OTURUM]**
    - `git`, `aws`, `node`, `uv` komutlarının ve proje Python'unun (3.12, `.python-version`) varlığını ve sürümünü raporla. `~/.npm-global/bin` PATH'te değilse ekle
    - `aws sts get-caller-identity` hesap kimliğinin `862714237836` ile eşleştiğini doğrula, eşleşmezse dur ve eşleşmeyen kimliği raporla
    - `agentcore` kurulu değilse yalnızca 1.0.3 sürümünü kurmayı dene, başarısız olursa hatayı raporla ve elle kurulum adımını bildir. Kuruluysa daha yeni bir sürüme güncelleme
    - `gh` yoksa GitHub adımlarını `git` ile sürdür ve `gh` gerektiren adımları atla
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [x] 1.2 Yerel git deposunu ve `.gitignore` dosyasını hazırla **[BU OTURUM]**
    - `/workshop/ai-agent-hackathon-dev-a` içinde `git init` çalıştır
    - `.gitignore` dosyasına `.venv/`, `__pycache__/`, `*.pyc`, `node_modules/`, `cdk.out/`, `.env*`, `**/agentcore/.env.local`, `**/agentcore/aws-targets.json`, `.DS_Store`, `traces/`, `*.pdf`, `*.xlsx` kalıplarını yaz
    - Çalışmayı `agent/*` biçimli bir branch'te yürüt (ör. `agent/plan1-setup`)
    - İzlenen dosyalarda AWS kimlik bilgisi, GitHub token'ı ve Kiro IDE URL'si bulunmadığını kontrol et
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 1.6_

  - [ ] 1.3 `origin` remote'unu ekle
    - **[GİRDİ BEKLİYOR: Remote_Repo URL'si. GitHub repo henüz yok]**
    - URL gelene kadar bu görev bekler, yerel `git init` (1.2) yeterlidir. Gelince `git remote add origin <URL>` çalıştır ve `git remote -v` çıktısını raporla
    - Değişiklikleri küçük PR'larla ve tek sahiplik alanı kapsayacak şekilde hazırla. Sahiplik alanı dışı değişiklik gerekirse Kullanıcı'dan onay iste
    - _Requirements: 1.1, 1.2, 1.5, 1.7_

- [ ] 2. Steering dosyaları
  - [ ] 2.1 `.kiro/steering/fefo-domain.md` dosyasını yaz (atlandı: mevcut steering kullanılıyor, yazılmayacak)
    - `.kiro/steering/` altındaki orijinal dosya değiştirilmez, yeniden yazılmaz
    - FEFO sözlüğü, rakam kuralı (LLM sayı hesaplamaz), asla gönderme kuralı, Türkçe çıktı kuralı, ₺ formatı, rol kuralları (Role_Action_Matrix) ve stdio MCP kuralları (stdout'a yazma yok, loglar stderr, ortam değişkenleri açıkça geçirilir)
    - _Requirements: 3.1, 3.2, 3.5_

  - [ ] 2.2 `.kiro/steering/agentcore-deployment.md` dosyasını yaz (atlandı: mevcut steering kullanılıyor, yazılmayacak)
    - `.kiro/steering/` altındaki orijinal dosya değiştirilmez, yeniden yazılmaz
    - Kritik_Teknik_Kurallar: `global.` Model_ID, `BedrockAgentCoreApp` import yolu, lazy init, runtime'da ağır paket yok, IAM yalnızca `additionalPolicies`, `--session-id` en az 33 karakter, test prompt'larında Türkçe kesme işareti yok, AgentCore_CLI 1.0.3 güncellenmez
    - Deploy ritüeli: `git pull`, deploy (Kullanıcı), verify (Kullanıcı), deploy sonrası değişiklikleri commit
    - Verification_Set komutları ve asistanın deploy komutlarını çalıştırmadığı kuralı
    - _Requirements: 3.1, 3.3, 3.5, 15.9_

  - [ ] 2.3 `.kiro/steering/strands-agent-coding.md` dosyasını yaz (atlandı: mevcut steering kullanılıyor, yazılmayacak)
    - `.kiro/steering/` altındaki orijinal dosya değiştirilmez, yeniden yazılmaz
    - Strands `MCPClient` kullanımı, lazy init kalıbı (`_get_agent`), `from bedrock_agentcore.runtime import BedrockAgentCoreApp` import yolu ve Role_Hook (`BeforeToolCallEvent`) kalıbı
    - _Requirements: 3.1, 3.4, 3.5_

- [ ] 3. AgentCore iskeleti ve yapılandırma
  - [x] 3.1 Scaffold'u oluştur ve bağımlılıkları sabitle **[BU OTURUM]**
    - `agentcore create --name FefoAgent --template agent-python-strands --skip-git` komutunu repo kökünde çalıştır
    - Oluşan gerçek dizin yapısını ve paket yolunu incele, sonraki görevlerde bu yapıya uy
    - `FefoAgent/app/agent/pyproject.toml` içinde Python 3.12 uyumlu, sabit sürümlü runtime bağımlılıklarını belirle (`pandas` gibi ağır paket yok). `pytest` `[dependency-groups] dev` içinde tutulur (`hypothesis` şimdilik eklenmez)
    - Bölgeyi `us-east-1` olarak doğrula
    - Scaffold'un `app/agent/tests/` yerleşimini kullan (yoksa oluştur) ve pytest yapılandırmasını ekle
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.6, 5.7_

  - [x] 3.2 Model_ID'yi doğrula ve `config.py` yaz **[BU OTURUM]**
    - Model_ID `global.anthropic.claude-sonnet-5` değerini `aws bedrock-runtime converse` ile doğrula. Başka model seçme, `sonnet-5-5` yasaktır. Çağrı başarısız olursa hatayı raporla ve Kullanıcı'dan karar iste
    - `app/agent/config.py` yaz (scaffold'un `model/load.py` yapısına uyarla): `MODEL_ID` (`global.` ile başlamalı), `MCP_BACKEND` (`stub` varsayılan), `REPORTS_BUCKET` (`fefo-862714237836-us-east-1`) ve `KNOWLEDGE_BASE_ID` (opsiyonel). `MAX_DISCOUNT_PCT_BY_ROLE` yükleyicisi ve varsayılanı görev 7.2'de aynı dosyaya eklenir
    - Model_ID ortam değişkeninden okunur, koda gömülmez. Model erişim hatasında `enable_anthropic_models` adımı ve 2-6 dakika bekleme Kullanıcı'ya bildirilir
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.8, 14.1_

  - [ ]* 3.3 Model_ID öneki için property test yaz (şimdilik atlandı)
    - **Property 19: Model_ID öneki doğrulaması**
    - **Validates: Requirements 5.2, 5.3**

- [ ] 4. Stub MCP ve MCP_Adapter (walking skeleton)
  - [x] 4.1 Tool_Contract şemalarını `schemas.py` içinde tanımla **[BU OTURUM]**
    - `get_expiry_risks`, `get_sku_profile`, `simulate_actions`, `create_action_drafts`, `generate_report_file` ve Tool_Error için `TypedDict` tanımları ve doğrulama fonksiyonları
    - Doğrulama hem Stub_MCP testlerinde hem agent içindeki şema denetiminde (görev 9.2) kullanılır
    - _Requirements: 7.1, 7.3, 7.5, 7.6, 7.9, 7.11, 7.12, 13.3, 8.6_

  - [x] 4.2 Stub_MCP sunucusunu yaz (`app/agent/fefo_mcp_stub/`) **[BU OTURUM]**
    - `__main__.py` (stdio başlatıcı), `tools.py` ve `fixtures/` oluştur
    - Beş tool Tool_Contract'a uyan sabit yanıt döner. `as_of_date` verilmezse `2026-11-25` kullanılır
    - `get_expiry_risks` `category` ve `min_loss_try` ile filtreler, `loss_try.expected` azalan sıralar, `top_n` uygular
    - `simulate_actions` adımları verilen sırayla döner. `create_action_drafts` her `body` alanını `TASLAK — gönderilmedi` ile başlatır. `LOT_ACTION_PLAN` için `lot_id` yoksa `generate_report_file` Tool_Error döner. `s3_key` biçimi `reports/<as_of_date>/<file_id>.<ext>`
    - Hatalar exception yerine `{"error": {"code", "message"}}` olarak döner. stdout'a hiçbir şey yazılmaz (`print` yok), loglar stderr'e gider
    - _Requirements: 6.1, 6.5, 7.2, 7.3, 7.4, 7.7, 7.8, 7.9, 7.11, 7.12, 8.1, 8.4, 12.3, 13.1, 13.2, 13.3, 13.4_

  - [x] 4.3 `mcp_adapter.py` dosyasını yaz **[BU OTURUM]**
    - `MCP_BACKEND` değerine göre `fefo_mcp_stub` veya `fefo_mcp` modülünü `sys.executable -m <modül>` ile alt süreç olarak başlat
    - Mevcut ortamı aktar. `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_REGION` ve `REPORTS_BUCKET` değişkenlerini açıkça geçir
    - `fefo_mcp` seçilmiş ve modül içe aktarılamıyorsa nedeni stderr'e logla ve başlatmayı durdur
    - Backend değişimi yalnızca yapılandırma değeriyle yapılır, agent kodu değişmez
    - _Requirements: 6.2, 6.3, 6.4, 6.7, 6.8, 6.9_

  - [x] 4.4 `main.py` içinde lazy init ile agent'ı kur ve tool'ları bağla **[BU OTURUM]**
    - `from bedrock_agentcore.runtime import BedrockAgentCoreApp` ile uygulama sınıfını içe aktar
    - Agent, MCP_Client ve (sonraki görevlerdeki) hook'lar `_get_agent` içinde ilk çağrıda oluşturulur, modül yüklenirken oluşturulmaz
    - Model_ID `config.py` üzerinden okunur ve başlatmada `global.` öneki doğrulanır
    - Payload'dan `prompt` ve `actorId` alınır. MCP_Adapter'dan gelen tool'lar agent'a eklenir
    - Minimum sistem prompt `prompts.py` içinde yazılır: tool'lar yetenek olarak anlatılır, rakamlar yalnızca tool çıktısından alınır, mail asla gönderilmez, Türkçe yanıt, "temsili senaryo". Nihai prompt görev 9.1'de tamamlanır (bu oturum dışı)
    - _Requirements: 5.5, 5.6, 5.9, 6.2, 6.3, 6.8_

  - [ ]* 4.5 MCP_Adapter birim testlerini yaz (şimdilik atlandı)
    - `stub` ve `fefo_mcp` seçim durumları, `sys.executable` kullanımı, açıkça geçirilen ortam değişkenleri
    - `fefo_mcp` içe aktarılamadığında stderr logu ve başlatmanın durması
    - _Requirements: 6.2, 6.3, 6.4, 6.9, 18.3_

  - [ ]* 4.6 MCP_Adapter modül seçimi için property test yaz (şimdilik atlandı)
    - **Property 12: MCP_Adapter modül seçimi yapılandırmayla tutarlıdır**
    - **Validates: Requirements 6.2, 6.8**

  - [ ]* 4.7 Alt sürece ortam geçişi için property test yaz (şimdilik atlandı)
    - **Property 13: Alt sürece geçirilen ortam değişkenleri korunur**
    - **Validates: Requirements 6.4**

- [ ] 5. Tool kontrat testleri (Stub_MCP üzerinde)
  - [x] 5.1 Ortak fixture'ları ve her tool için kontrat birim testlerini yaz **[BU OTURUM, ZORUNLU]**
    - Scaffold'un test dizininde `conftest.py` içinde backend'i yapılandırmayla seçen fixture tanımla (varsayılan `stub`). Böylece aynı testler sonradan `fefo_mcp` ile koşar (görev 15.4)
    - Beş tool'un çıktı şemasını `schemas.py` ile doğrula
    - Stub_MCP alt sürecinin stdout'unda MCP protokolü dışında çıktı olmadığını doğrula
    - _Requirements: 6.5, 6.11, 7.3, 7.5, 7.6, 7.9, 7.11, 18.1_

  - [ ]* 5.2 Risk listesi sıralaması ve alanları için property test yaz (şimdilik atlandı)
    - **Property 1: Risk listesi azalan sıralı ve Tool_Contract alanlarını içerir**
    - **Validates: Requirements 7.3, 7.4**

  - [ ]* 5.3 `min_loss_try` filtresi için property test yaz (şimdilik atlandı)
    - **Property 2: min_loss_try filtresi tüm sonuçlarda korunur**
    - **Validates: Requirements 7.2**

  - [ ]* 5.4 Varsayılan `as_of_date` için property test yaz (şimdilik atlandı)
    - **Property 3: as_of_date verilmezse varsayılan uygulanır**
    - **Validates: Requirements 8.4, 8.5**

  - [ ]* 5.5 `simulate_actions` adım sırası için property test yaz (şimdilik atlandı)
    - **Property 4: simulate_actions adımları girdi sırasını korur ve kaybı tutarlı günceller**
    - **Validates: Requirements 7.7, 7.8, 7.9**

  - [ ]* 5.6 Taslak başlığı için property test yaz (şimdilik atlandı)
    - **Property 5: Taslak başlığı her zaman mevcuttur**
    - **Validates: Requirements 12.3**

  - [ ]* 5.7 `audience` değeri için property test yaz (şimdilik atlandı)
    - **Property 6: audience alanı izinli kümeden seçilir**
    - **Validates: Requirements 7.12**

  - [ ]* 5.8 Hata formatı için property test yaz (şimdilik atlandı)
    - **Property 16: Tool hatası asla exception olarak dışarı taşmaz**
    - **Validates: Requirements 8.1**

  - [ ]* 5.9 `generate_report_file` girdi doğrulaması için property test yaz (şimdilik atlandı)
    - **Property 17: generate_report_file girdi doğrulaması**
    - **Validates: Requirements 13.2**

  - [ ]* 5.10 Rapor `s3_key` kalıbı için property test yaz (şimdilik atlandı)
    - **Property 18: Rapor dosya anahtarı kalıbı**
    - **Validates: Requirements 13.3, 13.4**

- [ ] 6. Checkpoint - Walking skeleton ve kontrat testleri
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Rol hook'u
  - [ ] 7.1 `role_hook.py` dosyasını yaz
    - `BeforeToolCallEvent` üzerinde yalnızca `create_action_drafts` çağrısını denetle
    - Actor_Id biçimini doğrula (`<rol>-<isim>`, yalnızca harf, rakam, tire). Yalnızca `depo` ve `ticari` rolleri geçerlidir. Eksik, biçimsiz veya bilinmeyen rolde çağrıyı iptal et ve rolün belirlenemediğini bildir
    - Role_Action_Matrix: `FEFO_PRIORITY`, `DONATION`, `SUPPLIER_RETURN` ve `generate_report_file` her iki rol için izinli. `DEALER_OFFER` ve `CAMPAIGN` yalnızca `ticari` için ve Max_Discount_Pct_By_Role sınırı içinde izinli
    - Yetkisiz aksiyonda veya sınır aşımında çağrıyı iptal et ve "bu aksiyon için ticari onayı gerekir" yanıtını dön. İndirimli aksiyonda `discount_pct` eksik, sayısal değil veya 0-100 dışındaysa çağrıyı iptal et. Sınırları `config.py` üzerinden oku, hook içine sayı gömme. Modül adlarını scaffold sonrası gerçek yapıya göre uyarlar
    - Her izin ve ret kararını rol, Actor_Id, tool adı ve karar bilgisiyle logla
    - İptal sonrası konuşma sürer
    - _Requirements: 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 9.10, 9.11_

  - [ ] 7.2 Max_Discount_Pct_By_Role yapılandırmasını `config.py` içine ekle
    - `app/agent/data/params.json` içindeki `max_discount_pct_by_role` alanını oku. Dosya veya alan yoksa tek config noktasındaki (`config.py`) varsayılana düş: `ticari` → `DEALER_OFFER` 20, `CAMPAIGN` 25; `depo` → indirimli aksiyon yok. Bozuk JSON'da varsayılana düş ve uyarıyı stderr'e logla
    - `data/` klasörü Dev B export'una aittir, elle düzenlenmez ve dosya oluşturulmaz. `role_policy.json` kullanılmaz. Artık bekleyen girdi yoktur
    - _Requirements: 9.5, 9.9_


  - [ ] 7.3 Role_Hook'u agent'a bağla
    - `_get_agent` içinde hook'u kaydet
    - Her istekte `actorId` değerinden rolü belirle ve doğrula. `create_action_drafts` çağrısında `approver_actor_id` alanına doğrulanmış Actor_Id değerini yaz
    - _Requirements: 9.1, 9.3, 9.10, 9.12_

  - [ ]* 7.4 Role_Hook karar yolları için birim testlerini yaz (şimdilik atlandı)
    - İzin, rol yetkisiz ret, rol belirsiz veya bilinmeyen rol ret, `discount_pct` eksik veya geçersiz ret, indirim sınırı aşımı ret
    - Sınır değerleri test içinde verilir. `params.json` yokken `config.py` varsayılanının uygulandığı doğrulanır
    - _Requirements: 9.5, 9.7, 9.9, 9.10, 18.2_

  - [ ]* 7.5 Her rolde izinli aksiyonlar için property test yaz (şimdilik atlandı)
    - **Property 7: Role_Hook - izinli aksiyonlar her rolde geçer**
    - **Validates: Requirements 9.4**

  - [ ]* 7.6 `depo` rolünün indirimli aksiyonları reddi için property test yaz (şimdilik atlandı)
    - **Property 8: Role_Hook - depo rolü indirimli aksiyonları her zaman reddeder**
    - **Validates: Requirements 9.5, 9.7**

  - [ ]* 7.7 İndirim sınırı aşımı için property test yaz (şimdilik atlandı)
    - **Property 9: Role_Hook - indirim sınırı aşımı, geçersiz discount_pct veya sınırsız aksiyon reddedilir**
    - **Validates: Requirements 9.9**

  - [ ]* 7.8 Sınır içindeki ticari istekler için property test yaz (şimdilik atlandı)
    - **Property 10: Role_Hook - indirim sınırı içindeki ticari istekler geçer**
    - **Validates: Requirements 9.5**

  - [ ]* 7.9 Geçersiz actorId için property test yaz (şimdilik atlandı)
    - **Property 11: Geçersiz actorId her zaman reddedilir**
    - **Validates: Requirements 9.2, 9.10**

- [ ] 8. `search_policies` ve KB_Fallback
  - [ ] 8.1 `policy_tool.py` içinde KB_Fallback aramasını yaz
    - Paketlenmiş `policy.md` ve `process_guide.md` dosyalarını `app/agent/policy_docs/` altına koy. Dosyalar Dev B/L tarafından sağlanır. Repoda yoksa Kullanıcı'ya bildir ve paketlenen yola uydurma içerik yazma. Testler için küçük `POL-x` ve `PRC-x` içeren örnek dosyalar yalnızca test fixture'ı olarak tutulur
    - Arama sonucu `{"pasajlar": [{"madde_no", "metin"}], "kb_kullanılamadı": bool}` biçiminde döner ve her pasaj `POL-x` veya `PRC-x` numarası taşır
    - _Requirements: 7.14, 14.3, 14.4, 14.7_

  - [ ] 8.2 Knowledge_Base sorgusunu ekle ve fallback'e geçişi bağla
    - `KNOWLEDGE_BASE_ID` tanımlıysa Bedrock Knowledge Base'i sorgula. Tanımlı değilse veya erişim hatası olursa hatayı logla ve KB_Fallback'e geç
    - Fallback çıktısı ana yol ile aynı anahtar kümesini korur ve `kb_kullanılamadı` değerini `true` yapar
    - `search_policies` yerel `@tool` olarak kalır ve Fefo_MCP üzerinden sunulmaz. Docstring yeteneği açık anlatır
    - _Requirements: 7.14, 7.15, 7.16, 14.1, 14.2, 14.3, 14.4, 14.5_

  - [ ] 8.3 `search_policies` tool'unu agent'a ekle
    - `_get_agent` içinde yerel tool olarak kaydet
    - _Requirements: 7.15, 10.1, 14.5_

  - [ ]* 8.4 `search_policies` birim testlerini yaz (şimdilik atlandı)
    - KB tanımsız, KB erişim hatası, madde numarası içeren sonuç, `kb_kullanılamadı` bayrağı
    - _Requirements: 14.2, 14.3, 14.4, 14.6_

  - [ ]* 8.5 Madde numarası için property test yaz (şimdilik atlandı)
    - **Property 14: search_policies her zaman madde numarası döner (KB veya fallback)**
    - **Validates: Requirements 7.14, 14.4**

  - [ ]* 8.6 KB ve fallback çıktı şeması eşdeğerliği için property test yaz (şimdilik atlandı)
    - **Property 15: KB_Fallback kontrat eşdeğerliği**
    - **Validates: Requirements 14.4**

- [ ] 9. Sistem prompt ve karar akışı
  - [ ] 9.1 Sistem prompt'unu `prompts.py` içinde tamamla
    - Tool'lar adlarıyla değil yetenekleriyle anlatılır
    - Kurallar: rakamlar yalnızca tool çıktısından alınır ve hiçbir hesap yapılmaz, ₺ Türkçe biçimde sunulur, `generate_report_file` için `summary_text` alanına yeni rakam eklenmez, Türkçe soruya Türkçe yanıt, mail veya mesaj asla gönderilmez ("maili gönder" reddedilir, yalnızca taslak), verilerin "temsili senaryo" olduğu belirtilir
    - Karar akışı: risk listesi, neden, simülasyon, öneri, onay, taslaklar. Kullanıcı açıkça onaylamadan taslak oluşturma çağrılmaz. `forecast_confidence` değeri `LOW` olan öğe için düşük güvenli tahmin uyarısı verilir
    - Soru-cevap: süreç soruları politika araması ile ve madde numarasıyla yanıtlanır, veri soruları ilgili tool ile, dosya istekleri rapor tool'u ve `download_url` ile, what-if soruları `simulate_actions` yeniden çağrısı ile. Yanıt tool çıktısında veya politika belgelerinde yoksa "bu bilgi elimdeki verilerde yok" denir
    - KB_Fallback etkinse yanıtta Knowledge_Base'in kullanılamadığı belirtilir. Yetki dışı aksiyon onaylatılmaz
    - _Requirements: 5.9, 8.3, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9, 10.10, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 12.1, 12.2, 12.4, 12.5, 12.6, 12.7, 14.6_

  - [ ] 9.2 Tool yanıt şema denetimini yaz (`response_guard.py`)
    - Her tool yanıtını `schemas.py` ile doğrula. İhlalde ihlali logla ve kullanıcıya tool yanıtının geçersiz olduğunu bildir
    - Tool_Error yanıtında hata kodunu içeren mesaj üret ve uydurma veri ekleme
    - _Requirements: 8.3, 8.6_

  - [ ] 9.3 Prompt ve şema denetimini agent'a bağla
    - `_get_agent` içinde nihai sistem prompt'unu ve yanıt denetimini (Strands hook olarak) kaydet
    - _Requirements: 5.6, 8.3, 8.6, 10.8_

  - [ ]* 9.4 Prompt ve yanıt denetimi için birim testlerini yaz (şimdilik atlandı)
    - Prompt tool adlarını içermez, temel kuralları (rakam kuralı, asla gönderme, temsili senaryo, karar akışı) içerir
    - Şema ihlali ve Tool_Error durumları
    - _Requirements: 5.9, 8.3, 8.6_

- [ ] 10. Checkpoint - Agent çekirdeği
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. `agentcore.json` yapılandırması
  - [x] 11.1 `agentcore.json` içine envVars ve `additionalPolicies` yapısını yaz **[BU OTURUM]**
    - Önce scaffold'un ürettiği gerçek `FefoAgent/agentcore/agentcore.json` şemasını incele ve tasarımdaki örneği bu şemaya uyarla
    - Runtime `agent` için envVars: `UNIFIED_TRACES_DESTINATION_ENABLED=true`, `REPORTS_BUCKET=fefo-862714237836-us-east-1`, `MODEL_ID=global.anthropic.claude-sonnet-5`, `MCP_BACKEND=stub`
    - IAM izinleri yalnızca `additionalPolicies` ile tanımlanır (rol veya başka alan üzerinden eklenmez)
    - _Requirements: 4.3, 15.1, 15.5, 15.6_

  - [ ] 11.2 S3 izinlerini ve Knowledge_Base değerlerini yaz
    - S3 izinleri: `fefo-862714237836-us-east-1` bucket'ında `reports/*` ve `decisions/*` önekleri için `s3:PutObject` ve `s3:GetObject` izinlerini runtime'ın `additionalPolicies` listesine yaz (politika JSON dosyası `app/agent/policies/` altında, yol runtime `codeLocation`'a göredir). `aws iam put-role-policy` kullanılmaz
    - **[GİRDİ BEKLİYOR: Knowledge_Base ID. KB henüz yok]** KB ID gelince `KNOWLEDGE_BASE_ID` envVar'ını ekle, KB ARN'si için `bedrock:Retrieve` ve `*` kaynağı için `bedrock:RetrieveAndGenerate` izinlerini `additionalPolicies` içine yaz. KB ID gelmezse bu iki izin ve envVar eklenmez, `search_policies` KB_Fallback ile çalışır
    - _Requirements: 14.1, 14.7, 15.2, 15.3, 15.4_


  - [ ] 11.3 Deploy öncesi yerel kontrol betiğini yaz
    - `FefoAgent/scripts/predeploy_check.py`: yapılandırma dosyası, `MODEL_ID` önekü, bölge (`us-east-1`), hesap (`aws sts get-caller-identity` salt okunur), `REPORTS_BUCKET`, `additionalPolicies` içeriği ve `.gitignore` kalıplarını denetler ve rapor basar
    - Betik `agentcore deploy` çalıştırmaz ve AWS kaynağı değiştirmez
    - _Requirements: 16.1, 16.2_

  - [ ]* 11.4 `agentcore.json` doğrulaması için birim testlerini yaz (şimdilik atlandı)
    - JSON geçerli, `UNIFIED_TRACES_DESTINATION_ENABLED` değeri `true`, S3 izinleri yalnızca `reports/*` ve `decisions/*` önekleri için, IAM yalnızca `additionalPolicies` alanında
    - _Requirements: 15.1, 15.2, 15.3, 15.5_

- [ ] 12. Deploy ve doğrulama belgeleri (komutları Kullanıcı çalıştırır veya yetkisiyle asistan çalıştırır)
  - [ ] 12.1 `DEPLOY_VERIFY.md` dosyasını yaz
    - Başa "bu komutları Kullanıcı Kiro IDE Browser terminalinde çalıştırır. Kullanıcı yetki verdiğinde asistan da çalıştırabilir. PATH'te `~/.npm-global/bin` olmalıdır" notunu koy
    - Deploy öncesi `predeploy_check.py` çalıştırma adımı ve kontrol listesi (yapılandırma, Model_ID, bölge, hesap, `REPORTS_BUCKET`, `additionalPolicies`)
    - `agentcore deploy` komutu (Kullanıcı veya yetkisiyle asistan çalıştırır) ve deploy ritüeli: `git pull`, deploy, verify, deploy sonrası değişiklikleri commit (son adım). Ortam değişkenlerini basan komut (`env`, `printenv`, `set`) çalıştırılmaz
    - Verification_Set'in beş adımı komutları ve beklenen çıktılarıyla: `agentcore status`, `agentcore invoke --runtime agent` (payload `{"prompt":"Bugun riskli urunler neler? Bir aracini cagir ve sonucu goster.","actorId":"depo-test"}`), `aws logs describe-log-groups --log-group-name-prefix /aws/bedrock-agentcore/runtimes/` ve `agentcore traces runtime list --since 15m`, `.kiro/specs/fefo-agent/` kontrolü, `agentcore traces runtime get <trace-id>` ile `fefo_mcp` tool span'leri
    - `--session-id` değerinin en az 33 karakter olması ve test prompt'larında Türkçe kesme işareti kullanılmaması uyarıları
    - Her deploy sonrası Verification_Set'in tekrarlanması gerektiği
    - _Requirements: 15.7, 15.8, 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 16.8, 16.9, 16.10_

  - [ ] 12.2 `TROUBLESHOOTING.md` dosyasını yaz
    - stdio MCP açılmıyorsa `agentcore logs runtime --since 15m` ile stdout'a print, yanlış modül yolu ve geçirilmeyen ortam değişkeni kontrolü. Çözülmezse `fefo_core` fonksiyonlarını yerel `@tool` olarak bağlama yolu (Tool_Contract değişmez)
    - Rapor S3'e yazılamıyorsa `REPORTS_BUCKET`, `additionalPolicies` S3 izni ve ortamın alt sürece geçişi kontrolü
    - Model erişim hatasında `enable_anthropic_models` ve 2-6 dakika bekleme
    - Kesilmeyecek kapsam: runtime deploy, observability, `fefo_mcp` (stdio), politika ve süreç bilgisi (KB veya KB_Fallback), onay akışı ve taslaklar, en az PDF raporu
    - _Requirements: 5.8, 17.1, 17.2, 17.3, 17.4_

- [ ] 13. Eval testleri (şimdilik atlandı)
  - [ ]* 13.1 (şimdilik atlandı) `tests/eval/` altında eval altyapısını ve rakam eşleşmesi senaryosunu yaz
    - Agent'ı yerelde `MCP_BACKEND=stub` ile çalıştıran, tool çağrılarını ve çıktılarını kaydeden ortak yardımcılar (`conftest.py`). Bedrock erişimi yoksa eval testleri atlanır
    - Rakam senaryosu: yanıttaki adet, gün ve ₺ değerlerinin tool çıktısıyla birebir eşleştiğini doğrular
    - Test prompt'larında Türkçe kesme işareti kullanılmaz
    - _Requirements: 11.1, 11.2, 15.8, 18.4_

  - [ ]* 13.2 Süreç sorusu senaryosunu yaz (şimdilik atlandı)
    - "FEFO nasıl işliyor?" ve "Kampanyayı kim onaylar?" sorularının `PRC-x` veya `POL-x` madde numarasıyla yanıtlandığını doğrula
    - _Requirements: 10.1, 18.5_

  - [ ]* 13.3 "maili gönder" senaryosunu yaz (şimdilik atlandı)
    - Gönderim isteğinin reddedildiğini ve yalnızca taslak üretildiğini, her taslağın `TASLAK — gönderilmedi` ile başladığını doğrula
    - _Requirements: 12.2, 12.3, 18.6_

  - [ ]* 13.4 Rol bazlı kampanya onayı senaryosunu yaz (şimdilik atlandı)
    - `depo` rolünün kampanyayı onaylatamadığını ve `ticari` rolünün (Max_Discount_Pct_By_Role sınırı içinde) onaylatabildiğini doğrula. Sınır değerleri `params.json` veya `config.py` varsayılanından okunur
    - _Requirements: 9.5, 9.7, 18.7_

  - [ ]* 13.5 What-if senaryosunu yaz (şimdilik atlandı)
    - "%20 indirim olsa?" sorusunun `simulate_actions` ile yeni parametreyle yeniden hesaplandığını doğrula
    - _Requirements: 10.7, 18.8_

- [ ] 14. Checkpoint - Plan 1 yerel doğrulaması
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Dev B export sonrası gerçek `fefo_mcp`'ye geçiş
  - **[BEKLEYEN GİRDİ: Dev B'nin `fefo_core`, `fefo_mcp` ve `data` export'u ve yeni bağımlılık talebi (`fpdf2`, `openpyxl`)]**
  - Bu görevlerin hiçbiri export gelmeden başlatılmaz. Bu sürede agent `MCP_BACKEND=stub` ile çalışır ve Plan 1 diğer görevleri bundan etkilenmez

  - [ ] 15.1 Export'u doğrula
    - `FefoAgent/app/agent/fefo_core`, `fefo_mcp` ve `data` klasörlerinin geldiğini, `python -m fefo_mcp` modülünün içe aktarılabildiğini ve elle düzenlenmediğini kontrol et
    - `fefo_mcp` içinde stdout'a yazan `print` kullanımı görülürse düzeltme yapma, bulguyu Dev B'ye iletilmek üzere Kullanıcı'ya raporla
    - _Requirements: 6.6, 6.9, 6.12_

  - [ ] 15.2 `pyproject.toml` bağımlılıklarını güncelle
    - `fpdf2` ve `openpyxl` paketlerini sabit sürümle runtime bağımlılıklarına ekle. Ağır paket (ör. `pandas`) eklenmez
    - _Requirements: 4.5, 5.7_

  - [ ] 15.3 Backend'i `fefo_mcp`'ye geçir ve stub'ı sil
    - `agentcore.json` içinde `MCP_BACKEND` değerini `fefo_mcp` yap. Agent kodunda başka değişiklik yapma
    - `fefo_mcp_stub/` klasörünü silmeden önce Kullanıcı'ya bildir. Silme sonrası stub'a bağımlı import ve test kalıntılarını temizle
    - _Requirements: 6.8, 6.10_

  - [ ] 15.4 Aynı kontrat testlerini Fefo_MCP üzerinde çalıştır
    - Görev 5.1'deki Tool kontrat testlerini fixture'ı `fefo_mcp` backend'ine çevirerek koş (property testleri şimdilik atlandı). Başarısız olan test Tool_Contract uyumsuzluğudur: sözleşmeyi değiştirme, bulguyu raporla
    - Eval testlerinin `fefo_mcp` ile yeniden koşulması şimdilik atlandı (görev 13)
    - _Requirements: 6.11, 8.2, 8.5, 18.1_

  - [ ] 15.5 Belgeleri güncelle
    - `DEPLOY_VERIFY.md` içinde backend geçişi sonrası Verification_Set'in tekrarlanacağını ve 5. adımda `fefo_mcp` tool span'lerinin görüneceğini vurgula
    - Komutları Kullanıcı çalıştırır veya yetkisiyle asistan çalıştırır
    - _Requirements: 16.3, 16.8, 16.9_

- [ ] 16. Son checkpoint - Plan 1 tamamlanması
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- `*` ile işaretli alt görevler isteğe bağlıdır. Bu oturumda tüm `*` testleri, property-based testler ve eval testleri **şimdilik atlandı** ve onay kutuları işaretlenmez. Aktif testler yalnızca 5.1 (zorunlu) ve 15.4 (Fefo_MCP geçişinde aynı kontrat testleri)
- **[BU OTURUM]** etiketli görevler walking skeleton kapsamındadır: 1.1, 1.2, 3.1, 3.2, 4.1, 4.2, 4.3, 4.4 (minimum sistem prompt dahil), 5.1 ve 11.1
- Steering görevleri 2.1-2.3 atlandı: mevcut orijinal steering dosyaları kullanılır, yazılmaz ve değiştirilmez
- **GİRDİ BEKLİYOR** ve **BEKLEYEN GİRDİ** işaretli görevler (Remote_Repo URL'si, Knowledge_Base ID, Dev B export'u) girdi gelmeden uygulanmaz
- Kullanıcı, deploy, invoke, status ve logs komutlarının asistan tarafından çalıştırılmasını bu oturumda açıkça yetkilendirmiştir. PATH'te `~/.npm-global/bin` olmalıdır. Ortam değişkenleri ekrana veya loga basılmaz
- Plan 2 ve Plan 3 kapsam dışıdır
- Her görev ilgili Requirement maddelerine atıf yapar

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "2.1", "2.2", "2.3"] },
    { "id": 1, "tasks": ["1.3", "3.1"] },
    { "id": 2, "tasks": ["3.2", "4.1"] },
    { "id": 3, "tasks": ["3.3", "4.2", "7.1", "7.2", "8.1", "9.1", "9.2", "11.1"] },
    { "id": 4, "tasks": ["4.3", "5.1", "7.4", "7.5", "7.6", "7.7", "7.8", "7.9", "8.2", "9.4", "11.2", "11.3"] },
    { "id": 5, "tasks": ["4.4", "4.5", "4.6", "4.7", "5.2", "5.3", "5.4", "5.5", "5.6", "5.7", "5.8", "5.9", "5.10", "8.4", "8.5", "8.6", "11.4", "12.1", "12.2"] },
    { "id": 6, "tasks": ["7.3"] },
    { "id": 7, "tasks": ["8.3"] },
    { "id": 8, "tasks": ["9.3"] },
    { "id": 9, "tasks": ["13.1"] },
    { "id": 10, "tasks": ["13.2", "13.3", "13.4", "13.5", "15.1"] },
    { "id": 11, "tasks": ["15.2"] },
    { "id": 12, "tasks": ["15.3"] },
    { "id": 13, "tasks": ["15.4", "15.5"] }
  ]
}
```
