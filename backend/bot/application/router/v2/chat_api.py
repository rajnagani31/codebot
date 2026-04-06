# SSE

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import redis
import json
import asyncio
import time

load_dotenv()

router = APIRouter(prefix="/v2/chat/SSE", tags=["SSE"])

rq = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


@router.post("/trade")
def create_trade(user_id: str, item_id: str):

    trade = {
        "user_id": user_id,
        "item_id": item_id,
        "status": "BUY",
        "comment": "I want to buy this item.",
    }

    # here might be some logic to save the trade to a database, etc.

    # then publish the trade to the Redis channel
    rq.publish("trade_channel", json.dumps(trade))

    return {"message": " your trade request has been sent."}


async def event_generator(user_id: int):
    pubsub = rq.pubsub()
    pubsub.subscribe("trade_channel")

    last_keep_alive = time.time()

    while True:  # 🔥 infinite loop required
        message = pubsub.get_message()

        if message and message["type"] == "message":
            data = json.loads(message["data"])

            if data["user_id"] == str(user_id):
                yield f"data: {json.dumps(data)}\n\n"

                text = f'someone bought item {data["item_id"]} 👀 Interested?'

                yield f"data: {text}\n\n"

        # Send keep-alive message periodically
        if time.time() - last_keep_alive > 3:  # Send every 30 seconds
            yield f"keep-alive: {json.dumps({'status': 'connected', 'user_id': user_id})}\n\n"
            last_keep_alive = time.time()

        await asyncio.sleep(0.5)  # 🔥 VERY IMPORTANT


@router.get("/sse/trade/stream/{user_id}")
async def notification_stream(user_id: int):
    return StreamingResponse(event_generator(user_id), media_type="text/event-stream")
    # return {'yes':'yes'}
