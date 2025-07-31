# examples/a2a_integration_example.py
import asyncio
import sys
import os

# 确保可以正确导入项目模块
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
# 添加a2a-python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'a2a-python', 'src')))

from agno.agent.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team.team import Team
from agents.agno_ext.a2a.a2a_agent import A2AAgent
from agents.servers.api import ServerAPI

api_key = "sk-P0aVuPxRCfYEntCF2bC3B4E6C5Da4e37916e702eFa74C4A5"
base_url = "http://proxy.aiapps.autel.com/v1"
model = OpenAIChat(id="gpt-4o", api_key=api_key, base_url=base_url)

async def main():
    # 初始化变量，以便在finally块中可以安全地访问
    remote_search_agent = None
    remote_analysis_agent = None
    remote_team_agent = None
    server_api = None

    try:
        # 创建A2AAgent连接到远程服务
        print("创建A2AAgent...")
        remote_search_agent = A2AAgent(
            base_url="http://localhost:8000/",  # 确保末尾有斜杠
            name="RemoteSearchAgent",
            role="远程搜索代理",
            agent_id="8e45f5a1-c032-4c6c-9913-2f3c4a8b5e01"  # 使用UUID格式
        )

        remote_analysis_agent = A2AAgent(
            base_url="http://localhost:8001/",  # 确保末尾有斜杠
            name="RemoteAnalysisAgent",
            role="远程分析代理",
            agent_id="6a72c340-9b5d-48e5-b8c7-f21a0d3e94fa"  # 使用UUID格式
        )

        # 创建本地代理
        local_agent = Agent(
            introduction="你是一个编程高手，负责处理编程相关的问题",
            name="LocalAgent",
            role="LocalAgent",
            model=model,
            agent_id="8d97f474-c0a6-4973-bd14-xx54296e54be"
        )

        # 创建本地团队
        local_team = Team(
            name="本地团队",
            members=[remote_search_agent, local_agent],
            mode="coordinate",
            model=model,
            team_id="8d97f474-c0a6-4973-bd14-a954296e54be"
        )

        # 创建连接到TeamServer的A2AAgent
        print("创建连接到TeamServer的A2AAgent...")
        remote_team_agent = A2AAgent(
            base_url="http://localhost:9000/",  # 确保末尾有斜杠
            name="RemoteTeamAgent",
            role="远程团队代理",
            agent_id="73406249-a559-456b-88ff-68475df7c7ae"
        )

        # 启动ServerAPI
        print("启动ServerAPI...")
        server_api = ServerAPI(
            agents=[remote_team_agent, remote_search_agent, remote_analysis_agent, local_agent],
            teams=[local_team],
            port=8089
        )
        await server_api.start()

        print("\n" + "=" * 50)
        print("服务已启动:")
        print("=" * 50)
        print(f"Search Agent: http://localhost:8000")
        print(f"Analysis Agent: http://localhost:8001")
        print(f"Team: http://localhost:9000")
        print(f"ServerAPI: http://localhost:8089")
        print("\n可以使用以下命令测试ServerAPI:")
        print('curl -X GET http://localhost:8089/agents')
        print('curl -X GET http://localhost:8089/teams')
        print('curl -X POST http://localhost:8089/agents/8e45f5a1-c032-4c6c-9913-2f3c4a8b5e01/run -H "Content-Type: application/json" -d \'{"message": "你好"}\'')
        print('curl -X POST http://localhost:8089/teams/8d97f474-c0a6-4973-bd14-a954296e54be/run -H "Content-Type: application/json" -d \'{"message": "请团队协作"}\'')

        print("\n按Ctrl+C停止服务...")

        # 保持服务运行
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n接收到停止信号，正在停止服务...")
    finally:
        # 停止所有服务
        if server_api:
            await server_api.stop()

        # 关闭A2A连接
        if remote_search_agent:
            await remote_search_agent.close()
        if remote_analysis_agent:
            await remote_analysis_agent.close()
        if remote_team_agent:
            await remote_team_agent.close()

        print("所有服务已停止")

if __name__ == "__main__":
    asyncio.run(main())