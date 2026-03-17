from fastapi import FastAPI

app = FastAPI()

@app.post("/items/")
def create_item(item: dict):
    return item
