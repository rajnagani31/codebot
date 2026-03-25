# Vector service over view

### Over goal

- when user ask a qestion to somthing generat and direact appling in system if creating in past by llm then vector find some information for same task(user query) and information and this information send to llm to create more good and updated answers 

### over flow

user query (for cli and chatbot)
↓
search information using query vector in DB (Qdrant)
↓
end send 5 data list from vector result
↓
all things coming in LLM 🧠 (here llm have -> user query + information according user need + system message + tools)
↓
llm apply tools if need otherwise the generat new information based on data
↓
llm generate new answer they stord in db with user query and AI response in vector DB
↓
user get a streming response

### why codebot use this flow?

1. LLM get past information according user need for know what fail and what success like (many command fail to creat a django project and some command work to create and setup a over django project)

2. what does exectly work here for this kind of task aspecially for CLI

3. remmeber user information and chat history

### Proc and cons for this flow

#### Proc

- LLM get past information for same task or query 
- LLM know about full chat history
- know about a user details and what they like and unlike

#### Cons

- LLM not get current session past information (vector return only same vector according query not 5 last message history)


# Another Memory Architecture

User → Thread → Short-term memory → Long-term memory (vector DB)
                              ↓
                        Context Builder
                              ↓
                             LLM


1️⃣ THREAD MEMORY (Session / Chat History)

-> like chatgpt sidebar
'Each conversation =  thread


#### Structre:
```bash
{
  "thread_id": "abc123",
  "thread_title: "ORM error"
  "user_id": 1,
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "ai", "content": "..."}
  ]
}
```
2️⃣ SHORT-TERM MEMORY (Last N messages)

👉 Used for immediate reasoning

```
Exmaple:
last_5_messages = [
    "User: ...",
    "AI: ...",
]
```

✔ Stored in DB (Postgres / Mongo)
✔ NOT vectorized
✔ Always passed to LLM

3️⃣ LONG-TERM MEMORY (Qdrant — what you built)

👉 Used for:
    - remebering facts
    - perfernces
    - past conversations

✔ semantic search
✔ filtered by user_id
✔ stored as "User + AI"

# ⚙️ FINAL FLOW (VERY IMPORTANT)


User Query
   ↓
1. Load Thread History (last 5–10 msgs)
   ↓
2. Search Qdrant (top 3 memories)
   ↓
3. Build Context
   ↓
4. Send to LLM
   ↓
5. Store response:
   - Thread DB
   - Qdrant (long-term)


# 🔥 FINAL ARCHITECTURE (Your Bot Now)


             ┌───────────────┐
             │   Thread DB   │  ← short-term
             └──────┬────────┘
                    ↓
User → Context Builder → LLM → Response
                    ↑
             ┌──────┴────────┐
             │   Qdrant DB   │  ← long-term
             └───────────────┘


# 🧠 What You Just Built

✔ ChatGPT-style memory
✔ Personalized responses
✔ Context-aware reasoning
✔ Scalable architecture