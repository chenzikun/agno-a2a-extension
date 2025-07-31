from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentModel(BaseModel):
    """
    代理模型信息
    """
    name: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None


class AgentGetResponse(BaseModel):
    """
    代理信息响应
    """
    agent_id: str
    name: str
    model: AgentModel
    tools: Optional[List[Dict[str, Any]]] = None
    add_context: Optional[bool] = None
    memory: Optional[Dict[str, Any]] = None
    storage: Optional[Dict[str, Any]] = None
    knowledge: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    instructions: Optional[str] = None


class AgentSessionsResponse(BaseModel):
    """
    代理会话列表响应
    """
    title: str
    session_id: str
    session_name: Optional[str] = None
    created_at: Optional[datetime] = None


class AgentRenameRequest(BaseModel):
    """
    代理会话重命名请求
    """
    name: str
    user_id: Optional[str] = None


class TeamGetResponse(BaseModel):
    """
    团队信息响应
    """
    team_id: str
    name: str
    description: Optional[str] = None
    model: Optional[AgentModel] = None
    storage: Optional[Dict[str, Any]] = None
    memory: Optional[Dict[str, Any]] = None
    members: List[Dict[str, Any]] = Field(default_factory=list)
    
    @classmethod
    def from_team(cls, team):
        """从Team实例创建响应对象"""
        # 获取成员信息
        members = []
        if hasattr(team, "members"):
            for member in team.members:
                member_dict = {
                    "name": getattr(member, "name", "Unknown"),
                    "id": getattr(member, "agent_id", None) or getattr(member, "team_id", None),
                    "role": getattr(member, "role", None)
                }
                members.append(member_dict)
                
        # 获取模型信息
        model = None
        if team.model:
            model = AgentModel(
                name=team.model.name,
                model=team.model.id,
                provider=team.model.provider
            )
            
        # 创建响应对象
        return cls(
            team_id=team.team_id,
            name=team.name,
            description=team.description,
            model=model,
            storage={"name": team.storage.__class__.__name__} if team.storage else None,
            memory={"name": team.memory.__class__.__name__} if team.memory else None,
            members=members
        )


class TeamSessionResponse(BaseModel):
    """
    团队会话列表响应
    """
    title: str
    session_id: str
    session_name: Optional[str] = None
    created_at: Optional[datetime] = None


class TeamRenameRequest(BaseModel):
    """
    团队会话重命名请求
    """
    name: str
    user_id: Optional[str] = None


class WorkflowsGetResponse(BaseModel):
    """
    工作流列表响应
    """
    workflow_id: str
    name: str
    description: Optional[str] = None


class WorkflowGetResponse(BaseModel):
    """
    工作流详情响应
    """
    workflow_id: str
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    storage: Optional[str] = None


class WorkflowRunRequest(BaseModel):
    """
    工作流运行请求
    """
    input: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class WorkflowSessionResponse(BaseModel):
    """
    工作流会话列表响应
    """
    title: str
    session_id: str
    session_name: Optional[str] = None
    created_at: Optional[datetime] = None


class WorkflowRenameRequest(BaseModel):
    """
    工作流会话重命名请求
    """
    name: str


class MemoryResponse(BaseModel):
    """
    记忆响应
    """
    memory: str
    topics: List[str] = Field(default_factory=list)
    last_updated: Optional[datetime] = None 