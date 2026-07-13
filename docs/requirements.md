# Requirements Document

## Introduction

Mela Express is a full digital operations and tracking platform for a multi-branch parcel delivery company operating across Ethiopia. The platform replaces a fully manual operation with a centralised backend that is the single source of truth for every parcel, branch, operator, and payment. Customers interact exclusively through a Telegram bot; operators and admins work through a web dashboard; Chapa handles all online payments alongside a parallel manual cash path.

The parcel is the central object around which every other concern — payments, notifications, manifests, and reporting — revolves.

---

## Glossary

- **Platform**: The Mela Express backend API, Telegram bot process, background workers, and web dashboard collectively.
- **API**: The FastAPI backend service that serves as the single source of truth for all clients.
- **Bot**: The Telegram bot process that acts as a thin adapter between Telegram users and the API.
- **Dashboard**: The Next.js web dashboard used by all staff roles.
- **Worker**: The Celery background worker process responsible for notifications, PDF generation, and scheduled tasks.
- **Parcel**: The central business entity representing a shipment from one branch to another.
- **Tracking_Code**: A unique identifier for a parcel following the format `MEX-{BRANCH_CODE}-{6DIGIT}` (e.g. `MEX-HW-000482`).
- **Branch**: A physical Mela Express office in a city (e.g. Hawassa, Addis Ababa).
- **Customer**: A sender or receiver identified by phone number, optionally linked to a Telegram account.
- **Staff_User**: An authenticated member of staff with one of the roles: Operator, Manager, Driver, or Admin.
- **Operator**: A branch staff member who registers parcels and collects cash.
- **Manager**: A branch manager who approves overrides and views branch reports.
- **Driver**: A staff member who marks parcels in transit or arrived.
- **Admin**: A super-admin with cross-branch visibility and system configuration access.
- **Manifest**: A transfer document grouping parcels dispatched from one branch to another.
- **Payment**: A financial record associated with a parcel, settled either via Chapa (online) or cash.
- **Chapa**: The third-party hosted payment gateway used for online payments.
- **Status_History**: An append-only audit log of every parcel state transition.
- **Notification_Log**: A delivery record for every Telegram or SMS notification sent by the platform.
- **Waybill**: A PDF document generated for each parcel at creation time.
- **Proof_Of_Delivery**: A record capturing a photo, signature, or notes confirming parcel delivery.
- **RBAC**: Role-based access control enforced on every protected API route.
- **JWT**: JSON Web Token used for staff authentication (15-minute access token, 7-day refresh token).

---

## Requirements

### Requirement 1: Parcel Creation

**User Story:** As an operator, I want to register a new parcel in the system, so that it receives a unique tracking code and enters the delivery workflow.

#### Acceptance Criteria

1. WHEN an authenticated operator submits a valid parcel creation request, THE API SHALL create a new Parcel record with `status=CREATED` and `payment_status=PENDING`.
2. WHEN a parcel is created, THE API SHALL generate a globally unique Tracking_Code matching the pattern `MEX-{BRANCH_CODE}-{6DIGIT}`.
3. WHEN a Tracking_Code candidate already exists in the database, THE API SHALL retry generation up to 10 times before returning an error.
4. WHEN a parcel is created, THE API SHALL create or retrieve the sender's Customer record by phone number.
5. WHEN a parcel is created, THE API SHALL insert a Parcel_Status_History row recording the transition from `null` to `CREATED`, the operator ID, and the branch ID.
6. WHEN a parcel is created, THE API SHALL enqueue a waybill PDF generation task after the database transaction commits.
7. WHEN a parcel is created and the sender has a linked Telegram account, THE API SHALL enqueue a Telegram intake notification after the database transaction commits.
8. IF the origin branch or destination branch does not exist or is inactive, THEN THE API SHALL return a `404` error and not create the parcel.
9. IF a parcel creation request is submitted by a user whose `branch_id` does not match `origin_branch_id`, THEN THE API SHALL return a `403` error.
10. THE API SHALL store parcel creation within a single atomic database transaction covering the Parcel row and the Status_History row.

---

### Requirement 2: Parcel Status Tracking

**User Story:** As a customer, I want to track my parcel using its tracking code, so that I know its current location and status.

#### Acceptance Criteria

1. WHEN a tracking code is submitted to the public tracking endpoint, THE API SHALL return the parcel's current status, origin branch, destination branch, and full status history.
2. WHEN the public tracking endpoint receives more than 10 requests per minute from a single IP address, THE API SHALL return a `429 Too Many Requests` response for subsequent requests within that window.
3. IF a submitted tracking code does not correspond to any parcel, THEN THE API SHALL return a `404` error.
4. THE API SHALL expose the public tracking endpoint without requiring authentication.

---

### Requirement 3: Parcel Status Updates (State Machine)

**User Story:** As an operator or driver, I want to advance a parcel through the delivery workflow, so that its status accurately reflects its physical location and condition.

#### Acceptance Criteria

1. WHEN a staff member submits a status update request, THE API SHALL validate the transition against the allowed state machine before making any database writes.
2. IF a requested status transition is not permitted by the state machine, THEN THE API SHALL return a `400` error with a message identifying the disallowed transition and listing allowed next states.
3. WHEN a valid status transition is applied, THE API SHALL update `parcel.status` and `parcel.updated_at` and insert a new Parcel_Status_History row within a single atomic transaction.
4. WHEN a status transition is committed, THE API SHALL enqueue status notifications for the sender (and receiver if linked) via the Worker.
5. WHEN a status transition is committed, THE API SHALL broadcast a real-time update to dashboard clients connected via WebSocket or Server-Sent Events.
6. WHILE a parcel's `payment_mode` is `BEFORE` and `payment_status` is not `PAID`, THE API SHALL reject transitions to `IN_TRANSIT`, `ARRIVED_AT_DESTINATION`, `READY_FOR_PICKUP`, or `DELIVERED` unless the requesting user is a Manager or Admin and supplies an `override_note`.
7. WHEN a Manager or Admin overrides the payment gate, THE API SHALL record the `override_note` in the Parcel_Status_History row.
8. IF a status update request is made by an Operator whose `branch_id` does not match the parcel's `origin_branch_id` or `destination_branch_id`, THEN THE API SHALL return a `403` error.
9. THE API SHALL enforce that DELIVERED, RETURNED, CANCELLED, and LOST are terminal states with no outbound transitions.

---

### Requirement 4: Payment — Online (Chapa)

**User Story:** As a customer, I want to pay for my parcel online through Chapa, so that I can complete the transaction without visiting a branch.

#### Acceptance Criteria

1. WHEN a customer initiates a Chapa payment, THE API SHALL create a Payment record with `status=PENDING` and `method=chapa`, then call the Chapa transaction initialisation API and return the `checkout_url` and `tx_ref`.
2. WHEN the Chapa webhook endpoint receives a POST request, THE API SHALL verify the HMAC-SHA256 signature against the raw request body using the configured webhook secret before processing anything.
3. IF the Chapa webhook signature is invalid, THEN THE API SHALL return `401` and make no database writes.
4. WHEN the webhook signature is valid, THE API SHALL call Chapa's server-side `verify` endpoint as the authoritative source of payment status.
5. WHEN Chapa's verify endpoint confirms `status=success`, THE API SHALL atomically set `payment.status=PAID`, `payment.verified_at=now()`, and `parcel.payment_status=PAID`.
6. WHEN a payment is confirmed as PAID, THE API SHALL enqueue a Telegram payment confirmation notification for the sender.
7. IF a Chapa webhook arrives for a `tx_ref` that is already marked `PAID`, THEN THE API SHALL return `200` without making any database writes (idempotency).
8. IF a Chapa webhook arrives for an unknown `tx_ref`, THEN THE API SHALL return `404` and log the event.
9. IF the Chapa verify API is unreachable when processing a webhook, THEN THE API SHALL leave the payment in `PENDING` status and enqueue a `retry_failed_webhook` task.
10. THE API SHALL always respond to the Chapa webhook endpoint within 5 seconds.

---

### Requirement 5: Payment — Cash Collection

**User Story:** As an operator, I want to record cash payments for parcels, so that cash transactions are tracked and reconciled by managers.

#### Acceptance Criteria

1. WHEN an operator records a cash payment for a parcel, THE API SHALL create a Payment record with `method=cash` and `status=PAID`.
2. WHEN a Manager or Admin manually overrides a payment status, THE API SHALL require a non-empty `override_reason` and record it on the Payment row.
3. IF a cash payment is recorded by a user without Operator or higher role, THEN THE API SHALL return a `403` error.
4. THE API SHALL expose a cash collection endpoint (`POST /api/payments/cash/{parcel_id}/collect`) accessible to Operators, Managers, and Admins only.

---

### Requirement 6: Telegram Bot — Customer Interface

**User Story:** As a customer, I want to interact with Mela Express through Telegram, so that I can register, track parcels, and pay without installing a separate app.

#### Acceptance Criteria

1. WHEN a customer sends `/start` to the Bot, THE Bot SHALL respond with a prompt requesting the customer to share their phone number using Telegram's native contact-sharing mechanism.
2. WHEN a customer shares their phone number, THE Bot SHALL call `POST /api/customers/link` to associate the `telegram_id` with the phone number.
3. WHEN the customer link is successful, THE Bot SHALL confirm linkage and inform the customer they can use `/track <code>` to track parcels.
4. WHEN a customer sends `/track <code>`, THE Bot SHALL call `GET /api/parcels/track/{code}` and return the parcel status details to the customer.
5. WHEN a customer taps the "Pay Now" inline button, THE Bot SHALL call `POST /api/payments/chapa/initiate` and return an inline button linking to the Chapa checkout URL.
6. THE Bot SHALL contain no business logic — every meaningful action SHALL be an HTTP call to the API.
7. THE Bot SHALL display a "My Parcels" option that retrieves all parcels for the linked customer's phone number via `GET /api/customers/me/parcels`.

---

### Requirement 7: Notifications

**User Story:** As a customer, I want to receive real-time notifications when my parcel status changes or payment is confirmed, so that I am always informed without needing to poll.

#### Acceptance Criteria

1. WHEN a parcel status changes, THE Worker SHALL enqueue a Telegram notification for the sender if a `telegram_id` is linked to the sender's Customer record.
2. WHEN a customer has no linked `telegram_id`, THE Worker SHALL send an SMS notification via the configured SMS gateway instead.
3. WHEN a Telegram notification task fails to deliver, THE Worker SHALL retry up to 3 times with exponential backoff before marking the Notification_Log entry as `failed`.
4. THE Worker SHALL log every notification attempt to the Notification_Log table, including channel, message, status, and timestamp.
5. WHEN a payment is confirmed as PAID, THE Worker SHALL send a payment confirmation notification to the sender.
6. THE Worker SHALL never send notifications inline within a database transaction — all notification dispatch SHALL occur after the transaction commits.
7. WHEN the Celery beat schedule fires a delay-check task (every hour), THE Worker SHALL identify all parcels with `status=IN_TRANSIT` beyond the configured threshold and alert admins.
8. WHEN the Celery beat schedule fires the daily digest task (07:00 EAT), THE Worker SHALL send a branch summary to the branch Manager via Telegram or email.

---

### Requirement 8: Inter-Branch Transfer Manifests

**User Story:** As a branch manager, I want to create and manage transfer manifests, so that parcels are tracked accurately when moved between branches.

#### Acceptance Criteria

1. WHEN a Manager or Admin creates a manifest, THE API SHALL create a Transfer_Manifest record and associate the specified parcel IDs with it, then bulk-update all included parcels to `status=IN_TRANSIT`.
2. WHEN a manifest is created, THE API SHALL generate a waybill PDF URL for the manifest and return it in the response.
3. WHEN a manifest is created, THE API SHALL enqueue notifications for all parcels included in the manifest.
4. WHEN a destination Operator submits a manifest receive request, THE API SHALL transition all confirmed parcels to `ARRIVED_AT_DESTINATION`.
5. WHEN a destination Operator submits a manifest receive request and some parcels are absent from the received list, THE API SHALL transition those missing parcels to `ON_HOLD` with an auto-generated note.
6. WHEN a manifest is fully received, THE API SHALL set the manifest `status=RECEIVED` and record `received_at`.
7. IF a manifest receive request is submitted by a user whose `branch_id` does not match the manifest's `destination_branch_id`, THEN THE API SHALL return a `403` error.
8. IF a receive request is submitted for a manifest not in `DISPATCHED` status, THEN THE API SHALL return a `400` error.
9. THE API SHALL record one Parcel_Status_History row per parcel for every manifest-receive operation.
10. WHEN a manifest receive operation completes, THE API SHALL enqueue bulk arrival notifications for all confirmed parcels.

---

### Requirement 9: Staff Authentication and RBAC

**User Story:** As a system administrator, I want all staff access to be authenticated and role-restricted, so that operators, managers, and admins can only perform actions appropriate to their role.

#### Acceptance Criteria

1. WHEN a staff member submits valid credentials to `POST /api/auth/login`, THE API SHALL return a JWT access token (valid 15 minutes) and a JWT refresh token (valid 7 days).
2. WHEN a JWT access token expires and a valid refresh token is submitted to `POST /api/auth/refresh`, THE API SHALL return a new access token.
3. IF a request to a protected route lacks a valid JWT, THEN THE API SHALL return `401 Unauthorized`.
4. IF a request is made by a Staff_User whose role is not permitted for that route, THEN THE API SHALL return `403 Forbidden`.
5. WHILE a Staff_User has role Operator, THE API SHALL restrict parcel read and write access to parcels where `origin_branch_id` or `destination_branch_id` matches the operator's `branch_id`.
6. THE API SHALL enforce RBAC through a reusable FastAPI dependency on every protected route.
7. THE API SHALL hash all staff passwords using bcrypt before storage and SHALL never store or log plaintext passwords.
8. WHEN a Manager or Admin makes a manual payment override, THE API SHALL surface the action in the operator overrides report accessible at `GET /api/reports/operator-overrides`.

---

### Requirement 10: Branch and Staff Administration

**User Story:** As an admin, I want to manage branches and staff accounts, so that the platform accurately reflects the company's operational structure.

#### Acceptance Criteria

1. WHEN an Admin creates a branch via `POST /api/branches`, THE API SHALL persist the branch with a unique `code` (2–5 uppercase characters) and an `is_active` flag defaulting to `TRUE`.
2. WHEN an Admin creates a staff account via `POST /api/staff`, THE API SHALL assign the account a role, link it to a branch, and hash the password before storage.
3. WHEN an Admin updates a staff record via `PATCH /api/staff/{id}`, THE API SHALL apply the changes and return the updated record.
4. IF a branch creation request includes a `code` that already exists, THEN THE API SHALL return a `409 Conflict` error.
5. THE API SHALL restrict all branch and staff management endpoints to users with the Admin role.
6. THE API SHALL allow branches to be deactivated by setting `is_active=FALSE` without deleting associated historical data.

---

### Requirement 11: Reporting and Reconciliation

**User Story:** As a branch manager or admin, I want access to operational reports, so that I can reconcile cash, monitor performance, and investigate exceptions.

#### Acceptance Criteria

1. WHEN a Manager or Admin requests a cash reconciliation report, THE API SHALL return all cash payments recorded within the specified date range for the user's branch (or all branches for Admin), grouped by operator.
2. WHEN a Manager or Admin requests a branch performance report, THE API SHALL return parcel counts by status, on-time delivery rates, and revenue totals for the specified period.
3. WHEN an Admin requests the operator overrides report, THE API SHALL return all payment override events with the operator ID, override reason, timestamp, and parcel reference.
4. WHEN an Admin requests the delay alerts report, THE API SHALL return all parcels currently in `IN_TRANSIT` status beyond the configured delay threshold.
5. THE API SHALL scope branch performance and cash reconciliation reports to the requesting Manager's `branch_id` unless the requesting user is Admin.
6. THE API SHALL restrict all reporting endpoints to users with Manager or Admin roles.

---

### Requirement 12: Waybill PDF Generation

**User Story:** As an operator, I want a waybill PDF to be generated automatically for each parcel, so that I have a printable document to attach to the shipment.

#### Acceptance Criteria

1. WHEN a parcel is created, THE Worker SHALL generate a waybill PDF from an HTML template and upload it to S3-compatible object storage.
2. WHEN a waybill PDF has been generated and stored, THE API SHALL return the S3 object URL when `GET /api/parcels/{id}/waybill` is called.
3. WHEN a waybill PDF has already been generated for a parcel, THE API SHALL return the stored URL without re-generating the PDF.
4. IF waybill PDF generation fails, THEN THE Worker SHALL log the error, and THE API SHALL return `503` with retry guidance when the waybill endpoint is requested — without blocking parcel operations.

---

### Requirement 13: Proof of Delivery

**User Story:** As an operator, I want to record proof of delivery for parcels, so that there is an auditable record confirming the customer received their shipment.

#### Acceptance Criteria

1. WHEN a parcel is marked `DELIVERED`, THE API SHALL allow an operator to submit proof of delivery including an optional photo URL, signature URL, and notes.
2. WHEN proof of delivery is submitted, THE API SHALL create a Proof_Of_Delivery record linked to the parcel and record the operator who submitted it.
3. IF proof of delivery is submitted for a parcel not in `DELIVERED` status, THEN THE API SHALL return a `400` error.
4. THE API SHALL enforce one Proof_Of_Delivery record per parcel (unique constraint on `parcel_id`).

---

### Requirement 14: Security and Data Integrity

**User Story:** As a system administrator, I want the platform to enforce security best practices throughout, so that customer data and financial transactions are protected.

#### Acceptance Criteria

1. THE API SHALL verify the Chapa webhook HMAC-SHA256 signature before reading or acting on any webhook payload.
2. THE API SHALL perform a server-side Chapa transaction verification call as the authoritative source of truth before marking any payment as PAID.
3. WHEN all payment and parcel status changes related to a payment event are written, THE API SHALL execute them within a single atomic database transaction.
4. THE API SHALL serve all traffic exclusively over HTTPS via an Nginx reverse proxy with TLS termination.
5. THE API SHALL never store, log, or expose credentials, secrets, or payment tokens in application logs or API responses.
6. THE API SHALL apply rate limiting to the public tracking endpoint (10 requests per minute per IP) using Redis counters.
7. THE API SHALL generate Tracking_Codes with a random 6-digit suffix (not a sequential counter) to prevent enumeration of shipment volume.
8. WHERE the Chapa webhook endpoint has already processed a `tx_ref` successfully, THE API SHALL treat subsequent webhook calls for that `tx_ref` as no-ops and return `200` without writing to the database.

---

### Requirement 15: Background Task Reliability

**User Story:** As a system operator, I want background tasks to be reliable and retried on failure, so that notifications and payment verifications are eventually delivered even under transient failures.

#### Acceptance Criteria

1. WHEN a Telegram notification task fails, THE Worker SHALL retry it up to 3 times using exponential backoff before recording a final `failed` status in the Notification_Log.
2. WHEN a Chapa verify call fails during webhook processing, THE Worker SHALL enqueue a `retry_failed_webhook` task with a 10-minute delay and return a success response to Chapa immediately.
3. WHEN the `retry_failed_webhook` task runs (every 15 minutes via Celery beat), THE Worker SHALL re-verify all PENDING payments older than 10 minutes.
4. THE Worker SHALL process all notification dispatch asynchronously, never blocking the API request path.
5. WHEN a daily manager digest task fires at 07:00 EAT, THE Worker SHALL generate and deliver branch summaries before 07:30 EAT.
6. WHEN a transit delay check task fires (every hour), THE Worker SHALL complete the scan and alert dispatch within the same scheduled execution window.

---

### Requirement 16: Real-Time Dashboard Updates

**User Story:** As a branch operator, I want the dashboard to update in real time when parcel statuses change, so that I always see the current state without manually refreshing.

#### Acceptance Criteria

1. WHEN a parcel status transition is committed to the database, THE API SHALL emit a real-time update event to all connected dashboard clients for the affected branch.
2. THE Dashboard SHALL display status updates to connected staff without requiring a page refresh.
3. WHILE a staff member is connected to the Dashboard, THE API SHALL maintain an open WebSocket or Server-Sent Events connection to deliver updates.
4. IF the real-time connection is interrupted, THE Dashboard SHALL attempt to reconnect automatically.

---

### Requirement 17: Customer Phone Linking

**User Story:** As a customer, I want my Telegram account to be linked to my phone number, so that the platform can push parcel notifications directly to me.

#### Acceptance Criteria

1. WHEN a customer shares their phone number via Telegram, THE API SHALL upsert the Customer record: create it if it does not exist, or update `telegram_id` if the record already exists.
2. WHEN the link operation succeeds, THE API SHALL return `{ linked: true }` to the Bot.
3. IF the phone number is already linked to a different `telegram_id`, THEN THE API SHALL overwrite with the new `telegram_id` and return `{ linked: true }`.
4. WHEN a customer is linked, all future parcel status events for parcels associated with that phone number SHALL trigger Telegram notifications rather than SMS notifications.

---

### Requirement 18: Performance and Scalability

**User Story:** As a system architect, I want the platform to handle expected load efficiently, so that response times remain acceptable as parcel volume grows.

#### Acceptance Criteria

1. THE API SHALL use asynchronous SQLAlchemy with a connection pool (`pool_size=10`, `max_overflow=20`) for all database operations.
2. THE API SHALL look up parcels by `tracking_code` using a database UNIQUE index to achieve O(log n) query performance.
3. WHEN a waybill PDF is first generated, THE Worker SHALL upload it to object storage; subsequent requests for the same waybill SHALL return the stored URL without re-generating.
4. THE API SHALL cache JWT validation results and rate-limit counters in Redis to avoid redundant database lookups per request.
5. THE API SHALL append Parcel_Status_History rows without UPDATE operations to allow safe concurrent writes to the audit log.
