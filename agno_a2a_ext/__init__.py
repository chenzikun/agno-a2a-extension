"""
AI-Agents 平台 - Agno A2A 扩展

一个强大的AI代理框架，用于构建、管理和部署智能代理应用。
基于Agno框架和A2A协议，提供完整的代理间通信和团队协作功能。
"""

__version__ = "1.0.0"
__author__ = "AI-Agents Team"
__email__ = "team@ai-agents.com"

# 导入核心模块
from agno_a2a_ext.servers.agent import AgentServer, AgentExecutorWrapper
from agno_a2a_ext.servers.team import TeamServer, TeamExecutorWrapper
from agno_a2a_ext.servers.api import ServerAPI
from agno_a2a_ext.servers.base import BaseServer
from agno_a2a_ext.agent.a2a.a2a_agent import A2AAgent
from agno_a2a_ext.apis.factory import AIFactory

# 导入工具和模式
try:
    from agno_a2a_ext.servers import schemas, utils
except ImportError:
    # 如果模块不存在，忽略错误
    pass

# 导出主要类和函数
__all__ = [
    # 服务器相关
    "AgentServer",
    "TeamServer", 
    "ServerAPI",
    "BaseServer",
    "AgentExecutorWrapper",
    "TeamExecutorWrapper",
    
    # 代理相关
    "A2AAgent",
    
    # 工厂类
    "AIFactory",
    
    # 工具和模式
    "schemas",
    "utils",
    
    # 版本信息
    "__version__",
    "__author__",
    "__email__",
]