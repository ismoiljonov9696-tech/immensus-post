# Immensus Post — avtomatik Telegram kontent tizimi

Bu loyiha `@immensuspost` kanaliga har kuni Toshkent vaqti bilan **09:00** va
**19:00** da post chiqaradi.

Jarayon:

1. Agent internetdan Taobao, 1688, Pinduoduo, Alibaba va AliExpress bo'yicha
   foydali, takrorlanmagan mavzu izlaydi.
2. Yozuvchi agent `style/examples.md` uslubida o'zbekcha post yozadi.
3. Nano Banana 4:5 formatda rasm yaratadi.
4. Haqiqiy `assets/logo.png` rasmning pastki o'ng burchagiga qo'yiladi.
5. Sifat agenti fakt, til, brend, narx, havola va formatni tekshiradi.
6. Post belgilangan vaqtda kanalga chiqadi va bot adminga xabar beradi.

Doimiy brend qoidalari:

- Brend: **Immensus Post**
- Avto kargo: **$6.2/kg**
- Avia kargo: **tez kunda** — faol xizmat yoki narx sifatida ko'rsatilmaydi
- Kanal: **@immensuspost**

## GitHub sozlamasi

Repository'ni private qiling va loyiha fayllarini uning ildiziga joylang.
`Settings → Secrets and variables → Actions` bo'limida uchta secret yarating:

- `TELEGRAM_BOT_TOKEN` — BotFather bergan yangi token
- `TELEGRAM_ADMIN_CHAT_ID` — post chiqqani haqida xabar oladigan shaxsiy chat ID
- `GEMINI_API_KEY` — Google AI Studio API kaliti

Muhim: oldin chatda yuborilgan Telegram tokenini BotFather'da `/revoke` qiling.
Yangi tokenni kodga yoki chatga yozmang.

Botni `@immensuspost` kanaliga **Post messages** huquqi bilan admin qiling.
Shaxsiy xabar olishingiz uchun botga avval `/start` yuboring.

## Birinchi sinov

1. GitHub'da `Actions → Tekshirish → Run workflow` ni ishga tushiring.
2. Barcha tekshiruvlar muvaffaqiyatli bo'lsa, `Actions → Postlarni tayyorlash`
   ichida workflow'ni qo'lda ishga tushiring.
3. `data/pending.json` ichida 2 ta tayyor post paydo bo'ladi.
4. Sinov postini darhol chiqarish kerak bo'lsa botga `/holat` yuboring yoki
   `Postlarni vaqtida chiqarish` workflow'ini ishga tushiring. Oddiy rejimda
   ular 09:00 va 19:00 ni kutadi.

## Bot buyruqlari

- `/holat` — navbat, oxirgi post va keyingi chiqish vaqti
- `/balans 10` — Gemini uchun ajratilgan balansni kuzatish
- `/pauza` — nashrni vaqtincha to'xtatish
- `/davom` — nashrni qayta yoqish
- `/yordam` — buyruqlar ro'yxati

## Mahalliy tekshiruv

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
$env:TELEGRAM_BOT_TOKEN = "YANGI_TOKEN"
$env:TELEGRAM_ADMIN_CHAT_ID = "SIZNING_CHAT_ID"
$env:GEMINI_API_KEY = "GEMINI_KALITI"
.venv\Scripts\python -m src.main check
```

Secretlarni `.env` faylida ishlatsangiz, bu faylni GitHub'ga yuklamang.

## Muhim fayllar

- `config.yaml` — kanal, narx, jadval, model va vizual sozlamalar
- `style/examples.md` — Immensus Post yozish uslubi
- `assets/logo.png` — yuborilgan Immensus Post logosi
- `.github/workflows/generate.yml` — kunlik 2 post tayyorlash
- `.github/workflows/tick.yml` — 09:00 va 19:00 da nashr qilish
- `data/` — mavzu arxivi va navbat

