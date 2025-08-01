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
    # 1. 创建基础Agent
    print("创建基础Agent...")
    local_agent = Agent(
        name="SearchAgent",
        role="天气查询专家",
        agent_id="search",
        tools=[Searxng(host="http://search.aiapps.autel.com")],
        model=model
    )

    # 初始化变量，以便在finally块中可以安全地访问
    remote_search_agent = None
    remote_analysis_agent = None
    team_server = None

    try:
        # 3. 创建A2AAgent连接到远程服务
        print("创建A2AAgent...")
        remote_search_agent = A2AAgent(
            base_url="http://localhost:8081",
            name="RemoteSearchAgent",
            role="远程搜索代理"
        )

        remote_analysis_agent = A2AAgent(
            base_url="http://localhost:8082",
            name="RemoteAnalysisAgent",
            role="远程分析代理"
        )

        # 4. 创建本地Team
        print("创建本地Team...")

        # 添加stream_member_events=True属性以支持流式处理
        local_team = Team(
            name="本地团队",
            members=[local_agent, remote_search_agent, remote_analysis_agent],
            mode="coordinate",
            model=model,
            team_id="8d97f474-c0a6-4973-bd14-a954296e54be",
            stream_member_events=True  # 添加此属性启用流式处理
        )

        # 5. 启动TeamServer
        print("启动TeamServer...")
        team_server = TeamServer(team=local_team, port=8083)
        await team_server.start()

        # 保持服务运行
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n接收到停止信号，正在停止服务...")
    finally:
        # 停止所有服务

        if team_server:
            await team_server.stop()

        # 关闭A2A连接
        if remote_search_agent:
            await remote_search_agent.close()
        if remote_analysis_agent:
            await remote_analysis_agent.close()

        print("所有服务已停止")


if __name__ == "__main__":
    asyncio.run(main())
