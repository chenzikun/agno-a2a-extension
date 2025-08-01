#!/usr/bin/env python3
"""
A2A Protocol Compatibility Test Script

Based on a2a-python's test_client.py standard testing pattern,
focusing on validating standard A2A protocol implementation, not data processing.
"""

import asyncio
import sys
import argparse
from uuid import uuid4
from typing import Dict
import httpx
from a2a.client import A2AClient
from a2a.types import (
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
    Role,
    Message,
    TextPart,
)
from a2a.client.errors import A2AClientHTTPError, A2AClientJSONError

# Default timeout settings
DEFAULT_TIMEOUT = 30.0


class A2AProtocolTester:
    """A2A Protocol Standard Tester"""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        self.timeout = timeout

    async def test_agent_card_retrieval(self, agent_url: str) -> bool:
        """
        Test Agent Card retrieval functionality
        
        Args:
            agent_url: Agent service URL
            
        Returns:
            bool: Whether the test was successful
        """
        print(f"\n=== Testing Agent Card Retrieval: {agent_url} ===")

        try:
            limits = httpx.Limits(max_connections=5, max_keepalive_connections=5)
            async with httpx.AsyncClient(timeout=self.timeout, limits=limits) as httpx_client:
                # Get Agent Card
                client = await A2AClient.get_client_from_agent_card_url(
                    httpx_client, agent_url
                )

                print(f"✓ Successfully retrieved Agent Card")
                print(f"  Agent name: {client.agent_card.name}")
                print(f"  Agent description: {client.agent_card.description}")
                print(f"  Protocol version: {client.agent_card.version}")
                print(f"  Input modes: {client.agent_card.default_input_modes}")
                print(f"  Output modes: {client.agent_card.default_output_modes}")

                if client.agent_card.capabilities:
                    print(f"  Capabilities: {client.agent_card.capabilities}")

                if client.agent_card.skills:
                    print(f"  Skills count: {len(client.agent_card.skills)}")
                    for skill in client.agent_card.skills:
                        print(f"    - {skill.name}: {skill.description}")

                return True

        except A2AClientHTTPError as e:
            print(f"❌ HTTP error: {e}")
            if hasattr(e, '__cause__') and e.__cause__:
                print(f"   Original error: {e.__cause__}")
            return False
        except A2AClientJSONError as e:
            print(f"❌ JSON parsing error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unknown error: {e}")
            return False

    async def test_message_send(self, agent_url: str, message: str = "Hello") -> bool:
        """
        Test standard message sending functionality
        
        Args:
            agent_url: Agent service URL
            message: Message content to send
            
        Returns:
            bool: Whether the test was successful
        """
        print(f"\n=== Testing Standard Message Sending: {agent_url} ===")

        try:
            limits = httpx.Limits(max_connections=5, max_keepalive_connections=5)
            async with httpx.AsyncClient(timeout=self.timeout, limits=limits) as httpx_client:
                client = await A2AClient.get_client_from_agent_card_url(
                    httpx_client, agent_url
                )

                # Create standard A2A message request
                request_id = uuid4().hex
                message_obj = Message(
                    role=Role.user,
                    parts=[TextPart(text=message)],
                    messageId=uuid4().hex
                )

                request = SendMessageRequest(
                    id=request_id,
                    params=MessageSendParams(message=message_obj)
                )

                print(f"Sending message: '{message}'")
                print(f"Request ID: {request_id}")

                # Send request
                response = await client.send_message(request)

                print(f"✓ Successfully received response")
                print(f"  Response ID: {response.root.id}")
                print(f"  Response role: {response.root.result.role}")

                # Check response structure
                if hasattr(response.root.result, 'parts') and response.root.result.parts:
                    response_text = ""
                    for part in response.root.result.parts:
                        if hasattr(part.root, 'text'):
                            response_text += part.root.text

                    print(f"  Response content: {response_text[:100]}{'...' if len(response_text) > 100 else ''}")

                return True

        except A2AClientHTTPError as e:
            print(f"❌ HTTP error: {e}")
            if hasattr(e, '__cause__') and e.__cause__:
                print(f"   Original error: {e.__cause__}")
            return False
        except A2AClientJSONError as e:
            print(f"❌ JSON parsing error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unknown error: {e}")
            return False

    async def test_streaming_message_send(self, agent_url: str, message: str = "Hello streaming") -> bool:
        """
        Test streaming message sending functionality
        
        Args:
            agent_url: Agent service URL
            message: Message content to send
            
        Returns:
            bool: Whether the test was successful
        """
        print(f"\n=== Testing Streaming Message Sending: {agent_url} ===")

        try:
            limits = httpx.Limits(max_connections=5, max_keepalive_connections=5)
            async with httpx.AsyncClient(timeout=self.timeout, limits=limits) as httpx_client:
                client = await A2AClient.get_client_from_agent_card_url(
                    httpx_client, agent_url
                )

                # Check if streaming is supported
                if not client.agent_card.capabilities.streaming:
                    print("⚠️  This agent doesn't support streaming, skipping streaming test")
                    return True

                # Create standard A2A streaming message request
                request_id = uuid4().hex
                message_obj = Message(
                    role=Role.user,
                    parts=[TextPart(text=message)],
                    messageId=uuid4().hex
                )

                request = SendStreamingMessageRequest(
                    id=request_id,
                    params=MessageSendParams(message=message_obj)
                )

                print(f"Sending streaming message: '{message}'")
                print(f"Request ID: {request_id}")

                # Send streaming request
                response_count = 0
                full_response = ""

                async for response in client.send_message_streaming(request):
                    response_count += 1
                    print(f"  Received streaming response #{response_count}")

                    if hasattr(response.root.result, 'parts') and response.root.result.parts:
                        for part in response.root.result.parts:
                            if hasattr(part.root, 'text'):
                                chunk_text = part.root.text
                                full_response += chunk_text
                                print(f"    Chunk content: {chunk_text}")

                print(f"✓ Streaming completed")
                print(f"  Total response chunks: {response_count}")
                print(f"  Full response length: {len(full_response)} characters")

                return True

        except A2AClientHTTPError as e:
            print(f"❌ HTTP error: {e}")
            if hasattr(e, '__cause__') and e.__cause__:
                print(f"   Original error: {e.__cause__}")
            return False
        except A2AClientJSONError as e:
            print(f"❌ JSON parsing error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unknown error: {e}")
            return False

    async def test_protocol_compliance(self, agent_url: str) -> Dict[str, bool]:
        """
        Test A2A protocol compliance
        
        Args:
            agent_url: Agent service URL
            
        Returns:
            Dict[str, bool]: Results of each test
        """
        print(f"\n=== A2A Protocol Compliance Testing: {agent_url} ===")

        results = {}

        # 1. Test Agent Card retrieval
        results['agent_card'] = await self.test_agent_card_retrieval(agent_url)

        # 2. Test standard message sending
        results['message_send'] = await self.test_message_send(agent_url)

        # 3. Test streaming message sending
        results['streaming'] = await self.test_streaming_message_send(agent_url)

        return results


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="A2A Protocol Standard Compliance Testing")
    parser.add_argument('--agent-url', default="http://localhost:8081", help="Agent service URL")
    parser.add_argument('--team-url', default="http://localhost:8083", help="Team service URL")
    parser.add_argument('--timeout', type=float, default=DEFAULT_TIMEOUT, help="HTTP request timeout (seconds)")
    parser.add_argument('--skip-team', action='store_true', help="Skip team testing")
    parser.add_argument('--skip-streaming', action='store_true', help="Skip streaming testing")
    return parser.parse_args()


async def main():
    """Main function"""
    args = parse_args()

    print("=" * 60)
    print("A2A Protocol Standard Compliance Testing")
    print("=" * 60)
    print(f"Agent URL: {args.agent_url}")
    if not args.skip_team:
        print(f"Team URL: {args.team_url}")
    print(f"Timeout setting: {args.timeout} seconds")
    print(f"Streaming test: {'Disabled' if args.skip_streaming else 'Enabled'}")
    print("=" * 60)

    tester = A2AProtocolTester(timeout=args.timeout)

    # Test agent service
    print("\n" + "=" * 40)
    print("Testing Agent Service")
    print("=" * 40)

    agent_results = await tester.test_protocol_compliance(args.agent_url)

    # Test team service (if not skipped)
    team_results = None
    if not args.skip_team:
        print("\n" + "=" * 40)
        print("Testing Team Service")
        print("=" * 40)

        team_results = await tester.test_protocol_compliance(args.team_url)

    # Test result summary
    print("\n" + "=" * 60)
    print("A2A Protocol Compliance Test Results")
    print("=" * 60)

    # Agent test results
    print("\nAgent Service Test Results:")
    for test_name, result in agent_results.items():
        status = "✓ Passed" if result else "❌ Failed"
        print(f"  {test_name}: {status}")

    # Team test results
    if team_results:
        print("\nTeam Service Test Results:")
        for test_name, result in team_results.items():
            status = "✓ Passed" if result else "❌ Failed"
            print(f"  {test_name}: {status}")

    # Overall assessment
    all_agent_tests_passed = all(agent_results.values())
    all_team_tests_passed = all(team_results.values()) if team_results else True

    if all_agent_tests_passed and all_team_tests_passed:
        print("\n🎉 All A2A protocol tests passed!")
        print("This service fully complies with A2A protocol standards.")
        return 0
    else:
        print("\n⚠️  Some A2A protocol tests failed")
        print("This service doesn't fully comply with A2A protocol standards, needs further inspection.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nError during test: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
