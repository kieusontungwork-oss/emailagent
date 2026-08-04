## Deferred from: code review of 1-1-email-ingestion-attachment-validation.md (2026-07-10)

- Incomplete Database State Transitions: Stays `RECEIVED` on success; can update in later epics.
- No DB Trigger for `updated_at` / Weak Schema Constraints: `VARCHAR(50)` without ENUM/trigger, can be hardened later.

## Deferred from: code review of 1-2-hybrid-pdf-parsing-text-scanned.md (2026-07-28)

- Base64 Image Payload RAM Usage for Large Scanned PDFs: Storing multiple high-res base64 images in Node.js heap memory for LM Studio API calls; acceptable design constraint for current air-gapped setup.

