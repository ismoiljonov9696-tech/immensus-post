# Immensus autopost — n8n ulash

Bu workflow ikki kanalni alohida boshqaradi. Ularning mavzulari va Telegram
kanallari bir-biriga aralashmaydi.

## Jadval (Asia/Tashkent)

- 20:00 — Immensus Post uchun 1 ta va Immensus Cargo uchun 1 ta ertangi post tayyorlanadi.
- 05:00 — ikkala kanalning alohida 07:00 kuzatuvchisi ishga tushadi.
- 07:00 — har bir kanalga o'z mavzusidagi bittadan post chiqadi.

Immensus Post faqat donalik va kichik onlayn xarid, Pinduoduo, Taobao, 1688,
Poizon/Dewu va Tmall qo'llanmalari haqida yozadi. Immensus Cargo professional
kargo mavzularini faqat o'z kanalida yozadi.

## GitHub token

GitHub'da fine-grained personal access token yarating:

- Repository access: `immensus-post` va `TG-Immensus_cargo`.
- Repository permissions → Actions: **Read and write**.
- Metadata: **Read-only**.

Tokenni chatga yoki JSON fayliga yozmang.

## n8n credential

n8n'da **Credentials → New credential → Header Auth**:

- Credential name: `GitHub Actions Token`
- Name: `Authorization`
- Value: `Bearer YOUR_GITHUB_FINE_GRAINED_TOKEN`

## Import va faollashtirish

1. **Workflows → Import from file** orqali `immensus-autopost-orchestrator.json` faylini import qiling.
2. To'rtta HTTP Request node'iga `GitHub Actions Token` credentialini tanlang.
3. Timezone `Asia/Tashkent` ekanini tekshiring.
4. Har bir HTTP node'ni **Execute step** bilan bir marta sinang.
5. GitHub Actions'da yangi run paydo bo'lsa, workflowni **Save** va **Publish/Active** qiling.

OpenAI va Telegram kalitlari n8n'ga ko'chirilmaydi; ular tegishli GitHub
reposining Secrets bo'limida qoladi.
