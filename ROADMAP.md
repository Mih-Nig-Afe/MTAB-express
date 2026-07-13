# Mela Express — Development Roadmap

## Phase 0 — Discovery (Week 1)

Goal: Validate assumptions, set up accounts, finalize branch list before writing a line of product code.

### Tasks
- [ ] Interview 2–3 branch operators: map exact parcel intake workflow, pain points with manual system
- [ ] Interview 1 branch manager: understand reconciliation, reporting needs
- [ ] Finalize branch list and assign short codes (e.g. HW, AA1, AA2, AA3, AA4, AD, DD, JJ)
- [ ] Set up Chapa merchant account, obtain live API keys, test sandbox checkout flow
- [ ] Confirm SMS gateway vendor (Ethio Telecom or third-party aggregator), obtain credentials
- [ ] Register Telegram bot via BotFather, configure webhook URL
- [ ] Provision VPS (Hetzner CX22 or DigitalOcean Droplet 4GB), set up Docker + Nginx + Let's Encrypt
- [ ] Set up S3-compatible bucket (Cloudflare R2 recommended for Ethiopia latency)
- [ ] Set up Sentry project for error monitoring
- [ ] Create GitHub repository, configure branch protection (main = production)

### Deliverables
- Branch code list + sample data for seeding
- Chapa sandbox integration verified end-to-end
- VPS running with HTTPS and health check endpoint responding

---

## Phase 1 — Core MVP: Single Branch (Weeks 2–5)

Goal: One branch (e.g. Hawassa) can create parcels, track them, and collect cash — with Telegram notifications working end-to-end.

### Backend
- [ ] Alembic migration: all core tables (branches, staff_users, customers, parcels, parcel_status_history, payments)
- [ ] Seed initial branch data and one admin account
- [ ] Auth: POST /api/auth/login returning JWT; FastAPI `get_current_user` dependency
- [ ] RBAC: `require_roles()` dependency, branch scoping on parcel queries
- [ ] Parcel CRUD: `POST /api/parcels`, `GET /api/parcels`, `GET /api/parcels/{id}`, `PATCH /api/parcels/{id}/status`
- [ ] Tracking code generation (MEX-{BRANCH_CODE}-{6DIGIT}, collision retry)
- [ ] State machine validator (`validate_transition`) with full allowed-transitions map
- [ ] Customer link endpoint: `POST /api/customers/link`
- [ ] Public tracking: `GET /api/parcels/track/{code}` with Redis rate limiting (10/min/IP)
- [ ] Cash payment: `POST /api/payments/cash/{parcel_id}/collect` with override_reason support
- [ ] Celery + Redis worker setup: `send_telegram_notification` task with 3× retry backoff

### Telegram Bot
- [ ] `/start` + phone contact sharing flow
- [ ] `/track <code>` with payment-pending "Pay now" button stub (non-functional in Phase 1)
- [ ] "My Parcels" button: list all parcels for caller's phone number
- [ ] Auto-notification on every parcel status change

### Web Dashboard (MVP — Operator)
- [ ] Next.js project setup with Tailwind, API client (axios/fetch with JWT interceptor)
- [ ] Login page
- [ ] Parcel list page (filterable by status)
- [ ] Parcel intake form (minimal clicks: ~6 fields to create a parcel)
- [ ] Parcel detail page (status history timeline, update status button)
- [ ] Cash collection action on parcel detail

### Testing
- [ ] Unit tests: state machine, tracking code generator, RBAC dependency
- [ ] Integration tests: full parcel lifecycle via API
- [ ] Hypothesis property tests: transition determinism, tracking code format

### Deliverables
- Hawassa branch fully operational on staging
- Operator can create parcel → customer receives Telegram notification → operator marks delivered

---

## Phase 2 — Payments & Multi-Branch (Weeks 6–8)

Goal: Chapa online payments live; all branches onboarded; inter-branch manifests working.

### Backend
- [ ] Chapa initiate: `POST /api/payments/chapa/initiate`
- [ ] Chapa webhook: `POST /api/payments/chapa/webhook` with HMAC verification + server-side verify
- [ ] Idempotency guard on webhook (already-PAID check)
- [ ] `retry_failed_webhook` Celery beat task (every 15 min, for Chapa verify timeouts)
- [ ] Payment gate: prepaid parcels blocked from advancing without payment (manager override with reason)
- [ ] Transfer manifests: `POST /api/manifests`, `POST /api/manifests/{id}/receive` (bulk)
- [ ] Waybill PDF generation: `generate_waybill_pdf` Celery task → HTML template → WeasyPrint → R2 upload
- [ ] `GET /api/parcels/{id}/waybill` endpoint returning signed S3 URL
- [ ] Alembic migrations: transfer_manifests, manifest_parcels, proof_of_delivery tables
- [ ] Branch seeding: all branches with correct codes

### Telegram Bot
- [ ] "Pay Now" button → Chapa checkout URL → payment confirmed notification
- [ ] "Confirm receipt" button on READY_FOR_PICKUP notification

### Web Dashboard
- [ ] Manifest creation page (select parcels, create manifest, print waybill)
- [ ] Manifest receive page (destination operator bulk-confirms arrival)
- [ ] Waybill download / print from parcel detail page
- [ ] Multi-branch: operators see only their branch; managers see their branch + reports

### Testing
- [ ] Chapa webhook integration test (mocked Chapa verify response)
- [ ] Idempotency test: duplicate webhook is safe no-op
- [ ] Manifest bulk-receive: partial receipt → missing parcels ON_HOLD

### Deliverables
- All branches active with seeded data
- Customer can pay via Chapa bot flow end-to-end
- Inter-branch manifest printed and bulk-received at destination

---

## Phase 3 — Notifications, Alerts & Proof of Delivery (Weeks 9–11)

Goal: Full notification coverage, delay alerts, SMS fallback, and delivery proof.

### Backend
- [ ] SMS notification task: `send_sms_notification` for customers without telegram_id
- [ ] Delay alert: Celery beat task (hourly) — parcels IN_TRANSIT > threshold → alert admin + branch manager
- [ ] Daily manager digest: Celery beat (07:00 EAT) — branch KPIs via Telegram/email
- [ ] Proof of delivery: `POST /api/parcels/{id}/proof` (photo/signature upload → R2)
- [ ] notification_log table + logging all dispatched notifications
- [ ] Public tracking page: `GET /api/parcels/public/{code}` (minimal, no auth, for melaexpress.com/track/...)

### Web Dashboard
- [ ] Notification log view (admin: see all sent notifications, failures)
- [ ] Delay alert dashboard widget
- [ ] Proof of delivery view on parcel detail

### Frontend (public)
- [ ] Public tracking page: `melaexpress.com/track/MEX-HW-000482` (Next.js static page, no auth)

### Testing
- [ ] SMS fallback triggers when telegram_id is null
- [ ] Delay alert fires correctly at threshold
- [ ] Proof of delivery upload and retrieval

### Deliverables
- Full branch rollout complete
- All notification channels active
- Public tracking URL live

---

## Phase 4 — Reporting & Admin Tools (Weeks 12–14)

Goal: Branch managers and HQ admin have actionable reporting.

### Backend
- [ ] `GET /api/reports/cash-reconciliation` — expected vs collected, by day/operator/branch
- [ ] `GET /api/reports/branch-performance` — volume, revenue, avg delivery time, exception rate
- [ ] `GET /api/reports/operator-overrides` — all manual override events with reason + operator
- [ ] `GET /api/reports/delay-alerts` — history of delay events
- [ ] CSV export for all report endpoints

### Web Dashboard
- [ ] Cash reconciliation page: table + day selector + operator filter
- [ ] Branch performance page: charts (revenue, volume, on-time rate)
- [ ] Admin override audit page
- [ ] Staff management: create/edit/deactivate staff accounts, assign roles + branches

### Deliverables
- Branch managers can close daily cash without a spreadsheet
- Admin can audit every manual override by operator

---

## Phase 5 — Polish & Advanced Features (Weeks 15+, ongoing)

Priority order (build based on operator/customer feedback):

1. **Rate calculator** — price lookup by weight × size × branch-pair at intake form
2. **Bulk shipment** — one sender, multiple parcels, one manifest, one payment
3. **Complaint / dispute ticketing** — tied to tracking code, visible to admin
4. **Customer saved profile** — frequent senders: auto-fill sender info from phone
5. **Insurance / declared value tier** — premium pricing band for high-value items
6. **Multi-language bot** — Amharic, Afaan Oromo, Somali (user preference stored on customer row)
7. **Return-to-sender flow** — structured RTS with notification to sender
8. **HQ analytics dashboard** — route heatmap, revenue by branch/month, on-time rate trend
9. **Staff performance tracking** — parcels/day per operator, override rate
10. **Branch capacity view** — current parcel count in each status per branch

---

## Non-Functional Milestones

| Milestone | Target |
|---|---|
| Staging environment live | End of Phase 0 |
| HTTPS + Nginx proxy configured | End of Phase 0 |
| CI/CD: GitHub Actions → staging deploy on push to main | End of Phase 1 |
| Sentry error alerting active | End of Phase 1 |
| Production deploy | Start of Phase 2 pilot |
| Database backups (daily, offsite) | Before production |
| Uptime monitoring (Better Uptime or similar) | Before production |
| Load test (50 concurrent parcel creates) | Before Phase 3 full rollout |
