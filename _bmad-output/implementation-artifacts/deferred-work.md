## Deferred from: code review of 1-1-email-ingestion-attachment-validation.md (2026-07-10)

- Incomplete Database State Transitions: Stays `RECEIVED` on success; can update in later epics.
- No DB Trigger for `updated_at` / Weak Schema Constraints: `VARCHAR(50)` without ENUM/trigger, can be hardened later.
