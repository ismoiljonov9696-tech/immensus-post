"""Prepared Post-only campaign: reusable cards, no AI requests."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

CARDS = [
    ("post-stages-01", "Yukingiz qaysi\nbosqichda?", [
        "Ro‘yxatga olindi", "Xitoy ombori", "Reysga yuklandi", "Yo‘lda",
        "Bojxona", "O‘zbekiston ombori", "Yetkazilmoqda", "Topshirildi"],
     "Yashil belgi — qayd etilgan bosqich.\nOlib ketish uchun operator xabarini kuting.",
     "Yukingiz qayerda? Mini App → Yuklarim bo‘limidagi ✓ belgilar orqali bosqichlarni kuzating.\n\nYashil belgi — qayd etilgan bosqich, to‘q sariq chegara — joriy holat. Omborga kelish va mijozga topshirish alohida bosqichlardir. Olib ketish bo‘yicha operator xabarini kuting.\n\n@immensuspost"),
    ("post-cost-02", "Faqat tovar narxiga\nqaramang.", [
        "Tovar narxi", "+ Yetkazish haqi", "+ Zarur qadoqlash", "= Jami xarajat"],
     "Sotuvchidan qadoqlangan vazn va\no‘lchamlarni so‘rang. Operatorga yuboring.",
     "Arzon mahsulot har doim ham arzon xarid degani emas.\n\nBuyurtmadan oldin tovar narxi, tashish haqi va zarur qadoqlash xarajatini birga hisoblang. Katta yoki nozik mahsulot bo‘lsa, qadoqlangan vazn va o‘lchamlarni sotuvchidan so‘rang.\n\nAniq hisob uchun shu ma’lumotlarni operatorga yuboring.\n\n@immensuspost"),
    ("post-track-03", "Trek raqami.\nMahsulot nomi. Tayyor.", [
        "Yuklarim → Trek qo‘shish", "Trek raqamini kiriting",
        "Mahsulot nomini yozing", "Saqlang va kuzating"],
     "Masalan: bolalar krossovkasi.\nQabul qilinguncha yuk kutilmoqda holatida.",
     "Trek qo‘shishda ikki ma’lumot kerak:\n1. Trek raqami.\n2. Mahsulot nomi.\n\nMasalan: «Bolalar krossovkasi». Yuklaringizni shu nom bilan oson topasiz.\n\nTrek qo‘shilgan, ammo omborga hali kelmaganmi? U kutilayotgan yuk sifatida turadi. Qabul qilingach holati yangilanadi.\n\n@immensuspost"),
]

def font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans" + ("-Bold" if bold else "") + ".ttf",
        "C:/Windows/Fonts/arial" + ("bd" if bold else "") + ".ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    raise RuntimeError("Post uchun o‘qiladigan shrift topilmadi")

def render(card, path):
    _, title, rows, note, _ = card
    navy, orange = "#102d50", "#f47728"
    im = Image.new("RGB", (1080, 1350), "#fffaf2")
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1080, 18), fill=orange)
    d.text((70, 65), "IMMENSUS", font=font(34, True), fill=navy)
    d.text((310, 65), "POST", font=font(34, True), fill=orange)
    d.multiline_text((70, 160), title, font=font(58, True), fill=navy, spacing=10)
    y = 365
    h = 76 if len(rows) > 4 else 135
    for i, row in enumerate(rows):
        d.rounded_rectangle((70, y, 1010, y+h-12), radius=18, fill="#eaf0f5")
        d.ellipse((90, y+12, 130, y+52), fill=orange)
        d.text((102, y+17), str(i+1), font=font(23, True), fill="white")
        d.text((154, y+16), row, font=font(30, True), fill=navy)
        y += h
    d.rounded_rectangle((70, 1035, 1010, 1185), radius=20, fill=navy)
    d.multiline_text((100, 1070), note, font=font(29), fill="white", spacing=14)
    d.line((70, 1240, 1010, 1240), fill="#c8d2dc", width=2)
    d.text((70, 1270), "Xitoy → O‘zbekiston", font=font(26), fill=navy)
    d.text((740, 1270), "@immensuspost", font=font(26, True), fill=navy)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)
    return path

def prepare(cfg):
    """Queue once, respecting existing dates and media persistence. True = handled."""
    if cfg["channel"]["id"] != "@immensuspost":
        return False
    from . import main as app, store
    from .config import WORK, load_secrets
    from .telegram import Bot
    campaign_ids = {c[0] for c in CARDS}
    if store.meta().get("prepared_guides_202611_done"):
        return any(p["id"] in campaign_ids for p in store.queued())
    seen = {p["id"] for p in store.pending()}
    seen.update(p.get("post_id") for p in store.archive())
    missing = [c for c in CARDS if c[0] not in seen]
    if not missing:
        store.set_meta(prepared_guides_202611_done=True)
        return any(p["id"] in campaign_ids for p in store.queued())
    secrets = load_secrets(strict=False)
    bot = Bot(secrets.telegram_token)
    for card in missing:
        post_id, title, _, _, caption = card
        when = app.next_publish_time(cfg)
        media = render(card, WORK / post_id / "image.png")
        post = {
            "id": post_id, "title": title.replace("\n", " "),
            "rubric": "Immensus Post — foydali yo‘riqnoma", "text": caption,
            "kind": "photo", "file_id": None, "media_path": str(media),
            "publish_at": when.isoformat(), "created_at": store.now_iso(),
            "est_cost_usd": 0, "rewrites": 0, "status": "ready",
        }
        app.stash_media(secrets, bot, post, media, "photo")
        if not post.get("file_id"):
            raise RuntimeError("Tayyor post rasmi Telegramga saqlanmadi; navbatga qo‘shilmadi")
        if app.mode_of(cfg) != "off":
            post["status"] = "preview"
            app.send_preview(cfg, secrets, bot, post, media, "photo",
                             app.preview_header(cfg, post, {}, when, []))
        store.add_pending(post)
        store.remember(post["title"], post["rubric"], post_id, [])
        if not store.sync_to_remote("tayyor post navbati: " + post_id):
            raise RuntimeError("Post navbati saqlanmadi; qayta tekshirish kerak")
    store.set_meta(prepared_guides_202611_done=True)
    return True
