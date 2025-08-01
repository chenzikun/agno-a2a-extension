#!/usr/bin/env python3
"""
A2AAgent功能测试

专注于测试A2AAgent的功能，包括连接、通信、错误处理等。
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
    """A2AAgent测试器"""

    def __init__(self):
        self.remote_search_agent = None
        self.remote_analysis_agent = None
        self.remote_team_agent = None
        self.local_team = None

    async def setup_agents(self):
        """设置A2AAgent"""
        print("设置A2AAgent...")

        # 创建A2AAgent连接到远程服务
        self.remote_search_agent = A2AAgent(
            base_url="http://localhost:8081/",
            name="RemoteSearchAgent",
            role="远程搜索代理",
            agent_id="8e45f5a1-c032-4c6c-9913-2f3c4a8b5e01"
        )

        self.remote_analysis_agent = A2AAgent(
            base_url="http://localhost:8082/",
            name="RemoteAnalysisAgent",
            role="远程分析代理",
            agent_id="6a72c340-9b5d-48e5-b8c7-f21a0d3e94fa"
        )

        # 创建连接到TeamServer的A2AAgent
        self.remote_team_agent = A2AAgent(
            base_url="http://localhost:8083/",
            name="RemoteTeamAgent",
            role="远程团队代理",
            agent_id="73406249-a559-456b-88ff-68475df7c7ae"
        )

        # 创建本地团队
        self.local_team = Team(
            name="本地团队",
            members=[self.remote_search_agent, self.remote_analysis_agent],
            mode="coordinate",
            model=model,
            team_id="8d97f474-c0a6-4973-bd14-a954296e54be"
        )

        print("✓ A2AAgent设置完成")

    async def test_remote_search_agent(self):
        """测试远程搜索代理"""
        print("\n=== 测试远程搜索代理 ===")

        try:
            response = await self.remote_search_agent.arun("你是什么角色?")
            print(f"✓ 远程搜索代理响应成功")
            print(f"  响应类型: {type(response).__name__}")
            print(f"  响应内容: {response.content[:100]}...")
            return True
        except Exception as e:
            print(f"❌ 远程搜索代理测试失败: {e}")
            return False

    async def test_remote_analysis_agent(self):
        """测试远程分析代理"""
        print("\n=== 测试远程分析代理 ===")

        try:
            response = await self.remote_analysis_agent.arun("请介绍一下你的分析能力")
            print(f"✓ 远程分析代理响应成功")
            print(f"  响应类型: {type(response).__name__}")
            print(f"  响应内容: {response.content[:100]}...")
            return True
        except Exception as e:
            print(f"❌ 远程分析代理测试失败: {e}")
            return False

    async def test_remote_team_agent(self):
        """测试远程团队代理"""
        print("\n=== 测试远程团队代理 ===")

        try:
            response = await self.remote_team_agent.arun("请介绍你的团队")
            print(f"✓ 远程团队代理响应成功")
            print(f"  响应类型: {type(response).__name__}")
            print(f"  响应内容: {response.content[:100]}...")
            return True
        except Exception as e:
            print(f"❌ 远程团队代理测试失败: {e}")
            return False

    async def test_local_team_with_a2a_agents(self):
        """测试包含A2AAgent的本地团队"""
        print("\n=== 测试本地团队（包含A2AAgent） ===")

        try:
            # 直接测试团队，不使用复杂的错误处理
            response = await self.local_team.arun("请团队成员协作介绍一下深圳")

            if response and hasattr(response, 'content'):
                print(f"✓ 本地团队测试成功")
                print(f"  响应内容: {response.content[:100]}...")
                return True
            else:
                print("❌ 本地团队测试失败")
                return False

        except Exception as e:
            print(f"❌ 本地团队测试异常: {e}")
            return False

    async def test_streaming_responses(self):
        """测试流式响应"""
        print("\n=== 测试流式响应 ===")

        try:
            # 测试搜索代理的流式响应
            print("测试搜索代理流式响应...")
            stream_response = await self.remote_search_agent.arun(
                "请详细介绍你的功能",
                stream=True
            )

            full_content = ""
            async for chunk in stream_response:
                if hasattr(chunk, 'content'):
                    full_content += chunk.content
                    print(f"  流式块: {chunk.content}")
                elif isinstance(chunk, str):
                    full_content += chunk
                    print(f"  流式块: {chunk}")

            print(f"✓ 流式响应测试成功")
            print(f"  完整内容长度: {len(full_content)} 字符")
            return True

        except Exception as e:
            print(f"❌ 流式响应测试失败: {e}")
            return False

    async def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("A2AAgent功能测试")
        print("=" * 60)

        # 设置代理
        await self.setup_agents()

        # 运行测试
        results = {}

        results['remote_search'] = await self.test_remote_search_agent()
        results['remote_analysis'] = await self.test_remote_analysis_agent()
        results['remote_team'] = await self.test_remote_team_agent()
        results['local_team'] = await self.test_local_team_with_a2a_agents()
        results['streaming'] = await self.test_streaming_responses()

        # 测试结果总结
        print("\n" + "=" * 60)
        print("A2AAgent测试结果")
        print("=" * 60)

        for test_name, result in results.items():
            status = "✓ 通过" if result else "❌ 失败"
            print(f"  {test_name}: {status}")

        all_passed = all(results.values())
        if all_passed:
            print("\n🎉 所有A2AAgent测试通过！")
            print("A2AAgent功能正常，可以正常使用。")
        else:
            print("\n⚠️  部分A2AAgent测试失败")
            print("需要检查A2AAgent的实现或远程服务状态。")

        return all_passed

    async def cleanup(self):
        """清理资源"""
        print("\n清理A2AAgent资源...")

        if self.remote_search_agent:
            await self.remote_search_agent.close()
        if self.remote_analysis_agent:
            await self.remote_analysis_agent.close()
        if self.remote_team_agent:
            await self.remote_team_agent.close()

        print("✓ A2AAgent资源已清理")


async def main():
    """主函数"""
    tester = A2AAgentTester()

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
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)
