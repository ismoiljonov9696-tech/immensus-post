# IMMENSUS Instagram AI — Meta + Google Cloud Run setup

Status: draft branch for dry-run ONLY. Not deployed. No outgoing Instagram replies, no CRM writes and no production AI conversation engine.

## Step 1 — Meta Developers

1. Visit https://developers.facebook.com/apps/ and create app IMMENSUS Social AI.
2. Select the Instagram API use case / Instagram API with Instagram Login. UI wording varies.
3. Request instagram_business_basic, instagram_business_manage_messages and instagram_business_manage_comments.
4. Instagram -> API setup with Instagram login -> add and authorize both CARGO and POST professional accounts separately. Copy their IG account IDs, NOT their tokens, into the Cloud Run plain configuration later.
5. Do not paste app secrets or access tokens into chat, git files or screenshots.

## Step 2 — Cloud Run from GitHub

Official Google documentation: https://docs.cloud.google.com/run/docs/continuous-deployment

1. Select the existing project at https://console.cloud.google.com/run. Enable required billing/APIs if prompted.
2. Choose Connect repository (Cloud Build), connect repo ismoiljonov9696-tech/immensus-post, branch feature/instagram-ai-crm-mvp-2026-10-13.
3. Dockerfile source location: services/instagram_ai/Dockerfile . Its directory must be used as the Docker build context.
4. Service name: immensus-instagram-webhook ; region: asia-southeast1 (or user's existing Cloud Run region); runtime port: 8080.
5. Allow unauthenticated HTTPS requests so that Meta can reach the webhook. The application verifies HMAC signatures for POSTs.
6. For dry-run, set max instances to 1, min instances 0 to limit cost.
7. Prevent unrelated Telegram app deployment or automatic merges.

Alternative, using Cloud Shell (when gcloud is already authenticated and in the correct Google Cloud project):

    git clone --depth=1 --branch feature/instagram-ai-crm-mvp-2026-10-13 https://github.com/ismoiljonov9696-tech/immensus-post.git
    cd immensus-post/services/instagram_ai
    gcloud run deploy immensus-instagram-webhook --source . --region asia-southeast1 --allow-unauthenticated --max-instances 1 --memory 256Mi --port 8080

First deploy can run without secrets but GET verification and event POSTs fail closed with 503 until configured.

## Step 3 — Cloud Secret Manager

In Google Cloud Secret Manager create:
- immensus-instagram-signing-secret : secret used by Meta to sign the Instagram webhook requests (confirm App Settings/Instagram product configuration in Meta).
- immensus-instagram-verify-token : random strong value selected by the project owner.

Cloud Run -> Edit & Deploy New Revision -> Variables & Secrets:
- META_APP_SECRET: secret-manager value immensus-instagram-signing-secret (the receiver currently uses this env name for its HMAC verification).
- IG_WEBHOOK_VERIFY_TOKEN: secret-manager value immensus-instagram-verify-token.
- IG_POST_ACCOUNT_ID: exact authorized Instagram professional account ID for IMMENSUS POST.
- IG_CARGO_ACCOUNT_ID: exact authorized Instagram professional account ID for IMMENSUS CARGO.

Give the Cloud Run runtime service account Secret Manager Secret Accessor role for these specific secrets only. No tokens/access keys in GitHub or plain files.

## Step 4 — Meta Webhooks

Use the ACTUAL Cloud Run URL displayed after deploy (do not invent it).

Meta Dashboard -> Instagram -> API setup with Instagram login -> Webhooks -> Configure.
- Callback URL = ACTUAL_CLOUD_RUN_URL/webhooks/instagram
- Verify Token = exact secret value from immensus-instagram-verify-token
- Subscribe to the comments and messages events. The Instagram Login setup may additionally require per-account webhook subscription.
- Save; Meta sends a GET handshake requiring our receiver to echo hub.challenge.

The receiver's endpoints:
- GET /healthz -> running status
- GET /webhooks/instagram -> subscription verification
- POST /webhooks/instagram -> check HMAC signature; identify brand; count DM/comment events only.

## Step 5 — Smoke test and safe rollout

1. Open ACTUAL_CLOUD_RUN_URL/healthz and confirm status ok.
2. Verify webhook in the Meta UI.
3. With a Meta app authorized test account, send a test DM and comment to each branded account.
4. Cloud Run logs show HTTP success; the app intentionally does NOT send outbound messages, save message text or create customers.
5. The app must obtain the correct webhook signing secret for this Instagram Login setup. If Meta verifies GET but delivers 401 on POST, carefully check which App Secret signs Instagram events; never disable signature checking to make the test pass.
6. Later milestones: durable queue, idempotency, scoped CRM adapters, operator handoff and audit, customer ID correlation, business-approved FAQ, official Meta send API, app review/advanced access, messaging window and private reply restrictions.

Security warning: GitHub repo immensus-post is public. Do not commit any customer data, Meta token, signing secret, Cloud IAM key or .env.
