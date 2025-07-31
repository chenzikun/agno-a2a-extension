import asyncio

from agno.agent.agent import Agent
from agno.memory import TeamMemory
from agno.models.openai import OpenAIChat
from agno.models.deepseek import DeepSeek
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.yfinance import YFinanceTools
from agno.team import Team
from agno.tools.mcp import MCPTools

from agents.agno_ext.memory import MySqlMemoryDb
from agents.agno_ext.storage.mysql import MySqlStorage

userid = "chenzikun@autel.com"

teamMemory = TeamMemory(
    user_id = userid,
    db=MySqlMemoryDb(
        table_name="team_memory",
        # schema="team",
        db_url="mysql+pymysql://root:root@10.240.3.251:13306/team"
    )
)

storage = MySqlStorage(
    table_name="team_storage",
    db_url="mysql+pymysql://root:root@10.240.3.251:13306/team"
)

base_model_config = dict(
    base_url="http://proxy.aiapps.autel.com/v1",
    api_key="sk-IxG3kIKpcB7Sv7Bz38957eAa6b8449A39cA153823592A043"
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


server_url = "http://localhost:9876/mcp"
mcp_tool = MCPTools(url=server_url, transport="streamable-http")



weather_agent = Agent(
    name="weather Agent",
    role="get the weather data",
    model=model,
    tools=[mcp_tool],
    instructions="使用中文城市名",
    show_tool_calls=True,
    markdown=True,
)



def get_team():
    agent_team = Team(
        mode="coordinate",
        members=[weather_agent, web_agent],
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
        add_datetime_to_instructions=True,
        tools=[mcp_tool]
    )
    return agent_team


async def main():
    team = get_team()

    result = await team.arun("深圳天气怎么样",
                             stream=True)
    async for chunk in result:
        print(chunk.content, end="", flush=True)
asyncio.run(main())
