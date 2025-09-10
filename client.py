import asyncio
from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

app = MCPApp(name="rag_client_demo")

async def run():
    async with app.run() as client:
        agent = Agent(
            name="rag-agent",
            instruction="Use rag-memory tools to store, chunk, embed, and search documents.",
            server_names=["rag-memory"]
        )

        async with agent:
            tools = await agent.list_tools()
            client.logger.info("Available Tools", data=tools)

            llm = await agent.attach_llm(OpenAIAugmentedLLM)

            # Store a document
            await llm.generate_str(
                "Call tool storeDocument with id='ml_intro', "
                "content='Machine learning is a subset of AI...', "
                "metadata={type:'educational', topic:'ML'}; then confirm."
            )

            # Chunk + Embed
            await llm.generate_str(
                "Call chunkDocument for documentId='ml_intro'; "
                "then embedChunks for the same doc; then confirm."
            )

            # Search
            result = await llm.generate_str(
                "Use hybridSearch for 'applications of artificial intelligence', "
                "limit=5, useGraph=true. Summarize results."
            )

            print("\n=== Hybrid Search Results ===\n", result)

if __name__ == "__main__":
    asyncio.run(run())