# AWS Deployment Overview for Codebot

Review date: 2026-04-03

## 1. Project overview

This project is a split application:

- Frontend: React + Vite in `frontend/`
- Backend: FastAPI in `backend/bot/`
- Database: PostgreSQL is required
- Vector memory: `pgvector` is required in PostgreSQL
- Optional realtime/SSE trade demo: Redis/Valkey is used in `backend/bot/application/router/v2/chat_api.py`
- External APIs: OpenAI is required for chat, Google OAuth is optional, DuckDuckGo/web access is optional when web search is enabled

## 2. What is good for deployment

- Frontend and backend are already separated. That makes it easy to host them either on one server or split them later.
- The frontend uses relative `/api` requests, which is good for reverse-proxy deployment from one domain. See `frontend/src/App.tsx`.
- The backend already loads important env vars from `.env`, including database, auth cookies, frontend URL, and Google OAuth settings. See `backend/bot/application/config.py`.
- Docker artifacts already exist (`Dockerfile`, `docker-compose.yml`), so container deployment is possible after fixes.
- Frontend production build works locally: `npm run build` passed.
- Backend imports successfully: `from backend.bot.application.main import app` passed.

## 3. What can break deployment now

### High-risk blockers

1. Dockerfile does not package the active backend correctly.
   - `Dockerfile` copies only `bot/`, but the real application code is in `backend/bot/`.
   - The shim package at `bot/__init__.py` points into `backend/bot`, so the container will miss the real app code unless `backend/` is copied too.
   - See `Dockerfile:16-17`.

2. Frontend dev proxy points to port `8002`, but the backend examples and container expose `8000`.
   - See `frontend/vite.config.ts:9-12`.
   - This is a dev-time mismatch and usually causes confusion during local testing and staging.

3. Realtime Redis connection is hardcoded to `localhost`.
   - `backend/bot/application/router/v2/chat_api.py:15`
   - In Docker or multi-service deployment this breaks, because Redis is not always on localhost.

4. The compose stack and app logic are inconsistent.
   - `docker-compose.yml` starts Valkey and Qdrant.
   - Main chat flow actually uses `PGVectorService()` and stores vectors in PostgreSQL, not Qdrant.
   - See `backend/bot/application/service/chat_service.py:83-85` and `backend/bot/application/service/chat_service.py:120-141`.
   - That means PostgreSQL with `pgvector` is a real requirement, but it is not present in `docker-compose.yml`.

5. There is no production CORS setup in the FastAPI app.
   - `backend/bot/application/main.py` only mounts routers.
   - If frontend and backend are deployed on different origins, auth cookies and browser requests will fail until CORS is added.

6. SSE behavior is not stable enough yet.
   - Local test run failed for `backend.tests.test_v2_chat_api`.
   - One test fails because invalid JSON is not handled.
   - Another fails because the stream output format does not match the test expectation.
   - This is important because streaming endpoints are one of the first things to break behind proxies.

### Medium-risk gaps

1. Database startup and migrations are not wired into deployment.
   - Auto-create startup is commented out in `backend/bot/application/main.py:16-19`.
   - `PGVectorService` may create schema ad hoc, but the main app should still run Alembic migrations as a deployment step.

2. `pgvector` is mandatory for current chat memory.
   - See `backend/bot/application/model/pg_vectore.py:19-29`.
   - Your PostgreSQL instance must have the `vector` extension enabled.

3. `requests` is imported directly for Google OAuth, but it is not declared directly in `pyproject.toml`.
   - Import usage: `backend/bot/application/service/auth_service.py:13` and `backend/bot/application/service/auth_service.py:301-323`
   - Dependency list: `pyproject.toml:7-28`
   - It may work because of transitive installs, but production packaging should declare it explicitly.

4. There is no `.env.example` file.
   - That makes first deployment slower and more error-prone.

5. There is no health-check endpoint like `/health`.
   - This makes EC2, Docker, or load balancer monitoring harder.

## 4. Recommended AWS setup for your free-tier account

### Best low-cost setup for this project right now

Use one EC2 instance first.

- AWS EC2
- One EBS volume
- Nginx or Caddy as reverse proxy
- Backend FastAPI on the same server
- PostgreSQL on the same server
- `pgvector` extension in PostgreSQL
- Redis/Valkey on the same server only if you keep the SSE trade feature
- Hostinger DNS for your domain

Why this is the best first deployment:

- Cheapest practical option
- Simplest to debug
- No CORS problem if frontend and backend share one domain
- No extra managed-service cost from ALB, Route 53, or RDS at the start

### Services I do not recommend for your first deploy

- Route 53: not needed because your domain is already at Hostinger, and Route 53 hosted zones are billed separately
- ALB: useful later, but usually unnecessary cost for one small app
- ECS/Fargate/EKS: too much complexity for this project stage
- RDS for the first deploy: better later, but local PostgreSQL on EC2 is simpler and cheaper for now

## 5. Recommended domain layout

### Option A: one domain, one server

- `yourdomain.com` -> frontend
- `yourdomain.com/api/...` -> backend through reverse proxy

This is the easiest option for your current code because the frontend already calls relative `/api` paths.

### Option B: split frontend and backend

- `app.yourdomain.com` -> frontend
- `api.yourdomain.com` -> backend

Use this only after adding:

- FastAPI CORS middleware
- secure cookie settings
- correct `FRONTEND_BASE_URL`
- correct `AUTH_COOKIE_DOMAIN`

## 6. How to deploy without Docker

### Server layout

On one Ubuntu EC2 instance:

1. Install Python 3.11, Node.js, PostgreSQL, Redis/Valkey, and Nginx or Caddy.
2. Clone the repo.
3. Create `.env`.
4. Create PostgreSQL database and enable `pgvector`.
5. Run Alembic migrations.
6. Install backend dependencies.
7. Build frontend with `npm run build`.
8. Run FastAPI with `uvicorn` under `systemd`.
9. Serve `frontend/dist` from Nginx or Caddy.
10. Reverse proxy `/api` to FastAPI on localhost.

### Frontend/backend management without Docker

- Frontend: build once into static files, serve from Nginx/Caddy
- Backend: run as a systemd service
- Database: local PostgreSQL service
- Redis: local service if needed

### Important Nginx/Caddy note

Your chat endpoint uses Server-Sent Events (`/api/chat/stream`), so reverse proxy config must not buffer SSE responses.

## 7. How to deploy with Docker

### Recommended Docker shape

Run on one EC2 instance with Docker Compose:

- `backend` container
- `postgres` container with persistent volume
- `redis` or `valkey` container if SSE feature is kept
- `nginx` container or host Nginx for static frontend and reverse proxy

### Current Docker work needed before this can be used

- Fix Dockerfile to copy `backend/`
- Decide whether frontend will be:
  - built separately and served by Nginx, or
  - built in a multi-stage Docker image
- Add PostgreSQL service to compose
- Either remove Qdrant from compose or switch app logic to actually use it
- Replace hardcoded Redis localhost with env-based config

### Frontend/backend management with Docker

- Frontend:
  - build in CI or a Docker multi-stage build
  - serve static files through Nginx
- Backend:
  - separate container
  - internal port only
- Database:
  - separate PostgreSQL container with volume
- Redis:
  - separate container only if still needed

## 8. Exact env/config you will need in production

Minimum likely env vars:

- `DATABASE_URL`
- `OPENAI_API_KEY`
- `JWT_SECRET`
- `FRONTEND_BASE_URL`
- `AUTH_COOKIE_SECURE=true`
- `AUTH_COOKIE_SAMESITE`
- `AUTH_COOKIE_DOMAIN`

Optional env vars:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `QDRANT_URL` only if you move back to Qdrant
- Redis host/port env vars should be added for SSE

## 9. AWS free-tier and cost notes

I checked current AWS docs while preparing this review.

- AWS changed Free Tier behavior on July 15, 2025.
- For accounts created on or after July 15, 2025, AWS documents a credits-based model and different EC2 free-tier behavior.
- AWS Route 53 hosted zones are billed, so you do not need Route 53 just because you own a Hostinger domain.
- AWS S3 docs recommend Amplify Hosting or CloudFront when you want secure static hosting with HTTPS.

Because of that, the safest low-cost path is:

- keep DNS at Hostinger
- use one EC2 server first
- add S3/CloudFront or Amplify only if you later want frontend and backend split

## 10. My deployment recommendation for this repo

### Phase 1: cheapest working deployment

- One Ubuntu EC2 instance
- One domain from Hostinger pointed to EC2 public IP
- Nginx or Caddy
- FastAPI backend on localhost
- Frontend static build on the same server
- PostgreSQL + `pgvector` on the same server
- Redis/Valkey only if the v2 SSE feature must stay

### Phase 2: after the app is stable

- Frontend on S3 + CloudFront or Amplify
- Backend on EC2
- Later move PostgreSQL to RDS if traffic grows

## 11. Immediate fixes before real deployment

1. Fix Dockerfile to include the real backend package.
2. Add PostgreSQL to Docker Compose or document non-Docker PostgreSQL setup clearly.
3. Replace hardcoded Redis localhost with env vars.
4. Add CORS middleware if frontend/backend will use different subdomains.
5. Add a `/health` endpoint.
6. Add `.env.example`.
7. Fix SSE tests and verify streaming through a reverse proxy.
8. Add `requests` explicitly to `pyproject.toml`.

## 12. Validation I ran

- `npm run build` in `frontend/`: passed
- `from backend.bot.application.main import app`: passed
- `python -m unittest backend.tests.test_v2_chat_api`: failed

## 13. Final answer in one line

For your AWS free-tier account, deploy this first on one EC2 Ubuntu server with Nginx/Caddy + FastAPI + PostgreSQL with `pgvector`, keep DNS in Hostinger, and treat Docker as a second step after fixing the current container and SSE/config issues.
