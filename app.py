# app.py
import os
import json
import asyncio
import logging
from fastapi import FastAPI, Body, Query
from fastapi.responses import JSONResponse

from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

logger = logging.getLogger("rag")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="RAG MCP Client")

# Create one global MCPApp; connect to the rag-memory MCP server when needed
mcp_app = MCPApp(name="rag_client_observer")

async def get_agent():
    # Start a client session per request (simple & safe for Cloud Run)
    client_cm = mcp_app.run()  # context manager
    client = await client_cm.__aenter__()
    agent = Agent(
        name="rag-agent",
        instruction="Use rag-memory tools to store, chunk, embed, and search documents.",
        server_names=["rag-memory"],
    )
    await agent.__aenter__()
    llm = await agent.attach_llm(OpenAIAugmentedLLM)
    return client_cm, client, agent, llm

async def cleanup(client_cm, agent):
    try:
        await agent.__aexit__(None, None, None)
    finally:
        await client_cm.__aexit__(None, None, None)

@app.get("/")
def health():
    return {"ok": True}

@app.post("/ingest")
async def ingest(payload: dict = Body(...)):
    """
    Body:
    {
      "id": "ml_intro",
      "content": "Machine learning is ...",
      "metadata": {"type":"edu","topic":"ML"}
    }
    """
    client_cm, client, agent, llm = await get_agent()
    try:
        doc_id = payload["id"]
        content = payload["content"]
        metadata = payload.get("metadata", {})

        # Ask the LLM to call the MCP tools explicitly (the agent/tooling handles the calls)
        resp = await llm.generate_str(
            f"Call tool storeDocument with id='{doc_id}', content={json.dumps(content)}, metadata={json.dumps(metadata)}; then confirm."
        )
        logger.info(json.dumps({"event":"storeDocument","doc_id":doc_id}))

        return JSONResponse({"status":"stored", "doc_id": doc_id, "llm_reply": resp})
    finally:
        await cleanup(client_cm, agent)

@app.post("/chunk")
async def chunk(documentId: str = Body(..., embed=True)):
    client_cm, client, agent, llm = await get_agent()
    try:
        resp = await llm.generate_str(
            f"Call chunkDocument for documentId='{documentId}'; then return the number of chunks."
        )
        logger.info(json.dumps({"event":"chunkDocument","doc_id":documentId}))
        return {"status":"chunked","doc_id":documentId,"llm_reply":resp}
    finally:
        await cleanup(client_cm, agent)

@app.post("/embed")
async def embed(documentId: str = Body(..., embed=True)):
    client_cm, client, agent, llm = await get_agent()
    try:
        resp = await llm.generate_str(
            f"Call embedChunks for documentId='{documentId}'; then confirm."
        )
        logger.info(json.dumps({"event":"embedChunks","doc_id":documentId}))
        return {"status":"embedded","doc_id":documentId,"llm_reply":resp}
    finally:
        await cleanup(client_cm, agent)

@app.get("/search")
async def search(q: str = Query(...), limit: int = 5, useGraph: bool = True):
    client_cm, client, agent, llm = await get_agent()
    try:
        resp = await llm.generate_str(
            f"Use hybridSearch for query={json.dumps(q)}, limit={limit}, useGraph={str(useGraph).lower()}. Summarize the top results with ids and scores."
        )
        logger.info(json.dumps({"event":"hybridSearch","query":q,"limit":limit,"useGraph":useGraph}))
        return {"query": q, "summary": resp}
    finally:
        await cleanup(client_cm, agent)
