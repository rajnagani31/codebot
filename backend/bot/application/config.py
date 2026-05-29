import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from bot.application.model.pg_vectore import Base
from bot.application.model import chat_history  # noqa: F401
from bot.application.model import web_search  # noqa: F401


PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env", override=False)


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost/codebot",
)
JWT_SECRET = os.getenv("JWT_SECRET", "codebot-dev-jwt-secret")
ACCESS_TOKEN_EXPIRES_SECONDS = int(os.getenv("ACCESS_TOKEN_EXPIRES_SECONDS", str(60 * 15)))
REFRESH_TOKEN_EXPIRES_SECONDS = int(os.getenv("REFRESH_TOKEN_EXPIRES_SECONDS", str(60 * 60 * 24 * 30)))
GUEST_SESSION_EXPIRES_SECONDS = int(os.getenv("GUEST_SESSION_EXPIRES_SECONDS", str(60 * 60 * 24 * 3)))
GUEST_MESSAGE_LIMIT = int(os.getenv("GUEST_MESSAGE_LIMIT", "5"))
AUTH_COOKIE_SECURE = os.getenv("AUTH_COOKIE_SECURE", "false").lower() == "true"
AUTH_COOKIE_SAMESITE = os.getenv("AUTH_COOKIE_SAMESITE", "lax")
AUTH_COOKIE_DOMAIN = os.getenv("AUTH_COOKIE_DOMAIN") or None
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://127.0.0.1:5173")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
AUTO_CREATE_SCHEMA = os.getenv("AUTO_CREATE_SCHEMA", "false").lower() == "true"
AUTO_MIGRATE_LEGACY_AUTH_SCHEMA = os.getenv("AUTO_MIGRATE_LEGACY_AUTH_SCHEMA", "true").lower() == "true"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
