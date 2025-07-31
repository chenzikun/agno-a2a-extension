from typing import Dict, List, Optional,  Callable, TypeVar
from uuid import uuid4
import logging
from threading import Lock

from agno.agent.agent import Agent
from agno.team.team import Team
from agno.workflow.workflow import Workflow

logger = logging.getLogger(__name__)

T = TypeVar('T', Agent, Team, Workflow)


class AIFactory:
    """
    AgentManager 负责管理所有的 agent、team 和 workflow
    可以从数据库加载配置，也可以通过 API 动态注册
    """
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AIFactory, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        """初始化 AgentManager，只在第一次创建实例时执行"""
        if self._initialized:
            return
            
        self._agents: Dict[str, Agent] = {}
        self._teams: Dict[str, Team] = {}
        self._workflows: Dict[str, Workflow] = {}
        
        # 数据库加载函数
        self._load_agents_from_db_fn: Optional[Callable[[], List[Agent]]] = None
        self._load_teams_from_db_fn: Optional[Callable[[], List[Team]]] = None
        self._load_workflows_from_db_fn: Optional[Callable[[], List[Workflow]]] = None
        
        # 保存函数
        self._save_agent_to_db_fn: Optional[Callable[[Agent], None]] = None
        self._save_team_to_db_fn: Optional[Callable[[Team], None]] = None
        self._save_workflow_to_db_fn: Optional[Callable[[Workflow], None]] = None
        
        # 是否已经从数据库加载
        self._agents_loaded = False
        self._teams_loaded = False
        self._workflows_loaded = False
        
        self._initialized = True
        logger.info("AgentManager initialized")

    def register_db_loaders(self,
                          load_agents_fn: Optional[Callable[[], List[Agent]]] = None,
                          load_teams_fn: Optional[Callable[[], List[Team]]] = None,
                          load_workflows_fn: Optional[Callable[[], List[Workflow]]] = None):
        """注册从数据库加载数据的函数"""
        if load_agents_fn:
            self._load_agents_from_db_fn = load_agents_fn
        if load_teams_fn:
            self._load_teams_from_db_fn = load_teams_fn
        if load_workflows_fn:
            self._load_workflows_from_db_fn = load_workflows_fn
        
        logger.info("Database loaders registered")
        return self

    def register_db_savers(self,
                         save_agent_fn: Optional[Callable[[Agent], None]] = None,
                         save_team_fn: Optional[Callable[[Team], None]] = None,
                         save_workflow_fn: Optional[Callable[[Workflow], None]] = None):
        """注册保存数据到数据库的函数"""
        if save_agent_fn:
            self._save_agent_to_db_fn = save_agent_fn
        if save_team_fn:
            self._save_team_to_db_fn = save_team_fn
        if save_workflow_fn:
            self._save_workflow_to_db_fn = save_workflow_fn
        
        logger.info("Database savers registered")
        return self

    def initialize(self, load_from_db: bool = True) -> 'AgentManager':
        """初始化 AgentManager，可选从数据库加载数据"""
        if load_from_db:
            self.load_all_from_db()
        return self

    def load_all_from_db(self) -> None:
        """从数据库加载所有数据"""
        self.load_agents_from_db()
        self.load_teams_from_db()
        self.load_workflows_from_db()

    def load_agents_from_db(self) -> None:
        """从数据库加载所有 agent"""
        if not self._load_agents_from_db_fn:
            logger.warning("No agent loader function registered")
            return
            
        agents = self._load_agents_from_db_fn()
        for agent in agents:
            self._register_agent(agent)
        
        self._agents_loaded = True
        logger.info(f"Loaded {len(agents)} agents from database")

    def load_teams_from_db(self) -> None:
        """从数据库加载所有 team"""
        if not self._load_teams_from_db_fn:
            logger.warning("No team loader function registered")
            return
            
        teams = self._load_teams_from_db_fn()
        for team in teams:
            self._register_team(team)
        
        self._teams_loaded = True
        logger.info(f"Loaded {len(teams)} teams from database")

    def load_workflows_from_db(self) -> None:
        """从数据库加载所有 workflow"""
        if not self._load_workflows_from_db_fn:
            logger.warning("No workflow loader function registered")
            return
            
        workflows = self._load_workflows_from_db_fn()
        for workflow in workflows:
            self._register_workflow(workflow)
        
        self._workflows_loaded = True
        logger.info(f"Loaded {len(workflows)} workflows from database")

    def _ensure_id(self, entity: T) -> str:
        """确保实体有 ID"""
        if isinstance(entity, Agent):
            if not entity.agent_id:
                entity.agent_id = str(uuid4())
            return entity.agent_id
        elif isinstance(entity, Team):
            if not entity.team_id:
                entity.team_id = str(uuid4())
            return entity.team_id
        elif isinstance(entity, Workflow):
            if not entity.workflow_id:
                entity.workflow_id = str(uuid4())
            return entity.workflow_id
        else:
            raise ValueError(f"Unknown entity type: {type(entity)}")

    def _initialize_entity(self, entity: T) -> T:
        """初始化实体"""
        if isinstance(entity, Agent):
            entity.initialize_agent()
        elif isinstance(entity, Team):
            entity.initialize_team()
            # 初始化团队成员
            for member in entity.members:
                if isinstance(member, Agent):
                    member.initialize_agent()
                elif isinstance(member, Team):
                    member.initialize_team()
        elif isinstance(entity, Workflow):
            pass  # workflow 不需要特殊初始化
        else:
            raise ValueError(f"Unknown entity type: {type(entity)}")
        
        return entity

    def _register_agent(self, agent: Agent) -> str:
        """注册 agent，返回 agent_id"""
        agent_id = self._ensure_id(agent)
        self._initialize_entity(agent)
        self._agents[agent_id] = agent
        
        # 如果有保存函数，保存到数据库
        if self._save_agent_to_db_fn:
            try:
                self._save_agent_to_db_fn(agent)
            except Exception as e:
                logger.error(f"Failed to save agent to database: {e}")
        
        return agent_id

    def _register_team(self, team: Team) -> str:
        """注册 team，返回 team_id"""
        team_id = self._ensure_id(team)
        self._initialize_entity(team)
        self._teams[team_id] = team
        
        # 如果有保存函数，保存到数据库
        if self._save_team_to_db_fn:
            try:
                self._save_team_to_db_fn(team)
            except Exception as e:
                logger.error(f"Failed to save team to database: {e}")
        
        return team_id

    def _register_workflow(self, workflow: Workflow) -> str:
        """注册 workflow，返回 workflow_id"""
        workflow_id = self._ensure_id(workflow)
        self._initialize_entity(workflow)
        self._workflows[workflow_id] = workflow
        
        # 如果有保存函数，保存到数据库
        if self._save_workflow_to_db_fn:
            try:
                self._save_workflow_to_db_fn(workflow)
            except Exception as e:
                logger.error(f"Failed to save workflow to database: {e}")
        
        return workflow_id

    def register(self, node: Agent|Team|Workflow):
        if isinstance(node, Agent):
            self._register_agent(node)
        if isinstance(node, Team):
            self._register_team(node)
        if isinstance(node, Workflow):
            self._register_workflow(node)


    def get_agent_by_id(self, agent_id: str) -> Optional[Agent]:
        """根据 ID 获取 agent"""
        # 确保已从数据库加载
        if not self._agents_loaded and self._load_agents_from_db_fn:
            self.load_agents_from_db()
            
        return self._agents.get(agent_id)

    def get_team_by_id(self, team_id: str) -> Optional[Team]:
        """根据 ID 获取 team"""
        # 确保已从数据库加载
        if not self._teams_loaded and self._load_teams_from_db_fn:
            self.load_teams_from_db()
            
        return self._teams.get(team_id)

    def get_workflow_by_id(self, workflow_id: str) -> Optional[Workflow]:
        """根据 ID 获取 workflow"""
        # 确保已从数据库加载
        if not self._workflows_loaded and self._load_workflows_from_db_fn:
            self.load_workflows_from_db()
            
        return self._workflows.get(workflow_id)

    def get_all_agents(self) -> List[Agent]:
        """获取所有 agent"""
        # 确保已从数据库加载
        if not self._agents_loaded and self._load_agents_from_db_fn:
            self.load_agents_from_db()
            
        return list(self._agents.values())

    def get_all_teams(self) -> List[Team]:
        """获取所有 team"""
        # 确保已从数据库加载
        if not self._teams_loaded and self._load_teams_from_db_fn:
            self.load_teams_from_db()
            
        return list(self._teams.values())

    def get_all_workflows(self) -> List[Workflow]:
        """获取所有 workflow"""
        # 确保已从数据库加载
        if not self._workflows_loaded and self._load_workflows_from_db_fn:
            self.load_workflows_from_db()
            
        return list(self._workflows.values())

    def remove_agent(self, agent_id: str) -> bool:
        """移除 agent，返回是否成功"""
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False

    def remove_team(self, team_id: str) -> bool:
        """移除 team，返回是否成功"""
        if team_id in self._teams:
            del self._teams[team_id]
            return True
        return False

    def remove_workflow(self, workflow_id: str) -> bool:
        """移除 workflow，返回是否成功"""
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            return True
        return False


# 单例实例
ai_factory = AIFactory()