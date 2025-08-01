import asyncio
import logging
import os
import traceback

from agno.tools.searxng import Searxng
from agno.agent.agent import Agent
from agno.models.openai import OpenAIChat
from agno_a2a_ext.servers.agent import AgentServer
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
api_key = os.environ.get("OPENAI_API_KEY")
base_url = os.environ.get("OPENAI_API_PROXY")


model = OpenAIChat(id="gpt-4o", api_key=api_key, base_url=base_url)


async def main():
    # 1. Create basic Agent
    print("Creating basic Agent...")
    search_agent = Agent(
        name="SearchAgent",
        role="Search Expert",
        agent_id="search",
        tools=[Searxng(host="http://search.aiapps.autel.com")],
        model=model
    )
    try:
        # Create server
        print("Starting AgentServer...")
        search_server = AgentServer(agent=search_agent, port=8081)
        await search_server.start()
        print("AgentServer is ready")

        # Keep service running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nReceived stop signal, stopping service...")
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        traceback.print_exc()
    finally:
        # Agent object doesn't have stop method, should be server object's method
        if 'search_server' in locals():
            try:
                await search_server.stop()
            except Exception as e:
                print(f"Error stopping server: {str(e)}")
        print("Service stopped")


asyncio.run(main())
