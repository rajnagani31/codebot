# PR Review Agent - Complete Architecture & Implementation Roadmap

## Overview
Building an intelligent PR review agent that integrates with GitHub, GitLab, and Bitbucket to automatically analyze code changes and post reviews using OpenAI GPT.

---

## Phase 1: Foundation & Architecture (Week 1)
**Goal:** Set up core infrastructure and data models

### Tasks (Do These First):
1. **Project Structure Setup**
   - Create configuration management system
   - Set up environment variables (.env, secrets management)
   - Create logging infrastructure
   - Set up error handling & monitoring

2. **Data Models** (Python Dataclasses/Pydantic)
   - `ReviewConfig` - Review rules and focus areas
   - `CodeChange` - File diff, language, metrics
   - `ReviewFinding` - Issue, severity, location, suggestion
   - `ReviewReport` - Aggregated findings and summary
   - `Platform` - GitHub/GitLab/Bitbucket metadata

3. **Core Interfaces**
   - `AIProvider` (abstract base for LLM integration)
   - `PlatformAdapter` (abstract for GitHub/GitLab/Bitbucket)
   - `ReviewEngine` (orchestrator)

---

## Phase 2: AI Integration (Week 2)
**Goal:** Connect to OpenAI and create review generation logic

### Tasks:
1. **OpenAI Integration**
   - GPT API client wrapper
   - Prompt engineering for code reviews
   - Token limit handling & chunking
   - Response parsing & validation

2. **Review Generation Engine**
   - Analyze code changes
   - Generate findings (bugs, security, style, performance)
   - Prioritize findings by severity
   - Create actionable suggestions

3. **Configurable Review Rules**
   - Define what to check (security, performance, style, etc.)
   - Severity levels mapping
   - Category-based review focus

---

## Phase 3: Platform Integrations (Week 3)
**Goal:** Connect to GitHub, GitLab, and Bitbucket

### Tasks:
1. **GitHub Adapter**
   - OAuth/PAT authentication
   - Fetch PR details & diffs
   - Post reviews as comments
   - Handle GitHub API rate limits

2. **GitLab Adapter**
   - GitLab API authentication
   - Fetch MR details & diffs
   - Post MR discussions/notes
   - Handle GitLab API rate limits

3. **Bitbucket Adapter**
   - Bitbucket API authentication
   - Fetch PR details & diffs
   - Post PR comments
   - Handle Bitbucket rate limits

---

## Phase 4: Webhook System (Week 4)
**Goal:** Real-time PR event handling

### Tasks:
1. **Webhook Server**
   - FastAPI/Flask endpoint for events
   - GitHub webhook handler (push, PR opened/updated)
   - GitLab webhook handler
   - Bitbucket webhook handler

2. **Event Processing**
   - Queue system (Redis/Celery for async processing)
   - Webhook signature verification
   - Deduplication logic

3. **Security**
   - HMAC signature validation
   - API key management
   - Rate limiting

---

## Phase 5: Advanced Features (Week 5)
**Goal:** Polish and optimize

### Tasks:
1. **Caching & Performance**
   - Cache review results
   - Avoid duplicate reviews
   - Optimize diff processing

2. **Filtering & Custom Rules**
   - Language-specific rules (Python, JS, Go, etc.)
   - File path exclusions (.md, .yml, etc.)
   - Review scope configuration

3. **Reporting & Analytics**
   - Track review metrics
   - Generate insights
   - Dashboard for monitoring

---

## Directory Structure

```
pr_reviewer_agent/
├── apps/
│   └── code_reviewer/
│       ├── model/              # Data models
│       │   ├── code_change.py
│       │   ├── review_finding.py
│       │   ├── review_report.py
│       │   ├── pull_request.py
│       │   ├── artifact_ref.py
│       │   └── review_job.py
│       ├── service/            # Business logic
│       │   ├── ai/
│       │   │   ├── openai_provider.py
│       │   │   ├── prompt_engine.py
│       │   │   └── ai_service.py
│       │   ├── platform/
│       │   │   ├── github_adapter.py
│       │   │   ├── gitlab_adapter.py
│       │   │   ├── bitbucket_adapter.py
│       │   │   └── platform_factory.py
│       │   ├── webhook/
│       │   │   ├── webhook_server.py
│       │   │   ├── event_processor.py
│       │   │   └── webhook_security_service.py
│       │   └── review/
│       │       ├── review_engine.py
│       │       ├── review_rules.py
│       │       └── review_service.py
│       ├── routers/            # API endpoints
│       │   ├── review_api.py
│       │   ├── webhook_api.py
│       │   └── stream_api.py
│       ├── common/             # Utilities
│       │   ├── config.py
│       │   ├── logger.py
│       │   ├── exceptions.py
│       │   └── constants.py
│       ├── main.py             # App entry point
│       └── __init__.py
├── tests/                      # Test suite
│       ├── unit/
│       ├── integration/
│       └── e2e/
├── .env.example               # Environment template
├── requirements.txt           # Dependencies
├── Dockerfile                 # Container config
├── docker-compose.yml         # Local development
└── README.md                  # Documentation
```

---

## Detailed Task Breakdown

### PHASE 1: FOUNDATION (Week 1)

#### 1.1 Configuration Management
**File:** `apps/code_reviewer/common/config.py`
```python
class Config:
    - OPENAI_API_KEY
    - GITHUB_TOKEN / GITLAB_TOKEN / BITBUCKET_TOKEN
    - WEBHOOK_SECRET
    - DATABASE_URL (optional)
    - LOG_LEVEL
    - REVIEW_RULES_CONFIG
```

**Deliverable:** Environment-based config loader with validation

#### 1.2 Logging Setup
**File:** `apps/code_reviewer/common/logger.py`
```python
- Structured logging with JSON output
- Different log levels per module
- Centralized error tracking
```

**Deliverable:** Reusable logger instance for all modules

#### 1.3 Exception Handling
**File:** `apps/code_reviewer/common/exceptions.py`
```python
- ReviewAgentException (base)
- AIProviderError
- PlatformAdapterError
- WebhookVerificationError
- RateLimitError
```

**Deliverable:** Custom exception hierarchy

#### 1.4 Data Models
**Files:**
- `apps/code_reviewer/model/code_change.py`
  ```python
  CodeChange:
    - file_path: str
    - language: str
    - old_content: str
    - new_content: str
    - additions: int
    - deletions: int
  ```

- `apps/code_reviewer/model/review_finding.py`
  ```python
  ReviewFinding:
    - id: str
    - file_path: str
    - line_number: int
    - severity: CRITICAL|HIGH|MEDIUM|LOW
    - category: SECURITY|PERFORMANCE|STYLE|BEST_PRACTICE
    - message: str
    - suggestion: str
  ```

- `apps/code_reviewer/model/review_report.py`
  ```python
  ReviewReport:
    - pr_id: str
    - findings: List[ReviewFinding]
    - summary: str
    - total_issues: int
  ```

- `apps/code_reviewer/model/pull_request.py`
  ```python
  PullRequest:
    - pr_id: str
    - platform: GITHUB|GITLAB|BITBUCKET
    - repository: str
    - branch: str
    - diff: str
    - files: List[CodeChange]
  ```

**Deliverable:** Pydantic models with validation

#### 1.5 Core Interfaces
**File:** `apps/code_reviewer/service/platform/base_adapter.py`
```python
class PlatformAdapter (ABC):
    - authenticate()
    - get_pr_details()
    - get_diff()
    - post_review()
    - post_comment()
```

**File:** `apps/code_reviewer/service/ai/base_provider.py`
```python
class AIProvider (ABC):
    - analyze_code()
    - generate_review()
    - parse_response()
```

**Deliverable:** Abstract base classes for all platforms

---

### PHASE 2: AI INTEGRATION (Week 2)

#### 2.1 OpenAI Client Wrapper
**File:** `apps/code_reviewer/service/ai/openai_provider.py`
```python
class OpenAIProvider(AIProvider):
    - __init__(api_key, model="gpt-4")
    - analyze_code(code_diff, rules)
    - handle_token_limits()
    - parse_gpt_response()
```

**Deliverable:** Wrapper around OpenAI API with error handling

#### 2.2 Prompt Engineering
**File:** `apps/code_reviewer/service/ai/prompt_engine.py`
```python
class PromptEngine:
    - build_security_prompt()
    - build_performance_prompt()
    - build_style_prompt()
    - build_best_practice_prompt()
    - build_comprehensive_prompt()
```

**Deliverable:** Dynamic prompt templates for different review types

#### 2.3 Review Rules Configuration
**File:** `apps/code_reviewer/service/review/review_rules.py`
```python
class ReviewRules:
    - check_security: bool
    - check_performance: bool
    - check_style: bool
    - check_best_practices: bool
    - excluded_patterns: List[str]
    - language_specific_rules: Dict
```

**Deliverable:** Configuration model for review customization

#### 2.4 Review Engine
**File:** `apps/code_reviewer/service/review/review_engine.py`
```python
class ReviewEngine:
    - __init__(ai_provider, rules)
    - review_code(pull_request)
    - generate_findings()
    - prioritize_findings()
    - create_report()
```

**Deliverable:** Main orchestrator for code analysis

---

### PHASE 3: PLATFORM INTEGRATIONS (Week 3)

#### 3.1 GitHub Adapter
**File:** `apps/code_reviewer/service/platform/github_adapter.py`
```python
class GitHubAdapter(PlatformAdapter):
    - authenticate(token)
    - get_pr_details(owner, repo, pr_number)
    - get_diff(owner, repo, pr_number)
    - post_review(owner, repo, pr_number, findings)
    - post_comment(owner, repo, pr_number, file, line, message)
    - handle_rate_limit()
```

**Dependencies:** PyGithub, requests

**Deliverable:** Full GitHub integration

#### 3.2 GitLab Adapter
**File:** `apps/code_reviewer/service/platform/gitlab_adapter.py`
```python
class GitLabAdapter(PlatformAdapter):
    - authenticate(token, base_url)
    - get_mr_details(project_id, mr_number)
    - get_diff(project_id, mr_number)
    - post_discussion(project_id, mr_number, findings)
    - post_note(project_id, mr_number, file, line, message)
```

**Dependencies:** python-gitlab

**Deliverable:** Full GitLab integration

#### 3.3 Bitbucket Adapter
**File:** `apps/code_reviewer/service/platform/bitbucket_adapter.py`
```python
class BitbucketAdapter(PlatformAdapter):
    - authenticate(username, app_password)
    - get_pr_details(workspace, repo, pr_id)
    - get_diff(workspace, repo, pr_id)
    - post_review(workspace, repo, pr_id, findings)
    - post_inline_comment(workspace, repo, pr_id, file, line, message)
```

**Dependencies:** atlassian-python-api

**Deliverable:** Full Bitbucket integration

#### 3.4 Platform Factory
**File:** `apps/code_reviewer/service/platform/platform_factory.py`
```python
class PlatformFactory:
    - create_adapter(platform, credentials)
    - get_platform_from_webhook(headers)
```

**Deliverable:** Dynamic platform adapter creation

---

### PHASE 4: WEBHOOK SYSTEM (Week 4)

#### 4.1 Webhook Server
**File:** `apps/code_reviewer/routers/webhook_api.py`
```python
@app.post("/webhook/github")
@app.post("/webhook/gitlab")
@app.post("/webhook/bitbucket")
- Receive webhook events
- Verify signatures
- Queue jobs for processing
```

**Deliverable:** FastAPI endpoints for webhooks

#### 4.2 Event Processor
**File:** `apps/code_reviewer/service/webhook/event_processor.py`
```python
class EventProcessor:
    - process_github_event(payload)
    - process_gitlab_event(payload)
    - process_bitbucket_event(payload)
    - extract_pr_info(payload)
    - queue_review_job(pr_info)
```

**Deliverable:** Event routing and job queuing

#### 4.3 Webhook Security
**File:** `apps/code_reviewer/service/webhook/webhook_security_service.py`
```python
class WebhookSecurityService:
    - verify_github_signature(signature, payload, secret)
    - verify_gitlab_signature(signature, payload, secret)
    - verify_bitbucket_signature(signature, payload, secret)
```

**Deliverable:** Signature verification for all platforms

#### 4.4 Async Job Processing
**File:** `apps/code_reviewer/service/webhook/job_queue.py`
```python
- Setup Celery worker
- Queue review jobs
- Handle retries and failures
- Track job status
```

**Deliverable:** Background job processing system

---

### PHASE 5: ADVANCED FEATURES (Week 5)

#### 5.1 Caching Layer
**File:** `apps/code_reviewer/service/review/review_cache.py`
```python
class ReviewCache:
    - cache_review_result(pr_id, result)
    - get_cached_review(pr_id)
    - invalidate_cache(pr_id)
```

**Deliverable:** Redis-based caching

#### 5.2 Language-Specific Rules
**File:** `apps/code_reviewer/service/review/language_rules.py`
```python
- Python-specific checks
- JavaScript/TypeScript checks
- Go-specific checks
- Java-specific checks
- etc.
```

**Deliverable:** Language detection and rule application

#### 5.3 Analytics & Reporting
**File:** `apps/code_reviewer/service/analytics/metrics_service.py`
```python
class MetricsService:
    - track_review_metrics()
    - generate_summary_report()
    - export_analytics()
```

**Deliverable:** Analytics dashboard and reporting

---

## Tech Stack & Dependencies

### Core Dependencies
```
fastapi==0.104.0
pydantic==2.0.0
python-dotenv==1.0.0
openai==1.0.0
PyGithub==2.1.1
python-gitlab==4.0.0
atlassian-python-api==3.41.0
requests==2.31.0
redis==5.0.0
celery==5.3.0
pytest==7.4.0
```

### Development Environment
```
Docker
Docker Compose
PostgreSQL (optional)
Redis (for caching & job queue)
```

---

## Implementation Checklist

### Week 1: Foundation
- [ ] Create project structure
- [ ] Set up .env configuration
- [ ] Implement logging system
- [ ] Create exception hierarchy
- [ ] Write Pydantic data models
- [ ] Define abstract base classes

### Week 2: AI Integration
- [ ] Implement OpenAI client wrapper
- [ ] Create prompt templates
- [ ] Build review rules configuration
- [ ] Implement review engine
- [ ] Test GPT integration end-to-end

### Week 3: Platforms
- [ ] Implement GitHub adapter
- [ ] Implement GitLab adapter
- [ ] Implement Bitbucket adapter
- [ ] Create platform factory
- [ ] Test each adapter independently

### Week 4: Webhooks
- [ ] Build webhook server
- [ ] Implement event processors
- [ ] Add signature verification
- [ ] Set up Celery + Redis
- [ ] Test webhook pipeline

### Week 5: Polish
- [ ] Add caching layer
- [ ] Implement language-specific rules
- [ ] Build analytics dashboard
- [ ] Performance testing & optimization
- [ ] Security audit
- [ ] Documentation & README

---

## Key Architectural Decisions

### 1. Multi-Platform Strategy
- Use **factory pattern** to create platform adapters dynamically
- Normalize all platform responses to common data models
- Handle API differences transparently

### 2. AI Integration
- Use **strategy pattern** for different review types
- Implement **prompt engineering** for better GPT responses
- Add **token management** to handle large diffs

### 3. Event Processing
- Use **async job queue** (Celery) for non-blocking processing
- Implement **deduplication** to avoid duplicate reviews
- Use **webhooks** for real-time triggers

### 4. Configuration
- Environment-based config for flexibility
- Per-repository review rules
- Per-user customization options

---

## Security Considerations

1. **Webhook Verification**
   - HMAC signature validation for all webhooks
   - Timestamp validation to prevent replay attacks

2. **API Keys**
   - Store in environment variables, never in code
   - Rotate regularly
   - Use least-privilege tokens

3. **Rate Limiting**
   - Implement per-user rate limits
   - Handle platform API rate limits gracefully

4. **Code Analysis**
   - Never log sensitive data (API keys, credentials)
   - Sanitize error messages
   - Validate all inputs

---

## Success Metrics

- ✅ Agent successfully analyzes PR diffs in <5 seconds
- ✅ Posts reviews to all 3 platforms (GitHub, GitLab, Bitbucket)
- ✅ >95% detection accuracy for security issues
- ✅ Configurable per-repository rules
- ✅ Zero security vulnerabilities in webhook handling
- ✅ <0.5% false positive rate

---

## Next Steps

1. **Choose implementation approach**: Sequential (phase by phase) or Parallel (multiple phases)
2. **Set up development environment**: Docker, local setup, testing framework
3. **Begin Phase 1**: Start with foundation and data models
4. **Schedule reviews**: After each phase completion

