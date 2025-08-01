import asyncio
import os

from agno.agent import Agent
from agno.memory import TeamMemory
from agno.models.openai import OpenAIChat
from agno.models.deepseek import DeepSeek
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.yfinance import YFinanceTools
from agno.team import Team
from agno_a2a_ext.agent.memory.mysql import MySqlMemoryDb
from agno_a2a_ext.agent.storage.mysql import MySqlStorage
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
api_key = os.environ.get("OPENAI_API_KEY")
base_url = os.environ.get("OPENAI_API_PROXY")

userid = "chenzikun@autel.com"

teamMemory = TeamMemory(
    user_id = userid,
    db=MySqlMemoryDb(
        table_name="team_memory",
        # schema="team",
        db_url="mysql+pymysql://root:root@10.240.3.251:13306/team"
    ),
)

storage = MySqlStorage(
    table_name="team_storage",
    db_url="mysql+pymysql://root:root@10.240.3.251:13306/team"
)

base_model_config = dict(
    base_url=base_url,
    api_key=api_key
)
assis_config = dict(
    id="gpt-4o",
    **base_model_config
)

r_model = dict(
    id="deepseek-reasoner",
    **base_model_config
)

model = OpenAIChat(**assis_config)
reasoning_model = DeepSeek(**r_model)

web_agent = Agent(
    name="Web Agent",
    role="Search the web for information",
    model=model,
    tools=[DuckDuckGoTools()],
    instructions="Always include sources",
    show_tool_calls=True,
    markdown=True,
)

finance_agent = Agent(
    name="Finance Agent",
    role="Get financial data",
    model=model,
    tools=[YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True)],
    instructions="Use tables to display data",
    show_tool_calls=True,
    markdown=True,
)

agent_team = Team(
    mode="coordinate",
    members=[web_agent],
    model=model,
    success_criteria="the user task was down.",
    instructions=["Always include sources", "Use tables to display data"],
    show_tool_calls=True,
    markdown=True,
    reasoning=True,
    reasoning_model=reasoning_model,
    debug_mode=True,
    memory=teamMemory,
    storage=storage,
    user_id=userid,
    add_datetime_to_instructions=True
)


async def main():
    result = await agent_team.arun("Who are you?",
                                   stream=True)
    async for chunk in result:
        print(chunk.content, end="", flush=True)


asyncio.run(main())
