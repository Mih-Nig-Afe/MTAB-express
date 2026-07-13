# Implementation Plan: Mela Express Platform

## Overview

Extend and productionise the existing `mela-express-backend/` skeleton (FastAPI, SQLAlchemy async,
Chapa service, Telegram bot, basic routers) into a full multi-branch parcel delivery platform.
Tasks are ordered so each step builds directly on committed code from the previous one.
The dashboard (`mela-express-dashboard/`) and public tracking page (`mela-express-public/`) are
new Next.js projects scaffolded from scratch.

Implementation language: **Python** (backend), **TypeScript / Next.js** (dashboard + public).

---

## Tasks

- [ ] 1. Extend backend models, schemas, and database configuration
  - [ ] 1.1 Add missing columns and tables to `app/models.py`
    - Add `code` (VARCHAR 5, UNIQUE) and `email` fields to `Branch`
    - Add `email` and `password_hash` fields to `StaffUser`
    - Add `size_category` (SizeCategoryEnum: small/medium/large/oversized) to `Parcel`
    - Add `override_reason` to `Payment`
    - Add `waybill_url` to `Parcel`
    - Create `ParcelProofOfDelivery` model (parcel_id UNIQUE, photo_url, signature_url, notes, recorded_by, created_at)
    - Create `TransferManifest` model (id, origin_branch_id, destination_branch_id, created_by, status ManifestStatusEnum, dispatched_at, received_at, created_at)
    - Create `ManifestParcel` association model (manifest_id, parcel_id, composite PK)
    - Create `NotificationLog` model (id, parcel_id, recipient_telegram_id, recipient_phone, channel, message, status, sent_at, created_at)
    - Add all necessary SQLAlchemy relationships and indexes per the design schema
    - _Requirements: 1.1, 7.4, 8.1, 12.1, 13.2_
  - [ ] 1.2 Update `app/schemas.py` with full Pydantic schemas
    - `ParcelCreate`: add `size_category`, enforce required fields
    - `ParcelOut`: add `waybill_url`, `origin_branch`, `destination_branch`, `status_history`
    - `ParcelStatusUpdate`: add `override_note` field
    - `BranchCreate` / `BranchOut`
    - `StaffCreate` / `StaffOut`
    - `CustomerLink`, `CustomerOut`
    - `ManifestCreate` / `ManifestOut`
    - `ManifestReceiveRequest`
    - `ProofOfDeliveryCreate` / `ProofOfDeliveryOut`
    - `CashCollectRequest` (add override_reason)
    - `ReportParams` (date range, branch_id filter)
    - _Requirements: 1.1, 5.2, 9.1, 10.1, 13.1_
  - [ ] 1.3 Upgrade `app/database.py` to production async engine settings
    - Set `pool_size=10`, `max_overflow=20` on the async engine
    - Add `pool_pre_ping=True`
    - Ensure `get_db` yields `AsyncSession` via `async_sessionmaker`
    - _Requirements: 18.1_

- [ ] 2. Set up Alembic migrations
  - [ ] 2.1 Initialise Alembic and write `alembic.ini` + `alembic/env.py`
    - Configure `env.py` to use the async engine from `app.database`
    - Point `target_metadata` at `Base.metadata`
    - Add `alembic/versions/` directory
    - _Requirements: 1.1, 10.1_
  - [ ] 2.2 Write `0001_initial_schema.py` migration
    - Create all enum types as PostgreSQL native enums (parcel_status, payment_mode, payment_method, payment_status, staff_role, manifest_status, size_category)
    - Create all tables in dependency order (branches → staff_users → customers → parcels → parcel_status_history → payments → transfer_manifests → manifest_parcels → notification_log → proof_of_delivery)
    - Add all UNIQUE constraints and indexes from the design schema
    - _Requirements: 1.1, 2.2, 14.2_
  - [ ] 2.3 Write `0002_add_proof_of_delivery.py` migration (separate idempotent migration)
    - Create `proof_of_delivery` table with UNIQUE constraint on `parcel_id`
    - _Requirements: 13.4_

- [ ] 3. Implement core security and RBAC layer (`app/core/` and `app/dependencies.py`)
  - [ ] 3.1 Create `app/core/security.py`
    - Implement `hash_password(plain: str) -> str` using `passlib[bcrypt]`
    - Implement `verify_password(plain: str, hashed: str) -> bool`
    - Implement `create_access_token(data: dict, expires_delta: timedelta) -> str` using `python-jose`
    - Implement `create_refresh_token(data: dict) -> str` (7-day expiry)
    - Implement `decode_token(token: str) -> dict` — raises `HTTPException(401)` on invalid/expired
    - _Requirements: 9.1, 9.7, 14.5_
  - [ ]* 3.2 Write property test for password hashing round-trip
    - **Property 13: Password Hashing Round-Trip**
    - **Validates: Requirements 9.7**
    - Use Hypothesis `@given(st.text(min_size=8, max_size=72))` to assert `verify_password(p, hash_password(p)) == True` and `hash_password(p) != p`
  - [ ] 3.3 Create `app/dependencies.py`
    - Implement `get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> StaffUser`
    - Implement `require_roles(*roles: StaffRole)` factory returning a FastAPI dependency that raises `403` if `user.role not in roles`
    - Implement `get_db` if not already in `database.py`
    - _Requirements: 9.3, 9.4, 9.6_
  - [ ]* 3.4 Write property test for JWT protection
    - **Property 12: JWT Protection on Protected Routes**
    - **Validates: Requirements 9.3**
    - Use `httpx.AsyncClient` with the FastAPI `app` to assert every protected route returns `401` when called without a Bearer token

- [ ] 4. Implement the parcel state machine and tracking code generator (`app/core/`)
  - [ ] 4.1 Create `app/core/state_machine.py`
    - Define `ALLOWED_TRANSITIONS: dict[ParcelStatus, set[ParcelStatus]]` matching the design (section 2.2)
    - Implement `validate_transition(from_status, to_status) -> None` — raises `ValueError` on invalid transition
    - Enforce terminal states (DELIVERED, RETURNED, CANCELLED, LOST) have empty transition sets
    - _Requirements: 3.1, 3.2, 3.9_
  - [ ]* 4.2 Write property tests for state machine determinism and terminal states
    - **Property 2: State Machine Determinism** — `@given` all status pairs, assert calling twice gives same result
    - **Property 3: State Machine Transition Validity** — assert every allowed pair passes, every disallowed pair raises
    - **Property 4: Terminal State Irreversibility** — assert all terminal states have empty allowed set
    - **Validates: Requirements 3.1, 3.2, 3.9**
  - [ ] 4.3 Create `app/core/tracking_code.py`
    - Implement `generate_tracking_code(db: AsyncSession, origin_branch: Branch) -> str`
    - Use `random.randint(100_000, 999_999)` for 6-digit suffix (non-sequential per Req 14.7)
    - Retry up to 10 times on collision, raise `HTTPException(500)` after max retries
    - Return code matching pattern `MEX-{branch.code.upper()}-{6DIGIT}`
    - _Requirements: 1.2, 1.3, 14.7_
  - [ ]* 4.4 Write property test for tracking code format and uniqueness
    - **Property 1: Tracking Code Format and Uniqueness**
    - **Validates: Requirements 1.2, 14.7**
    - Use Hypothesis with a mocked DB session: generated codes always match `^MEX-[A-Z0-9]{2,5}-\d{6}$`
  - [ ] 4.5 Create `app/core/pagination.py`
    - Implement `paginate(query, page: int, page_size: int)` helper returning `(items, total)`
    - _Requirements: 18.1_

- [ ] 5. Implement auth router (`app/routers/auth.py`)
  - [ ] 5.1 Create `app/routers/auth.py` with login and refresh endpoints
    - `POST /api/auth/login`: accept `phone` + `password`, query `staff_users`, verify bcrypt hash, return `{access_token, refresh_token, token_type}`
    - `POST /api/auth/refresh`: accept refresh token in body, validate, return new access token
    - Return `401` for invalid credentials, `403` for inactive accounts
    - Register router in `app/main.py`
    - _Requirements: 9.1, 9.2, 9.3_
  - [ ]* 5.2 Write unit tests for auth endpoints
    - Test valid login returns tokens
    - Test wrong password returns 401
    - Test expired refresh token returns 401
    - _Requirements: 9.1, 9.2_

- [ ] 6. Productionise parcel router and wire state machine + RBAC
  - [ ] 6.1 Refactor `app/routers/parcels.py` — parcel creation with full RBAC and atomic transaction
    - Replace `created_by: uuid.UUID` query param with `user: StaffUser = Depends(require_roles(OPERATOR, MANAGER, ADMIN))`
    - Call `generate_tracking_code` from `app.core.tracking_code` (6-digit, 10-retry)
    - Enforce `user.branch_id == payload.origin_branch_id` (403 otherwise)
    - Validate origin and destination branches exist and `is_active=True` (404 otherwise)
    - Wrap Parcel insert + ParcelStatusHistory insert in a single `async with db.begin()` transaction
    - After commit: enqueue `generate_waybill_pdf.delay(parcel_id)` and conditionally `send_telegram_notification.delay(...)` if sender has `telegram_id`
    - _Requirements: 1.1, 1.2, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10_
  - [ ] 6.2 Add `GET /api/parcels` list endpoint with branch-scoped filtering
    - Filter by `status`, `date_from`, `date_to`, `branch_id` query params
    - Scope results: Operators see only their branch parcels; Managers/Admins see all
    - Return paginated response using `app.core.pagination`
    - _Requirements: 9.5_
  - [ ] 6.3 Add `GET /api/parcels/{id}` detail endpoint with status history eager-loaded
    - Return `ParcelOut` with nested `status_history` list
    - Enforce branch RBAC (Operator 403 if neither branch matches)
    - _Requirements: 2.1, 9.5_
  - [ ] 6.4 Add Redis rate limiting to `GET /api/parcels/track/{code}`
    - Use `redis.asyncio` to increment a key `rate:track:{ip}` with 60-second TTL
    - Return `429` after 10 requests per minute per IP
    - Return parcel with full `status_history` (no auth required)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 14.6_
  - [ ]* 6.5 Write property test for rate limiting on public tracking endpoint
    - **Property 19: Rate Limiting on Public Tracking Endpoint**
    - **Validates: Requirements 2.2, 14.6**
    - Use a mocked Redis client; assert the 11th request in a window returns 429
  - [ ] 6.6 Refactor `PATCH /api/parcels/{id}/status` to use state machine + payment gate
    - Require auth via `Depends(require_roles(OPERATOR, MANAGER, DRIVER, ADMIN))`
    - Call `validate_transition(parcel.status, payload.to_status)` — return 400 on ValueError
    - Enforce payment gate: prepaid + unpaid + blocked status + no override → 402
    - Accept `override_note` in `ParcelStatusUpdate`; record it in `ParcelStatusHistory.note`
    - Enforce branch RBAC for Operators (403 if parcel not in their branch)
    - Wrap parcel update + history insert in single transaction; enqueue notifications after commit
    - Broadcast SSE/WebSocket event after commit
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9_
  - [ ]* 6.7 Write property tests for payment gate and RBAC scoping
    - **Property 5: Payment Gate Invariant** — prepaid + unpaid + Operator → 402
    - **Property 6: Payment Gate Override Records Note** — override_note present in history row
    - **Property 11: Branch RBAC Scoping** — Operator request for foreign-branch parcel → 403
    - **Validates: Requirements 1.9, 3.6, 3.7, 3.8, 9.4, 9.5**
  - [ ] 6.8 Add `GET /api/parcels/{id}/waybill` endpoint
    - If `parcel.waybill_url` is set, return it immediately (no re-generation)
    - If not yet generated, return 503 with retry guidance
    - _Requirements: 12.2, 12.3, 12.4_
  - [ ]* 6.9 Write property test for waybill idempotency
    - **Property 21: Waybill Generation Idempotency**
    - **Validates: Requirements 12.3, 18.3**

- [ ] 7. Productionise payments router
  - [ ] 7.1 Refactor `POST /api/payments/cash/{parcel_id}/collect`
    - Require `Depends(require_roles(OPERATOR, MANAGER, ADMIN))` — 403 for lower roles
    - Require non-empty `override_reason` in request body when caller is Operator
    - Store `override_reason` on the `Payment` row
    - Atomically set `payment.status=PAID` and `parcel.payment_status=PAID` in single transaction
    - Enqueue Telegram payment confirmation notification after commit
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  - [ ]* 7.2 Write property test for cash payment override reason
    - **Property 10: Cash Payment Requires Override Reason**
    - **Validates: Requirements 5.2**
  - [ ] 7.3 Refactor `POST /api/payments/chapa/initiate`
    - Create `Payment` row (status=PENDING, method=chapa) before calling Chapa
    - Return `{checkout_url, tx_ref}` on success
    - Handle `ChapaError` and return 502
    - _Requirements: 4.1_
  - [ ] 7.4 Productionise `POST /api/payments/chapa/webhook`
    - Verify HMAC-SHA256 signature using `verify_webhook_signature` before reading payload (401 on failure)
    - Look up payment by `tx_ref`; return 404 if unknown
    - Idempotency check: if `payment.status == PAID`, return 200 no-op
    - Call `verify_transaction(tx_ref)` as source of truth; on `ChapaError`, enqueue `retry_failed_webhook` task and return 200
    - Wrap PAID updates (`payment.status`, `payment.verified_at`, `parcel.payment_status`) in single `async with db.begin()` transaction
    - Enqueue Telegram payment confirmation notification after commit
    - Ensure total response time < 5 seconds (Chapa timeout expectation)
    - _Requirements: 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 4.10, 14.1, 14.2, 14.3_
  - [ ]* 7.5 Write property tests for Chapa webhook behaviour
    - **Property 7: Chapa Webhook Signature Verification** — pure HMAC function
    - **Property 8: Chapa Payment Atomicity** — mock DB to assert all-or-nothing writes
    - **Property 9: Chapa Webhook Idempotency** — duplicate webhook → 200, no DB writes
    - **Validates: Requirements 4.2, 4.5, 4.7, 14.1, 14.3**

- [ ] 8. Implement customers router (`app/routers/customers.py`)
  - [ ] 8.1 Create `POST /api/customers/link`
    - Upsert Customer by phone: create if not exists, overwrite `telegram_id` if exists (even if previously linked to different telegram_id)
    - Return `{linked: true}`
    - No auth required (called by Bot)
    - _Requirements: 17.1, 17.2, 17.3_
  - [ ]* 8.2 Write property test for customer phone upsert
    - **Property 18: Customer Phone Upsert**
    - **Validates: Requirements 17.1**
    - Hypothesis: calling link twice with same phone and different telegram_id produces exactly one Customer row with latest telegram_id
  - [ ] 8.3 Create `GET /api/customers/me/parcels`
    - Identify caller by `telegram_id` from query param (Bot passes it)
    - Return all parcels for the linked phone number
    - Return 404 if no customer found for telegram_id
    - _Requirements: 6.7_
  - [ ] 8.4 Register customers router in `app/main.py`
    - _Requirements: 6.2, 6.3_

- [ ] 9. Implement manifests router (`app/routers/manifests.py`)
  - [ ] 9.1 Create `POST /api/manifests` endpoint
    - Require `Depends(require_roles(MANAGER, ADMIN))`
    - Create `TransferManifest` row and bulk-insert `ManifestParcel` rows
    - Bulk-update all included parcels to `status=IN_TRANSIT` with individual history rows
    - Set manifest `status=DISPATCHED`, `dispatched_at=now()` after parcels updated
    - Enqueue bulk notifications after commit
    - Return manifest with `waybill_pdf_url` (placeholder URL until PDF task runs)
    - _Requirements: 8.1, 8.2, 8.3_
  - [ ] 9.2 Create `GET /api/manifests` and `GET /api/manifests/{id}` endpoints
    - Scope to calling user's branch for Manager; all branches for Admin
    - Return manifest with nested parcel list
    - _Requirements: 8.6_
  - [ ] 9.3 Create `POST /api/manifests/{id}/receive` endpoint
    - Require `Depends(require_roles(OPERATOR, MANAGER, ADMIN))`
    - Verify manifest is in `DISPATCHED` status — 400 otherwise
    - Verify `current_user.branch_id == manifest.destination_branch_id` — 403 otherwise
    - Transition received parcels → `ARRIVED_AT_DESTINATION` with history rows
    - Transition missing parcels → `ON_HOLD` with auto-note
    - Set manifest `status=RECEIVED`, `received_at=now()`
    - Enqueue bulk arrival notifications after commit
    - Return `{received: N, missing: M, missing_parcel_ids: [...]}`
    - _Requirements: 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10_
  - [ ]* 9.4 Write property test for manifest receive completeness
    - **Property 20: Manifest Receive Completeness**
    - **Validates: Requirements 8.4, 8.5, 8.9**
    - Hypothesis: for any partial received_parcel_ids subset, assert each missing parcel → ON_HOLD and each received parcel → ARRIVED_AT_DESTINATION with exactly one history row each

- [ ] 10. Implement branches and staff admin routers
  - [ ] 10.1 Create `app/routers/branches.py`
    - `POST /api/branches`: require Admin; persist with unique `code` (2–5 uppercase chars); return 409 on duplicate code; `is_active` defaults to TRUE
    - `GET /api/branches`: require Manager or Admin; return paginated list
    - `PATCH /api/branches/{id}`: require Admin; allow deactivation (`is_active=FALSE`) without deleting data
    - Register in `app/main.py`
    - _Requirements: 10.1, 10.4, 10.5, 10.6_
  - [ ] 10.2 Create `app/routers/staff.py`
    - `POST /api/staff`: require Admin; hash password via `app.core.security`; assign role + branch_id
    - `GET /api/staff`: require Admin; return paginated list
    - `PATCH /api/staff/{id}`: require Admin; apply partial updates; return updated record
    - Register in `app/main.py`
    - _Requirements: 10.2, 10.3, 10.5, 9.7_

- [ ] 11. Implement proof of delivery router
  - [ ] 11.1 Add `POST /api/parcels/{id}/proof` to `app/routers/parcels.py`
    - Require `Depends(require_roles(OPERATOR, MANAGER, ADMIN))`
    - Return 400 if parcel is not in `DELIVERED` status
    - Create `ProofOfDelivery` row; enforce DB UNIQUE constraint on `parcel_id` (return 409 if already exists)
    - Accept `photo_url`, `signature_url`, `notes` fields
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

- [ ] 12. Implement reporting router (`app/routers/reports.py`)
  - [ ] 12.1 Create `GET /api/reports/cash-reconciliation`
    - Require `Depends(require_roles(MANAGER, ADMIN))`
    - Filter by `date_from`, `date_to`; scope to `current_user.branch_id` for Manager, all branches for Admin
    - Group by operator; return `{operator_id, operator_name, total_collected, parcel_count}`
    - _Requirements: 11.1, 11.5, 11.6_
  - [ ] 12.2 Create `GET /api/reports/branch-performance`
    - Return parcel counts by status, revenue totals, and on-time delivery rate for specified period
    - Branch-scoped for Manager; all branches for Admin
    - _Requirements: 11.2, 11.5, 11.6_
  - [ ] 12.3 Create `GET /api/reports/operator-overrides`
    - Require Admin; return all Payment rows with non-null `override_reason`, joined to operator and parcel
    - _Requirements: 11.3, 9.8_
  - [ ] 12.4 Create `GET /api/reports/delay-alerts`
    - Return all parcels in `IN_TRANSIT` status beyond configured delay threshold (from `app.config`)
    - Require Manager or Admin
    - _Requirements: 11.4, 11.6_
  - [ ] 12.5 Register reports router in `app/main.py`
    - _Requirements: 11.1, 11.6_

- [ ] 13. Set up Celery workers (`app/workers/`)
  - [ ] 13.1 Create `app/workers/celery_app.py`
    - Instantiate `Celery` with Redis broker (`settings.redis_url`)
    - Configure result backend, task serializer (json), timezone (Africa/Addis_Ababa)
    - Export `celery_app` singleton used by all task modules
    - _Requirements: 15.4_
  - [ ] 13.2 Create `app/workers/notification_tasks.py`
    - Implement `send_telegram_notification(telegram_id, message)` task — 3 retries with exponential backoff (`autoretry_for=(Exception,)`, `retry_backoff=True`, `max_retries=3`)
    - Write `NotificationLog` row (status=queued → sent/failed) on each attempt
    - Implement `send_sms_notification(phone, message)` task — same retry pattern, calls `app.services.sms`
    - Implement `bulk_arrival_notifications(parcel_ids, branch_id)` task
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.6, 15.1, 15.4_
  - [ ]* 13.3 Write property test for notification retry behaviour
    - **Property 15: Notification Retry Behaviour**
    - **Validates: Requirements 7.3, 15.1**
    - Mock Telegram send to always fail; assert task retries exactly 3 times and final `notification_log.status == "failed"`
  - [ ]* 13.4 Write property test for notification log completeness
    - **Property 16: Notification Log Completeness**
    - **Validates: Requirements 7.4**
    - Assert every call to `send_telegram_notification` creates a `notification_log` row, regardless of success or failure
  - [ ]* 13.5 Write property test for notification conditional on Telegram linkage
    - **Property 14: Notification Conditional on Telegram Linkage**
    - **Validates: Requirements 1.7, 3.4, 4.6, 7.1, 7.2**
    - Assert `send_telegram_notification` is enqueued when customer has `telegram_id`, and `send_sms_notification` when `telegram_id` is None
  - [ ] 13.6 Create `app/workers/payment_tasks.py`
    - Implement `retry_failed_webhook(tx_ref)` task: re-call `verify_transaction(tx_ref)`, update Payment to PAID or FAILED
    - _Requirements: 4.9, 15.2, 15.3_
  - [ ] 13.7 Create `app/workers/pdf_tasks.py`
    - Implement `generate_waybill_pdf(parcel_id)` task
    - Load parcel from DB, render HTML template with parcel data, convert to PDF via WeasyPrint
    - Upload PDF to S3/R2 using `app.services.storage`
    - Update `parcel.waybill_url` with the stored object URL
    - Log error and set no URL (do NOT block parcel operations) on failure
    - _Requirements: 12.1, 12.4, 15.4_
  - [ ] 13.8 Create `app/workers/alert_tasks.py`
    - Implement `check_transit_delays()` task: query `IN_TRANSIT` parcels past threshold, send alerts to admins via `send_telegram_notification.delay`
    - Implement `daily_manager_digest()` task: aggregate branch KPIs, send Telegram/email digest to Manager per branch
    - _Requirements: 7.7, 7.8, 15.5, 15.6_
  - [ ] 13.9 Create `app/workers/beat_schedule.py`
    - Define `beat_schedule` for: `retry_failed_webhook` every 15 min, `check_transit_delays` every hour, `daily_manager_digest` at 07:00 Africa/Addis_Ababa
    - _Requirements: 7.7, 7.8, 15.3, 15.5_

- [ ] 14. Implement backend services (`app/services/`)
  - [ ] 14.1 Fix `verify_webhook_signature` in `app/services/chapa.py`
    - Replace `hmac.new(...)` with `hmac.new(...)` → correct call is `hmac.new` which doesn't exist; fix to `hmac.HMAC` or the `hmac` module's correct API (`hmac.new` → should be `hmac.HMAC` — use `hmac.digest` or `hmac.new` from stdlib)
    - The correct Python call is `hmac.new(key, msg, digestmod)` — verify this is what the current code uses and fix the typo
    - _Requirements: 4.2, 14.1_
  - [ ] 14.2 Upgrade `app/services/notifications.py` to dispatch via Celery tasks
    - Remove direct Telegram API calls (currently `notify_status_change` is synchronous)
    - Replace with `send_telegram_notification.delay(...)` and `send_sms_notification.delay(...)` calls
    - Implement `notify_status_change(parcel, sender)` and `notify_payment_confirmed(parcel, sender)` as thin dispatchers
    - _Requirements: 7.1, 7.2, 7.6_
  - [ ] 14.3 Create `app/services/pdf.py`
    - Implement `render_waybill_html(parcel: Parcel) -> str` — Jinja2 template with parcel fields
    - Implement `generate_pdf_bytes(html: str) -> bytes` — call WeasyPrint
    - _Requirements: 12.1_
  - [ ] 14.4 Create `app/services/storage.py`
    - Implement `upload_file(bucket: str, key: str, data: bytes, content_type: str) -> str` using `boto3`
    - Return the public URL of the uploaded object
    - Read `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET`, `S3_ENDPOINT_URL` from `settings`
    - _Requirements: 12.1, 12.2_
  - [ ] 14.5 Create `app/services/sms.py`
    - Implement `send_sms(phone: str, message: str) -> None` calling the configured SMS gateway
    - Read `SMS_API_URL`, `SMS_API_KEY` from `settings`
    - _Requirements: 7.2_

- [ ] 15. Implement real-time SSE / WebSocket broadcast in the API
  - [ ] 15.1 Add Server-Sent Events endpoint `GET /api/events/branch/{branch_id}`
    - Require auth via JWT
    - Use an in-process event bus (e.g. `asyncio.Queue` per branch_id) or Redis Pub/Sub
    - Emit a JSON event `{type: "status_update", parcel_id, tracking_code, new_status}` after each committed status transition
    - Call this emitter at the end of `PATCH /api/parcels/{id}/status` (after commit)
    - _Requirements: 3.5, 16.1, 16.2, 16.3_

- [ ] 16. Checkpoint — backend API feature complete
  - Ensure all backend tests pass, ask the user if questions arise.

- [ ] 17. Update `app/config.py` and complete `app/exceptions.py`
  - [ ] 17.1 Extend `app/config.py` (Pydantic Settings)
    - Add all required env vars: `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `REDIS_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET`, `S3_ENDPOINT_URL`, `SMS_API_URL`, `SMS_API_KEY`, `DELAY_THRESHOLD_HOURS`, `CELERY_BROKER_URL`
    - Add `chapa_webhook_secret` if not present
    - _Requirements: 14.5_
  - [ ] 17.2 Create `app/exceptions.py`
    - Define `ParcelNotFoundError`, `InvalidTransitionError`, `PaymentGateError`, `BranchNotFoundError`
    - Register FastAPI exception handlers in `app/main.py` mapping these to appropriate HTTP status codes
    - _Requirements: 1.8, 3.2_

- [ ] 18. Productionise and expand the Telegram bot (`app/bot/`)
  - [ ] 18.1 Split bot handlers into individual files under `app/bot/handlers/`
    - Create `app/bot/handlers/start.py` — `/start` command and contact sharing (`handle_contact`) calling `POST /api/customers/link`
    - Create `app/bot/handlers/track.py` — `/track <code>` command calling `GET /api/parcels/track/{code}`
    - Create `app/bot/handlers/my_parcels.py` — "My Parcels" inline keyboard callback calling `GET /api/customers/me/parcels`
    - Create `app/bot/handlers/payment.py` — "Pay Now" callback calling `POST /api/payments/chapa/initiate`; register `CallbackQueryHandler(handle_pay_button, pattern=r"^pay:")`
    - Create `app/bot/handlers/receipt.py` — "Confirm receipt" callback calling `PATCH /api/parcels/{id}/status` with `to_status=DELIVERED`
    - Create `app/bot/messages.py` — all message template strings (English)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_
  - [ ] 18.2 Refactor `app/bot/bot.py` to import and register all handlers from `handlers/`
    - Register all `CommandHandler`, `MessageHandler`, and `CallbackQueryHandler` entries
    - Ensure bot contains zero business logic — every handler ends with an API call
    - _Requirements: 6.6_
  - [ ]* 18.3 Write unit tests for bot handler routing
    - Mock `httpx.AsyncClient` to assert each handler calls the correct API endpoint
    - Test `/track` with unknown code returns "No parcel found" message
    - _Requirements: 6.4, 6.5_

- [ ] 19. Add property test for parcel status audit trail
  - [ ]* 19.1 Write property test for parcel status history append-only invariant
    - **Property 17: Parcel Status Audit Trail**
    - **Validates: Requirements 1.5, 3.3**
    - Hypothesis: after N status transitions on a parcel, `len(parcel_status_history)` == N+1 (initial CREATED row + N transitions)

- [ ] 20. Integration test suite for backend API
  - [ ]* 20.1 Write integration tests for full parcel lifecycle
    - Test CREATE → RECEIVED_AT_ORIGIN → IN_TRANSIT → ARRIVED_AT_DESTINATION → READY_FOR_PICKUP → DELIVERED
    - Use `httpx.AsyncClient` with in-memory test DB (SQLite async or Postgres test DB)
    - Assert status history row count at each step (Property 17)
    - _Requirements: 1.1, 3.3_
  - [ ]* 20.2 Write integration tests for Chapa payment flow
    - Mock Chapa `verify_transaction` to return success
    - Assert payment and parcel both marked PAID in single transaction
    - Assert duplicate webhook returns 200 without DB writes
    - _Requirements: 4.1, 4.5, 4.7_
  - [ ]* 20.3 Write integration tests for RBAC branch scoping
    - Operator from Branch A → 403 on Branch B parcel
    - Manager → 200 on any branch parcel
    - _Requirements: 9.4, 9.5_
  - [ ]* 20.4 Write integration tests for manifest bulk-receive
    - Partial receipt: missing parcels set to ON_HOLD; received parcels set to ARRIVED_AT_DESTINATION
    - _Requirements: 8.4, 8.5_

- [ ] 21. Final backend checkpoint — Ensure all tests pass
  - Ensure all unit, property, and integration tests pass, ask the user if questions arise.

- [ ] 22. Scaffold and configure `mela-express-dashboard/` (Next.js)
  - [ ] 22.1 Initialise Next.js project with TypeScript, Tailwind CSS, and App Router
    - Set up `package.json`, `tsconfig.json`, `tailwind.config.ts`, `next.config.ts`
    - Install dependencies: `axios`, `@radix-ui/react-*` (or similar headless UI), `react-hook-form`, `zod`, `swr` or `react-query`
    - Create `src/types/index.ts` mirroring backend Pydantic schemas (Parcel, Branch, StaffUser, Payment, Manifest, etc.)
    - _Requirements: 16.2_
  - [ ] 22.2 Implement `src/lib/api.ts` and `src/lib/auth.ts`
    - `api.ts`: Axios instance with base URL from env, JWT Bearer interceptor, 401 → redirect to login
    - `auth.ts`: `login(phone, password)`, token storage in `localStorage` (access + refresh), `refreshToken()`, `logout()`
    - _Requirements: 9.1, 9.2, 16.4_
  - [ ] 22.3 Build login page (`src/app/login/page.tsx`)
    - Form with phone + password fields; call `auth.login`; redirect to `/dashboard` on success
    - _Requirements: 9.1_
  - [ ] 22.4 Build dashboard layout (`src/app/layout.tsx`, `src/components/layout/`)
    - `Sidebar.tsx`: navigation links for all routes based on user role (hide admin-only links from non-admins)
    - `TopBar.tsx`: current user name, branch, logout button
    - `RoleGuard.tsx`: HOC that checks `user.role` and redirects unauthorized access
    - _Requirements: 9.4, 16.2_
  - [ ] 22.5 Build KPI dashboard page (`src/app/dashboard/page.tsx`)
    - Fetch branch performance stats from `GET /api/reports/branch-performance`
    - Display parcel counts by status, revenue total, recent activity
    - _Requirements: 11.2, 16.2_

- [ ] 23. Build parcel management pages (dashboard)
  - [ ] 23.1 Build `src/components/parcels/` shared components
    - `StatusBadge.tsx`: colored badge for each `ParcelStatus` value
    - `StatusTimeline.tsx`: renders `parcel_status_history` as a vertical timeline
    - `ParcelTable.tsx`: sortable table with tracking code, status, branches, created date
    - `ParcelForm.tsx`: intake form — origin/destination branch selects, sender/receiver phone+name, weight, price, payment mode
    - _Requirements: 1.1_
  - [ ] 23.2 Build parcel list page (`src/app/parcels/page.tsx`)
    - Fetch `GET /api/parcels` with status and date filters
    - Render `ParcelTable` with pagination
    - Link each row to detail page
    - _Requirements: 9.5_
  - [ ] 23.3 Build parcel intake form page (`src/app/parcels/new/page.tsx`)
    - Render `ParcelForm`, validate with `react-hook-form` + `zod`
    - POST to `POST /api/parcels`; redirect to detail page on success
    - _Requirements: 1.1_
  - [ ] 23.4 Build parcel detail page (`src/app/parcels/[id]/page.tsx`)
    - Fetch `GET /api/parcels/{id}` (with status history)
    - Display `StatusTimeline`, `StatusBadge`, waybill download button, cash collection action
    - Status update form (select next allowed status from state machine client-side hint)
    - Subscribe to SSE `GET /api/events/branch/{branch_id}` for real-time updates; reconnect on disconnect
    - _Requirements: 2.1, 3.5, 12.2, 16.2, 16.3, 16.4_

- [ ] 24. Build manifest management pages (dashboard)
  - [ ] 24.1 Build `src/components/manifests/` shared components
    - `ManifestTable.tsx`: table with manifest ID, origin → destination, status, parcel count
    - `ManifestReceiveForm.tsx`: checkbox list of parcels in manifest; submit confirmed/missing parcel IDs
    - _Requirements: 8.1_
  - [ ] 24.2 Build manifest list page (`src/app/manifests/page.tsx`) and create page (`src/app/manifests/new/page.tsx`)
    - List: fetch `GET /api/manifests`; render `ManifestTable`
    - Create: multi-select parcels (filter by origin branch, status=RECEIVED_AT_ORIGIN); POST to `POST /api/manifests`
    - _Requirements: 8.1, 8.2_
  - [ ] 24.3 Build manifest receive page (`src/app/manifests/[id]/receive/page.tsx`)
    - Fetch manifest with parcels from `GET /api/manifests/{id}`
    - Render `ManifestReceiveForm`; submit to `POST /api/manifests/{id}/receive`
    - _Requirements: 8.4, 8.5, 8.6_

- [ ] 25. Build cash, reports, and admin pages (dashboard)
  - [ ] 25.1 Build cash reconciliation page (`src/app/cash/page.tsx`)
    - Date range picker; fetch `GET /api/reports/cash-reconciliation`; table grouped by operator
    - _Requirements: 11.1_
  - [ ] 25.2 Build reports page (`src/app/reports/page.tsx`)
    - Branch performance charts; delay alerts table
    - _Requirements: 11.2, 11.4_
  - [ ] 25.3 Build admin pages (`src/app/admin/`)
    - `branches/page.tsx`: CRUD for branches (Admin only, guarded by `RoleGuard`)
    - `staff/page.tsx`: CRUD for staff accounts with role assignment
    - `overrides/page.tsx`: read-only table of operator override audit log from `GET /api/reports/operator-overrides`
    - _Requirements: 10.1, 10.2, 10.3, 11.3_

- [ ] 26. Checkpoint — dashboard feature complete
  - Ensure all dashboard pages render without errors and connect to the API, ask the user if questions arise.

- [ ] 27. Scaffold and build `mela-express-public/` tracking page
  - [ ] 27.1 Initialise Next.js project for `mela-express-public/`
    - Set up `package.json`, `tsconfig.json`, minimal Tailwind setup
    - _Requirements: 2.4_
  - [ ] 27.2 Build `src/app/track/[code]/page.tsx`
    - Server-side fetch `GET /api/parcels/track/{code}` (Next.js `fetch` with no auth)
    - Display tracking code, current status, origin/destination branch, and status history timeline
    - Show 404 page if tracking code not found
    - Page is fully public (no auth required)
    - _Requirements: 2.1, 2.3, 2.4_

- [ ] 28. Finalize Docker and infrastructure configuration
  - [ ] 28.1 Create `docker-compose.dev.yml`
    - Define services: `api` (hot reload with `uvicorn --reload`), `bot`, `worker`, `beat`, `db` (Postgres), `redis` (no Nginx in dev)
    - Mount source code volumes for hot reload
    - _Requirements: 14.4_
  - [ ] 28.2 Update `docker-compose.yml` (production)
    - Add `worker` and `beat` services running `celery -A app.workers.celery_app worker` and `celery -A app.workers.celery_app beat`
    - Add `nginx` service pointing to `docker/nginx/`
    - Ensure all services share an internal Docker network; only `nginx` exposes port 80/443
    - _Requirements: 14.4_
  - [ ] 28.3 Finalize `docker/nginx/sites-available/mela-express.conf`
    - Proxy `/api/` to the `api` service on port 8000
    - Proxy `/` to the `mela-express-dashboard` service
    - Add SSL/TLS termination with Certbot Let's Encrypt placeholders
    - _Requirements: 14.4_
  - [ ] 28.4 Write `scripts/seed_branches.py`
    - Read branch data from CSV; upsert into `branches` table via SQLAlchemy
    - _Requirements: 10.1_
  - [ ] 28.5 Write `scripts/seed_admin.py`
    - Create first admin account with hashed password from env vars
    - _Requirements: 10.2_

- [ ] 29. Final checkpoint — Ensure all tests pass and Docker Compose starts cleanly
  - Ensure all unit, property, and integration tests pass; verify `docker-compose up` starts all services without errors; ask the user if questions arise.


---

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP delivery
- Each task references specific requirements from `requirements.md` for full traceability
- The backend is Python; the dashboard and public site are TypeScript/Next.js
- All Celery tasks must be enqueued **after** database transaction commits — never inline
- Property tests use the `hypothesis` library; add `hypothesis` to `requirements-dev.txt`
- Migrations should be applied in order; never edit a committed migration file
- The `app/core/` package must have zero FastAPI or SQLAlchemy imports — pure Python only

---

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3"] },
    { "id": 1, "tasks": ["2.1", "17.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "17.2"] },
    { "id": 3, "tasks": ["3.1", "4.1", "4.3", "4.5"] },
    { "id": 4, "tasks": ["3.2", "3.3", "4.2", "4.4", "13.1"] },
    { "id": 5, "tasks": ["3.4", "5.1", "6.1", "7.1", "8.1", "9.1", "10.1", "10.2", "14.1", "14.5"] },
    { "id": 6, "tasks": ["5.2", "6.2", "6.3", "6.4", "7.3", "8.2", "8.3", "8.4", "11.1", "14.2", "14.3", "14.4"] },
    { "id": 7, "tasks": ["6.5", "6.6", "7.4", "9.2", "9.3", "12.1", "12.2", "12.3", "12.4", "12.5"] },
    { "id": 8, "tasks": ["6.7", "6.8", "7.2", "7.5", "9.4", "11.2", "13.2", "13.6", "13.7"] },
    { "id": 9, "tasks": ["6.9", "13.3", "13.4", "13.5", "13.8", "13.9", "14.2", "15.1"] },
    { "id": 10, "tasks": ["18.1", "19.1", "20.1", "20.2", "20.3", "20.4"] },
    { "id": 11, "tasks": ["18.2", "22.1"] },
    { "id": 12, "tasks": ["18.3", "22.2", "22.3", "27.1"] },
    { "id": 13, "tasks": ["22.4", "22.5", "23.1", "24.1", "27.2"] },
    { "id": 14, "tasks": ["23.2", "23.3", "24.2", "25.1", "25.2", "25.3"] },
    { "id": 15, "tasks": ["23.4", "24.3", "28.1", "28.2", "28.3"] },
    { "id": 16, "tasks": ["28.4", "28.5"] }
  ]
}
```
