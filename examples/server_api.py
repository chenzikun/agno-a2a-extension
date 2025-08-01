import asyncio
import os

from agno.agent.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team.team import Team
from agno_a2a_ext.agent.a2a.a2a_agent import A2AAgent
from agno_a2a_ext.servers.api import ServerAPI

api_key = os.environ.get("OPENAI_API_KEY")
base_url = os.environ.get("OPENAI_API_PROXY")
model = OpenAIChat(id="gpt-4o", api_key=api_key, base_url=base_url)


async def main():
    # Initialize variables so they can be safely accessed in finally block
    remote_search_agent = None
    remote_analysis_agent = None
    remote_team_agent = None
    server_api = None

    try:
        # Create A2AAgent to connect to remote services
        print("Creating A2AAgent...")
        remote_search_agent = A2AAgent(
            base_url="http://localhost:8081/",  # Ensure trailing slash
            name="RemoteSearchAgent",
            role="Remote Search Agent",
            agent_id="8e45f5a1-c032-4c6c-9913-2f3c4a8b5e01"  # Use UUID format
        )

        remote_analysis_agent = A2AAgent(
            base_url="http://localhost:8082/",  # Ensure trailing slash
            name="RemoteAnalysisAgent",
            role="Remote Analysis Agent",
            agent_id="6a72c340-9b5d-48e5-b8c7-f21a0d3e94fa"  # Use UUID format
        )

        # Create local agent
        local_agent = Agent(
            introduction="You are a programming expert responsible for handling programming-related questions",
            name="LocalAgent",
            role="LocalAgent",
            model=model,
            agent_id="8d97f474-c0a6-4973-bd14-xx54296e54be"
        )

        # Create local team
        local_team = Team(
            name="Local Team",
            members=[remote_search_agent, local_agent],
            mode="coordinate",
            model=model,
            team_id="8d97f474-c0a6-4973-bd14-a954296e54be"
        )

        # Create A2AAgent connected to TeamServer
        print("Creating A2AAgent connected to TeamServer...")
        remote_team_agent = A2AAgent(
            base_url="http://localhost:8083/",  # Ensure trailing slash
            name="RemoteTeamAgent",
            role="Remote Team Agent",
            agent_id="73406249-a559-456b-88ff-68475df7c7ae"
        )

        # Start ServerAPI
        print("Starting ServerAPI...")
        server_api = ServerAPI(
            agents=[remote_team_agent, remote_search_agent, remote_analysis_agent, local_agent],
            teams=[local_team],
            port=8084
        )
        await server_api.start()

        print("\n" + "=" * 50)
        print("Services started:")
        print("=" * 50)
        print(f"Search Agent: http://localhost:8081")
        print(f"Analysis Agent: http://localhost:8082")
        print(f"Team: http://localhost:8083")
        print(f"ServerAPI: http://localhost:8084")
        print("\nYou can test ServerAPI with the following commands:")
        print('curl -X GET http://localhost:8084/agents')
        print('curl -X GET http://localhost:8084/teams')
        print(
            'curl -X POST http://localhost:8084/agents/8e45f5a1-c032-4c6c-9913-2f3c4a8b5e01/run -H "Content-Type: application/json" -d \'{"message": "Hello"}\'')
        print(
            'curl -X POST http://localhost:8084/teams/8d97f474-c0a6-4973-bd14-a954296e54be/run -H "Content-Type: application/json" -d \'{"message": "Please collaborate as a team"}\'')

        print("\nPress Ctrl+C to stop services...")

        # Keep service running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nReceived stop signal, stopping services...")
    finally:
        # Stop all services
        if server_api:
            await server_api.stop()

        # Close A2A connections
        if remote_search_agent:
            await remote_search_agent.close()
        if remote_analysis_agent:
            await remote_analysis_agent.close()
        if remote_team_agent:
            await remote_team_agent.close()

        print("All services stopped")


if __name__ == "__main__":
    asyncio.run(main())
