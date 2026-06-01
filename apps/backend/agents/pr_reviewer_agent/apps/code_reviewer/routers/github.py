from fastapi import APIRouter, Depends, Request, HTTPException

from codebot.apps.backend.bot.application.core.database import SessionLocal

from ..webhook.verify_signature import verify_signature
from dotenv import load_dotenv
from code_reviewer.repository.git_repository import CodeReviewRepository
from code_reviewer.service.git_service import CodeReviewService


load_dotenv()

import os


router = APIRouter()

def get_code_review_service():
    return CodeReviewService(CodeReviewRepository(SessionLocal))

@router.post("/webhook/github")
async def github_webhook(request: Request, code_review_service: CodeReviewService = Depends(get_code_review_service)):
    payload = await request.body()
    print(dict(request.headers))
    print("SECRET:", os.getenv("GITHUB_WEBHOOK_SECRET"))
    print(
        "HEADER:",
        request.headers.get("X-Hub-Signature-256")
    )
    secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if not verify_signature(request.headers, payload, secret):
        print('1')
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # TODO: Process the webhook event
    # For now, just return a success response
    return {"status": "webhook received"}
    