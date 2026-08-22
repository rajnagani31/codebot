from fastapi.security import HTTPBearer

# HTTPBearer automatically generates the OpenAPI security scheme for Swagger UI (/docs)
bearer_scheme = HTTPBearer(
    scheme_name="BearerAuth",
    description="Paste your JWT access token here (e.g. from /api/auth/login)",
    auto_error=False,
)
