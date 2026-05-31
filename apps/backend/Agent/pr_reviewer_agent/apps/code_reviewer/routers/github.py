from fastapi import APIRouter, Request, HTTPException
from ..webhook.verify_signature import verify_signature
from dotenv import load_dotenv
load_dotenv()
import os


router = APIRouter()


@router.post("/github")
async def github_webhook(request: Request):
    payload = await request.body()


    secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if not verify_signature(request.headers, payload, secret):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # TODO: Process the webhook event
    # For now, just return a success response
    return {"status": "webhook received"}
    