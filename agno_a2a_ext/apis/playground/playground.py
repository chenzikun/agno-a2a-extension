from typing import List, Optional, Set, Callable, Dict, Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request



from agno_a2a_ext.apis.playground.settings import PlaygroundSettings

from agno.agent.agent import Agent
from agno.api.playground import create_playground_endpoint
from agno.api.schemas.playground import PlaygroundEndpointCreate
from agno.team.team import Team
from agno.utils.log import logger
from agno.workflow.workflow import Workflow


class Playground:
    def __init__(
        self,
        # agent: Optional[List[Agent]] = None,
        # teams: Optional[List[Team]] = None,
        # workflows: Optional[List[Workflow]] = None,
        settings: Optional[PlaygroundSettings] = None,
        api_app: Optional[FastAPI] = None,
        router: Optional[APIRouter] = None,
        get_agents_from_db: Optional[Callable[[], List[Agent]]] = None,
        get_teams_from_db: Optional[Callable[[], List[Team]]] = None,
        get_workflows_from_db: Optional[Callable[[], List[Workflow]]] = None,
    ):
        # self.agent: Optional[List[Agent]] = agent
        # self.workflows: Optional[List[Workflow]] = workflows
        # self.teams: Optional[List[Team]] = teams
        #
        # # 数据库获取函数
        # self.get_agents_from_db = get_agents_from_db
        # self.get_teams_from_db = get_teams_from_db
        # self.get_workflows_from_db = get_workflows_from_db
        
        # # 如果没有提供任何初始数据和数据库获取函数，则抛出错误
        # if not agent and not workflows and not teams and not get_agents_from_db and not get_teams_from_db and not get_workflows_from_db:
        #     raise ValueError("需要提供 agent、teams、workflows 列表或者对应的数据库获取函数")

        # # 初始化传入的对象
        # if self.agent:
        #     self._initialize_agents(self.agent)
        #
        # if self.teams:
        #     self._initialize_teams(self.teams)
        #
        # if self.workflows:
        #     self._initialize_workflows(self.workflows)

        self.settings: PlaygroundSettings = settings or PlaygroundSettings()
        self.api_app: Optional[FastAPI] = api_app
        self.router: Optional[APIRouter] = router
        self.endpoints_created: Set[str] = set()
    
    def _initialize_agents(self, agents: List[Agent]) -> None:
        """初始化代理列表"""
        for agent in agents:
            agent.initialize_agent()
    #
    def _initialize_teams(self, teams: List[Team]) -> None:
        """初始化团队列表"""
        for team in teams:
            team.initialize_team()
            for member in team.members:
                if isinstance(member, Agent):
                    member.initialize_agent()
                elif isinstance(member, Team):
                    member.initialize_team()

    def _initialize_workflows(self, workflows: List[Workflow]) -> None:
        """初始化工作流列表"""
        for workflow in workflows:
            if not workflow.workflow_id:
                workflow.workflow_id = generate_id(workflow.name)
    
    def get_router(self) -> APIRouter:
        """获取同步路由器"""
        from agent_api.routers.sync.agents import agents_router
        from agent_api.routers.sync.teams import teams_router
        from agent_api.routers.sync.workflows import workflows_router
        from agent_api.routers.sync.playground import playground_router
        for router in [agents_router, teams_router, workflows_router]:
            playground_router.include_router(router)
        return playground_router

    def get_async_router(self) -> APIRouter:
        """获取异步路由器"""
        from agent_api.routers._async.agents import agents_router
        from agent_api.routers._async.teams import teams_router
        from agent_api.routers._async.workflows import workflows_router
        from agent_api.routers._async.playground import playground_router
        for router in [agents_router, teams_router, workflows_router]:
            playground_router.include_router(router)
        return playground_router

    def get_app(self, use_async: bool = True, prefix: str = "/v1") -> FastAPI:
        if not self.api_app:
            self.api_app = FastAPI(
                title=self.settings.title,
                docs_url="/docs" if self.settings.docs_enabled else None,
                redoc_url="/redoc" if self.settings.docs_enabled else None,
                openapi_url="/openapi.json" if self.settings.docs_enabled else None,
            )

        if not self.api_app:
            raise Exception("API App could not be created.")

        @self.api_app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": str(exc.detail)},
            )

        async def general_exception_handler(request: Request, call_next):
            try:
                return await call_next(request)
            except Exception as e:
                return JSONResponse(
                    status_code=e.status_code if hasattr(e, "status_code") else 500,
                    content={"detail": str(e)},
                )

        self.api_app.middleware("http")(general_exception_handler)

        if not self.router:
            self.router = APIRouter(prefix=prefix)

        if not self.router:
            raise Exception("API Router could not be created.")

        if use_async:
            router = self.get_async_router()
        else:
            router = self.get_router()
        self.router.include_router(router)
        self.api_app.include_router(self.router)

        self.api_app.add_middleware(
            CORSMiddleware,
            allow_origins=self.settings.cors_origin_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"],
        )

        return self.api_app

    def create_endpoint(self, endpoint: str, prefix: str = "/v1") -> None:
        if endpoint in self.endpoints_created:
            return

        try:
            logger.info(f"Creating playground endpoint: {endpoint}")
            create_playground_endpoint(
                playground=PlaygroundEndpointCreate(endpoint=endpoint, playground_data={"prefix": prefix})
            )
        except Exception as e:
            logger.error(f"Could not create playground endpoint: {e}")
            logger.error("Please try again.")
            return

        self.endpoints_created.add(endpoint)


def generate_id(name: Optional[str] = None) -> str:
    if name:
        return name.lower().replace(" ", "-").replace("_", "-")
    else:
        return str(uuid4())
