# FEFO Politikası (sentetik taslak — içeriğin sahibi L)

> Bu dosya `data-gen/generate.py` tarafından üretilen kısa bir yer tutucudur. Sayılar `config/params.json` ile aynıdır.

- **POL-1.1** FEFO: Son kullanma tarihi en yakın uygun lot önce sevk edilir.
- **POL-1.2** Bayi kabul kuralı: Bir lot, `(SKT - sevk günü) >= min_days_on_receipt` ise o bayiye sevk edilebilir. Zincir bayilerde COLD için 6-7, DRY için 45-50 gün; geleneksel bayilerde COLD için 3-4, DRY için 20-22 gün.
- **POL-2.1** Bayiye özel teklif (DEALER_OFFER): `ticari` rolü en fazla %20 indirim onaylayabilir.
- **POL-2.2** Kampanya (CAMPAIGN): `ticari` rolü en fazla %25 indirim onaylayabilir.
- **POL-3.1** Bağış (DONATION): SKT'ye en az 1 gün kalmış olmalıdır.
- **POL-3.2** Tedarikçi iadesi (SUPPLIER_RETURN): ürün iadeye uygunsa ve SKT'ye en az 4 gün varsa yapılır; geri kazanım maliyetin %60'ıdır.
- **POL-4.1** Onay: `depo` FEFO, bağış ve iade aksiyonlarını; `ticari` bunlara ek olarak indirimli aksiyonları onaylar. Ajan hiçbir mesajı kendi başına göndermez.
