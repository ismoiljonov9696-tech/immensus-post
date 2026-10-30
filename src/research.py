"""Web-tadqiqot manbalarini xavfsiz tekshirish qoidalari."""
from __future__ import annotations

from urllib.parse import urlparse


UNTRUSTED_HOSTS = {
    "facebook.com", "instagram.com", "pinterest.com", "tiktok.com",
    "t.me", "telegram.me", "x.com",
}


def verified_sources(sources: list[dict] | None) -> list[dict]:
    """Faqat ochiq HTTPS havolalarni takrorsiz qaytaradi.

    Ijtimoiy tarmoq posti fakt uchun mustaqil manba hisoblanmaydi. YouTube
    ataylab bloklanmagan: rasmiy platforma kanali ayrim amaliy tugmalar uchun
    foydali bo'lishi mumkin, ammo tadqiqot prompti baribir rasmiy sahifalarni
    ustuvor qiladi.
    """
    result: list[dict] = []
    seen: set[str] = set()
    for source in sources or []:
        if not isinstance(source, dict):
            continue
        url = str(source.get("url") or "").strip()
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower().removeprefix("www.")
        if parsed.scheme != "https" or not host:
            continue
        if host in UNTRUSTED_HOSTS or any(host.endswith(f".{h}") for h in UNTRUSTED_HOSTS):
            continue
        normalized = url.split("#", 1)[0]
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append({
            "title": str(source.get("title") or host).strip(),
            "url": normalized,
        })
    return result


def require_sources(sources: list[dict] | None, minimum: int = 2) -> list[dict]:
    checked = verified_sources(sources)
    if len(checked) < minimum:
        raise RuntimeError(
            f"Web search {len(checked)} ta yaroqli manba topdi; kamida {minimum} ta kerak. "
            "Tekshirilmagan post tayyorlanmadi."
        )
    return checked
