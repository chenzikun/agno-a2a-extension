"""
AI-Agents Platform - Agno A2A Extension

A powerful AI agent framework for building, managing, and deploying intelligent agent applications.
Based on the Agno framework and A2A protocol, providing complete agent-to-agent communication and team collaboration capabilities.
"""

__version__ = "1.0.0"
__author__ = "AI-Agents Team"
__email__ = "team@ai-agents.com"

# Import core modules
from agno_a2a_ext.servers.agent import AgentServer, AgentExecutorWrapper
from agno_a2a_ext.servers.team import TeamServer, TeamExecutorWrapper
from agno_a2a_ext.servers.api import ServerAPI
from agno_a2a_ext.servers.base import BaseServer
from agno_a2a_ext.agent.a2a.a2a_agent import A2AAgent
from agno_a2a_ext.apis.factory import AIFactory

# Import utilities and schemas
try:
    from agno_a2a_ext.servers import schemas, utils
except ImportError:
    # Ignore error if modules don't exist
    pass

# Export main classes and functions
__all__ = [
    # Server related
    "AgentServer",
    "TeamServer", 
    "ServerAPI",
    "BaseServer",
    "AgentExecutorWrapper",
    "TeamExecutorWrapper",
    
    # Agent related
    "A2AAgent",
    
    # Factory class
    "AIFactory",
    
    # Utilities and schemas
    "schemas",
    "utils",
    
    # Version info
    "__version__",
    "__author__",
    "__email__",
]