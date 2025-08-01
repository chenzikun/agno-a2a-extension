"""
内存相关的数据库表ORM定义
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    JSON,
    Index,
    UniqueConstraint,
    BigInteger
)

from agno_a2a_ext.apis.models import Base
from agno_a2a_ext.apis.models.base import MemoryBase


class UserMemory(MemoryBase):
    """用户内存表"""
    __tablename__ = "user_memory"

    user_id = Column(String(255), nullable=False, index=True)
    memory_key = Column(String(255), nullable=False)
    memory_value = Column(Text, nullable=False)
    meta_data = Column(JSON, nullable=True)  # 重命名为meta_data避免冲突

    # 添加联合索引和唯一约束
    __table_args__ = (
        Index("idx_user_memory_user_id_key", "user_id", "memory_key"),
        UniqueConstraint("user_id", "memory_key", name="uq_user_memory_user_key"),
    )


class TeamMemory(MemoryBase):
    """团队内存表 - 匹配MySqlMemoryDb创建的表结构"""
    __tablename__ = "team_memory"

    # 覆盖基类中的id定义，使用String类型
    id = Column(String(255), primary_key=True)
    user_id = Column(String(255), index=True)
    memory = Column(JSON, nullable=False)


class AgentMemory(MemoryBase):
    """代理记忆表 - 匹配MySqlMemoryDb创建的表结构"""
    __tablename__ = "agent_memory"

    # 覆盖基类中的id定义，使用String类型
    id = Column(String(255), primary_key=True)
    user_id = Column(String(255), index=True)
    memory = Column(JSON, nullable=False)

    def __repr__(self):
        return f"<AgentMemory(id='{self.id}', user_id='{self.user_id}')>"
