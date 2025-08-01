# agent_server/servers/base.py
import asyncio
from abc import ABC, abstractmethod

import uvicorn
from fastapi import FastAPI

from a2a.server.apps.jsonrpc.fastapi_app import A2AFastAPIApplication
from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.request_handlers.default_request_handler import DefaultRequestHandler
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.types import AgentCard


class BaseServer(ABC):
    """A2A协议服务器基类"""
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 9000,
        name: str = "A2A Server",
        description: str = "A2A Protocol Server"
    ):
        """
        初始化基础服务器
        
        Args:
            host: 服务器主机
            port: 服务器端口
            name: 服务器名称
            description: 服务器描述
        """
        self.host = host
        self.port = port
        self.name = name
        self.description = description
        self._server = None
        self._task = None
    
    @abstractmethod
    def create_agent_card(self) -> AgentCard:
        """
        创建AgentCard
        
        Returns:
            AgentCard: 包含服务信息的卡片
        """
        pass
    
    @abstractmethod
    def create_executor(self) -> AgentExecutor:
        """
        创建执行器
        
        Returns:
            AgentExecutor: 具体的执行器实现
        """
        pass
    
    def create_app(self) -> FastAPI:
        """
        创建FastAPI应用
        
        Returns:
            FastAPI: 配置好的FastAPI应用
        """
        # 创建AgentCard
        agent_card = self.create_agent_card()
        
        # 创建执行器
        executor = self.create_executor()
        
        # 创建任务存储
        task_store = InMemoryTaskStore()
        
        # 创建请求处理器
        handler = DefaultRequestHandler(
            agent_executor=executor,
            task_store=task_store
        )
        
        # 创建A2A应用
        app = A2AFastAPIApplication(
            agent_card=agent_card,
            http_handler=handler
        ).build()
        
        return app
    
    async def start(self):
        """启动服务器"""
        app = self.create_app()
        
        config = uvicorn.Config(
            app=app,
            host=self.host,
            port=self.port
        )
        
        server = uvicorn.Server(config)
        self._server = server
        
        self._task = asyncio.create_task(server.serve())
        print(f"{self.__class__.__name__}已启动：http://{self.host}:{self.port}")
    
    async def stop(self):
        """停止服务器"""
        if self._server:
            self._server.should_exit = True
            
            if self._task and not self._task.done():
                self._task.cancel()
                
            self._server = None
            self._task = None
            print(f"{self.__class__.__name__}已停止") 