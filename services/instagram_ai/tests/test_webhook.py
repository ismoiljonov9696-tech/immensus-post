import hashlib
import hmac
import json

from fastapi.testclient import TestClient
from app.main import app, normalize_events, valid_signature, triage

client = TestClient(app)

def test_missing_secret_is_fail_closed(monkeypatch):
    monkeypatch.delenv("META_APP_SECRET", raising=False)
    assert client.post("/webhooks/instagram", json={"entry": []}).status_code == 503

def test_bad_signature_is_rejected(monkeypatch):
    monkeypatch.setenv("META_APP_SECRET", "secret")
    assert client.post("/webhooks/instagram", json={"entry": []}).status_code == 401

def test_verified_webhook_routes_two_brands(monkeypatch):
    monkeypatch.setenv("META_APP_SECRET", "secret")
    monkeypatch.setenv("IG_POST_ACCOUNT_ID", "post-account")
    monkeypatch.setenv("IG_CARGO_ACCOUNT_ID", "cargo-account")
    payload = {"entry": [
        {"id": "post-account", "changes": [{"field": "comments", "value": {"id": "c1", "text": "qancha kg?", "from": {"id": "u1"}}}]},
        {"id": "cargo-account", "messaging": [{"sender": {"id": "u2"}, "message": {"mid": "m1", "text": "tovar narxi?"}}]},
    ]}
    raw = json.dumps(payload).encode()
    sig = "sha256=" + hmac.new(b"secret", raw, hashlib.sha256).hexdigest()
    response = client.post("/webhooks/instagram", content=raw, headers={"X-Hub-Signature-256": sig})
    assert response.status_code == 200
    assert response.json()["routed"]["POST"] == 1
    assert response.json()["routed"]["CARGO"] == 1
    assert response.json()["routed"]["sales_leads"] == 1

def test_signature_verification():
    payload = b"test"
    signature = "sha256=" + hmac.new(b"test_secret", payload, hashlib.sha256).hexdigest()
    assert valid_signature(payload, signature, "test_secret")
    assert not valid_signature(payload + b"x", signature, "test_secret")

def test_operator_triage():
    assert triage("direct", "operator kerak", "POST") == "operator_review"
