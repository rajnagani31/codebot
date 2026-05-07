
import asyncio
import time , threading

def background_worker():
    while True:
        time.sleep(1)
        print(f"Logging the system health ")

async def fetch_orders():
    await asyncio.sleep(5)
    print("🎁 Order fetched")


t = threading.Thread(target=background_worker,daemon=True)
t.start()   
asyncio.run(fetch_orders())