#!/usr/bin/env python3
"""
A2AAgent Function Testing

Focus on testing A2AAgent functionality, including connection, communication, error handling, etc.
"""

import asyncio
import os
import sys
import traceback

from agno.models.openai import OpenAIChat
from agno.team.team import Team
from agno_a2a_ext.agent.a2a.a2a_agent import A2AAgent
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
api_key = os.environ.get("OPENAI_API_KEY")
base_url = os.environ.get("OPENAI_API_PROXY")

model = OpenAIChat(id="gpt-4o", api_key=api_key, base_url=base_url)


class A2AAgentTester:
    """A2AAgent Tester"""

    def __init__(self):
        self.remote_search_agent = None
        self.remote_analysis_agent = None
        self.remote_team_agent = None
        self.local_team = None

    async def setup_agents(self):
        """Setup A2AAgent"""
        print("Setting up A2AAgent...")

        # Create A2AAgent to connect to remote services
        self.remote_search_agent = A2AAgent(
            base_url="http://localhost:8081/",
            name="RemoteSearchAgent",
            role="Remote Search Agent",
            agent_id="8e45f5a1-c032-4c6c-9913-2f3c4a8b5e01"
        )

        self.remote_analysis_agent = A2AAgent(
            base_url="http://localhost:8082/",
            name="RemoteAnalysisAgent",
            role="Remote Analysis Agent",
            agent_id="6a72c340-9b5d-48e5-b8c7-f21a0d3e94fa"
        )

        # Create A2AAgent connected to TeamServer
        self.remote_team_agent = A2AAgent(
            base_url="http://localhost:8083/",
            name="RemoteTeamAgent",
            role="Remote Team Agent",
            agent_id="73406249-a559-456b-88ff-68475df7c7ae"
        )

        # Create local team
        self.local_team = Team(
            name="Local Team",
            members=[self.remote_search_agent, self.remote_analysis_agent],
            mode="coordinate",
            model=model,
            team_id="8d97f474-c0a6-4973-bd14-a954296e54be"
        )

        print("✓ A2AAgent setup completed")

    async def test_remote_search_agent(self):
        """Test remote search agent"""
        print("\n=== Testing Remote Search Agent ===")

        try:
            response = await self.remote_search_agent.arun("What is your role?")
            print(f"✓ Remote search agent response successful")
            print(f"  Response type: {type(response).__name__}")
            print(f"  Response content: {response.content[:100]}...")
            return True
        except Exception as e:
            print(f"❌ Remote search agent test failed: {e}")
            return False

    async def test_remote_analysis_agent(self):
        """Test remote analysis agent"""
        print("\n=== Testing Remote Analysis Agent ===")

        try:
            response = await self.remote_analysis_agent.arun("Please introduce your analysis capabilities")
            print(f"✓ Remote analysis agent response successful")
            print(f"  Response type: {type(response).__name__}")
            print(f"  Response content: {response.content[:100]}...")
            return True
        except Exception as e:
            print(f"❌ Remote analysis agent test failed: {e}")
            return False

    async def test_remote_team_agent(self):
        """Test remote team agent"""
        print("\n=== Testing Remote Team Agent ===")

        try:
            response = await self.remote_team_agent.arun("Please introduce your team")
            print(f"✓ Remote team agent response successful")
            print(f"  Response type: {type(response).__name__}")
            print(f"  Response content: {response.content[:100]}...")
            return True
        except Exception as e:
            print(f"❌ Remote team agent test failed: {e}")
            return False

    async def test_local_team_with_a2a_agents(self):
        """Test local team (with A2AAgent)"""
        print("\n=== Testing Local Team (with A2AAgent) ===")

        try:
            # Directly test the team, without complex error handling
            response = await self.local_team.arun("Please have team members collaborate to introduce Shenzhen")

            if response and hasattr(response, 'content'):
                print(f"✓ Local team test successful")
                print(f"  Response content: {response.content[:100]}...")
                return True
            else:
                print("❌ Local team test failed")
                return False

        except Exception as e:
            print(f"❌ Local team test exception: {e}")
            return False

    async def test_streaming_responses(self):
        """Test streaming responses"""
        print("\n=== Testing Streaming Responses ===")

        try:
            # Test search agent's streaming response
            print("Testing search agent streaming response...")
            stream_response = await self.remote_search_agent.arun(
                "Please introduce your capabilities in detail",
                stream=True
            )

            full_content = ""
            async for chunk in stream_response:
                if hasattr(chunk, 'content'):
                    full_content += chunk.content
                    print(f"  Streaming chunk: {chunk.content}")
                elif isinstance(chunk, str):
                    full_content += chunk
                    print(f"  Streaming chunk: {chunk}")

            print(f"✓ Streaming response test successful")
            print(f"  Full content length: {len(full_content)} characters")
            return True

        except Exception as e:
            print(f"❌ Streaming response test failed: {e}")
            return False

    async def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("A2AAgent Function Testing")
        print("=" * 60)

        # Set up agents
        await self.setup_agents()

        # Run tests
        results = {}

        results['remote_search'] = await self.test_remote_search_agent()
        results['remote_analysis'] = await self.test_remote_analysis_agent()
        results['remote_team'] = await self.test_remote_team_agent()
        results['local_team'] = await self.test_local_team_with_a2a_agents()
        results['streaming'] = await self.test_streaming_responses()

        # Test result summary
        print("\n" + "=" * 60)
        print("A2AAgent Test Results")
        print("=" * 60)

        for test_name, result in results.items():
            status = "✓ Passed" if result else "❌ Failed"
            print(f"  {test_name}: {status}")

        all_passed = all(results.values())
        if all_passed:
            print("\n🎉 All A2AAgent tests passed!")
            print("A2AAgent functionality is normal and can be used.")
        else:
            print("\n⚠️  部分A2AAgent测试失败")
            print("需要检查A2AAgent的实现或远程服务状态。")

        return all_passed

    async def cleanup(self):
        """Clean up resources"""
        print("\nCleaning up A2AAgent resources...")

        if self.remote_search_agent:
            await self.remote_search_agent.close()
        if self.remote_analysis_agent:
            await self.remote_analysis_agent.close()
        if self.remote_team_agent:
            await self.remote_team_agent.close()

        print("✓ A2AAgent resources cleaned")


async def main():
    """Main function"""
    tester = A2AAgentTester()

    try:
        success = await tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 130
    except Exception as e:
        print(f"\nError during test: {str(e)}")
        traceback.print_exc()
        return 1
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"Startup failed: {e}")
        sys.exit(1)
