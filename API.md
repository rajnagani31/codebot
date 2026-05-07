# API Guide

## Overview

This project now uses JWT-protected chat APIs.

Main idea:

- frontend first creates or restores a guest session
- backend returns a JWT token
- frontend sends that token in `Authorization: Bearer <token>`
- every thread and message belongs to the authenticated user from that token

Base prefix:

- auth APIs: `/api/auth/...`
- chat history APIs: `/api/...`
- stream API: `/api/chat/stream`

---

## Auth Rule For Protected APIs

These APIs require JWT:

- `GET /api/auth/me`
- `POST /api/threads`
- `GET /api/threads`
- `GET /api/threads/{thread_id}/messages`
- `POST /api/chat/stream`

Required header:

```http
Authorization: Bearer <jwt_token>
```

If token is missing or invalid:

- response is `401 Unauthorized`

---

## 1. `POST /api/auth/guest`

### What it does

Creates a new guest user session and returns a JWT token.

This is the first API the frontend should call if no token is already stored.

### Why it exists

Before this API, the frontend used a local fake `user_id`.

Now this API creates a real backend user record and gives the browser a signed token.

### Request

No request body is required.

Example:

```http
POST /api/auth/guest
```

### Response

```json
{
  "token": "jwt-token-here",
  "user_id": 1,
  "session_label": "a1b2c3d4e5f6",
  "expires_at": 1774470000
}
```

### Meaning of fields

- `token`: JWT used for later protected APIs
- `user_id`: backend user id
- `session_label`: short backend session label
- `expires_at`: unix timestamp when token expires

### Typical frontend use

1. Call `POST /api/auth/guest`
2. Save `token` in `localStorage`
3. Use that token for all next API calls

---

## 2. `GET /api/auth/me`

### What it does

Returns the current authenticated user from the JWT token.

### Why it exists

Used to verify that a stored token is still valid.

If frontend restarts, it can call this API with the saved JWT instead of creating a new guest session every time.

### Request

```http
GET /api/auth/me
Authorization: Bearer <jwt_token>
```

### Response

```json
{
  "id": 1,
  "session_label": "a1b2c3d4e5f6"
}
```

### When to use it

- app startup
- token restore check
- auth validation

---

## 3. `POST /api/threads`

### What it does

Creates a new chat thread for the authenticated user.

### Why it exists

One thread means one conversation.

Messages are stored under a thread id.

### Request

```http
POST /api/threads
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

```json
{
  "title": "Debug API issue",
  "mode": "chat",
  "client_session_id": "session-123"
}
```

### Request fields

- `title`: thread name shown in sidebar
- `mode`: one of `chat`, `code`, `debug`, `review`
- `client_session_id`: optional browser-side session id

### Response

```json
{
  "id": "thread_id",
  "title": "Debug API issue",
  "mode": "chat",
  "updated_at": "2026-03-26T10:00:00.000000",
  "last_message_at": null,
  "preview": "",
  "message_count": 0
}
```

### When frontend uses it

- user clicks `New chat`
- user sends first message and no active thread exists yet

---

## 4. `GET /api/threads`

### What it does

Returns all chat threads for the current authenticated user.

### Why it exists

This powers the chat sidebar.

### Request

```http
GET /api/threads
Authorization: Bearer <jwt_token>
```

### Response

```json
[
  {
    "id": "thread_1",
    "title": "Debug API issue",
    "mode": "debug",
    "updated_at": "2026-03-26T10:00:00.000000",
    "last_message_at": "2026-03-26T10:01:20.000000",
    "preview": "Check your request headers first...",
    "message_count": 4
  }
]
```

### Meaning of fields

- `id`: thread id
- `title`: sidebar title
- `mode`: current mode for that conversation
- `updated_at`: last thread update time
- `last_message_at`: last message time
- `preview`: latest message preview text
- `message_count`: total messages in the thread

### Frontend use

- load sidebar on startup
- refresh sidebar after a message finishes streaming

---

## 5. `GET /api/threads/{thread_id}/messages`

### What it does

Returns all saved messages for one thread.

### Why it exists

This loads the actual conversation when the user clicks a thread in the sidebar.

### Request

```http
GET /api/threads/thread_1/messages
Authorization: Bearer <jwt_token>
```

### Response

```json
[
  {
    "id": "msg_1",
    "role": "user",
    "content": "Why is my API failing?",
    "status": "completed",
    "created_at": "2026-03-26T10:00:00.000000",
    "completed_at": null
  },
  {
    "id": "msg_2",
    "role": "assistant",
    "content": "Check the auth header first.",
    "status": "completed",
    "created_at": "2026-03-26T10:00:01.000000",
    "completed_at": "2026-03-26T10:00:03.000000"
  }
]
```

### Message fields

- `id`: message id
- `role`: `user` or `assistant`
- `content`: saved message text
- `status`: `completed`, `streaming`, `failed`, `stopped`
- `created_at`: row created time
- `completed_at`: assistant finish time if available

### Error case

If the thread does not belong to the current user:

- response is `404 Thread not found`

---

## 6. `POST /api/chat/stream`

### What it does

This is the main chat API.

It:

1. validates JWT user
2. checks the thread belongs to that user
3. stores the user message immediately
4. creates an empty assistant draft with `status="streaming"`
5. runs the LLM graph
6. streams assistant chunks back to frontend
7. finalizes the assistant message as:
   - `completed`
   - `failed`
   - `stopped`
8. stores vector memory after success

### Why `/chat/stream` is important

It is not a normal JSON API.

It returns a streaming response with `text/event-stream`.

That means the frontend receives events while the assistant is still generating.

### Request

```http
POST /api/chat/stream
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

```json
{
  "thread_id": "thread_id",
  "query": "why is my api failing",
  "code": "optional code here",
  "mode": "debug"
}
```

### Request fields

- `thread_id`: target conversation
- `query`: current user message
- `code`: optional code context
- `mode`: one of `chat`, `code`, `debug`, `review`

### Response type

```http
Content-Type: text/event-stream
```

This means the response is a stream of SSE events.

---

## `/api/chat/stream` Event Types

### A. `message.created`

Sent once at stream start.

Purpose:

- tells frontend that backend created real database rows
- returns real ids for user message and assistant message

Example:

```text
event: message.created
data: {"thread_id":"thread_1","user_message":{"id":"m1","role":"user","content":"hello","status":"completed","created_at":"2026-03-26T10:00:00"},"assistant_message":{"id":"m2","role":"assistant","content":"","status":"streaming","created_at":"2026-03-26T10:00:00"}}
```

Frontend action:

- replace temporary local message ids with backend ids

### B. `message.delta`

Sent many times during generation.

Purpose:

- streams assistant text chunk by chunk

Example:

```text
event: message.delta
data: {"thread_id":"thread_1","assistant_message_id":"m2","delta":"Check "}
```

Frontend action:

- append `delta` text to current assistant message content

### C. `message.completed`

Sent once when generation ends successfully.

Purpose:

- marks the assistant row as completed
- returns final saved content

Example:

```text
event: message.completed
data: {"thread_id":"thread_1","assistant_message_id":"m2","status":"completed","content":"Check your auth header first.","completed_at":"2026-03-26T10:00:03"}
```

Frontend action:

- set assistant message `status="completed"`
- sync final content

### D. `message.failed`

Sent if streaming or generation fails.

Purpose:

- marks assistant row as failed
- returns partial content if any

Example:

```text
event: message.failed
data: {"thread_id":"thread_1","assistant_message_id":"m2","status":"failed","error":"provider error","content":"partial text"}
```

Frontend action:

- show error
- keep partial response if available
- set message status to `failed`

### E. Stopped Case

If user clicks Stop, backend finalizes assistant row as `stopped`.

In the current implementation, frontend aborts the request and then reloads thread data from backend.

So stopped state is mainly recovered by reloading stored messages after abort.

---

## Full Frontend Flow

### App startup

1. Read JWT token from `localStorage`
2. If token exists, call `GET /api/auth/me`
3. If token is invalid, call `POST /api/auth/guest`
4. Save returned token
5. Call `GET /api/threads`
6. Show sidebar

### When user opens a thread

1. Call `GET /api/threads/{thread_id}/messages`
2. Render full message history

### When user sends a new message

1. If no active thread, call `POST /api/threads`
2. Add temporary optimistic user/assistant messages in UI
3. Call `POST /api/chat/stream`
4. Handle `message.created`
5. Handle `message.delta`
6. Handle `message.completed` or `message.failed`
7. Refresh with:
   - `GET /api/threads`
   - `GET /api/threads/{thread_id}/messages`

---

## How Security Works

### Before

Old logic trusted browser `user_id`.

That was weak because anyone could send another user id manually.

### Now

Backend gets user identity only from JWT.

That means:

- browser cannot choose a different `user_id`
- thread access is checked against authenticated user
- message history is user-scoped

### Important note

Current login style is guest JWT session, not full username/password auth.

So it is much safer than raw `user_id`, but still not a full account system yet.

For production, next upgrade should be:

- real login/signup
- hashed passwords
- refresh tokens
- token rotation

---

## Message Status Meaning

### `completed`

- message finished normally

### `streaming`

- assistant draft exists and is currently generating

### `failed`

- generation crashed or provider failed

### `stopped`

- user aborted streaming before completion

### `pending`

- reserved for future use if needed

---

## Database Meaning Behind The APIs

### Auth APIs

Work with:

- `chat_users`

### Thread APIs

Work with:

- `chat_threads`

### Message APIs

Work with:

- `chat_messages`

### Vector memory

After successful stream, user and assistant content are also stored in vector memory for retrieval.

That vector storage is secondary memory, not the main source of truth for the sidebar.

---

## Common Errors

### `401 Unauthorized`

Reason:

- missing JWT
- invalid JWT
- expired JWT

### `404 Thread not found`

Reason:

- wrong thread id
- thread belongs to another user

### `500 Setup error: ...`

Reason:

- LLM setup problem
- DB problem
- service initialization issue

### `message.failed`

Reason:

- stream failed after request already started
- provider or graph error during generation

---

## Quick Summary

### Auth APIs

- `POST /api/auth/guest`: create guest JWT session
- `GET /api/auth/me`: validate current token and get user info

### Thread APIs

- `POST /api/threads`: create chat thread
- `GET /api/threads`: list sidebar threads
- `GET /api/threads/{thread_id}/messages`: load one chat history

### Chat API

- `POST /api/chat/stream`: save user message, stream assistant reply, finalize stored assistant message

### Most important API

`/api/chat/stream` is the main live chat endpoint.

It is responsible for:

- persistence
- streaming
- assistant generation
- final message state
- vector memory save after success
