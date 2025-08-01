import asyncio
import logging
import os
import traceback

from agno.tools.searxng import Searxng
from agno.agent.agent import Agent
from agno.models.openai import OpenAIChat
from agno_a2a_ext.servers.agent import AgentServer
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
api_key = os.environ.get("OPENAI_API_KEY")
base_url = os.environ.get("OPENAI_API_PROXY")


model = OpenAIChat(id="gpt-4o", api_key=api_key, base_url=base_url)


async def main():
    # 1. 创建基础Agent
    print("创建基础Agent...")
    search_agent = Agent(
        name="SearchAgent",
        role="搜索专家",
        agent_id="search",
        tools=[Searxng(host="http://search.aiapps.autel.com")],
        model=model
    )
    try:
        # 创建服务器
        print("启动AgentServer...")
        search_server = AgentServer(agent=search_agent, port=8081)
        await search_server.start()
        print("AgentServer已就绪")

        # 保持服务运行
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n接收到停止信号，正在停止服务...")
    except Exception as e:
        print(f"发生错误: {str(e)}")
        traceback.print_exc()
    finally:
        # Agent对象没有stop方法，应该是服务器对象的方法
        if 'search_server' in locals():
            try:
                await search_server.stop()
            except Exception as e:
                print(f"停止服务器时出错: {str(e)}")
        print("服务已停止")


asyncio.run(main())
