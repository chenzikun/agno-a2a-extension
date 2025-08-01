# examples/a2a_integration_example.py
import asyncio
import sys
import os

# 确保可以正确导入项目模块
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))


# 设置OpenAI API密钥

from agno.agent.agent import Agent
from agno.models.openai import OpenAIChat
import traceback
from agno_a2a_ext.servers.agent import AgentServer
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
api_key = os.environ.get("OPENAI_API_KEY")
base_url = os.environ.get("OPENAI_API_PROXY")
model = OpenAIChat(id="gpt-4o", api_key=api_key, base_url=base_url)


async def main():
    # 1. 创建基础Agent
    print("创建基础Agent...")
    analysis_agent = Agent(
        name="AnalysisAgent",
        role="分析专家",
        agent_id="analysis",
        model=model
    )
    try:

        # 创建服务器
        print("启动AgentServer...")
        analysis_server = AgentServer(agent=analysis_agent, port=8082)
        await analysis_server.start()
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
        if 'analysis_server' in locals():
            try:
                await analysis_server.stop()
            except Exception as e:
                print(f"停止服务器时出错: {str(e)}")
        print("服务已停止")

asyncio.run(main())