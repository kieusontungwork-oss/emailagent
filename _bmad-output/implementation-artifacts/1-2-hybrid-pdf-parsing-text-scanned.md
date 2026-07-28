---
baseline_commit: 6cce9ebe366d447689c8c3b294763c7d35be5764
---

# Story 1.2: Hybrid PDF Parsing (Text & Scanned)

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As the data extraction system,
I want to convert PDF attachments into Markdown, using a local Vision LLM for scanned pages,
So that the text is machine-readable for identifier extraction.

## Acceptance Criteria

1. **Given** a text-based PDF page
   **When** processed
   **Then** it is converted to Markdown using markitdown.
2. **Given** a scanned (image) PDF page
   **When** detected based on text density
   **Then** it is sent to the local Vision LLM via LM Studio for OCR conversion.
3. **Given** a multi-page or multi-PDF request
   **When** processed
   **Then** all results are merged into a single Markdown string for the LLM.

## Tasks / Subtasks

- [x] Task 1: Setup n8n PDF Parsing Sub-workflow (AC: 1, 2, 3)
  - [x] Create a new workflow `1-2-hybrid-pdf-parsing.json` in `n8n-workflows/epic-1/`.
  - [x] Configure the trigger/input to receive PDF attachments from the Controller.
- [x] Task 2: Page Splitting and Text Density Check (AC: 1, 2)
  - [x] Split each PDF into individual pages (using Execute Command with `pdftk` or `poppler-utils`, or a Code node with `pdf-lib`).
  - [x] Evaluate text density per page to classify as "text-based" or "scanned" (e.g., characters < 50).
- [x] Task 3: Conditional Routing and Processing (AC: 1, 2)
  - [x] Branch text-based pages: execute `markitdown` CLI to output Markdown.
  - [x] Branch scanned pages: convert the page to image and make an HTTP Request to the local LM Studio Vision LLM (`Llama-3.2-Vision`) for OCR conversion.
- [x] Task 4: Content Aggregation (AC: 3)
  - [x] Gather the generated Markdown text from all processed pages sequentially.
  - [x] Concatenate the output into a single Markdown string and return it to the Controller.

### Review Findings

- [x] [Review][Decision] Multi-PDF Attachment Processing — AC 3 specifies handling multi-PDF requests, but Write PDF to Disk currently hardcodes attachment_0. (Resolved: Option 1 — Controller invokes sub-workflow once per PDF attachment)
- [x] [Review][Patch] Fix Aggregated Markdown Output Lost by Cleanup Node [n8n-workflows/epic-1/1-2-hybrid-pdf-parsing.json]
- [x] [Review][Patch] Fix Out-of-Order Page Merging Across Parallel Execution Branches [n8n-workflows/epic-1/1-2-hybrid-pdf-parsing.json]
- [x] [Review][Patch] Fix Command Injection Vulnerability in ExecuteCommand Nodes [n8n-workflows/epic-1/1-2-hybrid-pdf-parsing.json]
- [x] [Review][Patch] Fix Resource Leak / Disk Accumulation on Workflow Failure [n8n-workflows/epic-1/1-2-hybrid-pdf-parsing.json]
- [x] [Review][Patch] Fix Brittle Empty stdout Splitting in Create Item Per Page Node [n8n-workflows/epic-1/1-2-hybrid-pdf-parsing.json]
- [x] [Review][Patch] Fix Workspace Path Fallback Collision Risk [n8n-workflows/epic-1/1-2-hybrid-pdf-parsing.json]
- [x] [Review][Patch] Fix Incorrect Double Escaping in Aggregation Separator [n8n-workflows/epic-1/1-2-hybrid-pdf-parsing.json]
- [x] [Review][Patch] Fix Missing Error Handling & Response Validation for Vision LLM Node [n8n-workflows/epic-1/1-2-hybrid-pdf-parsing.json]
- [x] [Review][Patch] Fix pdftk Shell Wrapper Pattern & Argument Parsing [Dockerfile.n8n]
- [x] [Review][Patch] Fix Text Density Evaluation Safeguards (Strip Control Chars/Whitespace) [n8n-workflows/epic-1/1-2-hybrid-pdf-parsing.json]
- [x] [Review][Patch] Make LM Studio Host Endpoint Configurable via Environment Variable [n8n-workflows/epic-1/1-2-hybrid-pdf-parsing.json]
- [x] [Review][Defer] Base64 Image Payload RAM Usage for Large Scanned PDFs [n8n-workflows/epic-1/1-2-hybrid-pdf-parsing.json] — deferred, pre-existing design constraint

## Dev Notes

- **Architecture constraints:** Rely entirely on n8n for orchestration. Must operate as a stateless orchestrator. All LLM inference must occur on a local Vision LLM hosted via LM Studio in the private air-gapped subnet (AD-4).
- **Execution of `markitdown`:** Since `markitdown` is a Python tool, it is called via an Execute Command node in n8n. The custom n8n Docker image (AD-6) satisfies this requirement by embedding Python, `markitdown`, and `pdftk` directly into the container.
- **Page Splitting:** Use standard CLI tools (e.g., `pdftoppm`, `pdftk`) if pure Javascript/Code node modules aren't sufficient for splitting and image conversion.
- **Vision LLM Integration:** LM Studio exposes an OpenAI-compatible API. Send the image as base64 or a local accessible path via an HTTP Request node to `http://<lm-studio-host>:1234/v1/chat/completions`.
- **Previous Story Learnings:** Story 1.1 successfully handled email ingestion and size validation. Now the input to this sub-workflow will be guaranteed valid PDFs under size/page limits.

### Project Structure Notes

- n8n workflows should be saved as JSON files in a version-controlled directory, e.g., `n8n-workflows/epic-1/1-2-hybrid-pdf-parsing.json`.

### References

- [Epics Document](file:///home/ryan/Projects/emailagent/_bmad-output/planning-artifacts/epics.md)
- [Architecture Spine](file:///home/ryan/Projects/emailagent/_bmad-output/planning-artifacts/architecture/architecture-EmailAgentV2-2026-07-02/ARCHITECTURE-SPINE.md)
- [Story 1.1](file:///home/ryan/Projects/emailagent/_bmad-output/implementation-artifacts/1-1-email-ingestion-attachment-validation.md)

## Dev Agent Record

### Agent Model Used

Gemini 3.1 Pro (High)

### Debug Log References

### Completion Notes List

- Implemented the `1-2-hybrid-pdf-parsing.json` sub-workflow using n8n.
- Configured a temporary workspace to handle file persistence during processing.
- Handled page splitting using `pdftk burst`.
- Leveraged `pdftotext` to evaluate character density to properly route to `markitdown` or `LM Studio` via `HTTP Request` node.
- Merged the outputs sequentially into a `full_markdown` text string using the Aggregate node.
- Appended cleanup logic to erase temporary workspace.

### File List

- `n8n-workflows/epic-1/1-2-hybrid-pdf-parsing.json`
