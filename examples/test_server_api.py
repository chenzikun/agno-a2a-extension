#!/usr/bin/env python3
"""
ServerAPI HTTP接口测试

专注于测试ServerAPI的HTTP接口，验证其功能性和协议合规性。
假设ServerAPI已经在运行（通过server_api.py启动）。
"""

import asyncio
import sys
import traceback

import httpx


class ServerAPITester:
    """ServerAPI测试器"""

    def __init__(self, base_url: str = "http://localhost:8089"):
        self.base_url = base_url

    async def test_health_check_endpoint(self):
        """测试健康检查端点"""
        print("\n=== 测试健康检查端点 ===")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health")

                print(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"✓ 健康检查通过")
                    print(f"  状态: {result.get('status', 'Unknown')}")
                    return True
                else:
                    print(f"❌ 健康检查失败: {response.text}")
                    return False

        except Exception as e:
            print(f"❌ 测试健康检查端点失败: {e}")
            return False

    async def test_agent_list_endpoint(self):
        """测试代理列表端点"""
        print("\n=== 测试代理列表端点 ===")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/agents")

                print(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    agents = response.json()
                    print(f"✓ 成功获取代理列表")
                    print(f"  代理数量: {len(agents)}")
                    for agent in agents:
                        print(f"    - {agent.get('name', 'Unknown')}: {agent.get('role', 'Unknown')}")
                    return True
                else:
                    print(f"❌ 获取代理列表失败: {response.text}")
                    return False

        except Exception as e:
            print(f"❌ 测试代理列表端点失败: {e}")
            return False

    async def test_team_list_endpoint(self):
        """测试团队列表端点"""
        print("\n=== 测试团队列表端点 ===")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/teams")

                print(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    teams = response.json()
                    print(f"✓ 成功获取团队列表")
                    print(f"  团队数量: {len(teams)}")
                    for team in teams:
                        print(f"    - {team.get('name', 'Unknown')}: {team.get('description', 'Unknown')}")
                    return True
                else:
                    print(f"❌ 获取团队列表失败: {response.text}")
                    return False

        except Exception as e:
            print(f"❌ 测试团队列表端点失败: {e}")
            return False

    async def test_agent_run_endpoint(self, agent_id: str = "8e45f5a1-c032-4c6c-9913-2f3c4a8b5e01"):
        """测试代理运行端点"""
        print(f"\n=== 测试代理运行端点: {agent_id} ===")

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "message": "你好，请介绍一下你自己"
                }

                response = await client.post(
                    f"{self.base_url}/agents/{agent_id}/run",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                print(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"✓ 成功调用代理")
                    print(f"  响应内容: {result.get('content', 'No content')[:100]}...")
                    return True
                else:
                    print(f"❌ 调用代理失败: {response.text}")
                    return False

        except Exception as e:
            print(f"❌ 测试代理运行端点失败: {e}")
            return False

    async def test_team_run_endpoint(self, team_id: str = "8d97f474-c0a6-4973-bd14-a954296e54be"):
        """测试团队运行端点"""
        print(f"\n=== 测试团队运行端点: {team_id} ===")

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "message": "请团队成员协作介绍一下深圳"
                }

                response = await client.post(
                    f"{self.base_url}/teams/{team_id}/run",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                print(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"✓ 成功调用团队")
                    print(f"  响应内容: {result.get('content', 'No content')[:100]}...")
                    return True
                else:
                    print(f"❌ 调用团队失败: {response.text}")
                    return False

        except Exception as e:
            print(f"❌ 测试团队运行端点失败: {e}")
            return False

    async def test_invalid_agent_endpoint(self):
        """测试无效代理端点"""
        print("\n=== 测试无效代理端点 ===")

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "message": "测试消息"
                }

                response = await client.post(
                    f"{self.base_url}/agents/invalid-agent-id/run",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                print(f"状态码: {response.status_code}")
                if response.status_code == 404:
                    print(f"✓ 正确处理无效代理ID")
                    return True
                else:
                    print(f"❌ 未正确处理无效代理ID: {response.text}")
                    return False

        except Exception as e:
            print(f"❌ 测试无效代理端点失败: {e}")
            return False

    async def test_invalid_team_endpoint(self):
        """测试无效团队端点"""
        print("\n=== 测试无效团队端点 ===")

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "message": "测试消息"
                }

                response = await client.post(
                    f"{self.base_url}/teams/invalid-team-id/run",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                print(f"状态码: {response.status_code}")
                if response.status_code == 404:
                    print(f"✓ 正确处理无效团队ID")
                    return True
                else:
                    print(f"❌ 未正确处理无效团队ID: {response.text}")
                    return False

        except Exception as e:
            print(f"❌ 测试无效团队端点失败: {e}")
            return False

    async def test_invalid_json_payload(self):
        """测试无效JSON载荷"""
        print("\n=== 测试无效JSON载荷 ===")

        try:
            async with httpx.AsyncClient() as client:
                # 发送无效的JSON
                response = await client.post(
                    f"{self.base_url}/agents/8e45f5a1-c032-4c6c-9913-2f3c4a8b5e01/run",
                    data="invalid json",
                    headers={"Content-Type": "application/json"}
                )

                print(f"状态码: {response.status_code}")
                if response.status_code == 422:  # Unprocessable Entity
                    print(f"✓ 正确处理无效JSON")
                    return True
                else:
                    print(f"❌ 未正确处理无效JSON: {response.text}")
                    return False

        except Exception as e:
            print(f"❌ 测试无效JSON载荷失败: {e}")
            return False

    async def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("ServerAPI HTTP接口测试")
        print("=" * 60)
        print(f"测试目标: {self.base_url}")
        print("注意: 请确保ServerAPI服务已启动 (python examples/server_api.py)")
        print("=" * 60)

        # 运行测试
        results = {}

        results['health_check'] = await self.test_health_check_endpoint()
        results['agent_list'] = await self.test_agent_list_endpoint()
        results['team_list'] = await self.test_team_list_endpoint()
        results['agent_run'] = await self.test_agent_run_endpoint()
        results['team_run'] = await self.test_team_run_endpoint()
        results['invalid_agent'] = await self.test_invalid_agent_endpoint()
        results['invalid_team'] = await self.test_invalid_team_endpoint()
        results['invalid_json'] = await self.test_invalid_json_payload()

        # 测试结果总结
        print("\n" + "=" * 60)
        print("ServerAPI测试结果")
        print("=" * 60)

        for test_name, result in results.items():
            status = "✓ 通过" if result else "❌ 失败"
            print(f"  {test_name}: {status}")

        all_passed = all(results.values())
        if all_passed:
            print("\n🎉 所有ServerAPI测试通过！")
            print("ServerAPI功能正常，接口响应正确。")
        else:
            print("\n⚠️  部分ServerAPI测试失败")
            print("需要检查ServerAPI的实现。")

        return all_passed


async def main():
    """主函数"""
    tester = ServerAPITester()

    try:
        success = await tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return 130
    except Exception as e:
        print(f"\n测试过程中发生错误: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)
