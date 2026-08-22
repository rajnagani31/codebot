# 🔐 Codebot & NeroAI Shared Authentication System

> Comprehensive Guide to the Authentication Architecture, Token Claims, Database Schema, Cookies, and User Flow Scenarios across **Codebot** and **NeroAI**.

---

## 📌 Executive Architecture Summary

The authentication system is built on a **Shared Token Issuer & Consumer Architecture**:

```
                                +----------------------------------+
                                |        FRONTEND APPLICATION      |
                                |     (React / Vite - Port 3000)   |
                                +----------------------------------+
                                         /                \
                1. /api/auth/login      /                  \ 2. /api/neroai/me
                (Receive JWT Tokens)   /                    \ (Header: Bearer <token>)
                                      v                      v
+----------------------------------------+                +----------------------------------------+
|            CODEBOT SERVICE             |                |             NEROAI SERVICE             |
|              (Port 8000)               |                |              (Port 8002)               |
+----------------------------------------+                +----------------------------------------+
| Role: AUTH ISSUER                      |                | Role: AUTH CONSUMER                    |
| - Handles /login, /signup, OAuth       |                | - Receives incoming Bearer tokens      |
| - Connects to PostgreSQL Database      |                | - NO database connections needed       |
| - Issues signed JWT Access Tokens      |                | - Verifies JWT signature statelessly   |
| - Uses `get_current_user_from_db`      |                | - Uses `get_current_user_from_token`   |
+----------------------------------------+                +----------------------------------------+
                    \                                                /
                     \                                              /
                      v                                            v
           +------------------------------------------------------------------+
           |                 apps/backend/shared/auth                       |
           |------------------------------------------------------------------|
           | - `get_current_user_from_token` (Stateless JWT Validator)       |
           | - `decode_access_token` (HMAC-SHA256 Signature Checker)          |
           | - `UserPrincipal` & `TokenPayload` Schemas                       |
           +------------------------------------------------------------------+
```

---

## 💾 1. What is Stored in DB vs. What is Used from DB

### A. `users` Table (`ChatUser`)
Stores persistent user identity records.

| Field Name | Type | Purpose / Description |
| :--- | :--- | :--- |
| `id` | `Integer (PK)` | Primary internal numeric User ID |
| `public_id` | `String` | Secure external string ID (e.g. `usr_980488acedba...`) |
| `email` | `String (Unique)` | User's email address (normalized to lowercase) |
| `password_hash` | `String` | PBKDF2-SHA256 hashed password (`pbkdf2_sha256$260000$...`) |
| `display_name` | `String` | User's full name or nickname |
| `user_type` | `String` | `"registered"` or `"guest"` |
| `auth_provider` | `String` | `"password"`, `"google"`, or `"guest"` |
| `google_sub` | `String` | Google OAuth Unique Subject ID |
| `is_active` | `Boolean` | Account status flag (`True`/`False`) |
| `email_verified` | `Boolean` | Whether user email has been verified |

---

### B. `user_sessions` Table (`UserSession`)
Stores active user sessions, refresh tokens, and guest quota counters.

| Field Name | Type | Purpose / Description |
| :--- | :--- | :--- |
| `id` | `Integer (PK)` | Primary Session ID (`sid`) |
| `user_id` | `Integer (FK)` | Links to `users.id` |
| `session_token_hash` | `String` | SHA-256 hash of active Access Token |
| `refresh_token_hash` | `String` | SHA-256 hash of active Refresh Token |
| `auth_method` | `String` | Method used to initiate session (`"password"`, `"google"`, `"guest"`) |
| `message_limit` | `Integer` | Max guest chat limit (Default: `5` for guest users, `Null` for registered) |
| `message_count` | `Integer` | Messages consumed by guest session so far |
| `expires_at` | `DateTime` | Access token expiration timestamp |
| `refresh_expires_at` | `DateTime` | Refresh token expiration timestamp |
| `revoked_at` | `DateTime` | Set when user explicitly logs out or revokes session |

---

## 🍪 2. Cookies vs. Tokens (JWT) Data Breakdown

The authentication system uses a **Dual-Delivery Strategy**:
1. **HTTP-Only Cookies**: Automatically attached by web browsers (Same-Origin).
2. **JSON Bearer Tokens**: Returned in response body for Postman, Mobile Apps, and Cross-Origin microservices (NeroAI).

### A. What Data is Stored in Cookies?

Cookies are HTTP-Only, Secure, and SameSite-protected to prevent XSS attacks.

| Cookie Name | Expiration | Purpose & Content |
| :--- | :--- | :--- |
| `codebot_access_token` | 15 Minutes | Contains signed JWT Access Token string |
| `codebot_refresh_token` | 30 Days | Contains signed JWT Refresh Token string |
| `guest_token` | 3 Days (Legacy) | Temporary guest token cookie (cleared upon login) |

---

### B. What Data is Stored inside the JWT Access Token?

The **Access Token** is cryptographically signed using **HMAC-SHA256 (`HS256`)** with `JWT_SECRET`. Anyone can decode the payload, but no one can tamper with it without invalidating the signature.

#### Access Token Payload JSON Structure:
```json
{
  "typ": "access",
  "sub": "64",
  "email": "user@example.com",
  "user_type": "registered",
  "sid": 110,
  "session_label": "92adaac87965",
  "provider": "password",
  "iat": 1724185000,
  "exp": 1724185900
}
```

* `sub`: Subject (Stringified User ID).
* `email`: User email address.
* `user_type`: `"registered"` or `"guest"`.
* `sid`: Session ID in `user_sessions` table.
* `exp`: Expiration timestamp in seconds.

#### Refresh Token Payload JSON Structure:
```json
{
  "typ": "refresh",
  "sub": "64",
  "sid": 110,
  "iat": 1724185000,
  "exp": 1726777000
}
```

---

## 🔄 3. Scenarios & Step-by-Step User Flows

### Scenario 1: Guest User Flow (First Time Visit)
1. **Request**: Unauthenticated user visits Frontend and sends a message without logging in.
2. **Guest Session Creation**: Frontend calls `POST /api/auth/guest`.
3. **Database Action**:
   - Creates `ChatUser(user_type="guest")`.
   - Creates `UserSession(message_limit=5, message_count=0)`.
4. **Response**: Sets `codebot_access_token` cookie & returns JSON tokens.
5. **Chat Message Execution**:
   - `POST /api/chat/stream` executes `auth_service.consume_chat_credit(current_user)`.
   - Database increments `message_count`.
   - Once `message_count >= 5`, backend throws `QuotaExceededError("Guest message limit reached. Sign in to continue.")`.

---

### Scenario 2: User Password Signup & Login
1. **User Request**: User fills out Signup/Login form on Frontend (`POST /api/auth/login`).
2. **Password Verification**: `AuthService` verifies password using PBKDF2-SHA256 constant-time hash comparison (`hmac.compare_digest`).
3. **Guest Upgrade**: If user was previously a guest, `AuthService` upgrades the existing guest account to full registered status instead of creating a duplicate user!
4. **Token Delivery**: Backend signs fresh JWT access token + refresh token and returns them in cookies and JSON payload.

---

### Scenario 3: Google OAuth Login Flow
1. **Initiation**: User clicks "Sign in with Google" -> Frontend requests `GET /api/auth/google/url`.
2. **Redirect**: User is redirected to Google OAuth Consent screen.
3. **Callback**: Google redirects to `GET /api/auth/google/callback?code=...&state=...`.
4. **Token Exchange**: Backend exchanges `code` with Google for access token, fetches profile info (`sub`, `email`, `name`).
5. **Account Linking**: Backend links Google ID to existing user email or creates a new `ChatUser(auth_provider="google")`.
6. **Frontend Redirect**: Redirects browser back to Frontend with `codebot_access_token` cookie set.

---

### Scenario 4: Microservice Agent Request (NeroAI Code Reviewer)
1. **Context**: User triggers PR Code Review in NeroAI (Port 8002).
2. **Frontend Action**: Frontend sends HTTP request to `http://localhost:8002/api/neroai/me` with header:
   ```http
   Authorization: Bearer eyJhbGciOiJIUzI1Ni...
   ```
3. **NeroAI Backend Execution**:
   - Endpoint dependency: `current_user: UserPrincipal = Depends(get_current_user_from_token)`.
   - `decode_access_token` verifies HMAC-SHA256 signature using `JWT_SECRET`.
   - Validates `exp` timestamp.
   - Extracts `user_id=64`, `email="user@example.com"`, `session_id=110` **in < 1 ms with ZERO database queries!**

---

### Scenario 5: Token Refresh & Logout
1. **Token Refresh (`POST /api/auth/refresh`)**:
   - When Access Token expires (401 Unauthorized), Frontend sends `codebot_refresh_token`.
   - Backend validates refresh token hash against `user_sessions` DB table.
   - Issues fresh 15-minute Access Token.
2. **Logout (`POST /api/auth/logout`)**:
   - Backend marks `revoked_at = datetime.utcnow()` in `user_sessions` table.
   - Clears HTTP cookies (`codebot_access_token`, `codebot_refresh_token`).

---

## 🛠️ 4. Codebase Reference Guide

### Which function should I import in my code?

| Goal / Requirement | Function to Import | Import Path | Behavior |
| :--- | :--- | :--- | :--- |
| **Stateless JWT Auth**<br>*(Microservices, NeroAI, High Performance)* | `get_current_user_from_token` | `from apps.backend.shared.auth import get_current_user_from_token` | Decodes JWT in memory (< 1 ms). No DB connection required. |
| **Database Session Auth**<br>*(Codebot Chatbot, Quota Enforcement)* | `get_current_user_from_db` | `from apps.backend.bot.application.dependencies.auth import get_current_user_from_db` | Queries PostgreSQL to fetch live guest credit counts and session status. |

---

### 🔬 Token Validation Data Breakdown

When backend validates a token, what data is extracted from the **Token Payload** vs. fetched as **External Data (PostgreSQL DB)**:

#### A. `get_current_user_from_token` (Stateless / Fast)
* **Strategy**: Pure in-memory cryptographic verification (`HS256` signature + `exp` validation).
* **DB Queries**: `0` DB calls.
* **Extracted from Token Payload**:
  * `id`: User ID (`payload.sub`)
  * `email`: User Email (`payload.email`)
  * `user_type`: `"registered"` or `"guest"` (`payload.user_type`)
  * `session_id`: Session ID (`payload.sid`)
* **External Data (DB)**: **`None`** (Fields like `display_name`, `public_id`, and `remaining_guest_messages` default to `None` / `0`).
* **Returned Model**: `UserPrincipal`

#### B. `get_current_user_from_db` (Stateful / Session & Quota Enforced)
* **Strategy**: Decodes `sid` from token, then queries PostgreSQL for live state.
* **DB Queries**: `2+` DB queries + active timestamps update (`touch_user`, `touch_session`).
* **Extracted from Token Payload**:
  * `sid`: Session ID (used for DB lookup).
  * Expiration & signature check.
* **External Data (Fetched live from PostgreSQL DB)**:
  * **User Profile (`ChatUser` table)**: `id`, `public_id`, `email`, `display_name`, `user_type`, `email_verified`, `session_label`.
  * **Session State (`UserSession` table)**: `session_id`, `auth_provider`, `session_expires_at`, `is_active`, `revoked_at`, token hash match.
  * **Guest Quota & Credit Limits**: `guest_message_limit`, `guest_messages_used`, `remaining_guest_messages` (`max(limit - count, 0)`).
* **Returned Model**: `AuthenticatedPrincipal`

#### Data Fields Comparison Matrix:

| Field | `get_current_user_from_token` | `get_current_user_from_db` |
| :--- | :---: | :---: |
| `id` | ✅ (From Token) | ✅ (From DB) |
| `email` | ✅ (From Token) | ✅ (From DB) |
| `user_type` | ✅ (From Token) | ✅ (From DB) |
| `session_id` | ✅ (From Token) | ✅ (From DB) |
| `public_id` | ❌ `None` | ✅ (From DB) |
| `display_name` | ❌ `None` | ✅ (From DB) |
| `auth_provider` | ❌ `None` | ✅ (From DB) |
| `email_verified` | ❌ `None` | ✅ (From DB) |
| `remaining_guest_messages` | ❌ `None` | ✅ (Live Calculated from DB) |
| **Revocation Check** | ❌ No | ✅ Yes (Verifies DB Session status) |

---

### Key File Locations

* 📁 **Shared Auth Package**: [apps/backend/shared/auth](file:///e:/raj/codebot/codebot/apps/backend/shared/auth)
  * [dependencies.py](file:///e:/raj/codebot/codebot/apps/backend/shared/auth/dependencies.py): `get_current_user_from_token` dependency.
  * [jwt_utils.py](file:///e:/raj/codebot/codebot/apps/backend/shared/auth/jwt_utils.py): HMAC-SHA256 signature & expiration verification.
  * [schemas.py](file:///e:/raj/codebot/codebot/apps/backend/shared/auth/schemas.py): `UserPrincipal` and `TokenPayload` Pydantic models.
  * [security.py](file:///e:/raj/codebot/codebot/apps/backend/shared/auth/security.py): Swagger UI (`/docs`) 🔒 "Authorize" button configuration.
* 📁 **Codebot Auth Issuer**: [apps/backend/bot/application/router/auth/auth_api.py](file:///e:/raj/codebot/codebot/apps/backend/bot/application/router/auth/auth_api.py)
* 📁 **NeroAI Auth Consumer**: [apps/backend/agents/pr_reviewer_agent/apps/code_reviewer/routers/github.py](file:///e:/raj/codebot/codebot/apps/backend/agents/pr_reviewer_agent/apps/code_reviewer/routers/github.py)

