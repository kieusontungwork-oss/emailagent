# Story 1.1: Email Ingestion & Attachment Validation

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an internal user,
I want the system to receive my email requests and validate my PDF attachments,
so that only valid requests proceed and I am notified immediately if my request is malformed.

## Acceptance Criteria

1. **Given** an incoming email, **When** it fails SPF/DMARC or is an auto-responder, **Then** it is silently dropped **And** it is logged as AUTH_FAILED.
2. **Given** a valid incoming email, **When** there are no PDF attachments or the PDF exceeds limits (1MB/50 pages) per email total, **Then** the system replies to the user with the appropriate error message **And** execution halts. (Note: non-PDF files are silently ignored/dropped while valid PDFs are processed).
3. **Given** a valid email with valid PDFs, **When** received, **Then** the attachments are downloaded, the Message-ID is logged for idempotency, and the files are passed to the next stage.

## Tasks / Subtasks

- [ ] Task 1: Setup n8n Email Trigger (AC: 1, 3)
  - [ ] Configure IMAP or Gmail Trigger node to watch the designated inbox.
  - [ ] Implement filter logic to discard auto-responders and SPF/DMARC failures.
- [ ] Task 2: Implement Idempotency Check (AC: 3)
  - [ ] Extract `Message-ID`.
  - [ ] Create `request_logs` table (if not exists) in PostgreSQL.
  - [ ] Insert `Message-ID` into `request_logs`. If duplicate, halt workflow.
- [ ] Task 3: Attachment Filtering & Validation (AC: 2, 3)
  - [ ] Filter out any non-PDF attachments.
  - [ ] Calculate total file size and total page count for all PDF attachments.
- [ ] Task 4: Error Handling & Routing (AC: 2)
  - [ ] Implement conditional branch: if total size > 1MB OR pages > 50 OR count == 0.
  - [ ] If invalid, send a user-friendly error reply via Gmail node and update DB status to `REJECTED`.
  - [ ] If valid, pass the binary data to the output of this sub-workflow.

## Dev Notes

- **Architecture constraints:** Rely entirely on n8n for orchestration. Do not write a custom Python microservice for email fetching.
- **Database Idempotency:** To avoid race conditions, rely on the PostgreSQL database constraint (UNIQUE index on `message_id`). Attempt the insert; if it violates the unique constraint, catch the error and halt the branch.
- **Attachment Size:** The 1MB and 50-page limits apply to the *entire payload* (all PDFs combined), not individual PDFs.
- **Error Routing:** In this story, the error reply is sent directly to the user. (A centralized "Mailroom" for system errors will be built in Epic 2, but user-facing validation errors can be handled here or passed to a generic error node).

### Project Structure Notes

- n8n workflows should be saved as JSON files in a version-controlled directory, e.g., `n8n-workflows/epic-1/1-1-email-ingestion.json`.
- DB migration scripts (e.g., `001_create_request_logs.sql`) should be stored in a `db/migrations/` folder.

### References

- [Epics Document](file:///Users/kieusontung/Work/Project/EmailAgentV2/_bmad-output/planning-artifacts/epics.md)
- [Architecture Spine](file:///Users/kieusontung/Work/Project/EmailAgentV2/_bmad-output/planning-artifacts/architecture/architecture-EmailAgentV2-2026-07-02/ARCHITECTURE-SPINE.md)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
