# EmailAgentV2 Addendum: Technical Implementation Constraints

This addendum captures the specific technical decisions, mechanisms, and architectural constraints agreed upon during the brainstorming and discovery phase.

## Orchestration & Pipeline

- **Workflow Engine:** The entire pipeline will be orchestrated using **n8n**.
- **Email Integration:** We will use the **n8n Native Gmail Node** for both triggering the workflow (listening for incoming emails) and sending the final replies. This "Pipeline" approach was chosen over a Gmail MCP Agent to maximize reliability and simplicity.

## Data Parsing & Extraction

- **Data Source Authority:** Only PDF attachments are considered the source of truth for requested IDs, as they represent official documents from a competent authority. Email body text is discarded for extraction purposes.
- **Batch Processing:** If an email contains multiple PDFs, the workflow must loop through all PDF attachments sequentially one by one.
- **PDF Parsing:** We will use the `microsoft/markitdown` library to convert text-based PDFs into Markdown for the AI to read.
- **Scanned PDFs & OCR:** Scanned PDFs will be detected and processed using a Local Vision LLM (e.g., Llama-3.2-Vision or Qwen2-VL) hosted via LM Studio. This option was explicitly chosen over traditional OCR because Vision models offer significantly better layout and table format preservation when converting images directly into Markdown text. *(Future Consideration: If a fallback to traditional OCR is needed later, note that Tesseract is weak for Vietnamese text; PaddleOCR or VietOCR are significantly better alternatives and should be evaluated instead.)*
- **AI Provider:** The extraction step will utilize a local LLM hosted via **LM Studio**'s API. This ensures all PII (CCCD, addresses, transaction histories) remains entirely local and secure.

## Database, Authorization & Query Generation

- **Authorization Table:** We will implement an `authorized_requesters` mapping table (or similar Row-Level Security view) to map employee email addresses to the specific branch, department, or customer segments they are allowed to query. The n8n pipeline will validate the requester's email against this table before executing any data queries.
- **Methodology:** We will **NOT** use AI to dynamically generate raw SQL queries (Text2SQL). Instead, the AI will output a structured JSON object containing the extracted parameters (e.g., `{"account_ids": ["00001", "00002"], "days": 30}`).
- **Execution:** An n8n node or script will take that JSON and map it to **pre-defined, parameterized SQL scripts**. This eliminates the risk of AI hallucinating SQL syntax or executing dangerous queries.
- **Database Scope:** The demo will operate against a database containing four primary tables: `customers`, `transactions`, `authorized_requesters`, and `request_logs` (for audit purposes).

## Production Architecture & Operations

### Concurrency Model

- **n8n Queue Mode**: n8n runs in Queue Mode with Redis as the message broker.
  The email-processing workflow has a **max concurrency of 1** (sequential
  processing). The bottleneck is the local LLM, not n8n.
- **Queue Depth**: Maximum 20 emails in the queue. If exceeded, the Gmail
  trigger pauses polling and resumes when the queue drops below 15. No emails
  are dropped—they remain in Gmail.
- **Health Monitor Workflow**: A separate n8n workflow runs every 60 seconds,
  checking queue depth. Alerts admin at depth > 10 (warning) and > 20 (critical).

### LLM Inference Concurrency

- **Text LLM (extraction)**: LM Studio continuous batching enabled, max 2
  concurrent requests, 90s timeout. n8n retries 3x with 10s backoff on failure.
- **Vision LLM (OCR)**: Hard-limited to 1 concurrent request via a Redis
  distributed lock (`vision_ocr_lock`). 120s timeout per PDF.

### Idempotency

- The Gmail `Message-ID` header is the unique key. The `request_logs` table
  enforces a `UNIQUE CONSTRAINT` on `gmail_message_id`.
- Before processing, the workflow checks for an existing log row. If found,
  the email is skipped.
- Reply deduplication: The workflow checks the Gmail Sent folder for an existing
  reply with `In-Reply-To: <Message-ID>` before sending.

### Recovery Strategy

- n8n uses **Postgres-backed execution storage** (not SQLite). All execution
  state is persisted.
- `request_logs.status` tracks each stage: `RECEIVED → PARSING → EXTRACTING → AUTHORIZING → QUERYING → GENERATING → SENT` (or `FAILED`).
- On worker crash, the execution appears as "Errored" in n8n. An admin can
  retry from the n8n UI. The workflow re-runs from the beginning; the
  idempotency check is skipped for retries (existing log row is updated in place).

### Timeout Matrix

| Stage                            | Timeout      | On Timeout                                             |
| -------------------------------- | ------------ | ------------------------------------------------------ |
| PDF text extraction (markitdown) | 30s per PDF  | Exception → admin alert`PARSE_TIMEOUT`              |
| OCR (Vision LLM)                 | 120s per PDF | Exception → admin alert`OCR_TIMEOUT`                |
| LLM extraction (text)            | 90s per PDF  | Retry 2x, then exception → admin alert`LLM_TIMEOUT` |
| DB query                         | 30s          | Exception → admin alert`DB_TIMEOUT`                 |
| Excel generation                 | 60s          | Exception → admin alert`EXCEL_TIMEOUT`              |
| Overall workflow                 | 15 minutes   | Hard kill → admin alert`WORKFLOW_TIMEOUT`           |

## PDF Processing Bounds & OCR Strategy

### Attachment Limits

| Limit                     | Value | On Exceed                                             |
| ------------------------- | ----- | ----------------------------------------------------- |
| Max file size per PDF     | 1 MB  | Exception → user reply "PDF exceeds 1MB limit"       |
| Max pages per PDF         | 50    | Exception → admin alert`PDF_PAGE_LIMIT`            |
| Max PDFs per email        | 10    | Exception → user reply "Max 10 PDFs per email"       |
| Max total attachment size | 10 MB | Exception → admin alert`ATTACHMENT_LIMIT_EXCEEDED` |
| Max total pages per email | 100   | Exception → admin alert`ATTACHMENT_LIMIT_EXCEEDED` |

### Hybrid PDF Detection (Per-Page)

- Text extraction is performed per-page using `pdfplumber`.
- A page is classified as **scanned** if:
  `len(extracted_text) / page_pixel_area < 0.0001`
- Only scanned pages are sent to the Vision LLM for OCR. Text pages use
  `markitdown` directly. Results are merged into a single Markdown string.
- This hybrid approach minimizes OCR latency (e.g., a 5-page PDF with 1
  scanned page only triggers OCR once).

### Malformed PDF Handling

- **Encrypted/password-protected**: `pdfplumber` raises `PDFPasswordIncorrect`
  → Exception path → admin alert `PDF_ENCRYPTED`.
- **Corrupted**: Any other `pdfplumber` exception → admin alert `PDF_CORRUPT`.
- **PDF bombs**: Mitigated by 1MB file size limit + 50-page hard cap + 30s
  parse timeout.

## LLM Extraction Schema & Validation

### Structured Output

- LM Studio's **JSON Mode** (strict schema enforcement) is enabled via the
  `response_format` parameter.
- The schema enforces:
  - `identifiers[]`: array of `{id_type, id_value, customer_name}`
  - `id_type`: enum `["CIF", "ACCOUNT_ID", "PHONE", "CCCD"]`
  - `requested_fields[]`: enum `["DOB", "CCCD", "ADDRESS", "PHONE", "TRANSACTIONS_30D", "TRANSACTIONS_90D"]`
- Unexpected keys are automatically stripped by LM Studio's strict mode.

### Post-Validation (Pydantic)

- A Python code node validates the LLM output using `pydantic`.
- If validation fails, the LLM call is retried once with a stricter prompt.
  On second failure → admin alert `LLM_INVALID_JSON`.

### ID Format Validation (Regex)

| ID Type    | Regex                | Invalid IDs                             |
| ---------- | -------------------- | --------------------------------------- |
| CIF        | `^[A-Z0-9]{6,12}$` | Dropped, logged as`INVALID_ID_FORMAT` |
| Account ID | `^\d{8,14}$`       | Dropped, logged as`INVALID_ID_FORMAT` |
| Phone      | `^(\+?84             | 0)?\d{9,11}$`                           |
| CCCD       | `^\d{12}$`         | Dropped, logged as`INVALID_ID_FORMAT` |

### Identifier Limit

- **Hard cap: 50 identifiers per email.** If exceeded, only the first 50 are
  processed. The reply email includes a warning: "Your request contained more
  than 50 identifiers. Only the first 50 have been processed."

### Prompt Injection Defense (4 Layers)

1. **XML delimiters**: PDF text wrapped in `<document>...</document>` tags.
   System prompt explicitly states the content is untrusted.
2. **Structured output**: JSON schema restricts output to predefined fields.
3. **Post-extraction validation**: Pydantic + regex validation.
4. **Parameterized queries**: No dynamic SQL is ever generated.

- An adversarial test suite of 20 injection PDFs must pass before go-live
  and after any prompt change.

## Name Matching & Authorization

### Authorization Enforcement (Application-Level)

- The n8n workflow queries `authorized_requesters` to retrieve the requester's
  allowed scopes (branch codes, department codes, customer segments).
- DB queries include a `WHERE` clause filtering by both authorized scopes AND
  extracted IDs (defense in depth).
- The DB service account has `SELECT` only on `customers`, `transactions`,
  `authorized_requesters`, and `INSERT` only on `request_logs`. No `UPDATE`,
  `DELETE`, or `DDL` privileges.

### Name Normalization Pipeline

Applied to both the DB customer name and the LLM-extracted name:

1. Convert to uppercase.
2. Remove diacritics (`unicodedata.normalize('NFD')` + strip combining marks).
3. Strip common titles: `MR`, `MRS`, `MS`, `DR`, `ONG`, `BA`, `CO`, `ANH`, `CHI`.
4. Collapse whitespace.
5. Remove punctuation.

### Name Matching Algorithm

| Name Length (normalized) | Max Levenshtein Distance |
| ------------------------ | ------------------------ |
| ≤ 5 chars               | 0 (exact match required) |
| 6–15 chars              | ≤ 2                     |
| > 15 chars               | ≤ 3                     |

- If the normalized name is in the **top 500 common Vietnamese names** list,
  the threshold is tightened by 1 (e.g., ≤ 1 instead of ≤ 2).
- On match failure: record is rejected, admin alert `NAME_MISMATCH`.

### Partial Match Data Leakage Prevention

- The Excel file contains **only successful records**. Failed IDs do not
  appear as empty rows.
- The reply email states: "✅ Processed X of Y requested identifiers.
  ⚠️ (Y−X) identifiers could not be verified. The data team has been notified."
- The requester is **NOT told which IDs failed** or the failure reason.
- The admin alert contains full details (ID, extracted name, DB name, distance).

### Break-Glass Override

- An admin can trigger a "Manual Override" workflow in n8n (requires SSO + RBAC).
- Inputs: `request_log_id`, ID to override, reason (free text).
- The override bypasses the name check, re-runs the query, generates a new
  Excel, and replies to the original thread.
- The override is logged in `request_logs` with: admin email, timestamp,
  reason, overridden ID.
- Overrides are reviewed monthly by the security team.

## Database Indexes & Query Templates

### Required Indexes (Must Verify Before Go-Live)

```sql
CREATE INDEX idx_customers_cif ON customers(cif);
CREATE INDEX idx_customers_account_id ON customers(account_id);
CREATE INDEX idx_customers_phone ON customers(phone);
CREATE INDEX idx_customers_branch ON customers(branch_code);
CREATE INDEX idx_transactions_account_date ON transactions(account_id, transaction_date DESC);
CREATE INDEX idx_auth_requesters_email ON authorized_requesters(email);
```

### Query Templates (Parameterized)

**Customer Query:**

```sql
SELECT customer_id, full_name, date_of_birth, cccd_number, address, phone_number
FROM customers
WHERE customer_id = ANY($1::text[])
  AND branch_code = ANY($2::text[]);
```

**Transaction Query:**

```sql
SELECT t.account_id, t.transaction_date, t.amount, t.description
FROM transactions t
WHERE t.account_id = ANY($1::text[])
  AND t.transaction_date >= ($2::timestamptz - INTERVAL '30 days')
  AND t.transaction_date <= $2::timestamptz
ORDER BY t.account_id, t.transaction_date DESC
LIMIT 10000;
```

- `$1` = extracted identifiers (array)
- `$2` = email received timestamp (UTC, converted to timestamptz)
- Date range is relative to the **email received timestamp**, not DB server clock.
- `LIMIT 10000` is the hard cap. On truncation, a note row is added to the Excel.

### DB Service Account Privileges

```sql
GRANT SELECT ON customers, transactions, authorized_requesters TO emailagent_app;
GRANT INSERT ON request_logs TO emailagent_app;
-- No UPDATE, DELETE, or DDL privileges.
```
