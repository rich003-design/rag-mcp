This is a small RAG client + web API that talks to a separate MCP RAG server (the “rag-memory-mcp” server) and exposes easy HTTP endpoints so you can see RAG steps happen:
•	/ingest → store a document
•	/chunk → split it into chunks
•	/embed → turn chunks into vectors
•	/search → retrieve relevant chunks (RAG retrieval)

I deployed this app to Cloud Run, so you can call those endpoints from anywhere and watch the steps in Cloud Logging.
The heavy lifting (vector DB, knowledge-graph features, etc.) lives inside the MCP server you connect to, not in your repo. 

Key files (what they do)
•	app.py (or main.py in earlier versions): FastAPI app that exposes /ingest, /chunk, /embed, /search. Each endpoint asks your agent to call the MCP tools.
•	client.py: sets up the agent plus LLM (OpenAI via OpenAIAugmentedLLM) and connects to the MCP server. The agent then uses tool-calling to invoke the server’s tools (e.g., storeDocument, chunkDocument, embedChunks, hybridSearch).
•	mcp_agent.config.yaml: tells the agent which MCP server(s) to connect to (e.g., rag-memory-mcp) and how.
•	pyproject.toml: Python deps (FastAPI, uvicorn, mcp_agent, OpenAI SDK, etc.).
•	GitHub Actions deploy.yaml (in .github/workflows/): builds a Docker image, pushes to Artifact Registry, and deploys to Cloud Run.

The vector store lives on the MCP server. Our client asks that server to embed and search; the server can use Qdrant or a local/persistent store depending on configuration. We’re decoupled from the storage so we can swap backends without changing our client.

Libraries & pieces used:
•	FastAPI + uvicorn → tiny web API so you can hit endpoints (/ingest, /search, …).
•	mcp_agent → a Python agent framework that connects to MCP servers and does tool-calling.
•	OpenAI SDK (via OpenAIAugmentedLLM) → the LLM that reasons & decides which MCP tool to call.
•	Model Context Protocol (MCP) → standard way to expose tools like “storeDocument”, “embedChunks”, “hybridSearch”. Your app is the MCP client; the RAG server is the MCP server. (The specific server, rag-memory-mcp, adds knowledge-graph + vector retrieval capabilities. ) PulseMCP+1
•	GitHub Actions + Cloud Run → CI/CD and serverless hosting.

How the workflow runs (end to end)
- We call POST /ingest with text + metadata.
- The FastAPI route asks the agent to “call storeDocument” on the MCP server.
- The server stores it (and may write nodes/edges for the graph).
- We call POST /chunk with the same documentId.
- The agent asks the server to run chunkDocument.
- The server splits the doc (e.g., by paragraphs/tokens) and remembers the chunks.
- We call POST /embed.
- The agent asks the server to run embedChunks.
- The server creates embeddings and saves them into the vector store.
- We call GET /search?q=…
- The agent asks the server to run hybrid retrieval (semantic vectors + graph/context filters).
- The server returns the most relevant chunks; your route returns a short summary.
- Throughout, the app writes structured logs so you can see: storeDocument, chunkDocument, embedChunks, hybridSearch in Cloud Logging.

The agent is like a smart coordinator:
•	It reads ourrequest (e.g., “Please store this doc” or “Search for X”).
•	It uses the LLM to decide which tool on the server to call.
•	It calls the tool via MCP, then returns the server’s result to your HTTP client.
•	It doesn’t store data itself; it delegates to the MCP server that owns the DB & vector index.
