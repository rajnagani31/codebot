# Celery Review Task Architecture Review

Reviewed file: `apps/backend/tasks/review_tasks.py`

Related files:

- `apps/backend/bot/application/core/celery.py`
- `apps/backend/agents/pr_reviewer_agent/apps/code_reviewer/routers/github.py`
- `apps/backend/agents/pr_reviewer_agent/apps/code_reviewer/service/git_service.py`
- `apps/backend/agents/pr_reviewer_agent/apps/code_reviewer/repository/git_repository.py`
- `docker-compose.yml`

## 1. Short Summary

The current PR review pipeline is a good first Celery architecture:

```text
GitHub webhook
  -> FastAPI route
  -> create review_jobs row
  -> review_pull_request task
  -> fetch changed files
  -> fan out review_file tasks, one per file
  -> aggregate_review task
  -> save final review JSON and mark job succeeded
```

There are four Celery tasks in `review_tasks.py`:

1. `review_pull_request`
2. `review_file`
3. `dummy_ai_review`
4. `aggregate_review`

The best part of the design is that one PR review does not happen inside the webhook HTTP request. The webhook only queues work, and Celery processes the expensive GitHub and AI calls in the background.

The main architecture risk is that concurrency is not explicitly controlled. The worker currently uses Celery defaults in Docker, and the database engine uses `StaticPool`, which can become a serious bottleneck or unsafe under threaded/process Celery workers.

## 2. What Is Good In This Architecture

### 2.1 Webhook Is Fast

The webhook route receives the GitHub event, stores/updates PR data, creates a queued review job, and calls:

```python
review_pull_request.delay(review_job_id)
```

This is good because GitHub webhooks should return quickly. AI review can take many seconds or minutes, so it should not block the HTTP request.

### 2.2 Clear Fan Out / Fan In Pattern

`review_pull_request` fetches changed files and then creates one `review_file` task per file:

```python
header = [review_file.s(review_job_id, file_data) for file_data in file_payloads]
async_result = chord(header)(aggregate_review.s(review_job_id))
```

This is a good Celery pattern:

- fan out: review many files in parallel
- fan in: aggregate all file results into one final review

### 2.3 Job Status Is Stored In Database

The pipeline updates the database:

- `QUEUED`
- `RUNNING`
- `SUCCEEDED`
- `FAILED`

It also tracks:

- total files
- processed files
- per-file review result
- final review JSON
- error code

This is good for frontend progress display and debugging failed jobs.

### 2.4 Retryable Errors Are Separated

The helper `_is_retryable()` treats temporary AI, network, Redis, timeout, and retryable HTTP status codes as retryable.

Good retryable examples:

- OpenAI/GitHub timeout
- network error
- HTTP 429 rate limit
- HTTP 500/502/503/504
- Redis temporary error

Non-retryable examples:

- missing review job context
- missing GitHub installation ID
- 401/403/404 type problems

### 2.5 Binary Or Missing Patch Files Are Skipped

`review_file` skips files where GitHub did not provide a text patch:

```python
if file.patch is None:
    result = FileReviewResult(... skipped=True ...)
```

This avoids wasting AI calls on binary files or files GitHub cannot represent as a patch.

### 2.6 Late Ack Is Enabled

Celery config has:

```python
task_acks_late=True
task_reject_on_worker_lost=True
```

This is good. If a worker dies in the middle of a task, Celery can requeue the task instead of silently losing it.

## 3. What Is Wrong Or Risky

### 3.1 No Explicit Worker Concurrency In Docker

In `docker-compose.yml`, the worker command is:

```bash
celery -A apps.backend.bot.application.core.celery:celery_app worker --loglevel=INFO
```

There is no `--concurrency`, no queue name, and no pool choice.

This means Celery chooses defaults based on the runtime. On Linux, default prefork concurrency is usually the number of CPUs visible to the container. On Windows local development, prefork is not a good choice, so your `agent.py` notes correctly suggest `--pool=solo` or `--pool=threads --concurrency=4`.

Recommended improvement:

```bash
celery -A apps.backend.bot.application.core.celery:celery_app worker \
  --loglevel=INFO \
  --pool=threads \
  --concurrency=4 \
  --prefetch-multiplier=1
```

For AWS `t3.small`, start smaller:

```bash
celery -A apps.backend.bot.application.core.celery:celery_app worker \
  --loglevel=INFO \
  --pool=threads \
  --concurrency=2 \
  --prefetch-multiplier=1
```

### 3.2 Database Uses `StaticPool`

`apps/backend/bot/application/core/database.py` creates the SQLAlchemy engine with:

```python
poolclass=StaticPool
```

This is not a good default for PostgreSQL production usage. `StaticPool` reuses one connection globally. That can create problems with concurrent Celery tasks, especially with threaded workers.

Recommended improvement for PostgreSQL:

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=os.getenv("DEBUG", "false").lower() == "true",
)
```

Keep `StaticPool` only for SQLite tests if needed.

### 3.3 Large Payloads Go Through Redis

`review_pull_request` sends the full file data to each `review_file` task:

```python
review_file.s(review_job_id, file_data)
```

`file_data` can include `patch`, and patches can be large. Redis broker and Redis result backend will store task messages and results. Large PRs can put pressure on Redis memory.

Better architecture:

- store changed file metadata/patches in DB or object storage
- pass only IDs through Celery
- let `review_file` load the patch by ID

### 3.4 Chord Failure Behavior Needs More Control

If one `review_file` task fails permanently, the chord callback `aggregate_review` normally does not run successfully. The job is marked failed inside `review_file`, which is good, but there is no custom chord error handler.

Recommended improvement:

- add a chord error callback
- save failed file name and error
- mark final job failed once, with a clear reason
- optionally aggregate partial results

### 3.5 Possible Duplicate Review Jobs

Every reviewable GitHub action creates a new `ReviewJob`. If GitHub retries a webhook delivery, or multiple synchronize events arrive quickly, multiple jobs can run for the same PR.

Recommended improvement:

- store GitHub delivery ID
- make webhook processing idempotent
- cancel older queued/running jobs for the same PR when a newer commit arrives
- only review the latest `head_sha`

### 3.6 No Task Time Limits

AI calls have an HTTP timeout of 60 seconds, but Celery does not have task-level limits.

Recommended improvement:

```python
task_soft_time_limit=120
task_time_limit=180
```

or per task:

```python
@celery_app.task(..., soft_time_limit=120, time_limit=180)
```

### 3.7 No Rate Limit For OpenAI Or GitHub

When a PR has many files, the chord can launch many AI calls in parallel. That can trigger OpenAI or GitHub rate limits.

Recommended improvement:

- use `--concurrency` deliberately
- add Celery task rate limits if needed
- separate queues for orchestration and AI work
- consider batching small files

### 3.8 Redis Result Backend Stores Full Results

Every `review_file` returns a full `FileReviewResult`. The chord needs those results, so Redis temporarily stores them. For large PRs, this can become memory-heavy.

Recommended improvement:

- have `review_file` save result to DB and return only `{filename, status}`
- have `aggregate_review` load final file results from DB

### 3.9 No Dedicated Queues

All tasks use the default queue.

Better structure:

```text
review.orchestrator -> review_pull_request, aggregate_review
review.ai           -> review_file, dummy_ai_review
```

This lets you scale AI workers separately from orchestration tasks.

### 3.10 Webhook Route Writes `payload.json`

The GitHub webhook route writes the full webhook payload to `payload.json`:

```python
with open("payload.json", "w") as f:
    json.dump(payload_dict, f, indent=4)
```

This is risky:

- concurrent requests overwrite the same file
- payload may contain sensitive repository data
- this should not run in production

Remove it or guard it behind a local debug flag.

## 4. Task By Task Explanation

## 4.1 `review_pull_request`

Role:

This is the main orchestrator task. It starts one PR review job.

Input:

```python
review_job_id: int
```

What it does:

1. Creates a repository object.
2. Marks the review job as `RUNNING`.
3. Loads review context from DB.
4. Validates that the repository has a GitHub installation ID.
5. Fetches changed files from GitHub.
6. Saves total file count to DB.
7. If no files changed, queues `aggregate_review` with an empty list.
8. If files exist, creates a Celery chord:
   - one `review_file` task per changed file
   - one `aggregate_review` callback after all file tasks finish

When it runs:

It runs after a GitHub PR webhook creates a queued review job. The route calls:

```python
review_pull_request.delay(review_job_id)
```

It runs for PR actions:

- `opened`
- `ready_for_review`
- `synchronize`
- `reopened`

It does not create a review job for `closed`.

Good:

- clean orchestrator role
- does not perform per-file AI review itself
- supports comparing `base_sha` and `head_sha`
- retries temporary network failures

Risk:

- retrying after partial chord dispatch can create duplicate child tasks in rare failure cases
- all changed file payloads are pushed into Redis
- no max files limit
- no rate control

## 4.2 `review_file`

Role:

This task reviews one changed file.

Input:

```python
review_job_id: int
file_data: dict
```

What it does:

1. Validates `file_data` into `PullRequestFile`.
2. If patch is missing, creates a skipped result.
3. If patch exists, calls `AIReviewService().review_file(...)`.
4. Saves the per-file result to `review_file_results`.
5. Increments `processed_files`.
6. Returns the file review result to Celery chord.

When it runs:

It runs only after `review_pull_request` fetches files and dispatches the chord. One task runs per changed file.

Example:

If a PR changes 12 files, Celery creates 12 `review_file` tasks.

Good:

- one file per task gives parallelism
- skipped binary/missing patches are handled cleanly
- per-file result is stored before aggregation
- retry handles temporary AI/network failures

Risk:

- every file can call OpenAI at the same time depending on concurrency
- large patches may hit model/token limits
- no per-file timeout at Celery level
- no rate limit
- if one file fails permanently, final aggregation may not happen

## 4.3 `dummy_ai_review`

Role:

This is a local/testing helper task. It calls the AI review service in dummy mode.

Input:

```python
filename: str
status: str
patch: str
```

What it does:

1. Calls `AIReviewService(use_dummy=True).review_file(...)`.
2. Returns a fake/dummy review result.

When it runs:

It does not appear to be used by the webhook pipeline. It runs only if a developer manually calls it or another part of the code imports and queues it.

Good:

- useful for testing Celery without OpenAI API key
- useful for validating JSON shape

Risk:

- not connected to real `review_job_id`
- does not save to DB
- should not be confused with production review

## 4.4 `aggregate_review`

Role:

This is the final aggregation task. It combines all file review results into one PR-level review result.

Input:

```python
file_reviews: list[dict]
review_job_id: int
```

What it does:

1. Validates each file result into `FileReviewResult`.
2. Counts findings by severity.
3. Counts total findings.
4. Counts skipped files.
5. Builds `FinalReviewResult`.
6. Saves final result JSON to DB.
7. Marks review job as `SUCCEEDED`.

When it runs:

It runs after all `review_file` tasks in the chord complete successfully. If no files changed, `review_pull_request` manually queues it with an empty list.

Good:

- clear final summary
- stores complete final review JSON
- marks job succeeded in one place

Risk:

- receives all file results through Redis result backend
- does not currently publish comments back to GitHub
- no custom handling for partial failure

## 5. Manual Terminal Commands

Run these from:

```powershell
cd E:\raj\codebot\codebot
```

### 5.1 Start Required Services With Docker

```powershell
docker compose up -d db redis
```

If you want the full app:

```powershell
docker compose up -d
```

### 5.2 Run Celery Worker Locally On Windows

Safe single-task worker:

```powershell
uv run celery -A apps.backend.bot.application.core.celery:celery_app worker --loglevel=INFO --pool=solo
```

Recommended local threaded worker:

```powershell
uv run celery -A apps.backend.bot.application.core.celery:celery_app worker --loglevel=INFO --pool=threads --concurrency=4 --prefetch-multiplier=1
```

### 5.3 Run Celery Worker On Linux / AWS

For a small server:

```bash
uv run celery -A apps.backend.bot.application.core.celery:celery_app worker --loglevel=INFO --pool=threads --concurrency=2 --prefetch-multiplier=1
```

For a bigger machine:

```bash
uv run celery -A apps.backend.bot.application.core.celery:celery_app worker --loglevel=INFO --pool=threads --concurrency=4 --prefetch-multiplier=1
```

### 5.4 Manually Queue A Real PR Review Job

Replace `1` with a real `review_jobs.id` from your database.

```powershell
uv run python -c "from apps.backend.tasks.review_tasks import review_pull_request; r = review_pull_request.delay(1); print(r.id)"
```

### 5.5 Manually Run Dummy AI Review

```powershell
uv run python -c "from apps.backend.tasks.review_tasks import dummy_ai_review; r = dummy_ai_review.delay('app.py', 'modified', '@@ -1 +1 @@\n-print(1)\n+print(2)'); print(r.get(timeout=30))"
```

### 5.6 Inspect Celery Worker

Active tasks:

```powershell
uv run celery -A apps.backend.bot.application.core.celery:celery_app inspect active
```

Reserved tasks:

```powershell
uv run celery -A apps.backend.bot.application.core.celery:celery_app inspect reserved
```

Registered tasks:

```powershell
uv run celery -A apps.backend.bot.application.core.celery:celery_app inspect registered
```

### 5.7 Docker Worker Logs

```powershell
docker compose logs -f celery_worker
```

## 6. How Many Requests Can It Handle?

Important: Celery does not limit by "requests" in the HTTP sense. It limits by active task slots.

One PR review creates:

```text
1 review_pull_request task
+ N review_file tasks, where N = changed files
+ 1 aggregate_review task
```

So a PR with 20 changed files creates about 22 Celery tasks.

## 6.1 Current Local Machine Estimate

On this machine, Python reports:

```text
os.cpu_count() = 8
```

Current Docker command has no explicit concurrency:

```bash
celery -A apps.backend.bot.application.core.celery:celery_app worker --loglevel=INFO
```

Expected local capacity:

| Worker command | Active tasks at once | Practical meaning |
|---|---:|---|
| `--pool=solo` | 1 | One task at a time. Slow but simplest for debugging. |
| `--pool=threads --concurrency=4` | 4 | Up to 4 Celery tasks active at once. Good local default. |
| Docker/Linux default on this 8 CPU machine | about 8 | Up to about 8 active tasks if Docker exposes all CPUs. |

Practical local PR handling:

- With concurrency 4, one PR can review up to 4 files at the same time.
- If two PRs arrive together, their file tasks share those 4 slots.
- If each AI file review takes 30 seconds, concurrency 4 means roughly 8 files per minute.
- If each AI file review takes 60 seconds, concurrency 4 means roughly 4 files per minute.

Recommended local setting:

```powershell
--pool=threads --concurrency=4 --prefetch-multiplier=1
```

## 6.2 AWS `t3.small` Estimate

AWS `t3.small` has 2 vCPUs and 2 GiB memory. AWS describes T3 as burstable general purpose instances with baseline CPU and burst capacity. Source: https://aws.amazon.com/ec2/instance-types/t3/

Expected capacity:

| AWS machine | Active Celery tasks at once | Recommended setting |
|---|---:|---|
| `t3.small` running backend + Redis + Postgres + worker on same VM | 1 to 2 | `--concurrency=1` or `--concurrency=2` |
| `t3.small` only running Celery worker, with DB/Redis elsewhere | 2 to 4 | start with `--concurrency=2`, test `4` carefully |

For your current all-in-one Docker compose stack on `t3.small`, use:

```bash
--pool=threads --concurrency=2 --prefetch-multiplier=1
```

Why not higher?

- `t3.small` only has 2 GiB RAM.
- Your compose stack also runs backend, Postgres, Redis, frontend, and Qdrant.
- AI tasks wait on network, but each active task still uses Python memory, DB connections, Redis result memory, and patch/result payload memory.
- T3 CPU is burstable, so high sustained concurrency can become unstable or slow after burst credits reduce.

Practical AWS `t3.small` PR handling:

- With concurrency 2, one PR reviews 2 files at the same time.
- If each AI review takes 30 seconds, expect about 4 files per minute.
- If each AI review takes 60 seconds, expect about 2 files per minute.
- Multiple PRs can be queued, but only 1 to 2 file reviews should actively run at once on this machine.

## 7. Recommended Next Architecture Changes

Priority order:

1. Remove `StaticPool` for PostgreSQL and use normal SQLAlchemy pooling.
2. Set explicit worker concurrency in Docker compose.
3. Add `--prefetch-multiplier=1`.
4. Add task time limits.
5. Add dedicated Celery queues for orchestrator and AI review tasks.
6. Reduce Redis payload size by passing IDs instead of full patches/results.
7. Add idempotency using GitHub delivery ID and/or PR `head_sha`.
8. Add chord error handler.
9. Remove production `payload.json` writing.
10. Add rate limiting for OpenAI calls.

## 8. Suggested Docker Compose Worker Command

For local development:

```yaml
command: >
  celery -A apps.backend.bot.application.core.celery:celery_app worker
  --loglevel=INFO
  --pool=threads
  --concurrency=4
  --prefetch-multiplier=1
```

For AWS `t3.small`:

```yaml
command: >
  celery -A apps.backend.bot.application.core.celery:celery_app worker
  --loglevel=INFO
  --pool=threads
  --concurrency=2
  --prefetch-multiplier=1
```

## 9. Final Opinion

The current design is directionally correct. The use of Celery chord for PR file review is good, and saving job progress in the database is the right foundation.

The system is not production-safe yet for larger PRs or concurrent users. The biggest fixes are explicit concurrency, proper DB pooling, smaller Redis task payloads, idempotent webhook/job handling, and better chord failure handling.
