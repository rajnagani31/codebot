# PR Reviewer Agent Model Overview

This document describes the database models defined under `backend/Agent/pr_reviewer_agent/apps/code_reviewer/model`.
It covers table definitions, columns, relationships, example data, and the expected PR review completion flow.

## Tables and Models

### `pull_requests`
- Model: `PullRequest`
- Table name: `pull_requests`
- Purpose: root aggregate for PR context. Stores PR metadata needed to run and report a review.
- Important constraints:
  - Unique on `(tenant_id, repo_id, pr_number)`
  - Indexes on `(repo_id, pr_number)` and `tenant_id`

Columns:
- `id` (`BigInteger`, PK, autoincrement)
- `tenant_id` (`Integer`, nullable)
- `repo_id` (`Integer`, nullable)
- `pr_number` (`Integer`, nullable)
- `commit_sha` (`String(64)`, nullable)
- `author` (`String(255)`, nullable)
- `state` (`Enum('OPEN','CLOSED','MERGED')`, default `OPEN`, nullable)
- `title` (`String(255)`, not null)
- `description` (`String`, nullable)
- `source_branch` (`String(255)`, not null)
- `target_branch` (`String(255)`, not null)
- `url` (`String(2048)`, not null)
- `created_at` (`DateTime(timezone=True)`, not null)
- `updated_at` (`DateTime(timezone=True)`, not null)

Example row:
```sql
INSERT INTO pull_requests
(tenant_id, repo_id, pr_number, commit_sha, author, state, title, description, source_branch, target_branch, url, created_at, updated_at)
VALUES
(10, 42, 123, 'a1b2c3d4e5f6', 'alice', 'OPEN', 'Add login retry', 'Retry login when token expires', 'feature/login-retry', 'main', 'https://github.com/org/repo/pull/123', now(), now());
```

---

### `review_jobs`
- Model: `ReviewJob`
- Table name: `review_jobs`
- Purpose: tracks the lifecycle of a review task for a PR.
- Important indexes:
  - `(status, queued_at)`
  - `(pr_id, queued_at)`

Columns:
- `id` (`BigInteger`, PK)
- `pr_id` (`BigInteger`, FK -> `pull_requests.id`, on delete cascade, not null)
- `status` (`Enum('QUEUED','RUNNING','SUCCEEDED','FAILED','CANCELED')`, default `QUEUED`, not null)
- `attempts` (`SmallInteger`, default `0`, not null)
- `queued_at` (`DateTime(timezone=True)`, default now, not null)
- `started_at` (`DateTime(timezone=True)`, nullable)
- `finished_at` (`DateTime(timezone=True)`, nullable)
- `error_code` (`String(64)`, nullable)
- `created_at` (`DateTime(timezone=True)`, not null)
- `updated_at` (`DateTime(timezone=True)`, not null)

Example row:
```sql
INSERT INTO review_jobs
(id, pr_id, status, attempts, queued_at, started_at, finished_at, error_code, created_at, updated_at)
VALUES
(1001, 501, 'SUCCEEDED', 1, now() - interval '5 minutes', now() - interval '4 minutes', now(), null, now() - interval '5 minutes', now());
```

---

### `review_reports`
- Model: `ReviewReport`
- Table name: `review_reports`
- Purpose: stores aggregate review output for a PR, including risk and model metadata.

Columns:
- `id` (`BigInteger`, PK, autoincrement)
- `pr_id` (`BigInteger`, FK -> `pull_requests.id`, on delete cascade, not null)
- `risk_score` (`Numeric(5,2)`, default `0`, not null)
- `totals_json` (`JSONB`, default `{}`, not null)
- `model_info_json` (`JSONB`, default `{}`, not null)
- `created_at` (`DateTime(timezone=True)`, not null)
- `updated_at` (`DateTime(timezone=True)`, not null)

Example row:
```sql
INSERT INTO review_reports
(pr_id, risk_score, totals_json, model_info_json, created_at, updated_at)
VALUES
(501, 7.50,
 '{"total_findings": 4, "critical": 1, "high": 1, "medium": 2}',
 '{"model_name":"gpt-4.1","prompt_tokens":1250,"completion_tokens":800}',
 now(), now());
```

---

### `review_findings`
- Model: `ReviewFinding`
- Table name: `review_findings`
- Purpose: stores individual findings/issues discovered during a review report.
- Important indexes:
  - `(report_id)`
  - `(severity, category)`

Columns:
- `id` (`BigInteger`, PK, autoincrement)
- `report_id` (`BigInteger`, FK -> `review_reports.id`, on delete cascade, not null)
- `file_path` (`Text`, not null)
- `line_start` (`Integer`, not null)
- `line_end` (`Integer`, nullable)
- `severity` (`Enum('CRITICAL','HIGH','MEDIUM','LOW','INFO')`, not null)
- `category` (`Enum('SECURITY','BUG','PERFORMANCE','STYLE','MAINTAINABILITY','TEST','DOCS','OTHER')`, not null)
- `title` (`String(255)`, not null)
- `summary` (`Text`, not null)
- `recommendation` (`Text`, nullable)
- `created_at` (`DateTime(timezone=True)`, not null)

Example row:
```sql
INSERT INTO review_findings
(report_id, file_path, line_start, line_end, severity, category, title, summary, recommendation, created_at)
VALUES
(210, 'src/app/auth.py', 112, 124, 'HIGH', 'SECURITY', 'Missing token validation', 'Auth middleware does not validate token expiry.', 'Add expiry validation before accepting the token.', now());
```

---

### `artifact_refs`
- Model: `ArtifactRef`
- Table name: `artifact_refs`
- Purpose: stores references to artifacts created during a review job, such as raw diffs, prompts, model responses, exported reports, or logs.
- Important constraint:
  - Unique `(job_id, artifact_type, artifact_uri)`
- Important index:
  - `(job_id, artifact_type)`

Columns:
- `id` (`BigInteger`, PK, autoincrement)
- `job_id` (`BigInteger`, FK -> `review_jobs.id`, on delete cascade, not null)
- `artifact_type` (`Enum('RAW_DIFF','PROMPT','MODEL_RESPONSE','REPORT_EXPORT','LOG','OTHER')`, not null)
- `artifact_uri` (`Text`, not null)
- `checksum` (`String(128)`, nullable)
- `created_at` (`DateTime(timezone=True)`, not null)
- `updated_at` (`DateTime(timezone=True)`, not null)

Example row:
```sql
INSERT INTO artifact_refs
(job_id, artifact_type, artifact_uri, checksum, created_at, updated_at)
VALUES
(1001, 'REPORT_EXPORT', 's3://bucket/reviews/1001/report.json', 'abc123def456', now(), now());
```

---

## Relationships and Data Flow

### Relationship graph
- `pull_requests.id` -> `review_jobs.pr_id`
- `pull_requests.id` -> `review_reports.pr_id`
- `review_reports.id` -> `review_findings.report_id`
- `review_jobs.id` -> `artifact_refs.job_id`

This means each PR can have multiple review jobs and multiple review findings through a report.

### Typical review completion flow

1. **PR record exists or is created**
   - A PR is represented in `pull_requests`.
   - If this is the first review for a PR, a new record is inserted.
   - Existing PRs are identified by `(tenant_id, repo_id, pr_number)`.

2. **Create a review job**
   - Insert a row into `review_jobs` with:
     - `pr_id` referencing the PR
     - `status = QUEUED`
     - `queued_at = now()`
     - `attempts = 0`

3. **Review worker starts the job**
   - Update the job row:
     - `status = RUNNING`
     - `started_at = now()`

4. **Collect artifacts while reviewing**
   - Optionally insert `artifact_refs` for intermediate outputs:
     - raw diff snapshots
     - prompt text
     - model responses
     - logs or exported reports
   - These artifacts are pointers only; actual data is stored externally.

5. **Generate the report**
   - Insert a `review_reports` row for `pr_id`.
   - Fill `risk_score` with the review’s computed severity score.
   - Store aggregated fields in `totals_json`.
   - Store model metadata, prompt/model stats, or tool output in `model_info_json`.

6. **Add findings**
   - For each detected issue, insert a `review_findings` row with:
     - `report_id` referencing the new report
     - path and line range
     - severity and category
     - title, summary, recommendation

7. **Complete the job**
   - Update `review_jobs` with:
     - `status = SUCCEEDED` or `FAILED` or `CANCELED`
     - `finished_at = now()`
     - `error_code` if there was a failure
   - `updated_at` is also refreshed automatically.

8. **Optional PR state update**
   - If the PR closes or merges, update `pull_requests.state` to `CLOSED` or `MERGED`.

## Notes

- The `DateTimeMixin` used by `PullRequest`, `ReviewJob`, `ReviewReport`, and `ArtifactRef` adds `created_at` and `updated_at` timestamps.
- `ReviewFinding` has its own `created_at` timestamp but not `updated_at`.
- `totals_json` and `model_info_json` are flexible JSON fields for storing summary counts, model metadata, or review metrics.
- Actual review orchestration code is not present in the immediate `model` directory, so this doc describes the data model and the expected database flow rather than exact service implementation.
