from fastapi import FastAPI, Request

from .config import AUTO_CREATE_SCHEMA, engine
from .model.pg_vectore import Base

from .router.auth.auth_api import router as auth_router
from .router.chat_history.chat_history_api import router as chat_history_router
# Use a relative import so this module works when loaded as `bot.application.main`
from .router.llm_api.chat_api import router as chat_router


app = FastAPI()


# @app.on_event("startup")
# def initialize_database():
#     if AUTO_CREATE_SCHEMA:
#         Base.metadata.create_all(bind=engine)


app.include_router(auth_router, prefix="/api")
app.include_router(chat_history_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
