"""Brend elementlari — logotipni rasmga qo'yish.

Logotipni AI ga chizdirib bo'lmaydi: har safar boshqacha va buzuq chiqadi.
Shuning uchun rasm generatsiya qilingandan keyin haqiqiy logo fayli
ustiga qo'yiladi — har safar bir xil, aniq va o'zgarmas.
"""
from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path

import requests

LOG = logging.getLogger("branding")

POSITIONS = ("bottom-right", "bottom-left", "top-right", "top-left")


def _position(base_size: tuple[int, int], item_size: tuple[int, int],
              position: str, margin: int) -> tuple[int, int]:
    base_w, base_h = base_size
    item_w, item_h = item_size
    x = margin if "left" in position else base_w - item_w - margin
    y = margin if "top" in position else base_h - item_h - margin
    return x, y


def apply_platform_logo(image_path: Path, cfg: dict, text: str) -> str | None:
    """Matnda platforma bo'lsa, uning haqiqiy wordmarkini rasmga qo'yadi.

    AI logoni o'zi chizmaydi: konfiguratsiyadagi logo fayli yuklanadi va
    o'zgartirilmasdan kompozitsiyaga qo'shiladi. Yuklash ishlamasa asosiy rasm
    baribir saqlanadi — post logo xatosi sabab to'xtab qolmaydi.
    """
    brand_cfg = (cfg.get("image") or {}).get("platform_logos") or {}
    if not brand_cfg.get("enabled", True):
        return None

    haystack = text.casefold()
    # Uzun nomlar avval: "alibaba" so'zi "aliexpress"ni noto'g'ri tutmasin.
    brands = brand_cfg.get("brands") or {}
    match = next((name for name in sorted(brands, key=len, reverse=True)
                  if name.casefold() in haystack), None)
    if not match:
        return None

    try:
        response = requests.get(brands[match], timeout=25,
                                headers={"User-Agent": "ImmensusPost/1.0"})
        response.raise_for_status()

        from PIL import Image, ImageDraw, ImageFilter

        base = Image.open(image_path).convert("RGBA")
        logo = Image.open(BytesIO(response.content)).convert("RGBA")
        width_pct = float(brand_cfg.get("width_percent", 28)) / 100
        target_w = max(int(base.width * width_pct), 48)
        target_h = max(int(logo.height * target_w / logo.width), 24)
        max_h = int(base.height * 0.16)
        if target_h > max_h:
            target_h = max_h
            target_w = max(int(logo.width * target_h / logo.height), 48)
        logo = logo.resize((target_w, target_h), Image.LANCZOS)

        margin = int(base.width * float(brand_cfg.get("margin_percent", 4)) / 100)
        position = brand_cfg.get("position", "top-left")
        if position not in POSITIONS:
            position = "top-left"
        x, y = _position(base.size, logo.size, position, margin)

        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        if brand_cfg.get("backdrop", True):
            pad = max(int(target_h * 0.35), 10)
            shade = Image.new("RGBA", base.size, (0, 0, 0, 0))
            ImageDraw.Draw(shade).rounded_rectangle(
                (x - pad, y - pad, x + target_w + pad, y + target_h + pad),
                radius=pad,
                fill=(255, 255, 255, 235),
            )
            shade = shade.filter(ImageFilter.GaussianBlur(1.2))
            layer = Image.alpha_composite(layer, shade)
        layer.paste(logo, (x, y), logo)
        Image.alpha_composite(base, layer).convert("RGB").save(image_path, "PNG")
        LOG.info("Haqiqiy platforma logosi qo'yildi: %s", match)
        return match
    except Exception as exc:                              # noqa: BLE001
        LOG.warning("%s logosi qo'yilmadi: %s", match, exc)
        return None


def find_logo(cfg: dict, root: Path) -> Path | None:
    """Logo faylini topadi.

    Sozlamadagi yo'l bo'yicha topilmasa, odatiy joylardan qidiradi —
    shunda faylni reponing ildiziga tashlasangiz ham ishlaydi va
    papka yaratish bilan ovora bo'lmaysiz.
    """
    logo_cfg = (cfg.get("image") or {}).get("logo") or {}
    rel = logo_cfg.get("path")

    candidates: list[Path] = []
    if rel:
        candidates.append(Path(rel) if Path(rel).is_absolute() else root / rel)
    for folder in (root / "assets", root):
        for ext in ("png", "PNG", "jpg", "jpeg", "webp"):
            candidates.append(folder / f"logo.{ext}")

    for path in candidates:
        if path.exists() and path.is_file():
            return path

    # logo* bilan boshlanadigan har qanday rasm
    for folder in (root / "assets", root):
        if folder.is_dir():
            for path in sorted(folder.glob("logo*")):
                if path.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                    return path
    return None


def apply_logo(image_path: Path, cfg: dict, root: Path) -> Path:
    """Rasmga logo qo'yadi. Logo topilmasa rasm o'zgarishsiz qoladi."""
    logo_cfg = (cfg.get("image") or {}).get("logo") or {}
    if logo_cfg.get("enabled") is False:
        return image_path

    logo_path = find_logo(cfg, root)
    if logo_path is None:
        LOG.warning("Logo fayli topilmadi (assets/logo.png yoki logo.png) — "
                    "rasm logosiz qoldi")
        return image_path
    LOG.info("Logo fayli: %s", logo_path.relative_to(root) if root in logo_path.parents
             else logo_path)

    try:
        from PIL import Image, ImageDraw, ImageFilter
    except ImportError:
        LOG.warning("Pillow o'rnatilmagan — logo qo'yilmadi")
        return image_path

    try:
        base = Image.open(image_path).convert("RGBA")
        logo = Image.open(logo_path).convert("RGBA")

        width_pct = float(logo_cfg.get("width_percent", 18)) / 100
        margin_pct = float(logo_cfg.get("margin_percent", 4)) / 100
        opacity = float(logo_cfg.get("opacity", 0.95))
        position = logo_cfg.get("position", "bottom-right")
        if position not in POSITIONS:
            position = "bottom-right"

        target_w = max(int(base.width * width_pct), 24)
        target_h = max(int(logo.height * target_w / logo.width), 12)
        logo = logo.resize((target_w, target_h), Image.LANCZOS)

        if opacity < 1:
            alpha = logo.getchannel("A").point(lambda a: int(a * opacity))
            logo.putalpha(alpha)

        margin = int(base.width * margin_pct)
        x, y = _position(base.size, logo.size, position, margin)

        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))

        # Shaffof PNG o'z alfa-kanali bilan qo'yiladi. Oq plashka faqat
        # sozlamada ataylab yoqilgandagina chiziladi.
        if logo_cfg.get("backdrop", False):
            pad = max(int(target_w * 0.12), 8)
            box = (x - pad, y - pad, x + target_w + pad, y + target_h + pad)
            shade = Image.new("RGBA", base.size, (0, 0, 0, 0))
            ImageDraw.Draw(shade).rounded_rectangle(
                box, radius=pad, fill=(255, 255, 255, 205)
            )
            shade = shade.filter(ImageFilter.GaussianBlur(1.5))
            layer = Image.alpha_composite(layer, shade)

        layer.paste(logo, (x, y), logo)
        out = Image.alpha_composite(base, layer).convert("RGB")
        out.save(image_path, "PNG")
        LOG.info("Logo qo'yildi: %s (%dpx, %s)", logo_path.name, target_w, position)
    except Exception as exc:                              # noqa: BLE001
        LOG.error("Logo qo'yilmadi: %s", exc)

    return image_path
