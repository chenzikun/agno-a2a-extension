"""
ServerAPI HTTP Interface Testing

Focus on testing ServerAPI's HTTP interface, validating its functionality and protocol compliance.
Assumes ServerAPI is already running (started via server_api.py).
"""
import asyncio
import sys
import traceback

import httpx


class ServerAPITester:
    """ServerAPI Tester"""

    def __init__(self, base_url: str = "http://localhost:8084"):
        self.base_url = base_url

    async def test_health_check_endpoint(self):
        """Test health check endpoint"""
        print("\n=== Testing Health Check Endpoint ===")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health")

                print(f"Status code: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"✓ Health check passed")
                    print(f"  Status: {result.get('status', 'Unknown')}")
                    return True
                else:
                    print(f"❌ Health check failed: {response.text}")
                    return False

        except Exception as e:
            print(f"❌ Failed to test health check endpoint: {e}")
            return False

    async def test_agent_list_endpoint(self):
        """Test agent list endpoint"""
        print("\n=== Testing Agent List Endpoint ===")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/agents")

                print(f"Status code: {response.status_code}")
                if response.status_code == 200:
                    agents = response.json()
                    print(f"✓ Successfully retrieved agent list")
                    print(f"  Agent count: {len(agents)}")
                    for agent in agents:
                        print(f"    - {agent.get('name', 'Unknown')}: {agent.get('role', 'Unknown')}")
                    return True
                else:
                    print(f"❌ Failed to get agent list: {response.text}")
                    return False

        except Exception as e:
            print(f"❌ Failed to test agent list endpoint: {e}")
            return False

    async def test_team_list_endpoint(self):
        """Test team list endpoint"""
        print("\n=== Testing Team List Endpoint ===")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/teams")

                print(f"Status code: {response.status_code}")
                if response.status_code == 200:
                    teams = response.json()
                    print(f"✓ Successfully retrieved team list")
                    print(f"  Team count: {len(teams)}")
                    for team in teams:
                        print(f"    - {team.get('name', 'Unknown')}: {team.get('description', 'Unknown')}")
                    return True
                else:
                    print(f"❌ Failed to get team list: {response.text}")
                    return False

        except Exception as e:
            print(f"❌ Failed to test team list endpoint: {e}")
            return False

    async def test_agent_run_endpoint(self, agent_id: str = "8e45f5a1-c032-4c6c-9913-2f3c4a8b5e01"):
        """Test agent run endpoint"""
        print(f"\n=== Testing Agent Run Endpoint: {agent_id} ===")

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "message": "Hello, please introduce yourself"
                }

                response = await client.post(
                    f"{self.base_url}/agents/{agent_id}/run",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                print(f"Status code: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"✓ Successfully called agent")
                    print(f"  Response content: {result.get('content', 'No content')[:100]}...")
                    return True
                else:
                    print(f"❌ Failed to call agent: {response.text}")
                    return False

        except Exception as e:
            print(f"❌ Failed to test agent run endpoint: {e}")
            return False

    async def test_team_run_endpoint(self, team_id: str = "8d97f474-c0a6-4973-bd14-a954296e54be"):
        """Test team run endpoint"""
        print(f"\n=== Testing Team Run Endpoint: {team_id} ===")

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "message": "Please have team members collaborate to introduce Shenzhen"
                }

                response = await client.post(
                    f"{self.base_url}/teams/{team_id}/run",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                print(f"Status code: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"✓ Successfully called team")
                    print(f"  Response content: {result.get('content', 'No content')[:100]}...")
                    return True
                else:
                    print(f"❌ Failed to call team: {response.text}")
                    return False

        except Exception as e:
            print(f"❌ Failed to test team run endpoint: {e}")
            return False

    async def test_invalid_agent_endpoint(self):
        """Test invalid agent endpoint"""
        print("\n=== Testing Invalid Agent Endpoint ===")

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "message": "Test message"
                }

                response = await client.post(
                    f"{self.base_url}/agents/invalid-agent-id/run",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                print(f"Status code: {response.status_code}")
                if response.status_code == 404:
                    print(f"✓ Correctly handled invalid agent ID")
                    return True
                else:
                    print(f"❌ Failed to properly handle invalid agent ID: {response.text}")
                    return False

        except Exception as e:
            print(f"❌ Failed to test invalid agent endpoint: {e}")
            return False

    async def test_invalid_team_endpoint(self):
        """Test invalid team endpoint"""
        print("\n=== Testing Invalid Team Endpoint ===")

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "message": "Test message"
                }

                response = await client.post(
                    f"{self.base_url}/teams/invalid-team-id/run",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                print(f"Status code: {response.status_code}")
                if response.status_code == 404:
                    print(f"✓ Correctly handled invalid team ID")
                    return True
                else:
                    print(f"❌ Failed to properly handle invalid team ID: {response.text}")
                    return False

        except Exception as e:
            print(f"❌ Failed to test invalid team endpoint: {e}")
            return False

    async def test_invalid_json_payload(self):
        """Test invalid JSON payload"""
        print("\n=== Testing Invalid JSON Payload ===")

        try:
            async with httpx.AsyncClient() as client:
                # Send invalid JSON
                response = await client.post(
                    f"{self.base_url}/agents/8e45f5a1-c032-4c6c-9913-2f3c4a8b5e01/run",
                    data="invalid json",
                    headers={"Content-Type": "application/json"}
                )

                print(f"Status code: {response.status_code}")
                if response.status_code == 422:  # Unprocessable Entity
                    print(f"✓ Correctly handled invalid JSON")
                    return True
                else:
                    print(f"❌ Failed to properly handle invalid JSON: {response.text}")
                    return False

        except Exception as e:
            print(f"❌ Failed to test invalid JSON payload: {e}")
            return False

    async def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("ServerAPI HTTP Interface Testing")
        print("=" * 60)
        print(f"Test target: {self.base_url}")
        print("Note: Please ensure ServerAPI service is running (python examples/server_api.py)")
        print("=" * 60)

        # Run tests
        results = {}

        results['health_check'] = await self.test_health_check_endpoint()
        results['agent_list'] = await self.test_agent_list_endpoint()
        results['team_list'] = await self.test_team_list_endpoint()
        results['agent_run'] = await self.test_agent_run_endpoint()
        results['team_run'] = await self.test_team_run_endpoint()
        results['invalid_agent'] = await self.test_invalid_agent_endpoint()
        results['invalid_team'] = await self.test_invalid_team_endpoint()
        results['invalid_json'] = await self.test_invalid_json_payload()

        # Test result summary
        print("\n" + "=" * 60)
        print("ServerAPI Test Results")
        print("=" * 60)

        for test_name, result in results.items():
            status = "✓ Passed" if result else "❌ Failed"
            print(f"  {test_name}: {status}")

        all_passed = all(results.values())
        if all_passed:
            print("\n🎉 All ServerAPI tests passed!")
            print("ServerAPI functionality is normal, interface responses are correct.")
        else:
            print("\n⚠️  Some ServerAPI tests failed")
            print("Need to check ServerAPI implementation.")

        return all_passed


async def main():
    """Main function"""
    tester = ServerAPITester()

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


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"Startup failed: {e}")
        sys.exit(1)
