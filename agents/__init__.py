"""
AI-Agents 平台

一个强大的AI代理框架，用于构建、管理和部署智能代理应用。
"""

__version__ = "1.0.0"
__author__ = "AI-Agents Team"
__email__ = "team@ai-agents.com"

# 导入核心模块
from sdk.agno import *
from servers import *
from apis import *

# 导出主要类和函数
__all__ = [
    # 从sdk.agno导出的内容
    "Agent",
    "Team", 
    "Model",
    "Tool",
    "Memory",
    "Storage",
    "VectorDB",
    "Embedder",
    "Document",
    "Workflow",
    "Playground",
    
    # 从servers导出的内容
    "AgentServer",
    "TeamServer", 
    "APIServer",
    
    # 从apis导出的内容
    "AsyncRouter",
    "SyncRouter",
    "PlaygroundAPI",
    
    # 版本信息
    "__version__",
    "__author__",
    "__email__",
] 