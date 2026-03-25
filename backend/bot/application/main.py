from fastapi import FastAPI, Request

# Use a relative import so this module works when loaded as `bot.application.main`
from .router.llm_api.chat_api import router as chat_router


app = FastAPI()
app.include_router(chat_router, prefix="/api")


