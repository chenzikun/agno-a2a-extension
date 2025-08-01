from agno_a2a_ext.apis.models.memory import MemoryBase
from sqlalchemy import (
    Column,
    String,
    Text,
    JSON,
    Index,
)

from agno_a2a_ext.apis.models.storage import StorageBase


class SessionMemory(MemoryBase):
    """会话内存表"""
    __tablename__ = "session_memory"

    session_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    message_type = Column(String(50), nullable=False)  # system, user, assistant, tool, etc.
    content = Column(Text, nullable=False)
    meta_data = Column(JSON, nullable=True)

    # 添加索引
    __table_args__ = (
        Index("idx_session_memory_session_id_created", "session_id", "created_at"),
    )


class SessionSummary(MemoryBase):
    """会话摘要表"""
    __tablename__ = "session_summary"

    session_id = Column(String(255), nullable=False, index=True, unique=True)
    user_id = Column(String(255), nullable=True, index=True)
    summary = Column(Text, nullable=False)
    meta_data = Column(JSON, nullable=True)


class AgentSession(StorageBase):
    """代理会话存储表"""
    __tablename__ = "agent_session"

    session_id = Column(String(255), nullable=False, index=True, unique=True)
    user_id = Column(String(255), nullable=True, index=True)
    agent_id = Column(String(255), nullable=True, index=True)
    session_name = Column(String(255), nullable=True)
    session_data = Column(JSON, nullable=True)
    extra_data = Column(JSON, nullable=True)

    # 添加索引
    __table_args__ = (
        Index("idx_agent_session_user_id", "user_id"),
    )
