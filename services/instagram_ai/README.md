# IMMENSUS Instagram AI + CRM — MVP 0.1 (DRY RUN)

**Status: code scaffold only; NOT deployed; NOT linked to live Instagram, CRM or operator panel.**

This separate service does not alter the existing Telegram auto-post service.

## Architecture
Instagram POST/CARGO professional accounts → Meta official webhook
→ signature validation + brand mapping → structured event normalization
→ (next milestone: durable queue, event-id deduplication)
→ approved business FAQ / AI escalation
→ operator inbox + unified customer identity
→ explicit CRM adapters (read first, write only when approved).

No automated outgoing comments or DMs have been implemented.

## Verified existing CRM structures (2026-10-13)
- POST Google Sheet: "Mijozlar", "Posilkalar", "Tracking", "Hudud kodlari".
- CARGO "Kargo Bot DB": "Mijozlar", "Yuklar", "Marketing", "Users", "Orders", etc.
- Do not overwrite or merge customer IDs. Instagram user-scoped IDs must be stored as channel identities and linked to an existing CRM record only after reliable matching or operator confirmation.
- Existing POST sample/demo row must not be treated as a real lead.
- POST user-visible claims: 1-piece orders, China to Uzbekistan, road delivery only. 13–16 days is estimated; no aviation claim.
- CARGO: B2B/sourcing, customs/quotes to human when information is incomplete.
- Price and tariffs: use ONLY a business-approved, versioned source. Do not infer price from public marketing drafts.

## Local dry-run
From services/instagram_ai:
    pip install -r requirements.txt pytest
    uvicorn app.main:app --reload
    pytest -q tests

Define in a local secret manager (never GitHub code, tickets, chat, or committed .env):
- META_APP_SECRET
- IG_WEBHOOK_VERIFY_TOKEN
- IG_POST_ACCOUNT_ID
- IG_CARGO_ACCOUNT_ID

Endpoints: GET /healthz, GET/POST /webhooks/instagram.

GET subscription verification: Meta hub.mode, hub.verify_token, hub.challenge.
POST: HMAC SHA-256 body verification mandatory, event counts only. No PII logs.

## Before production
1. Authorize both Instagram Professional profiles using official Meta API, grant approved messaging/comments scopes, webhooks, and required account access. Verify the app is allowed to serve accounts beyond test users.
2. Set cloud HTTPS endpoint and secure secret storage; apply rate limiting, provider IP/network controls where appropriate, WAF, monitoring, and tenancy isolation.
3. Implement durable event queue and unique event deduplication, retries and dead-letter handling before letting Meta retry traffic. Never log raw conversations by default.
4. Implement scoped CRM read adapter and operator inbox before CRM writes. Keep customer ID rules independent for POST and CARGO, audit merges, minimize personal data and set retention/access policy.
5. Draft brand-specific Uzbek answer templates; add source-grounded FAQ and escalation on prices, complaints, customs, forbidden goods and missing details.
6. Only then implement Meta replies with eligibility, messaging window (incl. 24h standard rules and approved exceptions), comment private reply policy and user consent checks.
7. Add tests for duplicate events, loops/echo messages, signature spoofing, quota, failures, timezones, wrong-account routing, operator pause, and data deletion.

## Suggested operator inbox statuses
NEW → AI_DRAFTED → OPERATOR_ASSIGNED → WAITING_CUSTOMER → RESOLVED.
The handoff must immediately stop automated replies on that thread.

## Webhook caution
Entry formats vary with Meta product and subscribed fields; capture fixtures from a dedicated test account and validate against current Meta docs before enabling.

This MVP returns only an in-memory tally; no queue, persistent CRM activity, direct messaging, comments, or AI API calls. It cannot serve production traffic until the above milestones are implemented.
