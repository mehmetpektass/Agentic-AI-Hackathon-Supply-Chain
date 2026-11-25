# FEFO Süreç Rehberi (sentetik taslak — içeriğin sahibi L)

> Bu dosya `data-gen/generate.py` tarafından üretilen kısa bir yer tutucudur.

- **PRC-1.1** Her sabah riskli lotlar listelenir; sıralama beklenen ₺ kaybına göredir.
- **PRC-1.2** Her lot için neden kodları gösterilir (ör. FIFO_VIOLATION, STRICT_DEALER_ONLY).
- **PRC-2.1** Risk seviyesi: beklenen kayıp 2.000 ₺'nin altında LOW, 10.000 ₺'ye kadar MEDIUM, üstü HIGH.
- **PRC-2.2** Kayıp şelalesi: aksiyonlar sırayla uygulanır; her adım kaybın ne kadar düştüğünü gösterir.
- **PRC-3.1** Onaydan sonra depo, ticari ekip ve tedarikçi için yalnızca TASLAK mesajlar hazırlanır.
- **PRC-3.2** Tahmin güveni LOW ise karar vermeden önce depo ekibi sayımı doğrular.
