import json
from fastapi import APIRouter, Depends, Request, HTTPException
from apps.backend.bot.application.core.database import SessionLocal
from apps.backend.bot.application import config
from ..webhook.verify_signature import verify_signature
from dotenv import load_dotenv
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.repository.git_repository import (
    CodeReviewRepository,
)
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.service.git_service import (
    CodeReviewService,
)
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.service.pr_resolver import (
    PrResolver,
)
from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.tasks import (
    review_pull_request,
)

from apps.backend.shared.auth import UserPrincipal, get_current_user_from_token

load_dotenv()

router = APIRouter()


def get_code_review_service():
    return CodeReviewService(CodeReviewRepository(SessionLocal))


@router.post("/webhook/github")
async def github_webhook(
    request: Request,
    current_user = Depends(get_current_user_from_token),
    code_review_service: CodeReviewService = Depends(get_code_review_service),
):

    payload = await request.body()

    if not config.GITHUB_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=500, detail="GitHub webhook secret is not configured"
        )

    if not verify_signature(request.headers, payload, config.GITHUB_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload_dict = json.loads(payload)
    # print(json.dumps(payload_dict, indent=4))
    
    # print(json.dumps(payload_dict, indent=4))
    with open("payload.json", "w") as f:
        json.dump(payload_dict, f, indent=4)

    github_event = request.headers.get("X-GitHub-Event")

    if github_event in {"installation", "installation_repositories"}:
        print("[Github events:]",github_event)
        repositories = code_review_service.process_installation_webhook(
            payload=payload_dict
        )
        return {"status": "installation received", "repositories": len(repositories)}

    resolver = PrResolver()
    action = resolver.resolver(payload=payload_dict)
    pull_request = code_review_service.process_webhook(payload=payload_dict, action=action)
    review_job_id = None

    print('[Pull Request]', pull_request)
    if pull_request is not None:
        review_job_id = code_review_service.repository.get_latest_queued_review_job_id(
            pull_request.id
        )
        if review_job_id is not None:
            print(f"[Review Job ID] {review_job_id} - Queued for review")
            review_pull_request.delay(review_job_id)

    return {"status": "webhook received", "review_job_id": review_job_id}


# action is pendingdocker compose up -d db redis


from fastapi import FastAPI

app = FastAPI()


@router.get("/me")
async def get_authenticated_agent_user(current_user: UserPrincipal = Depends(get_current_user_from_token)):
    return {
        "status": "authenticated",
        "user": current_user,
        "message": "Authenticated user successfully accessed NeroAI Code Review service."
    }


@router.get("/items/")
async def read_items(
    q: str | None = None,
    current_user: UserPrincipal = Depends(get_current_user_from_token),
):
    results = {
        "authenticated_user_id": current_user.id,
        "items": [{"item_id": "Foo"}, {"item_id": "Bar"}],
    }
    if q:
        results.update({"q": q})
    return results


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
