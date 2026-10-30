# Immensus Post — n8n ulash

Bu workflow faqat **Immensus Post** kanalini boshqaradi. Immensus Cargo bilan
hech qanday aloqa yoki node yo'q.

## Jadval (Asia/Tashkent)

- 20:00 — ertangi 07:00 uchun 1 ta rasmli post tayyorlanadi.
- 05:00 — GitHub kuzatuvchisi uyg'onadi.
- 07:00 — tayyor post Telegram kanaliga chiqariladi.

GitHub'dagi 06:11 ishga tushish faqat n8n ishlamasa zaxira hisoblanadi.
Navbat `--top-up 1` bilan to'ldirilgani sabab bir kunda ortiqcha post
tayyorlanmaydi.

## GitHub token

Fine-grained GitHub token yarating:

- Repository access: faqat `immensus-post`.
- Repository permissions → Actions: **Read and write**.
- Metadata: **Read-only**.

Tokenni JSON fayliga yoki chatga yozmang.

## n8n credential

n8n'da **Credentials → New credential → Header Auth**:

- Credential name: `GitHub Actions Token`
- Name: `Authorization`
- Value: `Bearer YOUR_GITHUB_FINE_GRAINED_TOKEN`

## Import va yoqish

1. **Workflows → Import from file** orqali
   `immensus-autopost-orchestrator.json` faylini import qiling.
2. Ikkala HTTP Request node'iga `GitHub Actions Token` credentialini ulang.
3. Workflow timezone `Asia/Tashkent` ekanini tekshiring.
4. HTTP node'larni bir martadan **Execute step** bilan sinang.
5. **Save**, so'ng **Publish/Active** qiling.

`OPENAI_API_KEY`, Telegram tokeni va kanal ID GitHub Secrets ichida qoladi.
