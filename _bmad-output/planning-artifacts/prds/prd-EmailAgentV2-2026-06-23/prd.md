---
title: EmailAgentV2
status: final
created: 2026-06-23
updated: 2026-06-25
---
# Product Requirements Document: EmailAgentV2

## 1. Product Vision & Scope

EmailAgentV2 is an automated workflow agent designed to process incoming data request emails from internal teams. It reads requested search criteria (such as Customer CIF, Phone number, or Account IDs) from emails and attached PDF documents, queries the relevant customer and transaction data from a structured database, and securely returns a formatted Excel report to the requester.

The goal is to eliminate manual data retrieval tasks for the data team while providing fast, reliable, and secure responses to business units.

## 2. Actors & Personas

- Requester (Internal User): An employee (e.g., Sales or Business Operations) who emails a request for customer/transaction data.
- Internal Admin (Data/IT Ops): The supervisor who receives email alerts when a request fails or contains invalid/missing information.
- EmailAgentV2 (The System): The automated agent orchestrating the extraction, querying, and delivery.

## 3. User Journeys

### 3.1 The Happy Path (Successful Query)

1. The Requester sends an email with one or more attached PDFs containing a list of Customer IDs and requested fields (e.g., DoB, CCCD, Address, 30-day transactions).
2. The System receives the email, verifies the presence of PDF attachments, and parses the PDFs sequentially one by one.
3. The System extracts the identifiers and the intent from the PDFs (ignoring email body text).
4. The System verifies the Requester's email address against an internal authorization mapping table for the requested customer IDs.
5. The System queries the Customer and Transaction tables.
6. The System generates an Excel file with two sheets: `Customer Info` and `Transactions`.
7. The System replies to the Requester's email with the Excel file attached. (If the requester replies again in the same thread with more IDs, the System repeats this process as a new run and replies within the same thread.)

### 3.2 The Exception Path (Missing Attachments, File Too Large, Missing Data, Invalid Data, Verification Mismatch, or Unauthorized Request)

1. The Requester sends an email without any PDF attachments, includes a PDF exceeding the 1MB file size limit, forgets to include the actual Account IDs in the PDF, provides IDs that do not exist in the database, provides IDs that fail the Name+ID verification check, or requests IDs they are not authorized to view.
2. The System parses the request and detects the missing/oversized PDFs or missing parameters, receives an empty result set from the database, detects a Name+ID verification mismatch, or rejects the request based on the authorization mapping table.
3. For validation errors (e.g., missing/oversized PDFs, no identifiers found), the system replies to the requester with a descriptive message. For data/authorization failures (e.g., IDs not found, name mismatch, unauthorized), it remains silent to the requester.
4. All cases generate an email alert notification with the error log to the Internal Admin email address detailing the failure reason and the original requester's details.

### 3.3 The Partial Match Path

1. The Requester sends an email with valid PDFs containing 5 Customer IDs.
2. The System successfully extracts and verifies 3 of the IDs, but 2 IDs are missing from the database or fail the Name+ID verification check.
3. The System generates the Excel file containing the data for the 3 successful IDs and replies to the Requester's email.
4. The System simultaneously sends an email alert to the Internal Admin detailing the 2 missing/failed IDs for further investigation.

## 4. Functional Requirements (FRs)

### FR-1: Email Ingestion (Updated)

- FR-1.1: The system MUST monitor a designated inbox for incoming data
  request emails. The workflow MUST trigger on all incoming emails to allow
  the system to send user-facing error replies if valid PDF attachments are missing.
- FR-1.2: The system MUST extract and download all attached PDF files.
- FR-1.3: The system MUST ignore non-PDF attachments (e.g., `.xlsx`, `.docx`, images) if valid PDF attachments are also present. If an email contains ONLY non-PDF attachments, or no attachments at all, the system MUST trigger the Exception Path and reply to the user.
- FR-1.4: The system MUST enforce a file size limit of 1MB per PDF, a
  maximum of 50 pages per PDF, a maximum of 10 PDFs per email, and a maximum
  of 100 total pages per email. Any limit exceeded MUST trigger the Exception
  Path with a user-facing reply explaining the limit.
- FR-1.5 (NEW): The system MUST verify email authentication (SPF + DMARC
  PASS). Unauthenticated emails MUST be silently dropped and logged as
  `AUTH_FAILED`.
- FR-1.6 (NEW): The system MUST filter out auto-responders by checking
  the `Auto-Submitted: auto-replied` header.
- FR-1.7 (NEW): The system MUST filter out its own sent emails by checking
  the custom header `X-EmailAgentV2-Sent: true`.
- FR-1.8 (NEW): The system MUST enforce a maximum of 10 replies per email
  thread. The 11th request in a thread MUST be rejected with admin alert
  `THREAD_LIMIT_EXCEEDED`.
- FR-1.9 (NEW): The system MUST use the Gmail `Message-ID` header for
  idempotency. If a message has already been processed (exists in
  `request_logs`), it MUST be skipped.

### FR-2: Document Parsing

- FR-2.1: The system MUST convert text-based PDF attachments into machine-readable markdown/text. If multiple PDFs are attached, the system MUST process them sequentially one by one.
- FR-2.2: The system MUST detect if a PDF is a scanned (image-only) document. If it is scanned, the system MUST use a local OCR module to convert the document into readable text format (preferably Markdown) prior to extraction. *(Future Consideration: For Vietnamese text OCR, PaddleOCR or VietOCR should be prioritized as they significantly outperform Tesseract).*

### FR-3: AI-Powered Data Extraction

- FR-3.1: The system MUST extract unique identifiers (e.g., CIF, Phone, CCCD, Account ID) from the parsed PDF text ONLY (the email body MUST NOT be used for extraction).
- FR-3.2: The system MUST identify the scope of the requested data (e.g., 30-day transaction history, Customer Address) from the PDF text ONLY.
- FR-3.3: The system MUST extract a secondary validation factor (e.g., Customer Name) associated with each identifier from the PDF to prevent silent typo/hallucination leaks.

### FR-4: Secure Database Querying & Authorization

- FR-4.1: The system MUST verify the requester's email address against an internal authorization mapping table (Row-Level Security approach) to ensure they are permitted to view data for the requested customer IDs.
- FR-4.2: If the requester is not authorized for one or more requested IDs, the system MUST halt processing and alert the Internal Admin (as per FR-7).
- FR-4.3: The system MUST execute database lookups against the `Customer` and `Transaction` tables using the extracted identifiers only after authorization is confirmed.
- FR-4.4: Multi-Factor Data Matching: The system MUST compare the database record's Customer Name against the LLM-extracted Customer Name. If there is a mismatch for a specific identifier, the system MUST exclude that identifier from the final report to prevent a wrong-customer data leak, but MUST continue processing any remaining valid identifiers as described in the Partial Match Path (Section 3.3).
- FR-4.5: The system MUST enforce strict parameterized queries; it MUST NOT execute raw SQL generated by an AI. This prevents SQL injection and hallucination risks.

### FR-5: Report Generation

- FR-5.1: The system MUST format the retrieved data into an Excel (`.xlsx`) file.
- FR-5.2: The output MUST contain at least two separate sheets: one for Customer Information and one for Transaction History.

### FR-6: Automated Delivery

- FR-6.1: The system MUST reply directly to the original email thread. If the requester replies again in the same thread with additional PDFs or IDs, the system MUST treat it as a new run and reply within that same thread.
- FR-6.2: The reply MUST include a professional message and the generated Excel file as an attachment.

### FR-7: Exception Handling & Admin Alerts (Updated)

#### User-Facing Error Replies

| Scenario                  | Reply to User? | Message                                                                                                      |
| ------------------------- | -------------- | ------------------------------------------------------------------------------------------------------------ |
| No PDF attachment         | ✅             | "Please attach PDF documents containing the requested IDs."                                                  |
| Non-PDF attachment only   | ✅             | "Only PDF attachments are supported. Please resend as PDF."                                                  |
| PDF > 1MB                 | ✅             | "PDF exceeds 1MB limit. Please compress or split and resend."                                                |
| > 10 PDFs or > 100 pages  | ✅             | "Maximum 10 PDFs / 100 pages per email. Please split your request."                                          |
| No identifiers extracted  | ✅             | "No identifiers found in the attached PDF(s). Ensure the document contains CIF, Account ID, Phone, or CCCD." |
| IDs not found in DB       | ❌ (Silent)    | —                                                                                                           |
| Name mismatch             | ❌ (Silent)    | —                                                                                                           |
| Unauthorized              | ❌ (Silent)    | —                                                                                                           |
| System error (LLM/OCR/DB) | ❌ (Silent)    | —                                                                                                           |

#### Admin Alert Rules

- One alert per email (not per ID). All failed IDs in a single email are
  listed in one alert.
- Throttle: Max 1 alert per requester per 15 minutes.
- Daily Digest: At 8:00 AM local time, a summary email is sent with total
  requests, success/failure counts, and error breakdown.

#### Admin Alert Content

Each admin alert MUST include:

- Error code (e.g., `NAME_MISMATCH`, `UNAUTHORIZED`, `LLM_TIMEOUT`)
- Requester email
- Original Gmail Message-ID
- Timestamp (UTC)
- n8n Execution ID + URL
- Failed identifiers table (ID type, ID value, extracted name, DB name, failure reason)
- Count of successful identifiers (if partial match)

#### Dead Letter Queue (DLQ)

- Requests that fail after 3 retries are moved to a `dlq_requests` table.
- Admin dashboard shows all DLQ items with actions: retry, resolve, delete.
- DLQ items are retained for 30 days, then auto-purged.

#### Escalation

- Admin alert → 4 hours (no ack) → Manager email.
- Manager alert → 2 hours (no ack) → IT Ops PagerDuty.
- Critical system errors (LLM/DB/n8n down) → Immediate PagerDuty.

### FR-8: Audit Logging

- FR-8.1: The system MUST log every incoming request into a central database.
- FR-8.2: The log MUST include the original email content, requester email, timestamp, requested identifiers, execution status (success/fail/unauthorized), and references to the attachments.

### FR-9: Report Security & Delivery (NEW)

- FR-9.1: The Excel file MUST be password-protected using AES-256 encryption.
- FR-9.2: The password MUST be a randomly generated 12-character alphanumeric
  string, unique per report.
- FR-9.3: The password MUST be delivered via a separate channel
  (Microsoft Teams DM or SMS) — NEVER in the same email as the attachment.
- FR-9.4: If the Excel file exceeds 5MB, it MUST be uploaded to an internal
  Nextcloud/SharePoint folder with a 7-day expiry link requiring SSO. The reply
  email contains the download link instead of the attachment.
- FR-9.5: The Excel file MUST be generated using `openpyxl` (Python) to
  ensure reliable multi-sheet generation (`Customer Info` and `Transactions`).
- FR-9.6: If the Transactions sheet exceeds 10,000 rows, it MUST be
  truncated with a note row: "⚠️ Results truncated. Showing 10,000 of {count}
  rows. Contact data@company.com for full export."
- FR-9.7: The reply email MUST include a "Data as of" timestamp showing
  the email received time in `Asia/Ho_Chi_Minh` timezone.

### FR-10: Observability & Health Monitoring (NEW)

- FR-10.1: The system MUST run health checks on all dependencies:
  | Component          | Check                                 | Interval |
  | ------------------ | ------------------------------------- | -------- |
  | LM Studio (text)   | `GET /v1/models`                    | 60s      |
  | LM Studio (vision) | `GET /v1/models` + model name check | 60s      |
  | Database           | `SELECT 1`                          | 30s      |
  | Gmail API          | Token validity                        | 5 min    |
  | n8n                | `GET /healthz`                      | 30s      |
  | Disk space (/tmp)  | `df -h`                             | 5 min    |
- FR-10.2: 3 consecutive health check failures for LLM/DB/n8n MUST trigger
  an immediate PagerDuty alert.
- FR-10.3: The system MUST expose Prometheus metrics including:
  `emails_received_total`, `processing_duration_seconds` (by stage),
  `llm_inference_seconds` (by model, pdf_type), `errors_total` (by error_code),
  `queue_depth`.
- FR-10.4: A Grafana dashboard MUST display: email volume (24h/7d/30d),
  P50/P95/P99 latency, error rate by category, LLM/OCR inference percentiles,
  queue depth over time.
- FR-10.5: A synthetic test email MUST be sent every hour in production.
  The expected response is validated automatically. On validation failure,
  admin alert `SELF_TEST_FAILED` is triggered.

### FR-11: Data Retention & PII Handling (NEW)

- FR-11.1: n8n MUST be configured to NOT save successful execution payloads
  (`EXECUTIONS_DATA_SAVE_ON_SUCCESS=none`). Error executions are saved for 30
  days (hot) / 90 days (archived).
- FR-11.2: PII fields (CCCD, phone) in n8n node outputs MUST be masked
  using regex data masking.
- FR-11.3: Temporary files (PDFs, Excel) MUST be stored in
  `/tmp/emailagentv2/{execution_id}/` and securely deleted (`shred -u`) after
  workflow completion.
- FR-11.4: A cron job MUST `shred` and remove any orphaned files older
  than 1 hour in `/tmp/emailagentv2/` every 15 minutes.
- FR-11.5: `request_logs` table: retained 90 days hot, 1 year anonymized
  (CCCD masked to last 4 digits).
- FR-11.6: `llm_audit_logs` table: retained 90 days, then purged. Stores
  prompt hash (not full prompt) and response JSON.
- FR-11.7: `dlq_requests` table: retained 30 days, then purged.
- FR-11.8: All secrets (DB credentials, Gmail OAuth, encryption keys) MUST
  be stored in HashiCorp Vault and injected at startup. No secrets in
  environment files or workflow code.

### FR-12: Testing & Acceptance Criteria (NEW)

- FR-12.1: Before go-live, the system MUST be tested against a corpus of
  100 real-world Vietnamese PDFs (50 text-based, 30 scanned, 20 hybrid).
- FR-12.2: Accuracy thresholds:
| Metric                             | Threshold |
| ---------------------------------- | --------- |
| ID extraction precision            | ≥ 95%    |
| ID extraction recall               | ≥ 90%    |
| Name matching precision            | ≥ 99.5%  |
| Name matching recall               | ≥ 95%    |
| End-to-end happy path success rate | ≥ 85%    |
- FR-12.3: An adversarial prompt injection test suite of 20 PDFs MUST be
  run before go-live and after any prompt change. Pass criteria: 0 injection
  successes.
- FR-12.4: The system MUST support three operating modes via
  `EMAILAGENT_MODE`:
  - `production`: Full pipeline, replies to requester.
  - `staging`: Full pipeline, replies redirected to `staging-test@company.com`,
    DB queries hit staging database.
  - `dry-run`: Full pipeline up to Excel generation, no email sent. Output
    saved to disk for manual review.

## 5. Non-Functional Requirements (NFRs)

- NFR-1 Privacy & Security: The system handles PII (Personally Identifiable Information). All data processing MUST occur within the secure local network.
- NFR-1.1 Prompt Injection Resilience: The LLM prompt MUST rigidly delimit untrusted document content (e.g., using `<document>` XML tags) and explicitly instruct the model to ignore embedded directives. Furthermore, the system's architectural reliance on strict parameterized SQL (FR-4.5) and the internal RLS map (FR-4.1) serve as the ultimate defense-in-depth against malicious extraction attempts.
- NFR-2 Reliability: The system MUST predictably fail-safe (routing to an admin) rather than returning incorrect data or hallucinated SQL results.
- NFR-3 Rate Limiting / Usage: There are no hard rate limits required for the MVP; the system assumes internal users will be reasonable in their request volume.
