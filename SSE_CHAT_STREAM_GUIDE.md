# SSE Guide For `/api/chat/stream`

## Purpose Of This Guide

This file explains only the streaming chat API:

- `POST /api/chat/stream`

It answers these doubts:

1. when SSE starts
2. what the SSE data means like your screenshot
3. when chat data is stored in DB
4. what `encode_sse_event` does
5. what `prepare_stream` and `finalize_stream` do

---

## 1. When SSE Starts

SSE starts after these backend steps are completed:

1. JWT user is validated
2. request body is validated
3. thread ownership is checked
4. `prepare_stream(...)` runs
5. FastAPI returns `StreamingResponse(..., media_type="text/event-stream")`
6. the async generator `event_stream()` starts yielding events

So SSE does **not** start at the exact first millisecond of the request.

It starts only after backend preparation is ready.

### In your current code

`prepare_stream(...)` runs before the first SSE event is sent.

That means:

- user message row is already created
- assistant draft row is already created
- previous context is prepared
- graph is ready

Then the first SSE event is sent:

- `message.created`

---

## 2. What The SSE Data Means In Your Screenshot

Your screenshot shows lines like:

- `message.created`
- `message.delta`
- `message.completed`

That is correct SSE event flow.

### A. `message.created`

This is the first event.

It means:

- backend created a real user message row
- backend created a real assistant draft row
- frontend can now replace temporary UI ids with database ids

Example meaning:

```text
message.created
{
  "thread_id": "...",
  "user_message": {...},
  "assistant_message": {...}
}
```

### B. `message.delta`

These are streaming chunks from the model.

Example from your screenshot:

- `"I"`
- `"am"`
- `"Code"`
- `"Bot"`

This does **not** mean each row is a full message.

It means:

- the assistant response is coming in small chunks
- frontend keeps appending each `delta` to the same assistant message

So if you receive:

```text
delta: "I"
delta: " am"
delta: " Code"
delta: "Bot"
```

frontend combines them into:

```text
I am CodeBot
```

### C. `message.completed`

This is the final success event.

It means:

- full assistant content is complete
- backend updated assistant row status to `completed`
- final content is now saved in DB

### Why SSE looks like many rows

Because SSE is an event stream, not one JSON response.

So instead of:

```json
{ "answer": "full text" }
```

you get:

```text
event 1 -> created
event 2 -> delta
event 3 -> delta
event 4 -> delta
event 5 -> completed
```

That is why your browser/network logs show many stream items.

---

## 3. When Chat Data Is Stored In DB

This is the most important part.

### Current behavior in your code

The data is stored in **two phases**.

### Phase 1. Stored Before Full Answer Completes

Inside `prepare_stream(...)`:

#### User message is stored immediately

- role = `user`
- status = `completed`

#### Assistant draft is stored immediately

- role = `assistant`
- content = `""`
- status = `streaming`

So the answer is:

- user chat is stored **before** streaming starts
- assistant draft row is also stored **before** full completion

### Phase 2. Assistant Final Content Is Stored After Stream Ends

Inside `finalize_stream(...)`:

- assistant content is updated with full response
- status becomes:
  - `completed`
  - `failed`
  - `stopped`

### So is it runtime or after complete?

Best exact answer:

- user message = stored immediately
- assistant draft = stored immediately
- assistant final text = stored after stream completes or fails or stops

So your API uses a **hybrid storage approach**.

### Why this is good

If stream crashes:

- user message is not lost
- assistant row still exists
- backend can mark it as `failed` or `stopped`

That is better than waiting until the whole response finishes.

---

## 4. What Is `encode_sse_event`

`encode_sse_event` is a helper function that converts normal Python data into valid SSE text format.

Current code:

```python
def encode_sse_event(event_name: str, payload: dict) -> str:
    return f"event: {event_name}\ndata: {json.dumps(payload, default=str)}\n\n"
```

### What it does

If you call:

```python
encode_sse_event(
    "message.delta",
    {"assistant_message_id": "m1", "delta": "Hello"}
)
```

it returns:

```text
event: message.delta
data: {"assistant_message_id":"m1","delta":"Hello"}

```

Important:

- `event:` = event name
- `data:` = event payload
- blank line at end = marks one SSE event is finished

### Why it is needed

SSE is not normal JSON.

Browser/client reads it as text stream with a specific format.

So `encode_sse_event` makes sure the response is written in correct SSE structure.

### Simple meaning

`encode_sse_event` = "convert Python dict into SSE event string"

---

## 5. What Does `prepare_stream`

`prepare_stream(...)` runs before streaming begins.

Its job is to prepare everything needed for the stream.

### In your current code it does these things

#### 1. Check thread exists for this user

If thread is not found:

- raises `KeyError("Thread not found")`

#### 2. Load recent messages

It loads previous user/assistant messages from that thread.

This helps send chat history into the LLM.

#### 3. Store current user message

It inserts a new DB row for the current user question.

#### 4. Create assistant draft row

It inserts a new DB row for assistant with:

- empty content
- status = `streaming`

#### 5. Load vector memory

It searches `pgvector` using the current query.

That produces `previous_context`.

#### 6. Build LLM message list

It converts recent saved chat messages into:

- `HumanMessage`
- `AIMessage`

and appends the current user query.

### Return value

It returns `ChatStreamContext`.

That object contains:

- `thread_id`
- `user_message`
- `assistant_message`
- `llm_messages`
- `previous_context`

### Simple meaning

`prepare_stream` = "do all setup work before the first SSE event is sent"

---

## 6. What Does `finalize_stream`

`finalize_stream(...)` runs after streaming ends, fails, or stops.

Its job is to close the lifecycle of the assistant message.

### In your current code it does these things

#### 1. Update assistant row

It updates the assistant message row with:

- final content
- final status
- error text if needed

### 2. Set final state

Possible final statuses:

- `completed`
- `failed`
- `stopped`

### 3. Store vector memory after success

If status is `completed` and content exists:

- store user message in vector memory
- store assistant message in vector memory

This is only for retrieval/memory search.

It is not the primary chat history.

### Simple meaning

`finalize_stream` = "finish the assistant message and save final result"

---

## 7. Full Lifecycle Of `/api/chat/stream`

Here is the complete flow:

### Step 1

Frontend sends:

```json
{
  "thread_id": "thread_1",
  "query": "what is your name?",
  "code": null,
  "mode": "chat"
}
```

### Step 2

Backend validates JWT user.

### Step 3

Backend calls `prepare_stream(...)`.

At this moment:

- user message saved in DB
- assistant draft saved in DB

### Step 4

SSE starts and backend sends:

- `message.created`

### Step 5

LLM starts generating and backend sends:

- `message.delta`
- `message.delta`
- `message.delta`

### Step 6

Backend accumulates full response in memory.

### Step 7

When generation finishes:

- backend calls `finalize_stream(...)`
- assistant row becomes `completed`
- final text is stored

### Step 8

Backend sends:

- `message.completed`

---

## 8. Difference Between SSE Data And DB Data

This is another common confusion.

### SSE data

SSE data is temporary transport data sent live to frontend.

Used for:

- real-time UI update
- typing/streaming effect

### DB data

DB data is permanent stored data.

Used for:

- sidebar history
- reloading old chats
- secure user-specific history

### Important point

Not every `message.delta` is stored as a separate DB row.

Current DB design stores:

- one user message row
- one assistant message row

The assistant row content is updated at finalization time.

---

## 9. Why This Design Is Better

### Better than storing only after full answer

Because:

- user message is not lost
- assistant draft is not lost
- failure/stopped state is possible

### Better than storing every token/chunk

Because:

- fewer DB writes
- simpler logic
- less database load

So current design is a good balance.

---

## 10. Short Answers To Your 5 Questions

### 1. When SSE starts

SSE starts after auth, request validation, thread check, and `prepare_stream(...)` complete.

### 2. What your screenshot means

It shows one chat stream lifecycle:

- `message.created` = DB rows created
- `message.delta` = partial assistant chunks
- `message.completed` = final saved answer

### 3. When chat is stored in DB

- user message: stored before stream starts
- assistant draft: stored before stream starts
- assistant final text: stored after stream ends/fails/stops

### 4. What `encode_sse_event` is

A helper that converts Python data into valid SSE text format.

### 5. What `prepare_stream` and `finalize_stream` are

- `prepare_stream` = setup before streaming
- `finalize_stream` = close and save final assistant result after streaming

---

## Final One-Line Summary

`/api/chat/stream` first creates DB rows, then streams SSE events live, then finalizes the assistant message in DB after generation completes, fails, or stops.

---

## 11. Deep Explanation Of `finalize_stream()` Line By Line

Yes, your understanding is correct.

`finalize_stream()` is mainly responsible for:

- updating the final assistant response in the main chat-history DB
- setting the final assistant status
- storing vector memory after successful completion

So this function does **two different jobs**:

1. finalize the main chat message row
2. push successful content into vector memory

### Current code

```python
def finalize_stream(
    self,
    *,
    user_id: int,
    thread_id: str,
    user_message_id: str,
    assistant_message_id: str,
    user_query: str,
    assistant_content: str,
    status: str,
    error_text: str | None = None,
):
    message = self.repository.finalize_message(
        message_id=assistant_message_id,
        content=assistant_content,
        status=status,
        error_text=error_text,
    )

    if message is None:
        return None

    if status == "completed" and assistant_content.strip():
        pg_vector_service = PGVectorService()
        pg_vector_service.store(
            user_id=user_id,
            text=user_query,
            type_="user_message",
            metadata={
                "thread_id": thread_id,
                "message_id": user_message_id,
                "role": "user",
            },
        )
        pg_vector_service.store(
            user_id=user_id,
            text=assistant_content,
            type_="assistant_message",
            metadata={
                "thread_id": thread_id,
                "message_id": assistant_message_id,
                "role": "assistant",
            },
        )

    return message
```

---

## 12. `finalize_stream()` Parameter Meaning

### `user_id`

Which authenticated user owns this chat.

Used when storing vector memory.

### `thread_id`

Which conversation thread this message belongs to.

Used in vector metadata.

### `user_message_id`

The already-created DB id of the current user message.

Used when storing vector metadata for the user query.

### `assistant_message_id`

The already-created DB id of the assistant draft message.

Used to update the final assistant row.

### `user_query`

The user’s text.

Used for vector storage after success.

### `assistant_content`

The final accumulated assistant response text.

This becomes the saved assistant content in the main DB.

### `status`

Final assistant state:

- `completed`
- `failed`
- `stopped`

### `error_text`

Optional error message if stream failed.

---

## 13. `finalize_stream()` Line By Line

### Function header

```python
def finalize_stream(...):
```

This defines the method that runs after streaming ends.

### First important block

```python
message = self.repository.finalize_message(
    message_id=assistant_message_id,
    content=assistant_content,
    status=status,
    error_text=error_text,
)
```

This is the first real action.

It calls the repository layer to update the assistant message row in the main relational database.

This means:

- find the assistant draft row by `assistant_message_id`
- replace empty draft content with final `assistant_content`
- set final `status`
- save `error_text` if present
- set `completed_at`

This is the main chat-history save step.

### Next block

```python
if message is None:
    return None
```

This is a safety check.

If repository could not find that assistant row:

- stop here
- do not continue to vector storage

Why this matters:

If the main message row does not exist, vector memory should also not be written because message linkage would be broken.

### Success-only vector block

```python
if status == "completed" and assistant_content.strip():
```

This means vector storage only happens when:

1. stream finished successfully
2. assistant response is not empty

So vector memory is **not** stored when:

- status is `failed`
- status is `stopped`
- assistant content is empty

### Create vector service

```python
pg_vector_service = PGVectorService()
```

This creates the vector service object.

It will:

- connect to pgvector-backed storage
- generate embeddings
- store searchable memory chunks

### Store user message in vector memory

```python
pg_vector_service.store(
    user_id=user_id,
    text=user_query,
    type_="user_message",
    metadata={
        "thread_id": thread_id,
        "message_id": user_message_id,
        "role": "user",
    },
)
```

This stores the user query in vector memory.

Important meaning:

- `user_id=user_id`
  - vector memory is scoped to this user
- `text=user_query`
  - actual text to embed and store
- `type_="user_message"`
  - labels this memory as user content
- `metadata={...}`
  - links this vector row back to real chat DB identifiers

Metadata meaning:

- `thread_id`
  - which chat thread it belongs to
- `message_id`
  - which user message row it came from
- `role`
  - confirms this vector row came from user text

### Store assistant message in vector memory

```python
pg_vector_service.store(
    user_id=user_id,
    text=assistant_content,
    type_="assistant_message",
    metadata={
        "thread_id": thread_id,
        "message_id": assistant_message_id,
        "role": "assistant",
    },
)
```

This stores the final assistant answer in vector memory.

It is the same pattern as user storage, but now:

- `text=assistant_content`
- `type_="assistant_message"`
- `message_id=assistant_message_id`
- `role="assistant"`

Why this is useful:

- future semantic search can find old assistant answers
- retrieval can use both user questions and assistant answers

### Final return

```python
return message
```

This returns the updated assistant DB row.

That returned object is later used by the API layer to send final SSE data like:

- `assistant_message_id`
- `status`
- `content`
- `completed_at`

---

## 14. Sub Function 1: `repository.finalize_message(...)`

This is the main DB update sub-function used by `finalize_stream()`.

### Current code

```python
def finalize_message(
    self,
    *,
    message_id: str,
    content: str,
    status: str,
    error_text: str | None = None,
    metadata_json: dict | None = None,
) -> ChatMessage | None:
    session = self.session_factory()
    now = datetime.utcnow()
    try:
        message = session.get(ChatMessage, message_id)
        if message is None:
            return None

        message.content = content
        message.status = status
        message.error_text = error_text
        message.metadata_json = metadata_json
        message.completed_at = now

        thread = session.get(ChatThread, message.thread_id)
        if thread is not None:
            thread.updated_at = now
            thread.last_message_at = now

        session.commit()
        session.refresh(message)
        return message
    finally:
        session.close()
```

### What each part does

#### `session = self.session_factory()`

Open a new SQLAlchemy DB session.

#### `now = datetime.utcnow()`

Create one shared timestamp for this finalize operation.

#### `message = session.get(ChatMessage, message_id)`

Find the assistant message row by id.

#### `if message is None: return None`

If row is missing, stop safely.

#### `message.content = content`

Save full assistant response text.

#### `message.status = status`

Set final state:

- completed
- failed
- stopped

#### `message.error_text = error_text`

Save stream error text if one exists.

#### `message.metadata_json = metadata_json`

Reserved extra metadata field.

#### `message.completed_at = now`

Mark when assistant finished or stopped.

#### `thread = session.get(ChatThread, message.thread_id)`

Load parent thread row.

#### `thread.updated_at = now`

Update thread modified time.

#### `thread.last_message_at = now`

Update latest message time for sidebar sorting.

#### `session.commit()`

Persist all DB changes.

#### `session.refresh(message)`

Reload the updated message object from DB.

#### `return message`

Return the saved assistant message.

#### `session.close()`

Always close DB session.

### Simple meaning

`repository.finalize_message()` = "save final assistant result in the main chat database"

---

## 15. Sub Function 2: `PGVectorService.store(...)`

This is the vector-storage sub-function used by `finalize_stream()`.

### Current code

```python
def store(
    self,
    user_id: int,
    text: str,
    type_: str,
    *,
    metadata: dict | None = None,
    user_session_id: str | None = None,
):
    session = self.Session()

    try:
        chunks = self.splitter.split_text(text)

        for chunk in chunks:
            embedding = self.embedding.embed_query(chunk)
            extra_metadata = {
                "timestamp": datetime.utcnow().isoformat()
            }

            if metadata:
                extra_metadata.update(metadata)

            row = VectorData(
                id=str(id.id4()),
                user_session_id=user_session_id,
                user_id=user_id,
                content=chunk,
                embedding=embedding,
                type=type_,
                extra_metadata=extra_metadata,
            )

            session.add(row)

        session.commit()

    except Exception as e:
        session.rollback()
        raise

    finally:
        session.close()
```

### What each part does

#### `session = self.Session()`

Open vector DB session.

#### `chunks = self.splitter.split_text(text)`

Split long text into smaller chunks.

Why:

- embeddings often work better on smaller pieces
- search later becomes more useful

#### `for chunk in chunks:`

Process each chunk one by one.

#### `embedding = self.embedding.embed_query(chunk)`

Generate embedding vector for that text chunk.

This is what makes semantic search possible.

#### `extra_metadata = {"timestamp": ...}`

Start metadata with save time.

#### `if metadata: extra_metadata.update(metadata)`

Merge custom metadata passed from `finalize_stream()`.

That is where these values are attached:

- `thread_id`
- `message_id`
- `role`

#### `row = VectorData(...)`

Create one vector DB row.

Main fields:

- `id`
- `user_id`
- `content`
- `embedding`
- `type`
- `extra_metadata`

#### `session.add(row)`

Queue row for insert.

#### `session.commit()`

Save all vector rows.

#### `session.rollback()`

Undo partial vector writes if error happens.

#### `session.close()`

Close DB session.

### Simple meaning

`PGVectorService.store()` = "turn text into embeddings and save searchable vector memory rows"

---

## 16. Very Important Distinction

### Main DB save

This happens first through:

- `self.repository.finalize_message(...)`

This stores the real assistant response in chat history.

### Vector save

This happens only after successful completion through:

- `pg_vector_service.store(...)`

This stores semantic-search memory.

So:

- main DB = source of truth for chat history
- vector DB = secondary memory for retrieval

---

## 17. Short Final Answer To Your Doubt

Yes.

`finalize_stream()` first saves the full assistant response in the main chat-history DB, and after that, if status is `completed`, it also stores the user query and assistant answer in vector memory using `PGVectorService.store(...)`.
