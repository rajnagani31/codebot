# Codebot Web Search - Bug Report & Proposed Fixes

**Date:** 2026-04-06
**Scope:** OpenAIToolGraph, web search tools, system prompts, flow naming
**Status:** Review only - no changes applied

---

## TABLE OF CONTENTS

1. [How Web Search Currently Works](#1-how-web-search-currently-works)
2. [Bug #1: Flow Names Are Outdated (LangGraph references)](#bug-1-flow-names-are-outdated)
3. [Bug #2: Safety Guard Commented Out](#bug-2-safety-guard-commented-out-in-web_search-execution)
4. [Bug #3: LLM Does Not Call read_web_page After web_search](#bug-3-llm-does-not-call-read_web_page-after-web_search)
5. [Bug #4: System Prompts Missing web_search Guidance in Most Modes](#bug-4-system-prompts-missing-web_search-guidance-in-most-modes)
6. [Bug #5: web_search Already Fetches Pages - read_web_page Is Redundant](#bug-5-web_search-already-fetches-pages-internally)
7. [Bug #6: Summarize Is Simple Truncation, Not Intelligent](#bug-6-summarize-is-simple-truncation-not-intelligent)
8. [Summary of All Proposed Changes](#summary-of-all-proposed-changes)

---

## 1. How Web Search Currently Works

### Complete Flow When `web_enabled=True`

```
User sends message (web_mode="on" or "auto")
    |
    v
OpenAIToolGraph.__init__()
    |-- Creates WebSearchService()
    |-- build_tools() includes web_search + read_web_page tools
    |-- LLM bound with ALL tools (base + web)
    |
    v
run_stream() starts the agentic loop
    |
    v
System prompt built with web guidance included
    |
    v
LLM receives message + tool schemas
    |
    v
LLM decides: call web_search(query="...") ?
    |
   YES
    |
    v
_execute_tool_call_events("web_search")
    |
    v
WebSearchService.search()
    |-- Step 1: DuckDuckGoSearchProvider.search(query, max_results=3)
    |       |-- Fetches HTML from https://html.duckduckgo.com/html/?q=...
    |       |-- Parses HTML to extract top 3 results (title, url, snippet)
    |
    |-- Step 2: WebContentService.fetch_many(urls)  <-- FETCHES ALL 3 PAGES
    |       |-- For each URL, downloads full HTML
    |       |-- Extracts clean text using BeautifulSoup
    |       |-- Builds preview (first ~1600 chars)
    |
    |-- Step 3: WebContentService.summarize() for each source
    |       |-- Simple text truncation to ~420 chars (NOT AI-powered)
    |
    |-- Step 4: store_sources() - saves to DB + PGVector
    |
    |-- Step 5: build_context_pack() - formats results for LLM
    |       Returns: { run_id, query, sources[], context_text }
    |
    v
ToolMessage sent back to LLM with:
    {
      "query": "...",
      "context": "[1] Title (domain)\nURL: ...\nSummary: ...\n\n[2]...",
      "sources": [{ rank, title, url, domain, snippet, summary, content_preview }]
    }
    |
    v
LLM reads the context and generates final answer
    |
    v
(LLM MAY also call read_web_page for a specific URL - but rarely does)
    |
    v
_build_metadata() classifies the flow and returns complete event
```

### How read_web_page Works (Separately)

```
LLM decides to call read_web_page(url="https://...")
    |
    v
_execute_tool_call_events("read_web_page")
    |
    v
WebSearchService.read_web_page(url)
    |-- WebContentService.fetch_and_extract(url)
    |       |-- Downloads full HTML
    |       |-- Extracts clean text + preview
    |-- summarize() - truncates to 520 chars
    |
    v
Returns to LLM: { title, url, summary, content_preview, content_text }
```

### Key Finding: web_search vs read_web_page

**web_search already fetches and reads all 3 pages internally** via `fetch_many()`.
The LLM receives summaries + content_preview for all 3 URLs.

**read_web_page** is a separate tool the LLM can call independently on any URL.
But the LLM rarely calls it after web_search because it already got content.

**They are called SEPARATELY by the LLM** - the LLM decides on its own whether
to call one, the other, or both. There is no automatic chaining.

---

## BUG #1: Flow Names Are Outdated

**File:** `openai_tool_graph.py` lines 271-278

### Current Code

```python
if web_tools_used and non_web_tools_used:
    execution_mode = "agent_with_web_search_flow"    # references LangGraph
elif web_tools_used:
    execution_mode = "web_search_flow"               # OK
elif non_web_tools_used:
    execution_mode = "langgraph_agent_flow"           # references LangGraph
else:
    execution_mode = "llm_only_flow"                  # OK
```

### Problem

- `"langgraph_agent_flow"` - LangGraph has been removed from the codebase. This name is misleading.
- `"agent_with_web_search_flow"` - Also implies LangGraph connection. Confusing since only OpenAI tool calling is used now.

### Proposed Fix

```python
if web_tools_used and non_web_tools_used:
    execution_mode = "tool_with_web_search_flow"
elif web_tools_used:
    execution_mode = "web_search_flow"
elif non_web_tools_used:
    execution_mode = "tool_flow"
else:
    execution_mode = "llm_only_flow"
```

### Files to Change

| File | Change |
|------|--------|
| `openai_tool_graph.py` line 272 | `"agent_with_web_search_flow"` -> `"tool_with_web_search_flow"` |
| `openai_tool_graph.py` line 276 | `"langgraph_agent_flow"` -> `"tool_flow"` |
| **Frontend** (if any) | Search for these old flow names and update display logic |
| **Database** | Existing metadata rows still have old names - decide if migration needed |

### Risk

LOW - these are metadata labels only, no logic depends on them.
Check frontend to confirm it doesn't render different UI based on these strings.

---

## BUG #2: Safety Guard Commented Out in web_search Execution

**File:** `openai_tool_graph.py` lines 163-166

### Current Code

```python
if tool_name == "web_search":
    # self.web_search_service = None
    # if self.web_search_service is None:
    #     raise RuntimeError("Web search is not enabled")
```

### Problem

The null-check safety guard for `web_search_service` is **commented out**.
If somehow `web_search` is called when `web_search_service is None`, it will crash with
an `AttributeError` on line 174 (`await self.web_search_service.search(...)`) instead of
a clean error message.

Note: `read_web_page` (line 208) still has its guard active.

### Proposed Fix

Uncomment the safety guard:

```python
if tool_name == "web_search":
    if self.web_search_service is None:
        raise RuntimeError("Web search is not enabled")
```

Also remove the debug comment `# self.web_search_service = None`.

### Files to Change

| File | Change |
|------|--------|
| `openai_tool_graph.py` lines 164-166 | Uncomment the null check, remove debug line |

### Risk

NONE - this is a safety guard restoration.

---

## BUG #3: LLM Does Not Call read_web_page After web_search

### Problem

When the LLM calls `web_search`, it gets back summaries (truncated ~420 chars) and
content_preview (~1600 chars) for each source. But this is often not enough information
to give a complete answer.

The LLM **should** call `read_web_page` on specific URLs when the summary is insufficient,
but it almost never does because:

1. **The system prompt gives weak guidance** - it only says "Use `read_web_page` when a
   specific URL needs deeper inspection" which is vague.
2. **The web_search result already includes partial content**, so the LLM thinks it has
   enough.
3. **No prompt tells the LLM to evaluate if the summaries are sufficient.**

### Root Cause Analysis

Actually, this is a **design question**, not purely a bug. Looking at the code:

**web_search already fetches full page content internally:**

```python
# WebSearchService.search() line 38
fetched_pages = await self.content_service.fetch_many(urls)  # fetches ALL pages
```

But then it only sends truncated summaries to the LLM:

```python
# build_context_pack() lines 114-116
source_lines = [
    f"[{rank}] {title} ({domain})\nURL: {url}\nSummary: {summary}"
    ...
]
```

The `summary` is only ~420 chars (truncated, not AI-summarized).
The `content_preview` (~1600 chars) IS included in the sources array but may not be
enough for the LLM to fully answer.

### Two Possible Approaches

**Approach A: Better system prompt (simple)**

Update the system prompt to instruct the LLM to call `read_web_page` when web_search
summaries are insufficient. This is the simpler fix.

**Approach B: Send more content from web_search directly (better)**

Since `web_search` already downloads full pages, send more content to the LLM directly
in the `context_text`. This avoids an extra LLM round-trip.

### Proposed Fix: Approach A + B Combined

**A. Update system prompt** (`system_prompt.py`):

In `_web_context_guidance()` when `web_enabled=True`:

```python
web_block = """
Web search tools are available.
- Use `web_search` to find current information. It returns summaries of top results.
- After web_search, if a summary is too short or unclear to answer fully,
  call `read_web_page` on that URL to get the complete page content.
- Use `read_web_page` directly when you already have a specific URL to read.
- Always cite sources with their URLs in your answer.
"""
```

**B. Include content_preview in context_text** (`web_search_service.py`):

```python
# build_context_pack() - include more content
source_lines = [
    f"[{source['rank']}] {source['title']} ({source['domain']})\n"
    f"URL: {source['url']}\n"
    f"Summary: {source['summary']}\n"
    f"Content: {source['content_preview']}"
    for source in source_summaries
]
```

### Files to Change

| File | Change |
|------|--------|
| `system_prompt.py` | Update `_web_context_guidance()` web_block text |
| `web_search_service.py` | Include `content_preview` in `build_context_pack()` context_text |

### Risk

MEDIUM - sending more content increases token usage. The `content_preview` is ~1600
chars per source x3 = ~4800 extra chars. This is acceptable but monitor costs.

---

## BUG #4: System Prompts Missing web_search Guidance in Most Modes

### Problem

The web search tool guidance (`_web_context_guidance()`) is **only included in the
`_chat_prompt`**. The other prompts (`code`, `debug`, `review`) do NOT call this function.

### Current State

| Prompt Mode | Calls `_web_context_guidance()`? | Has web guidance? |
|-------------|----------------------------------|-------------------|
| `chat`      | YES                              | Full guidance     |
| `code`      | NO                               | Only inline conditional strings |
| `debug`     | NO                               | Only inline conditional strings |
| `review`    | NO                               | Only inline conditional strings |
| `web_research` | NO (hardcoded)               | Hardcoded guidance |

The `code`, `debug`, and `review` prompts have only thin conditional lines like:
```python
"- Prefer current web references for package, library, or API questions." if web_preferred else ""
```

But they **never tell the LLM about the `web_search` and `read_web_page` tools** or
when to use them.

### Impact

When user selects `code`, `debug`, or `review` mode with web ON, the LLM has web tools
available but the system prompt **doesn't mention they exist**. The LLM may or may not
discover them from the tool schemas alone. This makes web search behavior inconsistent
across modes.

### Proposed Fix

Add `_web_context_guidance()` call to ALL prompt builders:

```python
def _code_prompt(...) -> str:
    web_block = _web_context_guidance(web_enabled, web_preferred, current_info_requested)
    return f"""
You are Codebot, a senior software engineer focused on implementation quality.
...
{web_block}
{_shared_context(previous_context)}
"""
```

Same for `_debug_prompt` and `_review_prompt`.

### Files to Change

| File | Change |
|------|--------|
| `system_prompt.py` `_code_prompt()` | Add `web_block = _web_context_guidance(...)` and include in template |
| `system_prompt.py` `_debug_prompt()` | Same |
| `system_prompt.py` `_review_prompt()` | Same |

### Risk

LOW - this only adds guidance text to the system prompt. It won't break anything,
it will just make the LLM more aware of its tools.

---

## BUG #5: web_search Already Fetches Pages Internally

### Problem (Design Issue)

`WebSearchService.search()` already downloads and extracts content from ALL 3 result URLs:

```python
fetched_pages = await self.content_service.fetch_many(urls)  # line 38
```

But only sends truncated summaries (~420 chars) to the LLM. The full `content_text`
is stored in the database and PGVector but NOT sent to the LLM.

Then the LLM would need to call `read_web_page` to re-download the same page it already
downloaded. This is **wasted work** - the page was already fetched and extracted.

### Proposed Fix

Option 1: Send more content from web_search directly (covered in Bug #3 Approach B).

Option 2: Cache fetched pages so `read_web_page` doesn't re-download:

```python
# In OpenAIToolGraph or WebSearchService, cache fetched page content
# so read_web_page can reuse it instead of re-fetching
```

Option 2 is more complex and may not be needed if Option 1 sends enough content.

### Files to Change

| File | Change |
|------|--------|
| `web_search_service.py` `build_context_pack()` | Include `content_preview` in context_text (same as Bug #3B) |

### Risk

LOW - same as Bug #3.

---

## BUG #6: Summarize Is Simple Truncation, Not Intelligent

### Current Code

```python
# content_extractor.py lines 274-293
def summarize(self, *, query, title, snippet, content, max_chars=420) -> str:
    text = " ".join(part for part in [snippet, content] if part).strip()
    text = re.sub(r"\s+", " ", text)
    summary = text[:max_chars].rsplit(" ", 1)[0].strip()
    return summary or text[:max_chars]
```

### Problem

This is just **character truncation**, not summarization. It takes the first 420 characters
of `snippet + content` and cuts at a word boundary. This means:

- If the page has a long header/navigation text before the actual content, the "summary"
  will be garbage.
- The summary is not query-aware - it doesn't find the most relevant section.

### Impact

The LLM gets poor-quality summaries from web_search, making it harder to answer well.
This also contributes to Bug #3 (LLM not having enough info).

### Proposed Fix

This is a larger improvement - not a quick fix. Two options:

**Option A (Simple):** Increase `max_chars` from 420 to 800-1000 and use `content_preview`
(which is already better structured, ~1600 chars).

**Option B (Better):** Use the LLM itself to summarize. Send the extracted content
to a fast/cheap model (gpt-4o-mini) with the query to get a query-relevant summary.
This adds latency and cost but gives much better results.

### Files to Change

| File | Change |
|------|--------|
| `content_extractor.py` `summarize()` | Option A: increase max_chars |
| `web_search_service.py` | Option B: add LLM-based summarization step |

### Risk

Option A: NONE. Option B: MEDIUM (adds latency + API cost per search).

---

## Summary of All Proposed Changes

### Priority Order

| # | Bug | Severity | Effort | Files |
|---|-----|----------|--------|-------|
| 1 | Safety guard commented out | HIGH | 1 min | `openai_tool_graph.py` |
| 2 | System prompts missing web guidance | HIGH | 5 min | `system_prompt.py` |
| 3 | Flow names reference LangGraph | LOW | 5 min | `openai_tool_graph.py` + frontend check |
| 4 | LLM doesn't call read_web_page | MEDIUM | 10 min | `system_prompt.py` + `web_search_service.py` |
| 5 | web_search fetches pages but sends truncated data | MEDIUM | 10 min | `web_search_service.py` |
| 6 | Summarize is simple truncation | LOW | varies | `content_extractor.py` |

### Quick Wins (can apply immediately)

1. **Uncomment safety guard** in `openai_tool_graph.py` line 164-166
2. **Add `_web_context_guidance()`** to `code`, `debug`, `review` prompts
3. **Rename flow names** to remove LangGraph references

### Requires Design Decision

4. **How much content to send from web_search** - increase `content_preview` in context?
5. **Whether to improve summarization** - truncation vs LLM-based summary
6. **Whether to cache fetched pages** for read_web_page reuse

---

### File Change Map

```
backend/bot/workflow/openai_flow/openai_tool/openai_tool_graph.py
  - Line 164-166: Uncomment safety guard
  - Line 272: "agent_with_web_search_flow" -> "tool_with_web_search_flow"
  - Line 276: "langgraph_agent_flow" -> "tool_flow"

backend/bot/workflow/openai_flow/system/system_prompt.py
  - _web_context_guidance(): Improve web tool instructions
  - _code_prompt(): Add web_block variable and include in template
  - _debug_prompt(): Add web_block variable and include in template
  - _review_prompt(): Add web_block variable and include in template

backend/bot/application/service/web_search_service.py
  - build_context_pack(): Include content_preview in context_text

backend/bot/workflow/web/content_extractor.py
  - summarize(): Increase max_chars (optional improvement)
```
