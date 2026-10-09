"""3-AGENT — RASSOM.

Post matnidan rasm tavsifi tuzadi va Nano Banana orqali rasm chizadi,
so'ng ustiga kompaniya logotipini qo'yadi.

Rasm mavzudan kelib chiqadi, mavzu esa rasmdan emas:
  1. Avval postning ASOSIY DARSI ajratiladi — post aynan nimani o'rgatyapti.
  2. Mavzuni bir qarashda tanitadigan 2–4 ta vizual tayanch ajratiladi.
  3. Shu darsni ko'rsatadigan UCHTA turli g'oya o'ylab topiladi va
     "aniqlik" hamda "kutilmaganlik" bo'yicha baholanadi. Avval aniqlik,
     keyin kutilmaganlik hisobga olinadi.
     Bitta so'rovda tavsif so'ralsa, model doim eng zerikarlisini beradi.
  3. Klishelar aniq taqiqlangan: quti uyumi, dunyo xaritasi, globus,
     qo'l siqish, o'suvchi diagramma.
  4. Kompozitsiya 7 ta uslubdan navbat bilan olinadi — lenta bir xil bo'lmaydi.
  5. Xitoy muhiti majburiy emas: sahna talab qilsa qo'yiladi, aks holda
     g'oya stol ustida yoki qo'lda ham ko'rsatilishi mumkin.
"""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from ..branding import apply_logo, apply_platform_logo, find_logo
from ..config import ROOT
from ..gemini import edit_image, generate_image, generate_json

LOG = logging.getLogger("agent3")

PROMPT_SYSTEM = """Siz reklama agentligining art-direktorisiz. Sizning ishingiz —
zerikarli, oldindan aytib bo'ladigan tasvirdan qochish.

Quyidagilar KLISHE va ular taqiqlanadi: bir-birining ustiga qalangan
bir xil qutilar, dunyo xaritasi ustidagi punktir chiziq, konteyner uyumi
umumiy planda, kompas, globus, qo'l siqish, ko'tarilayotgan diagramma,
sun'iy tabassumli ofis xodimi.

Yaxshi rasm bitta aniq g'oyani ko'rsatadi: tomoshabin post matnini o'qimasdan
ham mavzuni taxmin qila olishi kerak. Kutilmaganlik hech qachon mavzuning
aniqligidan ustun emas.

Odatda matn, harf, raqam, iyeroglif va logotip so'ramang. Faqat post aynan
Alipay, Taobao, 1688, Pinduoduo, Poizon/Dewu, Tmall yoki boshqa platforma haqida bo'lsa,
shu platformaning tanish ilova belgisi yoki interfeysini tahririy kontekstda
ko'rsatish mumkin. Boshqa tasodifiy brendlar va logolar bo'lmasin."""

# Kompozitsiya uslublari — har post uchun bittasi tanlanadi.
# Shuning uchun kanal lentasi bir xil rasmlar qatoriga aylanmaydi.
COMPOSITIONS = [
    "extreme close-up on the key object, shallow depth of field, the rest softly blurred",
    "isometric 3/4 view of a small diorama-like scene, clean drop shadows",
    "wide establishing shot of the environment, one human figure small in frame for scale",
    "top-down flat-lay of the objects arranged neatly on a surface",
    "split composition contrasting two states side by side, clear visual divide",
    "over-the-shoulder view of hands working with the objects, face out of frame",
    "single bold symbolic object centered on a clean background, generous negative space",
]

# Xitoy konteksti — MAJBURIY emas, sahna tabiiy talab qilgandagina.
# Har rasmni bozorga tiqishtirish aynan bir xillikka olib keladi.
CHINA_CUES = (
    "Show personal mobile shopping, a small individual parcel, or a simple "
    "home-based microbusiness desk, depending on the actual post: a smartphone, "
    "one pair of shoes, one garment, one accessory, a book, or one compact package. "
    "Do not show factories, containers, pallets, wholesale markets, cargo trucks, "
    "large box piles, business negotiations, or industrial logistics. "
    "Keep the setting relatable to an ordinary shopper using an app at home."
)

IDEA_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "lesson": {"type": "STRING"},
        "visual_anchors": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
        },
        "ideas": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "concept": {"type": "STRING"},
                    "why_it_works": {"type": "STRING"},
                    "clarity": {"type": "INTEGER"},
                    "surprise": {"type": "INTEGER"},
                },
                "required": ["concept", "why_it_works", "clarity", "surprise"],
            },
        },
        "chosen": {"type": "STRING"},
        "context_test": {"type": "STRING"},
        "prompt": {"type": "STRING"},
        "has_person": {"type": "BOOLEAN"},
    },
    "required": ["lesson", "visual_anchors", "ideas", "chosen", "context_test",
                 "prompt", "has_person"],
}


def _pick_composition(seed: str) -> str:
    idx = int(hashlib.sha1(seed.encode("utf-8")).hexdigest(), 16) % len(COMPOSITIONS)
    return COMPOSITIONS[idx]


PEOPLE_RULES = {
    "never": "Sahnada odam BO'LMASIN — faqat predmetlar va muhit.",

    # Standart. Odam MAVZU talab qilgandagina chiqadi.
    "sometimes": (
        "ODAM QO'SHISH QOIDASI — o'ylab ko'ring, avtomatik qo'shmang:\n"
        "  · Dars INSON HARAKATI haqida bo'lsa (o'lchash, tekshirish, "
        "savdolashish, qadoqlash, hujjat imzolash) — odam bo'lsin, chunki "
        "harakatni odamsiz ko'rsatib bo'lmaydi.\n"
        "  · Dars PREDMET, HUJJAT, RAQAM yoki JARAYON haqida bo'lsa "
        "(hajmli vazn, boj hujjatlari, quti o'lchami, narx) — ODAM KERAK EMAS. "
        "Predmetning o'zi ko'rsatilsin, u kuchliroq ishlaydi.\n"
        "  · Shubha bo'lsa — odamsiz qiling.\n"
        "  · Odam bo'lsa: o'zbek yoki xitoylik ishchi/tadbirkor, ish paytida "
        "tutilgan tabiiy lahza. Kameraga qaramasin, poza bermasin. Yuz "
        "ko'rinishi mumkin, lekin umumlashgan — hech kimga o'xshamasin.\n"
        "  · Odam bo'lsa, ustida SODDA BIR RANGLI ish kiyimi bo'lsin — "
        "to'q ko'k yoki to'q sariq jilet, polo yoki futbolka. Ko'krak qismi "
        "TOZA va BO'SH bo'lsin: na yozuv, na nishon, na logotip. "
        "(Logotip keyin alohida qo'yiladi.)"
    ),

    "often": (
        "Sahnada ODAM BO'LSIN — o'zbek yoki xitoylik ishchi, tadbirkor, "
        "sotuvchi. Ish paytida tutilgan tabiiy lahza, kameraga poza bermasin. "
        "Yuzi umumlashgan bo'lsin. Ustida sodda bir rangli ish kiyimi — "
        "ko'krak qismi toza va bo'sh, hech qanday yozuv yoki nishonsiz."
    ),
}


def _describe(post_text: str, topic_title: str, cfg: dict,
              composition: str, api_key: str, model: str) -> tuple[str, str, str, list[str], str, bool]:
    """Rasm tavsifini tuzadi.

    Bir bosqichda emas, uch bosqichda:
      1. Postning ASOSIY DARSI ajratiladi
      2. Uchta TURLI vizual g'oya o'ylab topiladi va "kutilmaganlik" bo'yicha
         baholanadi
      3. Eng kutilmagani tanlanadi va faqat o'shaning tavsifi yoziladi

    Bitta so'rovda darrov tavsif so'ralsa, model doim eng oddiy va eng
    zerikarli variantni beradi — konteyner va quti. Muqobil variantlarni
    ko'rishga majbur qilish rasmni jonlantiradi.
    """
    img = cfg["image"]
    people = PEOPLE_RULES.get(img.get("people", "often"), PEOPLE_RULES["often"])

    prompt = f"""Quyidagi Telegram posti uchun rasm g'oyasini topasiz.

POST SARLAVHASI: {topic_title}

POST MATNI:
{post_text[:1800]}

BOSQICH 1 — lesson
Post o'quvchiga QANDAY BITTA aniq narsani o'rgatyapti? Bir jumlada yozing.
Umumiy emas, aniq: "Pinduoduo'da rangni tanlash", "Taobao'da savatchaga
qo'shish", "Poizon'da oyoq kiyim o'lchamini tekshirish".

BOSQICH 1B — visual_anchors
Rasmni ko'rgan odam mavzuni MATNSIZ ham anglashi uchun 2–4 ta majburiy vizual
tayanch yozing. Postda platforma nomi bo'lsa uning tanish ilova belgisi yoki
interfeysi birinchi tayanch bo'lsin. Hujjat mavzusi bo'lsa hujjatning o'zi ham
ko'rinsin. Masalan Alipay xavfsizligi uchun: Alipay ko'k ilova belgisi/UI,
smartfon, shaxsni tasdiqlash uchun generik pasport, xavfsizlik qalqoni/qulf.
Pasportdagi ism, raqam va surat real bo'lmasin, shaxsiy ma'lumot o'qilmasin.

BOSQICH 2 — ideas (3 ta, BIR-BIRIDAN KESKIN FARQ QILSIN)
Shu darsni ko'rsatadigan uchta turli vizual g'oya. Ular turli yo'ldan borsin:
  · biri — jarayonning aniq lahzasi (qo'l, predmet, harakat)
  · biri — ikki holatning qarama-qarshiligi (to'g'ri / xato, oldin / keyin)
  · biri — kutilmagan metafora (masshtab o'yini, g'ayrioddiy nuqtai nazar,
    predmetning odatiy bo'lmagan holati)

Har biriga:
  concept — sahna nima (2-3 jumla, aniq predmetlar bilan)
  why_it_works — nega u aynan shu darsni ko'rsatadi
  clarity — 1..10, rasmni post matnisiz ko'rgan odam mavzuni qanchalik tez
            va to'g'ri tushunadi. Kamida ikkita visual_anchors katta va aniq
            ko'rinsa 8–10 ball, umumiy quti/konteyner sahnasi 1–3 ball.
  surprise — 1..10, qanchalik kutilmagan. Konteyner, quti uyumi, dunyo
             xaritasi, o'q-yo'nalish chizig'i kabi klishelar 1-3 ball oladi.

BOSQICH 3 — chosen, context_test va prompt
Avval clarity eng yuqori (kamida 8) bo'lgan g'oyani tanlang; shular ichida
surprise yuqorisini oling. Chiroyli metafora mavzuni yashirib yubormasin.
chosen — qaysi g'oya tanlanganini bir jumlada yozing.
context_test — odam captionni ko'rmasdan rasm nimani anglatishini qanday
bilishini bir jumlada yozing; qaysi ikki tayanch ko'rinishini ayting.
has_person — tanlangan sahnada odam bormi (yuz, gavda yoki qo'l). true/false.
prompt — o'sha g'oyaning INGLIZ TILIDAGI rasm tavsifi, 60-95 so'z.

prompt uchun talablar:
- Aniq jismoniy predmetlar: tarozi, hujjat, plomba, tasma, telefon ekrani,
  pul, javon, o'lchov lentasi, quti. Mavhum tasvir emas.
- visual_anchors ichidan kamida IKKITASI kadrning asosiy, katta va ravshan
  elementlari bo'lsin; fon bezagiga aylanib qolmasin.
- Postda nomi aytilgan platforma bo'lsa, uning tanish ilova belgisi yoki UI
  telefonda ravshan ko'rinsin. Boshqa brendlar qo'shilmasin.
- Pasport yoki ID kerak bo'lsa generik bo'lsin: o'qiladigan ism, raqam, tug'ilgan
  sana yoki real odam rasmi bo'lmasin.
- Muhit: {CHINA_CUES}
- Kompozitsiya (majburiy): {composition}
- Uslub: {img.get('style', '').strip()}
- Ranglar: {img.get('brand_colors', '')}
- Odamlar: {people}
- Rasmda o'qiladigan matn, raqam, iyeroglif, bayroq yoki watermark bo'lmasin.
  Faqat mavzuda nomi aniq aytilgan platformaning ilova belgisi/UI bundan
  mustasno; boshqa logolar bo'lmasin.
- Pastki o'ng burchakda logotip uchun toza joy qoldiring"""

    data = generate_json(prompt, api_key, IDEA_SCHEMA, model=model,
                         system=PROMPT_SYSTEM, temperature=1.0)

    ideas = data.get("ideas") or []
    for i in ideas:
        LOG.info("  g'oya (aniqlik %s, kutilmaganlik %s): %s",
                 i.get("clarity"), i.get("surprise"), str(i.get("concept"))[:88])

    desc = (data.get("prompt") or "").strip().strip('"').strip()
    if not desc:
        raise ValueError("Rasm tavsifi bo'sh qaytdi")
    anchors = [str(x).strip() for x in (data.get("visual_anchors") or []) if str(x).strip()]
    return (desc, data.get("lesson", ""), data.get("chosen", ""), anchors,
            data.get("context_test", ""), bool(data.get("has_person")))


def run(cfg: dict, post_text: str, out_path: Path, api_key: str,
        topic_title: str = "") -> tuple[Path, str]:
    img_cfg = cfg["image"]
    composition = _pick_composition(out_path.parent.name + topic_title)
    LOG.info("Kompozitsiya: %s", composition[:60])

    desc, lesson, chosen, anchors, context_test, has_person = _describe(
        post_text, topic_title or post_text[:80], cfg,
        composition, api_key, cfg["llm"]["model"])
    LOG.info("Post darsi   : %s", lesson[:100])
    LOG.info("Tanlangan    : %s", chosen[:100])
    LOG.info("Tayanchlar   : %s", "; ".join(anchors)[:180])
    LOG.info("Kontekst testi: %s", context_test[:160])
    LOG.info("Rasm tavsifi : %s", desc[:140])
    LOG.info("Odam bormi   : %s", "ha" if has_person else "yo'q")

    full_prompt = (
        f"{desc}\n\n"
        f"Composition: {composition}.\n"
        f"Style: {img_cfg.get('style', '').strip()}\n"
        f"Color palette: {img_cfg.get('brand_colors', '')}\n"
        f"Mandatory topic-recognition anchors: {'; '.join(anchors)}. At least two "
        f"must be large, clear, and visually dominant so the subject is obvious "
        f"without reading the caption. Context check: {context_test}\n"
        f"Natural documentary lighting, believable human proportions and hands. "
        f"No readable personal data, arbitrary text, numbers, Chinese characters, "
        f"watermarks or flags. If and only if the named topic is a specific app "
        f"or marketplace, show its recognizable app icon/interface clearly in an "
        f"editorial context; include no unrelated brand logos. No resemblance to any real or "
        f"famous person. Leave the bottom-right corner visually calm and uncluttered."
    )

    data, used = generate_image(
        full_prompt,
        api_key,
        model=img_cfg["model"],
        aspect_ratio=img_cfg.get("aspect_ratio", "1:1"),
        fallbacks=img_cfg.get("fallback_models") or [],
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    LOG.info("Rasm saqlandi: %s (%.0f KB, model: %s)", out_path.name, len(data) / 1024, used)

    apply_platform_logo(out_path, cfg, f"{topic_title}\n{post_text}")
    on_clothing = _logo_on_clothing(cfg, out_path, has_person, api_key)
    if not on_clothing:
        apply_logo(out_path, cfg, ROOT)      # burchakka qo'yish — kafolatlangan yo'l
    return out_path, desc


def _logo_on_clothing(cfg: dict, image_path: Path, has_person: bool,
                      api_key: str) -> bool:
    """Sahnada odam bo'lsa, logotipni uning kiyimiga joylashtiradi.

    Burchakka yopishtirish bilan farqi: bu yerda model logotipni matoning
    burmalariga, yorug'ligiga va istiqboliga moslab chizadi — go'yo kiyimda
    haqiqatan bosilgandek. Ikkita rasm kiritiladi: sahna va logotip fayli.

    Ishlamasa False qaytaradi va logotip odatdagidek burchakka qo'yiladi.
    """
    logo_cfg = (cfg.get("image") or {}).get("logo") or {}
    if not logo_cfg.get("enabled", True) or not logo_cfg.get("on_clothing", True):
        return False
    if not has_person:
        return False

    logo_path = find_logo(cfg, ROOT)
    if logo_path is None:
        return False

    prompt = (
        "Take the FIRST image (the photograph) and place the logo from the "
        "SECOND image onto the clothing of the person — on the chest of the "
        "vest, polo or t-shirt, or on the sleeve if the chest is not visible.\n"
        "Make it look genuinely printed or embroidered on the fabric: it must "
        "follow the folds and curvature of the cloth, match the lighting and "
        "shadows of the scene, and share the same perspective as the garment.\n"
        "Keep it modest in size — about the width of a hand's palm on the chest.\n"
        "Change NOTHING else: the person, pose, background, colors and framing "
        "must stay exactly as they are. Do not add any other text, letters or "
        "marks anywhere in the picture."
    )
    img_cfg = cfg["image"]
    try:
        result = edit_image(
            prompt,
            [image_path.read_bytes(), logo_path.read_bytes()],
            api_key,
            model=img_cfg["model"],
            fallbacks=img_cfg.get("fallback_models") or [],
        )
    except Exception as exc:                              # noqa: BLE001
        LOG.warning("Logotipni kiyimga qo'yib bo'lmadi (%s) — burchakka qo'yiladi",
                    str(exc)[:110])
        return False

    image_path.write_bytes(result)
    LOG.info("Logotip kiyimga joylashtirildi")
    return True

