# Auth And Depends

This file explains:

1. `POST /api/auth/guest`
2. `GET /api/auth/me`
3. `require_current_user`
4. `get_chat_service`
5. how FastAPI `Depends(...)` works in this project

---

## 1. `POST /api/auth/guest`

Code:
- [auth_api.py](/home/ubuntu/Documents/test/Codebot/Codebot/backend/bot/application/router/auth/auth_api.py#L10)
- [auth_service.py](/home/ubuntu/Documents/test/Codebot/Codebot/backend/bot/application/service/auth_service.py#L16)
- [chat_schema.py](/home/ubuntu/Documents/test/Codebot/Codebot/backend/bot/application/schema/chat_schema.py#L8)

Route:

```python
@router.post("/guest", response_model=UserSessionResponse)
def create_guest_session(auth_service: AuthService = Depends(get_auth_service)):
    return auth_service.create_guest_session()
```

This API is used to create a new guest user session.

### What happens step by step

1. FastAPI calls `get_auth_service()`.
2. `get_auth_service()` creates an `AuthService` object.
3. Route function receives that object as `auth_service`.
4. Route calls `auth_service.create_guest_session()`.
5. `create_guest_session()` creates a new user in database.
6. It generates a JWT-like token using the configured secret.
7. It returns session data to frontend.

### What `create_guest_session()` returns

Return shape:

```json
{
  "token": "jwt_token_here",
  "user_id": 1,
  "session_label": "abc123def456",
  "expires_at": 1712345678
}
```

Schema:

```python
class UserSessionResponse(BaseModel):
    token: str
    user_id: int
    session_label: str
    expires_at: int
```

### Why frontend calls this API

Frontend uses this API when there is no stored auth token yet.

After calling this API, frontend saves:
- `token`
- `user_id`
- `session_label`

Then it sends the token in later requests:

```http
Authorization: Bearer <token>
```

---

## 2. `GET /api/auth/me`

Code:
- [auth_api.py](/home/ubuntu/Documents/test/Codebot/Codebot/backend/bot/application/router/auth/auth_api.py#L14)
- [dependencies/auth.py](/home/ubuntu/Documents/test/Codebot/Codebot/backend/bot/application/dependencies/auth.py#L18)
- [chat_schema.py](/home/ubuntu/Documents/test/Codebot/Codebot/backend/bot/application/schema/chat_schema.py#L15)

Route:

```python
@router.get("/me", response_model=AuthenticatedUserResponse)
def get_authenticated_user(current_user=Depends(require_current_user)):
    return current_user
```

This API is used to check:
- is token valid?
- which user is currently authenticated?

### What happens step by step

1. Client sends request with `Authorization: Bearer <token>`.
2. FastAPI runs `require_current_user`.
3. `require_current_user` reads the bearer token.
4. It asks `AuthService` to decode and validate the token.
5. If token is valid, it loads the user from database.
6. Route receives that user as `current_user`.
7. Route returns `current_user`.

### What this API returns

Schema:

```python
class AuthenticatedUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_label: str
```

Example response:

```json
{
  "id": 1,
  "session_label": "abc123def456"
}
```

### If token is missing or invalid

This API returns `401 Unauthorized`.

Examples:
- no `Authorization` header
- wrong scheme
- invalid signature
- expired token
- user not found

---

## 3. Auth structure used in this project

Main files:
- [main.py](/home/ubuntu/Documents/test/Codebot/Codebot/backend/bot/application/main.py#L1)
- [auth_api.py](/home/ubuntu/Documents/test/Codebot/Codebot/backend/bot/application/router/auth/auth_api.py#L1)
- [dependencies/auth.py](/home/ubuntu/Documents/test/Codebot/Codebot/backend/bot/application/dependencies/auth.py#L1)
- [auth_service.py](/home/ubuntu/Documents/test/Codebot/Codebot/backend/bot/application/service/auth_service.py#L1)
- [config.py](/home/ubuntu/Documents/test/Codebot/Codebot/backend/bot/application/config.py#L1)
- [chat_repository.py](/home/ubuntu/Documents/test/Codebot/Codebot/backend/bot/application/repository/chat_repository.py#L1)

### Router registration

In `main.py`:

```python
app.include_router(auth_router, prefix="/api/auth")
```

Because of this:
- `@router.post("/guest")` becomes `POST /api/auth/guest`
- `@router.get("/me")` becomes `GET /api/auth/me`

### Auth flow overview

```text
Frontend
   ->
POST /api/auth/guest
   ->
AuthService.create_guest_session()
   ->
create user in DB + create token
   ->
return token to frontend

Frontend stores token
   ->
later sends Authorization: Bearer <token>
   ->
protected API uses require_current_user
   ->
AuthService validates token
   ->
user loaded from DB
   ->
route gets current_user
```

### What `AuthService` does

`AuthService` is the main auth business layer.

Responsibilities:
- create guest session
- generate token
- decode token
- verify signature
- check token expiry
- get current user from DB

Important methods:

#### `create_guest_session()`

Creates:
- database user
- token payload with:
  - `sub`
  - `session_label`
  - `iat`
  - `exp`

#### `get_user_from_token(token)`

Does:
1. decode token
2. read `sub`
3. convert `sub` to integer `user_id`
4. load user using repository
5. return user object

#### `_encode_token(payload)`

Builds token using:
- header
- payload
- HMAC SHA256 signature

#### `_decode_token(token)`

Validates:
- token format
- signature
- expiration

If something is wrong, it raises `AuthError`.

### Config used by auth

From [config.py](/home/ubuntu/Documents/test/Codebot/Codebot/backend/bot/application/config.py#L10):

```python
JWT_SECRET = os.getenv("JWT_SECRET", "codebot-dev-jwt-secret")
JWT_EXPIRES_SECONDS = int(os.getenv("JWT_EXPIRES_SECONDS", str(60 * 60 * 24 * 30)))
```

Meaning:
- `JWT_SECRET` is used to sign and verify token
- `JWT_EXPIRES_SECONDS` controls token lifetime

Default expiry here is:
- `60 * 60 * 24 * 30`
- 30 days

---

## 4. What `Depends(...)` means in FastAPI

`Depends(...)` tells FastAPI:

`"Before calling this route, first run this dependency and give me its result."`

Example:

```python
def create_guest_session(auth_service: AuthService = Depends(get_auth_service)):
```

Meaning:
- FastAPI runs `get_auth_service()`
- takes returned value
- passes it into `auth_service`

Another example:

```python
def get_authenticated_user(current_user=Depends(require_current_user)):
```

Meaning:
- FastAPI runs `require_current_user()`
- takes returned value
- passes it into `current_user`

So `Depends(...)` is dependency injection.

It helps to:
- reuse common logic
- avoid repeating auth code in every route
- create service objects automatically

---

## 5. `require_current_user`

Code:
- [dependencies/auth.py](/home/ubuntu/Documents/test/Codebot/Codebot/backend/bot/application/dependencies/auth.py#L18)

Function:

```python
def require_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization required")

    try:
        return auth_service.get_user_from_token(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
```

### What this function does

This is a protected-auth dependency.

Its job is:
- read bearer token from request header
- validate token
- fetch current user
- return current user object

### Inputs of `require_current_user`

#### `credentials = Depends(bearer_scheme)`

`bearer_scheme` is:

```python
bearer_scheme = HTTPBearer(auto_error=False)
```

This reads:

```http
Authorization: Bearer <token>
```

If header exists, it returns an object like:

```python
HTTPAuthorizationCredentials(
    scheme="Bearer",
    credentials="<actual-token>"
)
```

If header is missing, it returns `None` because `auto_error=False`.

#### `auth_service = Depends(get_auth_service)`

FastAPI creates an `AuthService` instance and passes it here.

### What `require_current_user` returns

It returns the authenticated user model from database.

In this project that is a `ChatUser` ORM object, with fields like:
- `id`
- `session_label`
- `created_at`
- `last_seen_at`

### Why route uses this

Example:

```python
def list_threads(
    current_user=Depends(require_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
```

This means:
- route is protected
- request must have valid bearer token
- after validation, route receives `current_user`
- then route can safely use `current_user.id`

### If auth fails

It raises:

```python
HTTPException(status_code=401, detail="...")
```

So the route function itself will not continue.

---

## 6. `get_auth_service`

Code:
- [dependencies/auth.py](/home/ubuntu/Documents/test/Codebot/Codebot/backend/bot/application/dependencies/auth.py#L10)

Function:

```python
def get_auth_service() -> AuthService:
    return AuthService(
        ChatRepository(SessionLocal),
        secret=JWT_SECRET,
        expires_in_seconds=JWT_EXPIRES_SECONDS,
    )
```

### What it does

This is a factory function.

It creates and returns a new `AuthService` object.

### What it returns

It returns:

```python
AuthService(
    repository=ChatRepository(SessionLocal),
    secret=JWT_SECRET,
    expires_in_seconds=JWT_EXPIRES_SECONDS,
)
```

So this service is ready to:
- create guest session
- validate token
- fetch user

### Why this is used

Without this dependency, every route would need to manually write:

```python
auth_service = AuthService(ChatRepository(SessionLocal), ...)
```

Using `Depends(get_auth_service)` keeps route code smaller and cleaner.

---

## 7. `get_chat_service`

Code:
- [chat_history_api.py](/home/ubuntu/Documents/test/Codebot/Codebot/backend/bot/application/router/chat_history/chat_history_api.py#L13)

Function:

```python
def get_chat_service() -> ChatService:
    return ChatService(ChatRepository(SessionLocal))
```

### What it does

This is also a factory dependency.

It creates and returns a `ChatService` object.

### What it returns

It returns:

```python
ChatService(ChatRepository(SessionLocal))
```

So route gets a service object that can:
- create thread
- list threads
- list messages
- prepare streaming
- finalize streaming

### Why route uses this

Example:

```python
def list_messages(
    thread_id: str,
    current_user=Depends(require_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
```

Meaning:
- first authenticate user
- then create chat service
- then execute route logic

Route can now call:

```python
chat_service.list_messages(user_id=current_user.id, thread_id=thread_id)
```

---

## 8. Full dependency chain example

For this route:

```python
@router.get("/threads/{thread_id}/messages")
def list_messages(
    thread_id: str,
    current_user=Depends(require_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
```

FastAPI flow is:

1. request comes in
2. FastAPI reads path parameter `thread_id`
3. FastAPI runs `require_current_user`
4. `require_current_user` runs `bearer_scheme`
5. `require_current_user` runs `get_auth_service`
6. `get_auth_service` returns `AuthService`
7. `require_current_user` validates token and returns user
8. FastAPI runs `get_chat_service`
9. `get_chat_service` returns `ChatService`
10. route function executes with:
    - `thread_id`
    - `current_user`
    - `chat_service`

So the route itself gets ready-made objects and can focus only on business logic.

---

## 9. Simple summary

### `POST /api/auth/guest`

- creates a guest user
- creates token
- returns session data

### `GET /api/auth/me`

- checks the given token
- returns current authenticated user

### `require_current_user`

- protected auth dependency
- reads bearer token
- validates token
- returns logged-in user

### `get_auth_service`

- creates and returns `AuthService`

### `get_chat_service`

- creates and returns `ChatService`

### `Depends(...)`

- tells FastAPI to run helper function first
- injects returned value into route function

---

## 10. One important design point

`require_current_user` does not directly create a token.

It only:
- reads token from request
- verifies token
- returns user

Token creation happens in:

- `AuthService.create_guest_session()`

Token validation happens in:

- `AuthService.get_user_from_token()`

That separation is good because:
- one part creates auth session
- another part protects private routes

