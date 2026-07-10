---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics"]
inputDocuments: [
  "_bmad-output/planning-artifacts/prds/prd-EmailAgentV2-2026-06-23/prd.md",
  "_bmad-output/planning-artifacts/prds/prd-EmailAgentV2-2026-06-23/addendum.md",
  "_bmad-output/planning-artifacts/architecture/architecture-EmailAgentV2-2026-07-02/ARCHITECTURE-SPINE.md",
  "_bmad-output/specs/spec-EmailAgentV2-Architecture/SPEC.md"
]
---
# EmailAgentV2 - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for EmailAgentV2, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR-1: Email Ingestion (Monitor inbox, extract PDFs, ignore non-PDFs, enforce file limits, verify SPF/DMARC, filter auto-responders and self-sent emails, enforce thread limits, use Message-ID for idempotency).
FR-2: Document Parsing (Convert text PDFs to markdown, use local Vision LLM for scanned PDFs).
FR-3: AI-Powered Data Extraction (Extract identifiers and scope from PDF text only, extract secondary validation factor).
FR-4: Secure Database Querying & Authorization (Verify requester email via RLS table, execute DB lookups only if authorized, perform multi-factor data matching on customer name, use parameterized queries).
FR-5: Report Generation (Format retrieved data into Excel with Customer Info and Transactions sheets).
FR-6: Automated Delivery (Reply to original thread with generated Excel).
FR-7: Exception Handling & Admin Alerts (Send user-facing replies for validation errors, silently drop auth/system errors, send admin alerts for all failures with specific error codes, use DLQ, escalate).
FR-8: Audit Logging (Log every incoming request into a central database).
FR-9: Report Security & Delivery (AES-256 password protection for Excel, separate channel delivery for password, Nextcloud link for files >5MB, handle truncation gracefully).
FR-10: Observability & Health Monitoring (Health checks for LLM/DB/n8n/Gmail, Prometheus metrics, Grafana dashboard, synthetic tests).
FR-11: Data Retention & PII Handling (n8n saves on error only, regex mask PII, shred tmp files, retain request_logs/llm_audit_logs/dlq as specified, use Vault for secrets).
FR-12: Testing & Acceptance Criteria (Support production, staging, dry-run modes, pass accuracy thresholds and prompt injection tests).

### NonFunctional Requirements

NFR-1: Privacy & Security (All processing within secure local network).
NFR-1.1: Prompt Injection Resilience (Rigidly delimit untrusted document content, explicit system prompt instructions, defense-in-depth via parameterized SQL and RLS).
NFR-2: Reliability (Predictably fail-safe routing to admin rather than hallucinations).
NFR-3: Rate Limiting / Usage (Assume reasonable internal usage, no hard limits for MVP).

### Additional Requirements

- Architecture relies on n8n as a stateless orchestrator and PostgreSQL for all state.
- Modular workflow design (Controller + Sub-workflows like Mailroom).
- Workflow must be managed via Git-backed CI/CD pipeline.
- Must use Local Vision LLM (e.g., Llama-3.2-Vision) hosted via LM Studio in an air-gapped subnet.
- Strictly read-only parameterized queries; no AI-generated raw SQL.
- Hard cap: 50 identifiers per email.
- Name Matching Algorithm with specific Levenshtein distance constraints.

### UX Design Requirements

N/A - Backend orchestration system.

### FR Coverage Map

FR-1: Epic 1 - Email Ingestion
FR-2: Epic 1 - Document Parsing
FR-3: Epic 1 - AI-Powered Data Extraction
FR-4: Epic 1 - Secure Database Querying & Authorization
FR-5: Epic 1 - Report Generation
FR-6: Epic 1 - Automated Delivery
FR-7: Epic 2 - Exception Handling & Admin Alerts
FR-8: Epic 1 - Audit Logging
FR-9: Epic 3 - Report Security & Delivery
FR-10: Epic 4 - Observability & Health Monitoring
FR-11: Epic 3 - Data Retention & PII Handling
FR-12: Epic 4 - Testing & Acceptance Criteria

## Epic List

### Epic 1: Core Automated Data Retrieval (The Happy Path)

Internal users can email valid PDFs containing identifiers, and the system securely extracts them, queries the database, generates a basic Excel report, and replies to the user.
**FRs covered:** FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-8

### Epic 2: Exception Handling & Admin Alerting (The Edge Cases)

The system gracefully handles all error states, sending helpful replies to users for invalid requests and routing authorization/system failures silently to the admin.
**FRs covered:** FR-7

### Epic 3: Secure Delivery & PII Compliance

Ensure reports are securely delivered (password-protected Excel, passwords via secondary channels, Nextcloud links) and PII is properly masked/shredded.
**FRs covered:** FR-9, FR-11

### Epic 4: Enterprise Observability & Quality Assurance

The engineering and operations teams can proactively monitor, test, and maintain the system's health, extraction accuracy, and performance.
**FRs covered:** FR-10, FR-12

---

## Epic 1: Core Automated Data Retrieval (The Happy Path)

Internal users can email valid PDFs containing identifiers, and the system securely extracts them, queries the database, generates a basic Excel report, and replies to the user.

### Story 1.1: Email Ingestion & Attachment Validation

As an internal user,
I want the system to receive my email requests and validate my PDF attachments,
So that only valid requests proceed and I am notified immediately if my request is malformed.

**Acceptance Criteria:**

**Given** an incoming email
**When** it fails SPF/DMARC or is an auto-responder
**Then** it is silently dropped
**And** it is logged as AUTH_FAILED.

**Given** a valid incoming email
**When** there are no PDF attachments or the PDF exceeds limits (1MB/50 pages)
**Then** the system replies to the user with the appropriate error message
**And** execution halts.

**Given** a valid email with valid PDFs
**When** received
**Then** the attachments are downloaded, the Message-ID is logged for idempotency, and the files are passed to the next stage.

### Story 1.2: Hybrid PDF Parsing (Text & Scanned)

As the data extraction system,
I want to convert PDF attachments into Markdown, using a local Vision LLM for scanned pages,
So that the text is machine-readable for identifier extraction.

**Acceptance Criteria:**

**Given** a text-based PDF page
**When** processed
**Then** it is converted to Markdown using markitdown.

**Given** a scanned (image) PDF page
**When** detected based on text density
**Then** it is sent to the local Vision LLM via LM Studio for OCR conversion.

**Given** a multi-page or multi-PDF request
**When** processed
**Then** all results are merged into a single Markdown string for the LLM.

### Story 1.3: AI-Powered Identifier Extraction

As the data extraction system,
I want to extract a structured list of identifiers from the parsed text using a local LLM in JSON mode,
So that I have exactly what I need to query the database.

**Acceptance Criteria:**

**Given** the Markdown text
**When** sent to the local Text LLM
**Then** it returns a strict JSON array of identifiers and requested scopes.

**Given** the LLM JSON output
**When** validated using Pydantic
**Then** the identifiers are checked against Regex rules and invalid ones are discarded.

**Given** a request with >50 identifiers
**When** extracted
**Then** it is hard-capped at 50 identifiers.

### Story 1.4: Secure Database Query & Verification

As the reporting system,
I want to verify the requester's authorization and execute parameterized queries for the extracted IDs,
So that no unauthorized data or mismatched customer names are leaked.

**Acceptance Criteria:**

**Given** the requester's email
**When** checked against authorized_requesters
**Then** the system retrieves their allowed scopes.

**Given** the authorized scopes and extracted IDs
**When** querying PostgreSQL
**Then** strict parameterized queries are used.

**Given** the DB results
**When** the DB Customer Name is compared to the LLM-extracted Customer Name
**Then** any mismatch beyond the allowed Levenshtein distance is dropped from the final dataset.

### Story 1.5: Excel Generation & Email Delivery

As an internal user,
I want to receive an automated email reply containing a formatted Excel report with my requested data,
So that I don't have to wait for manual data retrieval.

**Acceptance Criteria:**

**Given** the validated dataset
**When** formatting
**Then** an .xlsx file is generated with Customer Info and Transactions sheets.

**Given** the Excel file
**When** ready
**Then** the system replies to the original email thread with the file attached.

**Given** a successful run
**When** complete
**Then** the status is updated in the request_logs table.

## Epic 2: Exception Handling & Admin Alerting (The Edge Cases)

The system gracefully handles all error states, routing authorization or system failures silently to the admin with detailed alerts, while tracking unresolvable errors in a queue.

### Story 2.1: The Mailroom Error Handler

As the system orchestrator,
I want a centralized "Mailroom" sub-workflow to process all execution errors from other workflows,
So that I can standardize error handling without repeating logic in every sub-workflow.

**Acceptance Criteria:**

**Given** any sub-workflow failure
**When** it throws an error
**Then** the structured error envelope is passed to the Mailroom.

**Given** an error envelope
**When** processed
**Then** the Mailroom determines if it requires a user reply or just an admin alert.

### Story 2.2: Admin Alert Notifications

As an internal admin,
I want to receive an email alert with detailed execution metadata when a system or authorization failure occurs,
So that I can investigate the failure without leaking sensitive information to the requester.

**Acceptance Criteria:**

**Given** an unauthorized or system error (e.g., NAME_MISMATCH, DB_TIMEOUT)
**When** processed by the Mailroom
**Then** an email is sent to the admin with the Error code, original Message-ID, n8n execution URL, and a table of failed identifiers.

**Given** multiple failed IDs in a single email
**When** processing
**Then** all failed IDs are grouped into one single alert.

**Given** a high volume of failures
**When** alerting
**Then** the system throttles alerts to max 1 per requester per 15 minutes.

### Story 2.3: Dead Letter Queue (DLQ)

As an internal admin,
I want requests that fail after 3 retries to be saved into a DLQ database table,
So that I can manually review, retry, or delete them via an admin dashboard later.

**Acceptance Criteria:**

**Given** a request that fails completely
**When** retries are exhausted
**Then** it is inserted into the dlq_requests table.

**Given** DLQ items
**When** 30 days pass
**Then** they are automatically purged via a scheduled job.

### Story 2.4: Admin Daily Digest & Escalation

As a data manager,
I want a daily digest of all system activity and automatic escalation for critical failures,
So that I can ensure operational health and SLA compliance.

**Acceptance Criteria:**

**Given** a daily schedule at 8:00 AM
**When** triggered
**Then** a summary email is sent with total requests, success/failure counts, and error breakdown.

**Given** an unacknowledged admin alert for 4 hours
**When** checking status
**Then** it escalates to the Manager email.

**Given** an unacknowledged manager alert for 2 hours
**When** checking status
**Then** it triggers IT Ops PagerDuty.

## Epic 3: Secure Delivery & PII Compliance

Ensure reports are securely delivered (password-protected Excel, passwords via secondary channels, Nextcloud links) and PII is properly masked/shredded.

### Story 3.1: Password-Protected Excel Generation

As an internal user,
I want the generated Excel reports to be encrypted,
So that sensitive customer data is protected in transit and at rest.

**Acceptance Criteria:**

**Given** an Excel report
**When** generated
**Then** it is password-protected using AES-256 encryption.

**Given** the encryption process
**When** triggered
**Then** a random 12-character alphanumeric password is generated uniquely for that specific report.

### Story 3.2: Out-of-Band Password Delivery

As an internal user,
I want to receive the report password via a separate channel (Teams or SMS),
So that the password is not compromised if my email inbox is intercepted.

**Acceptance Criteria:**

**Given** the generated password
**When** the reply email is drafted
**Then** the password is strictly excluded from the email body.

**Given** the generated password
**When** the email is sent
**Then** an automated message containing the password is sent via Microsoft Teams DM (or SMS) to the requester.

### Story 3.3: Large File Handling (Nextcloud)

As an internal user,
I want to receive large reports via a secure download link instead of an attachment,
So that I do not hit corporate email attachment limits.

**Acceptance Criteria:**

**Given** the generated Excel file
**When** it exceeds 5MB
**Then** it is uploaded to an internal Nextcloud/SharePoint folder rather than attached to the email.

**Given** a Nextcloud upload
**When** complete
**Then** a 7-day expiry link requiring SSO is generated.

**Given** the generated link
**When** replying
**Then** the email contains the secure download link and instructions.

### Story 3.4: PII Masking and Data Shredding

As a security officer,
I want PII to be masked in logs and temporary files to be securely destroyed,
So that the system complies with data retention and privacy policies.

**Acceptance Criteria:**

**Given** n8n node outputs
**When** executed
**Then** PII fields (e.g., CCCD, phone numbers) are masked using regex before being saved to any execution logs.

**Given** a completed workflow (success or failure)
**When** finishing
**Then** all temporary files in /tmp/emailagentv2/{execution_id}/ are securely deleted using shred -u.

**Given** orphaned files older than 1 hour in /tmp/emailagentv2/
**When** the cleanup cron job runs every 15 minutes
**Then** they are securely shredded.

**Given** the request_logs table
**When** 90 days pass
**Then** an automated job anonymizes the CCCD down to the last 4 digits.
