from fastapi import FastAPI, Request

from .config import initialize_database
from .router.auth.auth_api import router as auth_router
from .router.chat_history.chat_history_api import router as chat_history_router
# Use a relative import so this module works when loaded as `bot.application.main`
from .router.llm_api.chat_api import router as chat_router


app = FastAPI()
app.add_event_handler("startup", initialize_database)
app.include_router(auth_router, prefix="/api/auth")
app.include_router(chat_history_router, prefix="/api")
app.include_router(chat_router, prefix="/api")

