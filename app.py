# app.py
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
def health():
    return {"ok": True}

# Optional: a trigger endpoint you can hit if you want to run your RAG flow from the web.
# Keep it quick; avoid long-running CPU here.
@app.post("/run")
def run_workflow():
    # TODO: call a lightweight function or queue a background task
    # e.g., kick off your MCP client logic asynchronously
    return JSONResponse({"status": "started"})