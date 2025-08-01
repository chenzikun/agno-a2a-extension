# examples/a2a_integration_example.py
import asyncio
import sys
import os

# Ensure correct import of project modules
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))


# Set OpenAI API key

from agno.agent.agent import Agent
from agno.models.openai import OpenAIChat
import traceback
from agno_a2a_ext.servers.agent import AgentServer
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
api_key = os.environ.get("OPENAI_API_KEY")
base_url = os.environ.get("OPENAI_API_PROXY")
model = OpenAIChat(id="gpt-4o", api_key=api_key, base_url=base_url)


async def main():
    # 1. Create basic Agent
    print("Creating basic Agent...")
    analysis_agent = Agent(
        name="AnalysisAgent",
        role="Analysis Expert",
        agent_id="analysis",
        model=model
    )
    try:

        # Create server
        print("Starting AgentServer...")
        analysis_server = AgentServer(agent=analysis_agent, port=8082)
        await analysis_server.start()
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
        if 'analysis_server' in locals():
            try:
                await analysis_server.stop()
            except Exception as e:
                print(f"Error stopping server: {str(e)}")
        print("Service stopped")

asyncio.run(main())