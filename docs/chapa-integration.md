# Chapa Integration Notes

## Webhook Verification

HMAC-SHA256 signature must be verified against the raw request body before processing.
Secret is configured via `CHAPA_WEBHOOK_SECRET` env var.

## Server-Side Verification

Always call `GET /transaction/verify/{tx_ref}` as the authoritative source of payment status.
Never trust the webhook payload `status` field alone.
