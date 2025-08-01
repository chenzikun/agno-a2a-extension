import asyncio
import os

from agno.tools.searxng import Searxng

from agno.agent.agent import Agent
from agno_a2a_ext.agent.a2a.a2a_agent import A2AAgent
from agno.team.team import Team
from agno.models.openai import OpenAIChat

from agno_a2a_ext.servers.team import TeamServer
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
api_key = os.environ.get("OPENAI_API_KEY")
base_url = os.environ.get("OPENAI_API_PROXY")
model = OpenAIChat(id="gpt-4o", api_key=api_key, base_url=base_url)


async def main():
    # 1. Create basic Agent
    print("Creating basic Agent...")
    local_agent = Agent(
        name="SearchAgent",
        role="Weather Query Expert",
        agent_id="search",
        tools=[Searxng(host="http://search.aiapps.autel.com")],
        model=model
    )

    # Initialize variables so they can be safely accessed in finally block
    remote_search_agent = None
    remote_analysis_agent = None
    team_server = None

    try:
        # 3. Create A2AAgent to connect to remote services
        print("Creating A2AAgent...")
        remote_search_agent = A2AAgent(
            base_url="http://localhost:8081",
            name="RemoteSearchAgent",
            role="Remote Search Agent"
        )

        remote_analysis_agent = A2AAgent(
            base_url="http://localhost:8082",
            name="RemoteAnalysisAgent",
            role="Remote Analysis Agent"
        )

        # 4. Create local Team
        print("Creating local Team...")

        # Add stream_member_events=True attribute to support streaming
        local_team = Team(
            name="Local Team",
            members=[local_agent, remote_search_agent, remote_analysis_agent],
            mode="coordinate",
            model=model,
            team_id="8d97f474-c0a6-4973-bd14-a954296e54be",
            stream_member_events=True  # Add this attribute to enable streaming
        )

        # 5. Start TeamServer
        print("Starting TeamServer...")
        team_server = TeamServer(team=local_team, port=8083)
        await team_server.start()

        # Keep service running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nReceived stop signal, stopping service...")
    finally:
        # Stop all services

        if team_server:
            await team_server.stop()

        # Close A2A connections
        if remote_search_agent:
            await remote_search_agent.close()
        if remote_analysis_agent:
            await remote_analysis_agent.close()

        print("All services stopped")


if __name__ == "__main__":
    asyncio.run(main())
