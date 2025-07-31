# examples/a2a_integration_example.py
import asyncio
import sys
import os

# 确保可以正确导入项目模块
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
# 添加a2a-python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'a2a-python', 'src')))

from agno.tools.searxng import Searxng

# 设置OpenAI API密钥
# 注意：在实际使用时，请替换为您自己的API密钥，或从环境变量或配置文件中读取
os.environ["OPENAI_API_KEY"] = "your-openai-api-key-here"  # 替换为您的API密钥

from agno.agent.agent import Agent
from agents.agno_ext.a2a.a2a_agent import A2AAgent
from agno.team.team import Team
from agno.models.openai import OpenAIChat

from agents.servers.team import TeamServer

api_key = "sk-P0aVuPxRCfYEntCF2bC3B4E6C5Da4e37916e702eFa74C4A5"
base_url = "http://proxy.aiapps.autel.com/v1"
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
            base_url="http://localhost:8000",
            name="RemoteSearchAgent",
            role="远程搜索代理"
        )

        remote_analysis_agent = A2AAgent(
            base_url="http://localhost:8001",
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
        team_server = TeamServer(team=local_team, port=9000)
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