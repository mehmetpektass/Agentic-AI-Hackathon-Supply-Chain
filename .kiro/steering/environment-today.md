---
inclusion: always
---

# Ortam durumu (2026-11-25)

Bu ortam workshop'un hazır IDE'si değil. Aşağıdakiler gerçek durumu yansıtır.

## Workshop yardımcı komutları
`create_knowledge_base`, `enable_anthropic_models`, `create_backend_systems` ve `cleanup_workshop` bu ortamda YOK. Bunları çalıştırmayı deneme. Karşılığı gereken işi AWS CLI / agentcore CLI / CDK ile yap.

## IDE proxy'si
- `$IDE_URL` tanımlı DEĞİL.
- Kiro tarayıcıda çalışıyor (code-server). `VSCODE_PROXY_URI=https://d3iphfa9i8xj8o.cloudfront.net/proxy/{{port}}/` mevcut.
- Chat UI: `$IDE_URL` yok, bu yüzden `localhost:8888` üzerinde çalışır. Tarayıcıdan erişim için CloudFront proxy'si `https://d3iphfa9i8xj8o.cloudfront.net/proxy/8888/` denenebilir (doğrulanmadı).

## AWS
- Hesap: 862714237836
- Bölge: us-east-1 (`AWS_REGION` ve `AWS_DEFAULT_REGION` env değişkeninden)
- Kimlik: EC2 instance role (`WSParticipantRole`), geçici kimlik bilgileri. Profil yok.
- S3 bucket: `fefo-862714237836-us-east-1` (public erişim kapalı, SSE-S3). `S3_BUCKET_NAME` env değişkeni tanımlı değil, bu adı kullan.
- Bedrock: `ws-bedrock-model-allowlist-policy-1` açık deny uygular. Politikayı değiştirmeye çalışma.
- **İzinli agent modeli: `global.anthropic.claude-sonnet-5`; sonnet-5-5 yasak** (AccessDenied). Steering dosyalarındaki örnek model ID'leri yerine bunu kullan. `global.anthropic.claude-sonnet-5` ile converse testi 2026-11-25'te başarılı.
- AgentCore: `aws bedrock-agentcore-control list-agent-runtimes` çalışıyor (şu an runtime yok).

## Kurulu araçlar
| Araç | Sürüm |
|---|---|
| OS | Amazon Linux 2023, x86_64 |
| node | v24.22.3 |
| npm | 11.19.1 (global prefix: `~/.npm-global`) |
| python3 (sistem) | 3.9.25 (kullanma) |
| Python (proje) | 3.12.16, uv ile kurulu, `.python-version` = 3.12 |
| uv / uvx | 0.13.9 |
| cdk | 2.1149.0 |
| @aws/agentcore | 1.0.3 (sabit, güncelleme yapma) |
| docker | 25.0.14 |
| git | 2.50.1 |
| jq | 1.8.1 |
| aws cli | 2.42.2 |

PATH'e `~/.npm-global/bin` eklendi (`~/.bashrc`). Yeni terminal gerekebilir.

## Steering ve MCP
- `.kiro/steering/agentcore-deployment.md` ve `strands-agent-coding.md` workspace'te mevcut (orijinal workshop dosyaları, değiştirme).
- Workspace `.kiro/settings/mcp.json`: `strands-agents`, `bedrock-agentcore-mcp-server`. İkisi de başlatılıp `initialize` yanıtı verdi.
- Kullanıcı seviyesi `~/.kiro/settings/mcp.json`: `aws-mcp`.

## Güvenlik
Tüm ortam değişkenlerini basan komut (`env`, `printenv`, `set`) çalıştırma. Gereken değişkeni adıyla kontrol et.
