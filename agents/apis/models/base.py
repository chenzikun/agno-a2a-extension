import datetime
import time

from sqlalchemy import Column, Integer, DateTime, BigInteger, func, String, JSON

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ModelBase(Base):
    __abstract__ = True

    created_at = Column(BigInteger, default=lambda: int(time.time()))
    updated_at = Column(BigInteger, default=lambda: int(time.time()), onupdate=lambda: int(time.time()))


class StorageBase(ModelBase):
    """存储基础表，抽象类"""
    __abstract__ = True

    session_id = Column(String(255), primary_key=True)
    user_id = Column(String(255), index=True)
    memory = Column(JSON, nullable=False, comment="Session memory")
    session_data = Column(JSON, nullable=False, comment="Session data")
    extra_data = Column(JSON, nullable=False, comment="Extra data")


class MemoryBase(ModelBase):
    """存储基础表，抽象类"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)

