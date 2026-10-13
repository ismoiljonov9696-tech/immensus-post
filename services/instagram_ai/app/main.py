"""IMMENSUS Instagram inbound webhook — xavfsiz, faqat sinov rejimi.

Ushbu bosqichda hech qanday DM, komment yoki CRM yozuvi YUBORILMAYDI.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse

app = FastAPI(title="IMMENSUS Instagram AI Intake", version="0.1.0")


def valid_signature(raw_body: bytes, header: str | None, app_secret: str) -> bool:
    """Meta X-Hub-Signature-256: faqat asl baytlar bilan HMAC tekshirish."""
    if not header or not header.startswith("sha256=") or not app_secret:
        return False
    expected = "sha256=" + hmac.new(
        app_secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, header)


def account_brand(account_id: str) -> str | None:
    """Bir Instagram profilining muloqoti boshqa brendga ko'chib ketmasin."""
    if account_id and account_id == os.getenv("IG_POST_ACCOUNT_ID", ""):
        return "POST"
    if account_id and account_id == os.getenv("IG_CARGO_ACCOUNT_ID", ""):
        return "CARGO"
    return None


def normalize_events(payload: dict[str, Any]) -> list[dict[str, str]]:
    """Meta webhookning komment va Direct voqealarini bir shaklga keltirish."""
    events: list[dict[str, str]] = []
    for entry in payload.get("entry", []):
        if not isinstance(entry, dict):
            continue
        account_id = str(entry.get("id") or "")
        for change in entry.get("changes", []):
            if not isinstance(change, dict) or change.get("field") not in (
                "comments", "live_comments"
            ):
                continue
            value = change.get("value") or {}
            if not isinstance(value, dict):
                continue
            events.append({
                "kind": "comment",
                "account_id": account_id,
                "event_id": str(value.get("id") or ""),
                "sender_id": str((value.get("from") or {}).get("id") or ""),
                "text": str(value.get("text") or ""),
            })
        for item in entry.get("messaging", []):
            if not isinstance(item, dict):
                continue
            message = item.get("message") or {}
            if not isinstance(message, dict) or message.get("is_echo"):
                continue
            recipient_id = str((item.get("recipient") or {}).get("id") or "")
            events.append({
                "kind": "direct",
                "account_id": account_id or recipient_id,
                "event_id": str(message.get("mid") or ""),
                "sender_id": str((item.get("sender") or {}).get("id") or ""),
                "text": str(message.get("text") or ""),
            })
    return events


def triage(kind: str, text: str, brand: str) -> str:
    """Faqat yo'naltirish. Bu LLM emas va hech qanday javob jo'natmaydi."""
    cleaned = text.casefold()
    human_words = ("operator", "odam bilan", "shikoyat", "yo'qol", "yiring", "bojxona muammo")
    if not cleaned.strip() or any(word in cleaned for word in human_words):
        return "operator_review"
    if kind == "comment":
        return "comment_review"
    sales_words = ("narx", "qancha", "tovar", "yuk", "olib kel", "zakaz", "kg", "posilka")
    if any(word in cleaned for word in sales_words):
        return "post_sales_lead" if brand == "POST" else "cargo_sales_lead"
    return "faq_review"


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "dry_run"}


@app.get("/webhooks/instagram")
def verify_subscription(request: Request) -> PlainTextResponse:
    token = os.getenv("IG_WEBHOOK_VERIFY_TOKEN", "")
    if not token:
        raise HTTPException(status_code=503, detail="Webhook token is not configured")
    supplied = request.query_params.get("hub.verify_token", "")
    if (
        request.query_params.get("hub.mode") != "subscribe"
        or not hmac.compare_digest(token, supplied)
    ):
        raise HTTPException(status_code=403, detail="Invalid verification")
    return PlainTextResponse(request.query_params.get("hub.challenge", ""))


@app.post("/webhooks/instagram")
async def receive_webhook(request: Request) -> dict[str, Any]:
    secret = os.getenv("META_APP_SECRET", "")
    if not secret:
        raise HTTPException(status_code=503, detail="Meta secret is not configured")
    raw = await request.body()
    if len(raw) > 256 * 1024:
        raise HTTPException(status_code=413, detail="Webhook exceeds size limit")
    if not valid_signature(raw, request.headers.get("X-Hub-Signature-256"), secret):
        raise HTTPException(status_code=401, detail="Invalid Meta signature")
    try:
        payload = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="Invalid JSON")
    if not isinstance(payload, dict) or not isinstance(payload.get("entry"), list):
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    routed: dict[str, int] = {
        "POST": 0, "CARGO": 0, "unknown_account": 0, "operator_review": 0,
        "sales_leads": 0,
    }
    events = normalize_events(payload)
    for event in events:
        brand = account_brand(event["account_id"])
        if brand is None:
            routed["unknown_account"] += 1
            continue
        routed[brand] += 1
        intent = triage(event["kind"], event["text"], brand)
        if intent == "operator_review":
            routed["operator_review"] += 1
        elif intent.endswith("_sales_lead"):
            routed["sales_leads"] += 1

    # Maxfiy mijoz xabarlari, IDlari yoki telefonlari logga yozilmaydi.
    # MVP-2: durable queue + dedup + CRM adapter + operator paneli.
    # MVP-3: Meta 24-soatlik qoidalar tekshirilib, explicit opt-in bilan send.
    return {"accepted": True, "mode": "dry_run", "events": len(events), "routed": routed}
