"""
存储相关的数据库表ORM定义
"""
from sqlalchemy import (
    Column,
    String,
    JSON,
    Index,
    LargeBinary,
    BigInteger
)

from agents.apis.models import Base
from agents.apis.models.base import StorageBase


class AgentStorage(StorageBase):  # 不再继承StorageBase，避免id冲突
    """代理存储表 - 用于存储Agent的会话数据"""
    __tablename__ = "agent_storage"

    # 使用session_id作为主键
    agent_id = Column(String(255), index=True)
    team_session_id = Column(String(255), index=True, nullable=True)
    agent_data = Column(JSON, nullable=False, comment="Agent data")

    def __repr__(self):
        return f"<AgentStorage(session_id='{self.session_id}', agent_id='{self.agent_id}')>"


class TeamStorage(StorageBase):  # 不再继承StorageBase，避免id冲突
    """团队存储表 - 用于存储Team的会话数据"""
    __tablename__ = "team_storage"

    # 使用session_id作为主键
    team_id = Column(String(255), index=True)
    team_session_id = Column(String(255), index=True, nullable=True)
    team_data = Column(JSON, nullable=False, comment="Team data")

    def __repr__(self):
        return f"<TeamStorage(session_id='{self.session_id}', team_id='{self.team_id}')>"


class WorkflowStorage(StorageBase):
    __tablename__ = "workflow_storage"

    # 使用session_id作为主键
    workflow_id = Column(String(255), index=True)
    workflow_data = Column(JSON, nullable=False, comment="Team data")

    def __repr__(self):
        return f"<WorkflowStorage(session_id='{self.session_id}', workflow_id='{self.workflow_id}')>"
