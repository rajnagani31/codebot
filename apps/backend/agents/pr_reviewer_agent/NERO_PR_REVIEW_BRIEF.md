# Nero PR Review Service — What's Done & What's Next

## Current Status

GitHub webhook is integrated and tested. Database models are production-ready.
The service receives GitHub events and can verify signatures — but does nothing with them yet.

---

## What Is Already Built

| Area | Status | Notes |
|---|---|---|
| DB Models (PullRequest, ReviewJob, ReviewReport, ReviewFinding, ArtifactRef) | Done | Full SQLAlchemy ORM, indexes, enums |
| Alembic setup | Done | env.py wired, ready to run migrations |
| Webhook signature verification | Done | HMAC SHA256 via `verify_signature.py` |
| GitHub webhook endpoint `POST /api/webhook/github` | Done (skeleton) | Receives event, verifies sig — then stops |
| FastAPI app wired | Done | Router mounted at `/api` prefix |

---

## What Is Pending (Ordered by Priority)

### 1. Run Alembic Migrations
Multiple unresolved migration files exist (`10c2c4fa`, `3863dc99`, `7aee32f3`, `912c7e3e`, `96d28bd7`).
Need to consolidate and run `alembic upgrade head` to create tables in Postgres.

**Ticket:** P2-001 (subtask: migration)

---

### 2. Webhook Event Processing — Idempotency & Job Creation (P2-002)
The webhook handler has a `# TODO: Process the webhook event` comment and stops there.

Must implement:
- Parse GitHub payload for `pull_request` events (opened, synchronize, reopened)
- Build idempotency key from `(delivery_id, repo, pr_number, action, sha)`
- Add `webhook_events` table to deduplicate retried deliveries
- Create a `PullRequest` row if it does not exist
- Create a `ReviewJob` row with status `QUEUED`
- Return `{ job_id, status: "queued" }` in under 2 seconds

**File to edit:** `apps/code_reviewer/routers/github.py`

---

### 3. Repository Layer — CRUD Methods (P2-001)
`repository/git_repository.py` has only a constructor. Need:
- `get_or_create_pull_request(repo_id, pr_number, ...)`
- `create_review_job(pr_id) -> ReviewJob`
- `get_job_by_id(job_id)`
- `update_job_status(job_id, status, ...)`
- `create_review_report(pr_id, ...) -> ReviewReport`
- `add_findings(report_id, findings: list)`

---

### 4. Celery + Redis Bootstrap (P2-010)
All review processing must be async. Need:
- `celery_app.py` with queues: `review.ingest`, `review.chunk`, `review.analyze`, `review.aggregate`
- Retry policy with exponential backoff
- Worker command added to docker-compose

---

### 5. Enqueue-on-Webhook Flow (P2-011)
Once Celery is up, the webhook handler replaces direct processing with:
```python
job = create_review_job(pr_id)
enqueue_pr_review.delay(job_id=job.id, payload=payload)
return { "job_id": job.id, "status": "queued" }
```
Create `review_orchestrator.py` to own this logic.

---

### 6. GitHub PR Diff Fetcher (P2-012)
Worker task that fetches the PR diff from GitHub API.

- `providers/base.py` — abstract provider interface
- `providers/github_provider.py` — implements:
  - `get_pr_metadata(repo, pr_number)`
  - `get_changed_files(repo, pr_number)`
  - `get_unified_diff(repo, pr_number)`
- Normalize to internal DTO
- Store raw diff as artifact (URI in `artifact_refs`, content in object storage)

---

### 7. Diff Chunker (P2-013)
Split large diffs into chunks safe for LLM context windows.

- `chunker.py`: split by file, then by hunk/token limit
- Configurable max tokens per chunk
- Skip binary files
- Publish one `analyze_chunk` task per chunk

---

### 8. LLM Reviewer Task (P2-014)
Per-chunk Celery task that calls an LLM and produces findings.

- Prompt template: send diff chunk + review instructions
- Parse structured response into `ReviewFinding` rows
- Retry on rate-limit / 5xx, fail-fast on invalid payload
- Store raw prompt + response as `ArtifactRef`

---

### 9. Review Report API (P2-003)
Read-only API so frontend can poll job status and fetch the final report.

```
GET /api/v1/reviews/jobs/{job_id}
GET /api/v1/reviews/pr/{repo_id}/{pr_number}/latest
GET /api/v1/reviews/reports/{report_id}
```

Pydantic schemas in `schema/review_schema.py`.

---

## Debug Issues to Fix Before Moving On

1. **Print statements leaking secrets** — `github.py` lines 24-32 print raw headers and the webhook secret. Remove before any further testing.
2. **Duplicate webhook security service** — two files exist: `webhook/webhook_security_service.py` and `service/webhook/webhook_security_service.py`. Delete one.
3. **Import paths** — `github.py` uses relative imports (`from code_reviewer...`) that may break depending on how the app is started. Switch to absolute imports.
4. **`nero/base.py` is empty** — fill in or remove to avoid confusion.

---

## Immediate Next 3 Tasks (This Sprint)

| # | Task | Why First |
|---|---|---|
| 1 | Fix debug prints + consolidate migration files → run `alembic upgrade head` | Tables must exist before any code can write to DB |
| 2 | Implement idempotency table + job creation in webhook handler (P2-002) | This closes the gap between "webhook received" and "work tracked" |
| 3 | Bootstrap Celery + Redis, enqueue job from webhook (P2-010, P2-011) | Moves processing off the request thread — required before diff fetching |

---

## File Map

```
apps/code_reviewer/
├── model/                  ← DONE
├── routers/github.py       ← NEXT: add job creation + idempotency
├── repository/             ← NEXT: add CRUD methods
├── service/                ← NEXT: orchestrator + review logic
├── webhook/                ← fix: remove duplicate, clean up
└── providers/              ← CREATE: GitHub diff fetcher
```
