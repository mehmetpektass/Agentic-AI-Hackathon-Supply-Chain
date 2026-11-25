# Requirements Document

## Introduction

FEFO Agent (First Expired, First Out), Dev A sorumluluğundaki Agent ve AgentCore katmanıdır. Agent, depo lotlarının son kullanma tarihinden (SKT) önce satılıp satılmayacağını tahmin eden tool sonuçlarını kullanır, riskli lotları ₺ kaybıyla listeler, nedenini açıklar, aksiyon kombinasyonlarının kaybı ne kadar düşürdüğünü (kayıp şelalesi) gösterir ve onay sonrası yalnızca TASLAK mesaj üretir. Desteklenen aksiyonlar: `FEFO_PRIORITY`, `DEALER_OFFER`, `CAMPAIGN`, `DONATION`, `SUPPLIER_RETURN`. Veri sentetiktir ve "temsili senaryo" olarak sunulur.

Kapsam Plan 1 görev 1-7'dir: repo kurulumu, steering dosyaları, AgentCore iskeleti, stub MCP ile walking skeleton, tool kontratları, rol hook'u, soru-cevap ve dosya davranışı, deploy hazırlığı ve doğrulama. Agent başlangıçta Stub_MCP'ye bağlanır. Dev B `fefo_mcp` modülünü export ettiğinde gerçek Fefo_MCP'ye geçilir. Plan 2 ve Plan 3 kapsam dışıdır. Hesap mantığı yalnızca Dev B'nin `pipeline/fefo_core` modülündedir. FEFO_Agent hesap yapmaz.

Kaynak: `/workshop/ai-agent-hackathon-dev-a/TEAM_PLAN_FEFO_AGENT.md` (Takım Planı). Tool kontratları iki geliştirici onayı olmadan değişmez. Kod dili Python 3.12'dir (`.python-version`, uv ile kurulu). Tasarım çıktıları Türkçe yapısal sözde kod ile ifade edilir. Dev A sahiplik alanı: `FefoAgent/` (export klasörleri `app/agent/fefo_core`, `app/agent/fefo_mcp`, `app/agent/data` hariç), `.kiro/steering/`, kök md dosyaları ve `tests/eval/` çalıştırma.

## Glossary

- **FEFO_Agent**: Python ile yazılan, Strands Agents kullanan ve AgentCore_Runtime üzerinde çalışan ajan uygulaması (`FefoAgent/`).
- **Project_Setup**: Repo kurulumunu, ortam doğrulamasını ve scaffold adımlarını yürüten Dev A iş akışı.
- **AgentCore_CLI**: `agentcore` komut satırı aracı, sabit sürüm 1.0.3.
- **AgentCore_Runtime**: FEFO_Agent'ın deploy edildiği Amazon Bedrock AgentCore çalışma ortamı.
- **Stub_MCP**: `FefoAgent/app/agent/fefo_mcp_stub/` altındaki, Tool_Contract'a uyan sabit yanıtlı sahte stdio MCP sunucusu.
- **Fefo_MCP**: Dev B'nin export edeceği, official mcp SDK FastMCP ile yazılmış gerçek stdio MCP modülü (`fefo_mcp`).
- **MCP_Adapter**: FEFO_Agent içinde Stub_MCP ile Fefo_MCP arasında yapılandırmayla seçim yapan ve seçilen modülü alt süreç olarak başlatan katman.
- **MCP_Client**: Strands `MCPClient` nesnesi.
- **Tool_Contract**: Takım Planı bölüm 4'te tanımlı, her tool için ad, girdi ve çıktı şemasından oluşan sözleşme.
- **Tool_Error**: `{"error": {"code": "...", "message": "..."}}` biçimindeki hata yanıtı.
- **Default_As_Of_Date**: `2026-11-25`.
- **Role_Hook**: Strands `BeforeToolCallEvent` hook'u olarak çalışan ve `create_action_drafts` çağrısını denetleyen bileşen.
- **Actor_Id**: `<rol>-<isim>` biçiminde (ör. `depo-ahmet`, `ticari-zeynep`), yalnızca harf, rakam ve tire içeren kullanıcı kimliği.
- **Role_Action_Matrix**: Rol ve aksiyon yetkilerini tanımlayan tablo (Requirement 9).
- **Max_Discount_Pct_By_Role**: Rol bazında, indirimli aksiyon tipi başına azami indirim yüzdesini tanımlayan yapılandırma değeri. Kaynağı `app/agent/data/params.json` içindeki `max_discount_pct_by_role` alanıdır. Dosya veya alan yoksa `config.py` içindeki tek varsayılan kullanılır: `ticari` için `DEALER_OFFER` 20, `CAMPAIGN` 25; `depo` için indirimli aksiyon yok. `data/` klasörü Dev B export'una aittir ve elle düzenlenmez.
- **Draft_Header**: Her taslağın başındaki `TASLAK — gönderilmedi` ibaresi.
- **Policy_Search_Tool**: FEFO_Agent içinde yer alan yerel `search_policies` tool'u.
- **Policy_Docs**: `policy.md` ve `process_guide.md` dosyaları. Madde numaraları `POL-x` ve `PRC-x` biçimindedir.
- **Knowledge_Base**: Policy_Docs içeren Amazon Bedrock Knowledge Base.
- **KB_Fallback**: Knowledge_Base yokken veya erişilemezken paketlenmiş Policy_Docs içinde arama yapan, aynı Tool_Contract'ı koruyan yedek davranış.
- **Model_ID**: Bedrock çıkarım profili kimliği, `global.` önekli.
- **Runtime_Dependencies**: AgentCore_Runtime içinde çalışması gereken Python paketleri (`FefoAgent/app/agent/pyproject.toml`).
- **Agentcore_Config**: `FefoAgent/agentcore/agentcore.json` dosyası.
- **Reports_Bucket**: `REPORTS_BUCKET` ortam değişkeniyle adlandırılan, değeri `fefo-862714237836-us-east-1` olan S3 bucket'ı (`S3_BUCKET_NAME` ortam değişkeni tanımlı değildir, bu ad doğrudan kullanılır).
- **Steering_Files**: `.kiro/steering/` altındaki `fefo-domain.md`, `agentcore-deployment.md` ve `strands-agent-coding.md`.
- **Kritik_Teknik_Kurallar**: Requirement 15, madde 9'da listelenen teknik kurallar kümesi.
- **Verification_Set**: Takım Planı bölüm 9'daki beş doğrulama adımı.
- **Eval_Set**: Takım Planı bölüm 9'daki değerlendirme senaryoları.
- **Remote_Repo**: Henüz mevcut olmayan GitHub private deposu. Kullanıcı oluşturup URL'sini ilettiğinde `origin` olarak eklenir.
- **Kullanıcı**: Dev A geliştiricisi. Deploy, invoke, status ve logs komutlarını kendisi çalıştırabilir veya bu oturumda asistana açıkça yetki vermiştir (Requirement 16).
- **Repo**: `/workshop/ai-agent-hackathon-dev-a` dizinindeki git deposu.
- **AWS_Region**: `us-east-1`.
- **AWS_Account**: `862714237836`.

## Requirements

### Requirement 1: Git Deposu ve Gizli Bilgi Yönetimi

**User Story:** As a Dev A geliştiricisi, I want Repo'nun git ile hazırlanmasını ve sırların dışarıda tutulmasını, so that çalışmam Remote_Repo ile güvenle senkronize edilebilsin.

#### Acceptance Criteria

1. WHEN Kullanıcı Remote_Repo URL'sini ilettiğinde, THE Project_Setup SHALL `git init` çalıştırıp URL'yi `origin` remote'u olarak eklemek.
2. IF Remote_Repo URL'si henüz iletilmemişse, THEN THE Project_Setup SHALL yerel `git init` işlemini tamamlayıp remote ekleme adımını Kullanıcı girdisi bekleyen adım olarak işaretlemek.
3. THE Repo SHALL `.gitignore` dosyasında `.venv/`, `__pycache__/`, `*.pyc`, `node_modules/`, `cdk.out/`, `.env*`, `**/agentcore/.env.local`, `**/agentcore/aws-targets.json`, `.DS_Store`, `traces/`, `*.pdf` ve `*.xlsx` kalıplarını listelemek.
4. THE Repo SHALL AWS kimlik bilgilerini, GitHub token'ını ve Kiro IDE URL'sini hiçbir izlenen dosyada içermemek.
5. THE Project_Setup SHALL Dev A değişikliklerini `agent/*` adlı branch'lerde ve tek sahiplik alanı kapsayan küçük PR'larla hazırlamak.
6. THE Project_Setup SHALL `FefoAgent/agentcore/agentcore.json`, `FefoAgent/app/agent/pyproject.toml` ve `.kiro/steering/` dosyalarını yalnızca Dev A sahipliğinde değiştirmek.
7. IF bir değişiklik Dev A sahiplik alanı dışındaki bir dosyayı gerektiriyorsa, THEN THE Project_Setup SHALL dosyayı değiştirmeden değişiklik önerisini Kullanıcı'ya bildirip onay istemek.

### Requirement 2: Ortam Önkoşulları

**User Story:** As a Dev A geliştiricisi, I want ortam önkoşullarının doğrulanmasını, so that eksik araçlar erken tespit edilsin.

#### Acceptance Criteria

1. WHEN ortam doğrulaması çalıştırıldığında, THE Project_Setup SHALL `git`, `aws`, `node`, `uv` ve proje Python'unun (3.12, `.python-version`) varlığını ve sürümlerini raporlamak.
2. WHEN ortam doğrulaması çalıştırıldığında, THE Project_Setup SHALL `aws sts get-caller-identity` çıktısındaki hesap kimliğinin AWS_Account ile eşleştiğini doğrulamak.
3. IF `aws sts get-caller-identity` çıktısındaki hesap kimliği AWS_Account'tan farklıysa, THEN THE Project_Setup SHALL işlemi durdurup eşleşmeyen hesap kimliğini raporlamak.
4. WHEN AgentCore_CLI kurulu değilse, THE Project_Setup SHALL AgentCore_CLI 1.0.3 sürümünü kurmayı denemek.
5. IF AgentCore_CLI 1.0.3 kurulumu başarısız olursa, THEN THE Project_Setup SHALL hata mesajını raporlayıp Kullanıcı'ya elle kurulum adımını bildirmek.
6. WHILE AgentCore_CLI 1.0.3 kuruluyken, THE Project_Setup SHALL AgentCore_CLI'yı daha yeni bir sürüme güncellememek.
7. IF `gh` komutu kurulu değilse, THEN THE Project_Setup SHALL GitHub işlemlerini `git` ile sürdürmek ve `gh` gerektiren adımları atlamak.

### Requirement 3: Steering Dosyaları

**User Story:** As a Dev A geliştiricisi, I want alan kurallarının steering dosyalarına yazılmasını, so that Kiro oturumları aynı kurallarla çalışsın.

#### Acceptance Criteria

1. THE Repo SHALL `.kiro/steering/fefo-domain.md`, `.kiro/steering/agentcore-deployment.md` ve `.kiro/steering/strands-agent-coding.md` dosyalarını içermek.
2. THE `fefo-domain.md` SHALL FEFO sözlüğünü, rakam kuralını, asla gönderme kuralını, Türkçe çıktı kuralını, ₺ formatını, rol kurallarını ve stdio MCP kurallarını içermek.
3. THE `agentcore-deployment.md` SHALL Kritik_Teknik_Kurallar'ı (Requirement 15), deploy ritüelini (`git pull`, deploy, verify, deploy sonrası değişiklikleri commit) ve Verification_Set komutlarını içermek.
4. THE `strands-agent-coding.md` SHALL Strands MCP_Client kullanımını, lazy init kalıbını, BedrockAgentCoreApp import yolunu ve Role_Hook kalıbını içermek.
5. THE Steering_Files SHALL Dev A sahipliğinde kalıp `.kiro/steering/` dizininde tutulmak.
6. THE Project_Setup SHALL `.kiro/steering/` altında hâlihazırda bulunan orijinal Steering_Files dosyalarını yeniden yazmamak ve değiştirmemek. Mevcut dosyalar kullanılır. Bu dosyalardaki örnek model kimlikleri yerine `global.anthropic.claude-sonnet-5` geçerlidir.

### Requirement 4: AgentCore Proje İskeleti

**User Story:** As a Dev A geliştiricisi, I want AgentCore projesinin kontrollü iskeletlenmesini, so that agent deploy edilebilir yapıda olsun.

#### Acceptance Criteria

1. THE Project_Setup SHALL iskeleti `agentcore create --name FefoAgent --template agent-python-strands --skip-git` komutuyla oluşturmak.
2. THE Repo SHALL `FefoAgent/` altında AgentCore_CLI ile oluşturulmuş Python tabanlı bir agent projesi içermek.
3. THE FEFO_Agent SHALL AWS_Region'ı bölge olarak kullanmak.
4. THE Runtime_Dependencies SHALL `FefoAgent/app/agent/pyproject.toml` içinde Python 3.12 ile uyumlu ve sabit sürümlerle listelenmek.
5. WHEN Dev B `fefo_mcp` için yeni bağımlılık (`fpdf2`, `openpyxl`) talep ettiğinde, THE Project_Setup SHALL bağımlılığı `pyproject.toml` dosyasına eklemek.
6. THE Repo SHALL Plan 2 ve Plan 3 bileşenlerini içermemek.

### Requirement 5: Model ve Uygulama Giriş Noktası

**User Story:** As a Dev A geliştiricisi, I want modelin ve giriş noktasının doğru yapılandırılmasını, so that agent AgentCore_Runtime üzerinde başlasın.

#### Acceptance Criteria

1. WHEN model doğrulaması yapıldığında, THE Project_Setup SHALL Model_ID olarak `global.anthropic.claude-sonnet-5` değerini kullanmak ve bu değeri bir Bedrock converse çağrısıyla doğrulamak. Hesapta model allowlist politikası vardır, `global.anthropic.claude-sonnet-5-5` yasaktır ve başka model seçilmez.
2. THE FEFO_Agent SHALL Model_ID'yi koda gömmek yerine yapılandırma değeri olarak okumak.
3. WHEN FEFO_Agent başlatıldığında, THE FEFO_Agent SHALL yapılandırılmış Model_ID'nin `global.` ile başladığını doğrulamak.
4. IF `global.anthropic.claude-sonnet-5` ile converse çağrısı başarısız olursa, THEN THE Project_Setup SHALL hatayı raporlayıp başka bir model seçmeden Kullanıcı'dan karar istemek.
5. THE FEFO_Agent SHALL uygulama sınıfını `from bedrock_agentcore.runtime import BedrockAgentCoreApp` ifadesiyle içe aktarmak.
6. THE FEFO_Agent SHALL agent nesnesini, MCP_Client'ı ve Role_Hook'u modül yüklenirken değil `_get_agent` fonksiyonu içinde ilk çağrıda oluşturmak (lazy init).
7. THE Runtime_Dependencies SHALL yalnızca runtime'da gereken paketleri içermek ve `pandas` gibi ağır paketleri içermemek.
8. IF Model erişim hatası alınırsa, THEN THE Project_Setup SHALL `enable_anthropic_models` adımını uygulamayı ve 2-6 dakika beklemeyi Kullanıcı'ya bildirmek.
9. THE FEFO_Agent SHALL sistem prompt'unda tool'ları adlarıyla değil yetenekleriyle anlatmak.

### Requirement 6: Stub MCP, Adapter ve stdio Kuralları

**User Story:** As a Dev A geliştiricisi, I want Stub_MCP ile çalışan ve sonradan Fefo_MCP'ye geçilebilen bir agent'ı, so that Dev B'nin çıktısını beklemeden geliştirme yapabileyim.

#### Acceptance Criteria

1. THE Stub_MCP SHALL `FefoAgent/app/agent/fefo_mcp_stub/` altında bulunmak ve `get_expiry_risks`, `get_sku_profile`, `simulate_actions`, `create_action_drafts` ve `generate_report_file` tool'larının her biri için Tool_Contract şemasına uyan sabit yanıt dönmek.
2. THE MCP_Adapter SHALL yapılandırma değeriyle Stub_MCP veya Fefo_MCP arasında seçim yapmak.
3. THE MCP_Adapter SHALL seçilen MCP modülünü, FEFO_Agent'ı çalıştıran aynı Python yorumlayıcısıyla modül olarak alt süreç şeklinde başlatmak.
4. THE MCP_Adapter SHALL AWS kimlik bilgisi değişkenlerini, `AWS_REGION` değişkenini ve `REPORTS_BUCKET` değişkenini alt sürece açıkça geçirmek ve mevcut ortamın kopyasını aktarmak. Ortam hiçbir zaman ekrana veya loga yazılmaz.
5. THE Stub_MCP SHALL stdout'a hiçbir çıktı yazmamak ve tüm logları stderr'e yazmak.
6. THE Fefo_MCP SHALL stdout'a hiçbir çıktı yazmamak ve tüm logları stderr'e yazmak.
7. THE MCP_Adapter SHALL MCP alt sürecinin veri dosyalarını paket içinden göreli yolla okumasını sağlamak.
8. WHEN yapılandırma Fefo_MCP'yi seçtiğinde, THE MCP_Adapter SHALL FEFO_Agent kodunda başka değişiklik gerektirmeden tool çağrılarını Fefo_MCP'ye yönlendirmek.
9. IF Fefo_MCP seçilmiş ancak modül içe aktarılamıyorsa, THEN THE MCP_Adapter SHALL hata nedenini stderr'e loglayıp başlatmayı durdurmak.
10. WHEN Dev B `fefo_mcp` export ettiğinde, THE Project_Setup SHALL Stub_MCP'yi silip MCP_Client'ı Fefo_MCP'ye bağlamak.
11. WHEN Fefo_MCP bağlandığında, THE FEFO_Agent SHALL Stub_MCP ile aynı Tool_Contract testlerini geçmek.
12. THE Project_Setup SHALL `FefoAgent/app/agent/fefo_core`, `fefo_mcp` ve `data` export klasörlerini elle düzenlememek.

### Requirement 7: Tool Kontratları

**User Story:** As a FEFO operatörü, I want agent'ın tool'ları kontrata uygun kullanmasını, so that stok ve SKT yanıtları tutarlı olsun.

#### Acceptance Criteria

1. THE FEFO_Agent SHALL tool girdi ve çıktılarını JSON olarak işlemek, para alanlarını `_try`, miktar alanlarını `_units` son ekiyle ve tarihleri ISO biçiminde ele almak.
2. THE `get_expiry_risks` SHALL `as_of_date?`, `category?` (`COLD` veya `DRY`), `min_loss_try?` (varsayılan 0) ve `top_n?` (varsayılan 10) girdilerini kabul etmek.
3. THE `get_expiry_risks` SHALL `as_of_date`, `total_expected_loss_try` ve her öğede `sku_id`, `sku_name`, `category`, `lot_id`, `qty_units`, `expiry_date`, `days_to_expiry`, `location_bin`, `sellable_window_days`, `forecast_units_in_window`, `at_risk_units`, `loss_try`, `risk_level` (`LOW`, `MEDIUM`, `HIGH`), `reason_codes`, `forecast_confidence` (`HIGH`, `MEDIUM`, `LOW`) ve `wape` alanlarını içeren çıktı dönmek.
4. THE `get_expiry_risks` SHALL `forecast_units_in_window`, `at_risk_units` ve `loss_try` alanlarını `low`, `expected` ve `high` değerleriyle dönmek ve öğeleri `loss_try.expected` değerine göre azalan sıralamak.
5. THE `get_sku_profile` SHALL `sku_id` girdisini kabul edip `sku`, `daily_velocity` (`avg_7d`, `avg_30d`, `trend_pct`), `weekday_factors` (`Mon`..`Sun`), `forecast_method`, `wape`, `lots`, `dealers` ve `signals` alanlarını içeren çıktı dönmek.
6. THE `get_sku_profile` SHALL her `lots` öğesinde `lot_id`, `qty_units`, `expiry_date`, `location_bin` ve `last_shipped_date` alanlarını, her `dealers` öğesinde `dealer_id`, `dealer_type`, `share_pct`, `avg_daily_units`, `last_order_date`, `days_since_last_order`, `min_days_on_receipt` ve `eligible_for_lot_ids` alanlarını dönmek.
7. THE `simulate_actions` SHALL `lot_id`, `actions` (`type` ve `params` çiftleri, verilen sırayla uygulanır) ve `as_of_date?` girdilerini kabul etmek.
8. THE `simulate_actions` SHALL aksiyon parametrelerini `FEFO_PRIORITY` için parametresiz, `DEALER_OFFER` için `{dealer_ids?, discount_pct}`, `CAMPAIGN` için `{discount_pct}`, `DONATION` için `{units?}` ve `SUPPLIER_RETURN` için `{units?}` olarak kabul etmek.
9. THE `simulate_actions` SHALL `lot_id`, `baseline_loss_try`, `steps`, `final_loss_try` ve `total_net_benefit_try` alanlarını dönmek ve her adımda `action`, `params`, `feasible`, `infeasible_reason?`, `units_saved`, `loss_after_try`, `action_cost_try`, `net_benefit_try`, `kg_saved` ve `policy_refs` alanlarını içermek.
10. THE `create_action_drafts` SHALL `lot_id`, `approved_actions` ve `approver_actor_id` girdilerini kabul etmek.
11. THE `create_action_drafts` SHALL `decision_id`, `status` (`DRAFT`), `drafts` (her biri `audience`, `subject`, `body`) ve `summary` (`final_loss_try`, `total_net_benefit_try`, `kg_saved`) alanlarını dönmek.
12. THE `create_action_drafts` SHALL `audience` değerini `WAREHOUSE`, `COMMERCIAL`, `SUPPLIER`, `DEALER` veya `DONATION_PARTNER` kümesinden seçmek.
13. WHEN `create_action_drafts` çağrıldığında, THE Fefo_MCP SHALL kararı `s3://$REPORTS_BUCKET/decisions/<decision_id>.json` anahtarına kaydetmek.
14. THE Policy_Search_Tool SHALL `search_policies` adıyla, `query` girdisini kabul etmek ve Policy_Docs içinden ilgili pasajları ile `POL-x` veya `PRC-x` madde numaralarını dönmek.
15. THE Policy_Search_Tool SHALL FEFO_Agent içinde yerel tool olarak çalışmak ve Fefo_MCP üzerinden sunulmamak.
16. THE FEFO_Agent SHALL tool docstring'lerinin tool yeteneğini açık anlatmasını sağlamak.
17. THE Project_Setup SHALL Tool_Contract'ta değişiklik yapmadan önce iki geliştiricinin onayını istemek.

### Requirement 8: Hata Formatı ve Varsayılan Tarih

**User Story:** As a FEFO operatörü, I want hataların ve tarih varsayılanının tutarlı olmasını, so that yanıtlar öngörülebilir olsun.

#### Acceptance Criteria

1. IF bir tool çağrısı hata ile sonuçlanırsa, THEN THE Stub_MCP SHALL exception fırlatmak yerine Tool_Error biçiminde `code` ve `message` alanlarını içeren yanıt dönmek.
2. IF bir tool çağrısı hata ile sonuçlanırsa, THEN THE Fefo_MCP SHALL exception fırlatmak yerine Tool_Error biçiminde `code` ve `message` alanlarını içeren yanıt dönmek.
3. IF bir tool Tool_Error dönerse, THEN THE FEFO_Agent SHALL hata kodunu içeren bir yanıt üretmek ve uydurma veri eklememek.
4. WHEN `as_of_date` verilmeden bir tool çağrıldığında, THE Stub_MCP SHALL Default_As_Of_Date değerini kullanmak.
5. WHEN `as_of_date` verilmeden bir tool çağrıldığında, THE Fefo_MCP SHALL Default_As_Of_Date değerini kullanmak.
6. IF bir tool yanıtı Tool_Contract çıktı şemasına uymuyorsa, THEN THE FEFO_Agent SHALL şema ihlalini loglayıp kullanıcıya tool yanıtının geçersiz olduğunu bildirmek.

### Requirement 9: Rol Hook'u ve Onay Matrisi

**User Story:** As a sistem yöneticisi, I want rol bazlı onay kontrolü, so that her kullanıcı yalnızca rolünün izin verdiği aksiyonları onaylatsın.

#### Acceptance Criteria

1. WHEN bir istek alındığında, THE Role_Hook SHALL istek yükündeki `actorId` değerinden çağıranın rolünü belirlemek.
2. THE Role_Hook SHALL `actorId` değerini `<rol>-<isim>` biçiminde ve yalnızca harf, rakam ve tire içeren Actor_Id olarak doğrulamak ve yalnızca `depo` ile `ticari` rollerini geçerli saymak. Bilinmeyen rol reddedilir.
3. THE Role_Hook SHALL Strands `BeforeToolCallEvent` hook'u olarak kaydedilmek ve `create_action_drafts` tool çağrısını denetlemek.
4. THE Role_Action_Matrix SHALL `FEFO_PRIORITY`, `DONATION`, `SUPPLIER_RETURN` ve `generate_report_file` için `depo` ve `ticari` rollerine izin vermek.
5. THE Role_Action_Matrix SHALL `DEALER_OFFER` ve `CAMPAIGN` için yalnızca `ticari` rolüne ve Max_Discount_Pct_By_Role sınırları içinde izin vermek.
6. WHEN `create_action_drafts` çağrılmadan önce, THE Role_Hook SHALL `approved_actions` içindeki her aksiyonu çağıranın rolüne göre Role_Action_Matrix ile karşılaştırmak.
7. IF `approved_actions` içinde çağıranın rolünün yetkisi dışında bir aksiyon varsa, THEN THE Role_Hook SHALL tool çağrısını iptal edip agent'a "bu aksiyon için ticari onayı gerekir" yanıtını dönmek.
8. IF çağrı Role_Hook tarafından iptal edilirse, THEN THE FEFO_Agent SHALL konuşmayı sonlandırmadan sürdürmek.
9. IF indirimli bir aksiyonda (`DEALER_OFFER`, `CAMPAIGN`) `discount_pct` eksikse, sayısal değilse, 0-100 aralığı dışındaysa veya çağıranın rolü için Max_Discount_Pct_By_Role sınırını aşıyorsa, THEN THE Role_Hook SHALL tool çağrısını iptal etmek.
10. IF `actorId` eksikse veya Actor_Id biçimine uymuyorsa, THEN THE Role_Hook SHALL isteği reddedip rolün belirlenemediğini bildirmek.
11. THE Role_Hook SHALL her izin ve ret kararını rol, Actor_Id, tool adı ve karar bilgileriyle loglamak.
12. WHEN `create_action_drafts` çağrıldığında, THE FEFO_Agent SHALL `approver_actor_id` alanına doğrulanmış Actor_Id değerini yazmak.

### Requirement 10: Soru-Cevap Davranışı

**User Story:** As a FEFO operatörü, I want agent'a doğal dilde soru sorabilmeyi, so that süreç, veri ve rapor ihtiyaçlarıma hızlı yanıt alayım.

#### Acceptance Criteria

1. WHEN kullanıcı bir süreç sorusu sorduğunda (ör. "FEFO nasıl işliyor?", "Kampanyayı kim onaylar?"), THE FEFO_Agent SHALL `search_policies` tool'unu çağırıp yanıtta `PRC-x` veya `POL-x` madde numarasını belirtmek.
2. WHEN kullanıcı bir veri sorusu sorduğunda, THE FEFO_Agent SHALL ilgili tool'u çağırıp yanıtı tool çıktısına dayandırmak.
3. WHEN kullanıcı PDF veya Excel dosyası istediğinde, THE FEFO_Agent SHALL `generate_report_file` tool'unu çağırıp yanıtta `download_url` indirme linkini sunmak.
4. IF sorunun yanıtı ne Knowledge_Base'de ne de tool çıktısında bulunuyorsa, THEN THE FEFO_Agent SHALL "bu bilgi elimdeki verilerde yok" yanıtını vermek.
5. THE FEFO_Agent SHALL tool çıktısında veya Policy_Docs'ta yer almayan stok, parti, tarih veya kural bilgisini yanıta eklememek.
6. WHEN kullanıcı Türkçe soru sorduğunda, THE FEFO_Agent SHALL yanıtı Türkçe vermek.
7. WHEN kullanıcı "%20 indirim olsa?" gibi bir what-if sorusu sorduğunda, THE FEFO_Agent SHALL `simulate_actions` tool'unu yeni parametreyle çağırıp sonucu yeniden hesaplatmak.
8. WHEN FEFO_Agent bir risk listesi sunduğunda, THE FEFO_Agent SHALL karar akışını risk listesi, neden, simülasyon, öneri, onay ve taslaklar sırasıyla izlemek.
9. WHILE bir öğenin `forecast_confidence` değeri `LOW` iken, THE FEFO_Agent SHALL o öğe için düşük güvenli tahmin uyarısı sunmak.
10. THE FEFO_Agent SHALL verileri "temsili senaryo" olarak sunmak.

### Requirement 11: Rakam Kuralı

**User Story:** As a FEFO operatörü, I want rakamların yalnızca tool çıktısından gelmesini, so that sayısal yanıtlar doğrulanabilir olsun.

#### Acceptance Criteria

1. THE FEFO_Agent SHALL adet, gün ve ₺ değerlerini yalnızca tool çıktısından aldığı haliyle yanıta yazmak.
2. THE FEFO_Agent SHALL toplama, çıkarma, oran veya yuvarlama gibi hiçbir sayısal hesabı kendisi yapmamak.
3. IF kullanıcı tool çıktısında bulunmayan bir sayısal değer isterse, THEN THE FEFO_Agent SHALL değeri hesaplatmak için uygun tool'u çağırmak.
4. IF uygun bir tool bulunmuyorsa, THEN THE FEFO_Agent SHALL değerin elimdeki verilerde olmadığını belirtmek.
5. THE FEFO_Agent SHALL ₺ değerlerini Türkçe biçimde sunmak.
6. THE FEFO_Agent SHALL `generate_report_file` için `summary_text` alanına yeni rakam eklememek.

### Requirement 12: Asla Gönderme Kuralı ve Taslaklar

**User Story:** As a depo veya ticari yetkilisi, I want agent'ın yalnızca taslak üretmesini, so that hiçbir mesaj onayım olmadan gönderilmesin.

#### Acceptance Criteria

1. THE FEFO_Agent SHALL mail veya mesajı kendi başına göndermemek.
2. IF kullanıcı "maili gönder" gibi bir gönderim isterse, THEN THE FEFO_Agent SHALL isteği reddedip yalnızca taslak hazırlayabileceğini bildirmek.
3. THE `create_action_drafts` SHALL her taslağın `body` alanını Draft_Header ile başlatmak.
4. THE FEFO_Agent SHALL `create_action_drafts` tool'unu yalnızca kullanıcı aksiyonları açıkça onayladıktan sonra çağırmak.
5. IF kullanıcı henüz onay vermediyse, THEN THE FEFO_Agent SHALL kararı kesinleştirmemek ve onay istemek.
6. IF bir aksiyon çağıranın rolünün yetkisi dışındaysa, THEN THE FEFO_Agent SHALL aksiyonu onaylatmamak.
7. THE FEFO_Agent SHALL taslakları depo, ticari ve tedarikçi hedef kitleleri için sunmak.

### Requirement 13: Rapor Dosyaları

**User Story:** As a FEFO operatörü, I want PDF veya Excel rapor ve indirme linki almayı, so that bulguları paylaşabileyim.

#### Acceptance Criteria

1. THE `generate_report_file` SHALL `report_type` (`DAILY_RISK`, `LOT_ACTION_PLAN`, `RISK_TABLE`), `format` (`pdf`, `xlsx`), `lot_id?`, `decision_id?`, `summary_text?` ve `as_of_date?` girdilerini kabul etmek.
2. IF `report_type` değeri `LOT_ACTION_PLAN` ise ve `lot_id` verilmemişse, THEN THE `generate_report_file` SHALL Tool_Error dönmek.
3. THE `generate_report_file` SHALL `file_id`, `file_name`, `format`, `s3_key`, `download_url`, `expires_in_sec` ve `size_bytes` alanlarını dönmek.
4. THE Fefo_MCP SHALL raporu `s3://$REPORTS_BUCKET/reports/<as_of_date>/<file_id>.<ext>` anahtarına yazmak.
5. THE Fefo_MCP SHALL `download_url` değerini yaklaşık 1 saat geçerli presigned URL olarak üretmek.
6. IF rapor S3'e yazılamazsa, THEN THE Fefo_MCP SHALL Tool_Error dönmek ve FEFO_Agent SHALL kullanıcıya hata kodunu bildirmek.
7. THE Project_Setup SHALL en az PDF rapor akışını kesilmeyecek kapsamda tutmak.

### Requirement 14: Knowledge Base ve Fallback

**User Story:** As a FEFO operatörü, I want politika ve süreç bilgisine Knowledge_Base veya yedek kaynaktan ulaşmayı, so that süreç soruları her durumda yanıtlansın.

#### Acceptance Criteria

1. THE FEFO_Agent SHALL Knowledge_Base kimliğini `KNOWLEDGE_BASE_ID` ortam değişkeninden okumak.
2. WHERE `KNOWLEDGE_BASE_ID` tanımlıysa, THE Policy_Search_Tool SHALL Knowledge_Base'i sorgulamak.
3. IF `KNOWLEDGE_BASE_ID` tanımlı değilse veya Knowledge_Base erişilemezse, THEN THE Policy_Search_Tool SHALL KB_Fallback davranışına geçmek.
4. THE KB_Fallback SHALL paketlenmiş `policy.md` ve `process_guide.md` dosyalarında arama yapmak ve Policy_Search_Tool ile aynı Tool_Contract çıktısını dönmek.
5. WHILE KB_Fallback etkinken, THE FEFO_Agent SHALL tool tabanlı yanıtları sunmaya devam etmek.
6. WHILE KB_Fallback etkinken, THE FEFO_Agent SHALL süreç yanıtında Knowledge_Base kullanılamadığını belirtmek.
7. IF Knowledge_Base oluşturulamıyorsa, THEN THE Project_Setup SHALL iki md dosyasını pakete dahil edip yerel `search_policies` ile devam etmek.

### Requirement 15: Kritik Teknik Kurallar, IAM ve Gözlemlenebilirlik

**User Story:** As a Dev A geliştiricisi, I want kritik teknik kuralların requirement olarak izlenmesini, so that deploy hatasız çalışsın.

#### Acceptance Criteria

1. THE Agentcore_Config SHALL IAM izinlerini yalnızca `additionalPolicies` alanıyla tanımlamak.
2. THE Agentcore_Config SHALL AgentCore_Runtime ortam değişkenlerine `REPORTS_BUCKET` değerini `fefo-862714237836-us-east-1` olarak, `MODEL_ID` değerini `global.anthropic.claude-sonnet-5` olarak ve `MCP_BACKEND` değerini `stub` olarak eklemek.
3. THE Agentcore_Config SHALL `additionalPolicies` içinde Reports_Bucket için `reports/*` ve `decisions/*` önekleri üzerinde `s3:PutObject` ve `s3:GetObject` izinlerini tanımlamak.
4. WHERE `KNOWLEDGE_BASE_ID` tanımlıysa, THE Agentcore_Config SHALL `additionalPolicies` içinde Knowledge_Base ARN'si için `bedrock:Retrieve` ve `*` kaynağı için `bedrock:RetrieveAndGenerate` izinlerini tanımlamak.
5. THE Agentcore_Config SHALL AgentCore_Runtime ortam değişkenlerine `UNIFIED_TRACES_DESTINATION_ENABLED=true` değerini eklemek.
6. WHEN AgentCore_Runtime'a bir invoke yapıldığında, THE AgentCore_Runtime SHALL tool span'lerini AgentCore Observability üzerinden CloudWatch'a iletmek.
7. WHEN `agentcore invoke` komutu kullanılırken, THE Project_Setup SHALL `--session-id` değerini en az 33 karakterle belgelemek.
8. THE Project_Setup SHALL test prompt'larında Türkçe kesme işareti kullanmamak.
9. THE Project_Setup SHALL Kritik_Teknik_Kurallar listesini (global. Model_ID, BedrockAgentCoreApp import yolu, lazy init, runtime'da ağır paket yok, IAM yalnızca `additionalPolicies`, `--session-id` en az 33 karakter, kesme işaretsiz test prompt'ları, AgentCore_CLI 1.0.3 güncellenmez) Steering_Files içinde tutmak.

### Requirement 16: Deploy ve Doğrulama Sorumluluğu

**User Story:** As a Kullanıcı, I want deploy ve doğrulama adımlarını kendim çalıştırabilmeyi veya asistana açıkça yetkilendirebilmeyi, so that AWS kaynak değişiklikleri kontrolümde kalsın.

#### Acceptance Criteria

1. THE Project_Setup SHALL `agentcore deploy`, `agentcore invoke`, `agentcore status` ve `agentcore logs` komutlarını yalnızca Kullanıcı'nın bu oturumda açıkça verdiği yetkiyle çalıştırmak. Kullanıcı bu yetkiyi vermiştir. Komutlar ayrıca Kullanıcı tarafından Kiro IDE Browser terminalinde de çalıştırılabilir ve belgelenir. Komut çalıştırmadan önce `~/.npm-global/bin` dizininin PATH'te olduğu doğrulanır.
2. WHEN deploy hazırlığı tamamlandığında, THE Project_Setup SHALL deploy öncesi yerel kontrol listesini (yapılandırma, Model_ID, bölge, hesap, `REPORTS_BUCKET`, `additionalPolicies`) raporlamak.
3. THE Project_Setup SHALL Verification_Set'in beş adımını komutlarıyla ve beklenen başarılı çıktısıyla belgelemek.
4. THE Verification_Set SHALL `agentcore status` ile runtime'ın deployed olduğunu ve ARN'nin göründüğünü doğrulamak.
5. THE Verification_Set SHALL `agentcore invoke --runtime agent` komutunu `{"prompt":"Bugun riskli urunler neler? Bir aracini cagir ve sonucu goster.","actorId":"depo-test"}` yüküyle çalıştırıp yanıtın tool verisi içerdiğini doğrulamak.
6. THE Verification_Set SHALL `aws logs describe-log-groups --log-group-name-prefix /aws/bedrock-agentcore/runtimes/` ile `-DEFAULT` log grubunu ve `agentcore traces runtime list --since 15m` ile invoke'un trace'ini doğrulamak.
7. THE Verification_Set SHALL `.kiro/specs/<isim>/` dizininin agent'ın nasıl yapıldığını belgelediğini doğrulamak.
8. THE Verification_Set SHALL `agentcore traces runtime get <trace-id>` çıktısında `fefo_mcp` tool span'lerinin göründüğünü doğrulamak.
9. WHEN her deploy tamamlandığında, THE Project_Setup SHALL Verification_Set'in tekrarlanmasını Kullanıcı'ya bildirmek.
10. THE Project_Setup SHALL deploy sonrası değişikliklerin commit edilmesini deploy ritüelinin son adımı olarak belgelemek.

### Requirement 17: Fallback Davranışları

**User Story:** As a Dev A geliştiricisi, I want bilinen arızalar için tanımlı çözüm yollarını, so that demo kesintiye uğramasın.

#### Acceptance Criteria

1. IF stdio MCP runtime'da açılmıyorsa, THEN THE Project_Setup SHALL `agentcore logs runtime --since 15m` komutuyla stdout'a print, yanlış modül yolu ve geçirilmeyen ortam değişkeni nedenlerini kontrol etmeyi belgelemek.
2. IF stdio MCP sorunu çözülemezse, THEN THE Project_Setup SHALL `fefo_core` fonksiyonlarını yerel `@tool` olarak bağlayıp Tool_Contract'ı değiştirmeden sürdürmek.
3. IF rapor S3'e yazılamıyorsa, THEN THE Project_Setup SHALL `REPORTS_BUCKET` değerini, `additionalPolicies` içindeki S3 iznini ve ortamın alt sürece geçirilip geçirilmediğini kontrol etmeyi belgelemek.
4. THE Project_Setup SHALL runtime deploy, observability, `fefo_mcp` (stdio), politika ve süreç bilgisi (Knowledge_Base veya KB_Fallback), onay akışı ile taslaklar ve en az PDF raporu kesilmeyecek kapsam olarak korumak.

### Requirement 18: Test, Eval ve Kapsam Sınırı

**User Story:** As a Dev A geliştiricisi, I want testlerin ve kapsam sınırının belirgin olmasını, so that Plan 1 teslimi doğrulanabilir olsun.

#### Acceptance Criteria

1. THE Repo SHALL Stub_MCP ile çalışan ve her Tool_Contract çıktı şemasını doğrulayan birim testlerini içermek.
2. THE Repo SHALL Role_Hook karar yollarını (izin, ret, rol belirsiz, indirim sınırı aşımı) kapsayan testleri içermek.
3. THE Repo SHALL MCP_Adapter'ın Stub_MCP ve Fefo_MCP seçim durumlarını kapsayan testleri içermek.
4. THE Eval_Set SHALL rakamların tool çıktısıyla birebir eşleştiğini doğrulamak.
5. THE Eval_Set SHALL süreç sorularının madde numarasıyla yanıtlandığını doğrulamak.
6. THE Eval_Set SHALL "maili gönder" isteğinin reddedilip yalnızca taslak üretildiğini doğrulamak.
7. THE Eval_Set SHALL `depo` rolünün kampanyayı onaylatamadığını ve `ticari` rolünün onaylatabildiğini doğrulamak.
8. THE Eval_Set SHALL "%20 indirim olsa?" sorusunun yeniden hesaplandığını doğrulamak.
9. WHERE Plan 2 veya Plan 3 kapsamında bir özellik talep edilirse, THE Project_Setup SHALL talebi Plan 1 dışı olarak işaretleyip uygulamamak.
10. IF Plan 1 testleri başarılı değilse, THEN THE Project_Setup SHALL Plan 2 ve Plan 3 çalışmasını başlatmamak.

## Test Kapsamı Kararı

Bu oturumda yalnızca Tool kontrat testleri (Stub_MCP kontrat doğrulaması) aktiftir. Aşağıdakiler şimdilik atlandı: Requirement 18.1 dışındaki birim testleri (Role_Hook, MCP_Adapter, search_policies, yapılandırma), tüm property-based testler ve Eval_Set (18.4-18.8). Atlanan testlerin gereksinimleri geçerliliğini korur, yalnızca bu aşamada yazılmaz ve çalıştırılmaz. Requirement 18.2 ve 18.3 için testler şimdilik atlandı. Requirement 18.10 bu oturumda yalnızca aktif kontrat testleri için geçerlidir.

## Açık Girdiler

Kesinleşen değerler: S3 bucket `fefo-862714237836-us-east-1`, Model_ID `global.anthropic.claude-sonnet-5`, Python 3.12, Max_Discount_Pct_By_Role için `config.py` varsayılanı. Bekleyen girdiler:

- Remote_Repo URL'si (GitHub deposu henüz yok). Yerel `git init` yapılır, `origin` sonra eklenir.
- Knowledge_Base ID (`KNOWLEDGE_BASE_ID`) henüz yok. `search_policies` KB_Fallback ile çalışır. ID gelince `agentcore.json` içine eklenir.
- Dev B export'u (`fefo_core`, `fefo_mcp`, `data`). Gelene kadar `MCP_BACKEND=stub`.

Plan 2 ve Plan 3 kapsam dışıdır.
