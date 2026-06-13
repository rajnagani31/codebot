from itertools import count
import json
from operator import countOf

from fastapi import APIRouter, Depends, Request, HTTPException

from apps.backend.bot.application.core.database import SessionLocal

from ..webhook.verify_signature import verify_signature
from dotenv import load_dotenv
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.repository.git_repository import CodeReviewRepository
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.service.git_service import CodeReviewService
from apps.backend.bot.application.dependencies.auth import get_current_user
from fastapi import Depends
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.service.pr_resolver import PrResolver
load_dotenv()

import os


router = APIRouter()

def get_code_review_service():
    return CodeReviewService(CodeReviewRepository(SessionLocal))

@router.post("/webhook/github")
async def github_webhook(
    request: Request,
    current_user = 1,
    code_review_service: CodeReviewService = Depends(get_code_review_service),
    ):

    count = 0
    payload = await request.body()

    print("SECRET:", os.getenv("GITHUB_WEBHOOK_SECRET"))
    print("HEADER:", request.headers.get("X-Hub-Signature-256"))
    print("Installation:",request.headers.get("installation"))

    
    secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if not verify_signature(request.headers, payload, secret): # type: ignore

        raise HTTPException(status_code=401, detail="Invalid signature")
    print('type(payload):', type(payload))

    # dict data print
    payload_dict = json.loads(payload)
    # print(json.dumps(payload_dict, indent=4))
    with open("payload.json", "w") as f:
        json.dump(payload_dict, f, indent=4)

    # resolver
    resolver = PrResolver()
    action = resolver.resolver(payload=payload_dict)
    
    # call service to process the webhook event as dict paload
    code_review_service.process_webhook(payload=payload_dict, action=action)
    # TODO: Process the webhook event
    # For now, just return a success response
    print('pr count', count)
    return {"status": "webhook received"}


# action is pending














   
    
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