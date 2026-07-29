# Human-in-the-loop (HITL) for chat streaming

## Scope

This document describes how to add approval gates to the existing `POST /chat/stream` flow. It is intended for actions that can have an external or sensitive effect (for example, write/delete operations, sending a request, publishing content, or accessing protected data). Read-only actions such as `web_search` normally do not need approval.

## Current flow

```text
Client --POST /chat/stream--> chat_api.py
  -> consume chat credit
  -> ChatService.prepare_stream()
     -> saves completed user message
     -> saves assistant message with status=streaming
  -> OpenAIToolGraph.run_stream()
     -> streams LLM deltas via SSE
     -> directly executes every returned tool call
  -> ChatService.finalize_stream()
     -> assistant status=completed/stopped/failed
     -> stores completed messages in vector memory
```

The direct tool execution is the point to change: `OpenAIToolGraph._execute_tool_call_events()` currently invokes the tool as soon as the model returns a tool call. A human approval cannot safely wait inside this generator: SSE connections can be closed, server workers can restart, and the process-held conversation/tool-call state would be lost.

## Target flow

```text
Client --POST /chat/stream--> create messages + run
  -> stream normal output
  -> model proposes protected tool call
  -> persist immutable approval checkpoint
  -> assistant message status = awaiting_approval
  -> SSE: approval.required
  -> finish this stream

Reviewer --POST /chat/approvals/{id}/decision--> approve / reject / edit
  -> atomically claim the pending approval
  -> rejected: finalize assistant as rejected/cancelled
  -> approved: resume the persisted run, execute the approved arguments,
               and stream/finalize through a new run stream or job
```

Use a durable checkpoint. Do not put the approval task only inside `metadata_json`; a dedicated table permits authorization, locking, audit history, expiry, retries, and reporting.

## API-level changes

### 1. Define an approval policy

Add a policy module close to `openai_tool_graph.py`, e.g. `hitl_policy.py`:

- `requires_approval(tool_name, tool_args, user, context) -> bool`
- `approval_summary(...) -> str` produces an understandable reviewer prompt.
- Allow-list safe read-only tools; default unknown or side-effecting tools to approval.
- Validate all tool arguments server-side. Approval is never permission to use arbitrary model-supplied arguments.

The policy should run before a tool is invoked—not after it has created an external side effect.

### 2. Extend graph events and stop at the checkpoint

Add `run_id` to `GraphRunContext`. When the graph sees a protected tool call, it should:

1. Create an approval record with the tool name, sanitized arguments, and a serialized continuation state.
2. Yield an `approval_required` event instead of calling `_execute_tool_call_events()`.
3. Return from `run_stream()` immediately after yielding the event.

Suggested event:

```text
event: approval.required
data: {
  "run_id": 42,
  "approval_id": 99,
  "thread_id": 7,
  "assistant_message_id": 123,
  "tool_name": "send_email",
  "summary": "Send email to …",
  "expires_at": "…"
}
```

In `chat_api.py`, handle this event before the normal `complete` case. Persist the assistant as `awaiting_approval`, emit `message.awaiting_approval`/`approval.required`, and end the generator. Do **not** call `finalize_stream(... status="completed")`, and do **not** write vector memory yet.

### 3. Add decision and resume endpoints

Suggested endpoints:

- `GET /chat/approvals?status=pending` — reviewer queue; restrict this to authorized reviewer/admin roles.
- `POST /chat/approvals/{approval_id}/decision` — body: `decision` (`approved` or `rejected`), optional `reviewer_note`, optional `approved_args`.
- `GET /chat/runs/{run_id}/stream` — SSE stream for a resumed run, or return a `stream_url` from the decision endpoint.

The decision request must authenticate the reviewer and record the reviewer identity. It must use an idempotency key and an atomic conditional update (`WHERE status = 'pending'`) so double-clicks and concurrent reviewers cannot execute an action twice.

On approval, reconstruct the graph from persisted state, execute only the approved (and schema-validated) call, append its `ToolMessage`, and continue the LLM loop. On rejection, add a tool result stating that the action was denied; either let the LLM propose a safe alternative or finish the assistant message as `rejected`.

For a first version, the decision endpoint may synchronously run a new SSE response. For production, create a background job/worker and let clients subscribe to the run stream; this survives HTTP disconnects and supports multiple API workers.

### 4. Make credits and cancellation correct

`consume_chat_credit()` currently happens before the stream begins. Consume one credit only for creation of the user request/run—not again when an approval resumes it. Decide and document whether rejected/expired requests are refundable; if yes, persist a `credit_ledger` entry rather than decrementing a counter only.

Treat client disconnect as `stopped` only while the run is actively streaming. An assistant in `awaiting_approval` must remain pending after the original SSE connection ends. Add expiry handling to mark old approvals/runs as `expired` and finalize the assistant accordingly.

## Database changes

Add a durable run table and an approval table. Keep `chat_messages` as the user-visible transcript, but do not rely on it as the workflow state machine.

### `chat_runs`

Recommended columns:

| Column | Purpose |
| --- | --- |
| `id`, `public_id` | Internal key and safe API identifier |
| `user_id`, `thread_id`, `assistant_message_id` | Ownership and transcript linkage |
| `status` | `running`, `awaiting_approval`, `resuming`, `completed`, `failed`, `stopped`, `expired` |
| `continuation_json` | Serialized conversation, model/prompt choice, accumulated output, tool loop state |
| `metadata_json`, `error_text` | Run-level audit/debug data |
| `created_at`, `updated_at`, `completed_at` | Lifecycle timestamps |

Index `(user_id, thread_id)`, `(status, updated_at)`, and make `assistant_message_id` unique if one run owns one assistant message.

### `tool_approvals`

Recommended columns:

| Column | Purpose |
| --- | --- |
| `id`, `public_id`, `run_id` | Identity and run linkage |
| `sequence_no` | Supports more than one approval in a run |
| `tool_call_id`, `tool_name` | Exact proposed tool call |
| `proposed_args_json`, `approved_args_json` | Immutable proposal and final validated input |
| `summary`, `risk_level` | Reviewer-facing display |
| `status` | `pending`, `approved`, `rejected`, `expired`, `cancelled`, `executing`, `executed`, `failed` |
| `requested_by_user_id`, `decided_by_user_id` | Requester and reviewer audit trail |
| `reviewer_note`, `decision_reason` | Human rationale |
| `idempotency_key`, `version` | Duplicate/race protection |
| `expires_at`, `decided_at`, `executed_at`, `created_at`, `updated_at` | Lifecycle/audit timestamps |

Add a unique constraint on `(run_id, sequence_no)` and indexes for `(status, expires_at)` and `(run_id, status)`. The database transaction that marks an approval `approved` should also move its run to `resuming`; use row locking or optimistic `version` checks.

### Existing models and migrations

- Add SQLAlchemy models to `application/model/chat_history.py` (or a focused `hitl.py` model file imported by `application/model/__init__.py`).
- Add repository methods for creation, queue listing, atomic decision, claiming/resuming, and expiry.
- Add an Alembic revision under `alembic/versions/`; the project has Alembic configured with `Base.metadata` in `alembic/env.py`.
- Add `run_id` and `approval_id` to `ChatMessage.metadata_json` for convenient UI lookup, but keep the relational tables authoritative.

## Continuation state

The existing graph holds `conversation`, `tools_used`, sources, citations, `web_search_run_id`, and accumulated assistant text only in local variables. Persist enough state to rebuild them exactly after approval:

- normalized LangChain messages, including each AI `tool_calls` item and each `ToolMessage` with its `tool_call_id`;
- resolved choice/model/prompt settings;
- accumulated assistant content already shown to the user;
- metadata (`tools_used`, sources, citations, web-search run id);
- the pending tool call and its sequence number.

Prefer a versioned JSON format such as `{ "schema_version": 1, ... }`. Encrypt/redact secrets and sensitive tool arguments; never store access tokens or credentials in the checkpoint. If the state becomes large, store it in object storage and keep a reference/checksum in `chat_runs`.

## Message states and UI contract

Add at least `awaiting_approval`, `rejected`, and `expired` to the accepted application-level message statuses. Update `recent_messages()` deliberately: it should include only conversation content safe to send to the model. In particular, an unfinished assistant message should not be treated as a completed answer in a new user turn.

The client should render the streamed draft, show the approval request separately, then reconnect to the run stream after a decision. It must tolerate duplicate SSE events and should refresh thread history after terminal events.

## Delivery order

1. Implement the read-only policy and approval database schema/repositories.
2. Introduce `chat_runs` and use it for every newly created stream, without gating tools yet.
3. Add `approval.required` and stop the graph before one protected test tool; verify no side effect occurs.
4. Add authenticated, atomic approve/reject and resume logic.
5. Move resume execution to a worker/queue if the API will run with multiple workers or approvals may wait for long periods.
6. Add tests for approval/rejection, duplicate decisions, expiry, reconnect, process restart, authorization, and “tool executes exactly once.”

## Main design rule

HITL must be a persisted state machine: **propose -> save checkpoint -> decide -> atomically claim -> execute -> resume/finalize**. The original SSE stream is only a delivery channel, not the durable source of truth.
