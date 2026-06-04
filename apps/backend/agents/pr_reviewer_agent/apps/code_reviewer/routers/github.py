import json

from fastapi import APIRouter, Depends, Request, HTTPException

from bot.application.core.database import SessionLocal

from ..webhook.verify_signature import verify_signature
from dotenv import load_dotenv
from agents.pr_reviewer_agent.apps.code_reviewer.repository.git_repository import CodeReviewRepository
from agents.pr_reviewer_agent.apps.code_reviewer.service.git_service import CodeReviewService


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
    print("HEADER:", request.headers.get("X-Hub-Signature-256"))
    print("Installation:",request.headers.get("installation"))

    
    secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if not verify_signature(request.headers, payload, secret):

        raise HTTPException(status_code=401, detail="Invalid signature")
    print('type(payload):', type(payload))

    # dict data print
    payload_dict = json.loads(payload)
    print(json.dumps(payload_dict, indent=4))
    with open("payload.json", "w") as f:
        json.dump(payload_dict, f, indent=4)
    # call service to process the webhook event as dict paload
    code_review_service.create_pull_request(payload=payload_dict)
    
    # TODO: Process the webhook event
    # For now, just return a success response
    return {"status": "webhook received"}





















   
    
# current
"""
GitHub App
      ↓
Installed on your codebot repo
      ↓
Webhook
      ↓
FastAPI
"""

# future
"""
User
   ↓
Install CodeRabbit GitHub App
   ↓
Select repositories
   ↓
GitHub creates installation
   ↓
Webhook events start flowing
"""

# final

"""
User installs GitHub App
          ↓
GitHub Installation Created
          ↓
Store installation_id
          ↓
PR Opened
          ↓
Webhook
          ↓
Generate Installation Token
          ↓
Fetch PR Files
          ↓
AI Review
          ↓
Post GitHub Review
"""