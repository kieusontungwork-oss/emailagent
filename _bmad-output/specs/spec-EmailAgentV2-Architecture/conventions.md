# Conventions & Stack

## Consistency Conventions

| Concern                          | Convention                                                                                                                                          |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Naming (workflows, nodes)        | Snake_case for workflow names (e.g.,`extract_pdf_data`). Title Case for nodes describing action (e.g., `Query Postgres`).                       |
| Data & formats (error envelopes) | Errors passed to Mailroom must include`{ "error_type": "string", "message": "string", "requires_user_reply": boolean, "original_email": object }` |
| State & cross-cutting            | Secrets must be injected at runtime via HashiCorp Vault. Hardcoding credentials in n8n nodes is banned.                                             |

## Stack

| Name                         | Version          |
| ---------------------------- | ---------------- |
| n8n                          | 1.x (Queue Mode) |
| PostgreSQL                   | 16.x             |
| Redis                        | 7.x              |
| Python (openpyxl)            | 3.12+            |
| LM Studio / Llama-3.2-Vision | Latest           |
| HashiCorp Vault              | Latest           |

## Deferred Decisions

| Decision                                           | Reason                                                                                                                                   |
| -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| CI/CD Tooling Choice (GitHub Actions vs GitLab CI) | Deferred until infra team establishes the repository location. The invariant is the*pattern* (Git-backed), not the specific CI runner. |
