---
id: SPEC-EmailAgentV2-Architecture
companions:
  - architecture-diagrams.md
  - conventions.md
sources:
  - ../../planning-artifacts/architecture/architecture-EmailAgentV2-2026-07-02/ARCHITECTURE-SPINE.md
---
> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability only — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# EmailAgentV2 Architecture Spec

## Why

The system needs an Event-Driven, Modular Orchestration Pipeline centered around n8n acting as a stateless traffic controller, to react to incoming email events, delegate distinct units of work (extraction, data querying, formatting, alerting), and rely on PostgreSQL for all domain and operational state. This prevents monolithic workflow spaghetti and state fragmentation.

## Capabilities

- **CAP-1**
  - **intent:** System ingests incoming email events via Gmail trigger and acts as a stateless traffic controller.
  - **success:** Controller workflow receives email payload and attachments and passes them to downstream sub-workflows.
- **CAP-2**
  - **intent:** System extracts text and scanned PDF data using a local Vision LLM (Llama-3.2-Vision) in an air-gapped subnet.
  - **success:** Extracted structured data is reliably returned without sending data to external cloud LLM providers.
- **CAP-3**
  - **intent:** System executes read-only queries against Customer and Transaction tables in PostgreSQL to validate and retrieve domain data based on extracted IDs.
  - **success:** Data is queried using parameterized SELECT queries without generating raw SQL, ensuring zero unauthorized data modification.
- **CAP-4**
  - **intent:** System routes all errors from sub-workflows to a universal Mailroom Error-Handler sub-workflow.
  - **success:** Errors generate structured error envelopes and send appropriate admin alerts or user error replies.
- **CAP-5**
  - **intent:** System tracks all workflow state and idempotency checks in PostgreSQL.
  - **success:** Duplicate email processing is prevented and state is maintained even if Redis is flushed.

## Constraints

- n8n must operate as a stateless orchestrator.
- Pipeline must be split into a main Controller workflow and independent Sub-workflows (Data Prep, LLM Extraction, DB/Report).
- All LLM inference must occur on a local Vision LLM (e.g., Llama-3.2-Vision) hosted via LM Studio within the private air-gapped subnet.
- DB user must have strictly read-only permissions on domain tables.
- n8n workflow JSON definitions must be managed as Infrastructure as Code via a Git-backed CI/CD pipeline.
- Secrets must be injected at runtime via HashiCorp Vault; hardcoding credentials in n8n nodes is banned.

## Non-goals

- Manual UI-driven edits to workflows in the production environment.
- Using cloud-based LLM providers for data extraction.
- Using Redis for long-term state or idempotency tracking.

## Success signal

- The system successfully ingests incoming emails, delegates extraction and data querying to isolated sub-workflows, manages all state in PostgreSQL, and handles errors via a centralized Mailroom, running autonomously without manual intervention.

## Assumptions

- Assumed Redis is strictly limited to n8n's internal queue mode queuing.
- Assumed Git-backed CI/CD pipeline is available or will be provisioned.

## Open Questions

- CI/CD Tooling Choice (GitHub Actions vs GitLab CI) is deferred, needs resolution.
