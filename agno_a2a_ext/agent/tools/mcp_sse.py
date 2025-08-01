import asyncio
from typing import Callable, List, Optional

from agno.tools import Toolkit
from agno.tools.function import Function
from agno.utils.log import log_debug, logger

from agno.tools.mcp import MCPTools


class SSEMCPTools(Toolkit):
    """
    专门用于SSE传输的MCP工具，自动管理连接生命周期。
    该类在初始化时就连接MCP服务并获取所有工具信息。
    
    参数:
        url: SSE服务器的URL
        include_tools: 要包含的工具名称列表
        exclude_tools: 要排除的工具名称列表
    """

    def __init__(
            self,
            url: str,
            include_tools: Optional[List[str]] = None,
            exclude_tools: Optional[List[str]] = None,
            **kwargs,
    ):
        super().__init__(name="SSEMCPTools", **kwargs)

        self.url = url
        self.include_tools = include_tools
        self.exclude_tools = exclude_tools

        # 内部MCPTools实例
        self._mcp_tools = None

        # 连接和资源状态
        self._connection = None
        self._lock = asyncio.Lock()

        # 立即初始化工具
        self._initialize_tools_sync()

        log_debug(f"SSEMCPTools已初始化，URL: {url}, 工具数量: {len(self.functions)}")

    def _initialize_tools_sync(self):
        """在实例化时同步初始化工具"""
        # 创建临时事件循环执行异步初始化
        loop = asyncio.get_event_loop()
        new_loop = False
        if not loop:
            loop = asyncio.new_event_loop()
            new_loop = True
        try:
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._initialize_tools())
        except Exception as e:
            logger.error(e)
        finally:
            if new_loop:
                loop.close()

    async def _initialize_tools(self):
        """连接MCP服务并获取所有工具信息"""
        try:
            # 创建MCPTools实例
            self._mcp_tools = MCPTools(
                url=self.url,
                transport="sse",
                include_tools=self.include_tools,
                exclude_tools=self.exclude_tools
            )

            # 连接MCP服务
            self._connection = await self._mcp_tools.__aenter__()

            # 清空现有函数
            self.functions.clear()

            # 从MCP服务获取工具列表和schema
            tools_response = await self._mcp_tools.session.list_tools()
            tool_info_map = {}

            # 构建工具信息映射
            for tool in tools_response.tools:
                name = tool.name
                description = tool.description
                parameters = tool.inputSchema

                # 确保参数符合JSON Schema规范
                if not parameters or not isinstance(parameters, dict) or parameters.get('type') != 'object':
                    parameters = {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }

                tool_info_map[name] = {
                    "description": description,
                    "parameters": parameters
                }

                log_debug(f"发现MCP工具: {name}, 参数: {parameters}")

            # 为每个工具创建代理函数
            for name, func in self._mcp_tools.functions.items():
                # 获取工具信息，如果不在列表中则使用默认值
                tool_info = tool_info_map.get(name, {
                    "description": func.description,
                    "parameters": func.parameters
                })

                # 创建代理函数
                proxy_func = self._create_proxy_function(name, func.entrypoint)

                # 注册函数
                self.functions[name] = Function(
                    name=name,
                    description=tool_info["description"],
                    parameters=tool_info["parameters"],
                    entrypoint=proxy_func,
                    skip_entrypoint_processing=True  # 跳过参数解析，避免agent参数的处理错误
                )

                log_debug(f"MCP SSE工具已注册: {name}")

            log_debug(f"已初始化 {len(self.functions)} 个MCP工具")

        except Exception as e:
            logger.error(f"初始化MCP SSE工具失败: {e}")
            # 清理连接
            if self._connection is not None and hasattr(self, "_mcp_tools") and self._mcp_tools is not None:
                try:
                    await self._mcp_tools.__aexit__(None, None, None)
                except Exception:
                    pass
                self._connection = None
            raise

    def _create_proxy_function(self, tool_name: str, original_entrypoint: Callable) -> Callable:
        """创建代理函数，确保连接存在并转发调用"""

        async def proxy_function(agent, *args, **kwargs):
            """代理函数，确保连接存在并转发调用"""
            # 检查连接
            async with self._lock:
                if self._connection is None and self._mcp_tools is not None:
                    self._connection = await self._mcp_tools.__aenter__()

            try:
                # 调用原始函数 - 传递agent参数
                return await original_entrypoint(agent, *args, **kwargs)
            except Exception as e:
                logger.error(f"调用工具失败 {tool_name}: {e}")
                # 处理连接错误
                if "connection" in str(e).lower():
                    async with self._lock:
                        if self._connection is not None and hasattr(self, "_mcp_tools") and self._mcp_tools is not None:
                            await self._mcp_tools.__aexit__(None, None, None)
                            self._connection = None
                            # 尝试重新连接
                            self._connection = await self._mcp_tools.__aenter__()
                raise

        return proxy_function

    async def __aenter__(self):
        """支持异步上下文管理器使用方式"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """清理资源"""
        if hasattr(self, "_mcp_tools") and self._mcp_tools is not None and self._connection is not None:
            await self._mcp_tools.__aexit__(exc_type, exc_val, exc_tb)
            self._connection = None

    def __del__(self):
        """确保对象销毁时释放资源"""
        if hasattr(self, "_mcp_tools") and self._mcp_tools is not None and hasattr(self,
                                                                                   "_connection") and self._connection is not None:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._mcp_tools.__aexit__(None, None, None))
                loop.close()
            except Exception:
                pass
