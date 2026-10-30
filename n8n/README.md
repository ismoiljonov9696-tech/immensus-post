# Immensus autopost — n8n ulash

Bu workflow n8n'ni markaziy jadval sifatida ishlatadi. Post yaratish, rasm,
sifat nazorati va Telegramga chiqarish GitHub Actions ichidagi mavjud kodda
qoladi. n8n faqat ishlarni ishonchli vaqtda uyg'otadi.

## Jadval (Asia/Tashkent)

- 20:00 — Immensus Post uchun 1 ta, Immensus Cargo uchun 1 ta post tayyorlash.
- 05:00 — ikkala kanalning 07:00 post kuzatuvchisini ishga tushirish.

Kuzatuvchi GitHub ichida har daqiqa vaqtni tekshiradi va postni 07:00 da
chiqaradi. Bu GitHub cron navbati kechikishining oldini oladi.

Immensus Post ichidagi `generate.yml` to'liq zanjirni bajaradi: OpenAI Web
Search → 2+ manba tekshiruvi → post yozish → rasm → sifat nazorati → navbat.

## 1. GitHub token yaratish

GitHub'da **Settings → Developer settings → Personal access tokens →
Fine-grained tokens → Generate new token** bo'limiga kiring.

- Repository access: faqat `immensus-post` va `TG-Immensus_cargo`.
- Repository permissions → Actions: **Read and write**.
- Metadata: **Read-only** (avtomatik qo'shiladi).

Tokenni chatga yoki workflow JSON ichiga yozmang.

## 2. n8n credential yaratish

n8n'da **Credentials → New credential → Header Auth** ni tanlang:

- Credential name: `GitHub Actions Token`
- Name: `Authorization`
- Value: `Bearer YOUR_GITHUB_FINE_GRAINED_TOKEN`

Saqlang.

## 3. Workflowni import qilish

1. n8n'da **Workflows → Add workflow → Import from file** ni bosing.
2. `immensus-autopost-orchestrator.json` faylini tanlang.
3. Har bir GitHub HTTP Request node'ida `GitHub Actions Token` credentialini
   tanlang. Importdan keyin qizil ogohlantirishlar shundan yo'qoladi.
4. Workflow settings ichida timezone `Asia/Tashkent` ekanini tekshiring.
5. Avval bittadan HTTP node'ni **Execute step** bilan sinang. GitHub Actions
   sahifasida yangi workflow run paydo bo'lsa ulanish ishlayapti.
6. Workflowni **Save**, keyin **Publish/Active** qiling.

## Muhim

- n8n ishlayotgan server doim yoqilgan bo'lishi kerak.
- `OPENAI_API_KEY`, Telegram tokeni va kanal ID'lari n8n'ga ko'chirilmaydi;
  ular ikkala GitHub reposidagi Secrets ichida qoladi.
- Dastlab GitHub'dagi eski `schedule` triggerlari zaxira sifatida qoldiriladi.
  n8n bir necha kun barqaror ishlagach, takroriy ishlar ko'rinsa ularni
  o'chirish mumkin.
