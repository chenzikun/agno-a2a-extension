from uuid import uuid4
import traceback

from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.types import AgentCard
from a2a.types import Message, Role, Part, TextPart
from agno.agent.agent import Agent

from agents.servers.base import BaseServer


class AgentExecutorWrapper(AgentExecutor):
    """将Agent包装为A2A执行器"""

    def __init__(self, agent: Agent):
        """
        初始化执行器
        
        Args:
            agent: 要包装的Agent实例
        """
        self.agent = agent

    async def execute(self, context, event_queue):
        """
        执行Agent并将结果放入事件队列
        
        Args:
            context: 请求上下文
            event_queue: 事件队列
        """

        try:
            # 从请求中提取消息
            message = ""
            session_id = None
            stream = True  # 默认启用流式响应

            # 尝试从context中获取信息，处理不同的结构
            if hasattr(context, "request") and context.request:
                print(f"DEBUG AgentExecutorWrapper: 从context.request获取信息, request类型={type(context.request)}")
                if hasattr(context.request, "message") and context.request.message:
                    print(f"DEBUG AgentExecutorWrapper: 找到message, 类型={type(context.request.message)}")
                    print(f"DEBUG AgentExecutorWrapper: message属性={dir(context.request.message)}")
                    # 从消息部分提取文本
                    if hasattr(context.request.message, "parts"):
                        print(f"DEBUG AgentExecutorWrapper: 找到parts, 数量={len(context.request.message.parts)}")
                        for i, part in enumerate(context.request.message.parts):
                            print(f"DEBUG AgentExecutorWrapper: 处理part[{i}], 类型={type(part)}, 属性={dir(part)}")
                            if hasattr(part, "root") and hasattr(part.root, "text"):
                                print(f"DEBUG AgentExecutorWrapper: 从part.root.text获取文本: '{part.root.text}'")
                                message += part.root.text
                            elif hasattr(part, "text"):
                                print(f"DEBUG AgentExecutorWrapper: 从part.text获取文本: '{part.text}'")
                                message += part.text
                            else:
                                print(f"DEBUG AgentExecutorWrapper: 无法从part获取文本")
                if hasattr(context.request, "configuration") and context.request.configuration:
                    print(f"DEBUG AgentExecutorWrapper: 找到configuration")
                    session_id = context.request.configuration.sessionId
                    print(f"DEBUG AgentExecutorWrapper: session_id = {session_id}")
            elif hasattr(context, "params") and context.params:
                print(f"DEBUG AgentExecutorWrapper: 从context.params获取信息, params类型={type(context.params)}")
                # 尝试从params获取信息
                if hasattr(context.params, "message") and context.params.message:
                    print(f"DEBUG AgentExecutorWrapper: 找到message, 类型={type(context.params.message)}")
                    # 从消息部分提取文本
                    if hasattr(context.params.message, "parts"):
                        print(f"DEBUG AgentExecutorWrapper: 找到parts, 数量={len(context.params.message.parts)}")
                        for i, part in enumerate(context.params.message.parts):
                            print(f"DEBUG AgentExecutorWrapper: 处理part[{i}], 类型={type(part)}, 属性={dir(part)}")
                            if hasattr(part, "root") and hasattr(part.root, "text"):
                                print(f"DEBUG AgentExecutorWrapper: 从part.root.text获取文本: '{part.root.text}'")
                                message += part.root.text
                            elif hasattr(part, "text"):
                                print(f"DEBUG AgentExecutorWrapper: 从part.text获取文本: '{part.text}'")
                                message += part.text
                            else:
                                print(f"DEBUG AgentExecutorWrapper: 无法从part获取文本")
                if hasattr(context.params, "configuration") and context.params.configuration:
                    print(f"DEBUG AgentExecutorWrapper: 找到configuration")
                    session_id = context.params.configuration.sessionId
                    print(f"DEBUG AgentExecutorWrapper: session_id = {session_id}")

            # 尝试直接从context提取消息
            if not message and hasattr(context, "message"):
                print(f"DEBUG AgentExecutorWrapper: 尝试从context.message获取信息, 类型={type(context.message)}")
                if context.message:
                    print(f"DEBUG AgentExecutorWrapper: context.message={context.message}")
                    if isinstance(context.message, str):
                        message = context.message
                        print(f"DEBUG AgentExecutorWrapper: 直接获取字符串消息: '{message}'")
                    elif hasattr(context.message, "parts") and context.message.parts:
                        print(
                            f"DEBUG AgentExecutorWrapper: 从context.message.parts提取, 数量={len(context.message.parts)}")
                        for i, part in enumerate(context.message.parts):
                            if hasattr(part, "root") and hasattr(part.root, "text"):
                                message += part.root.text
                                print(
                                    f"DEBUG AgentExecutorWrapper: 从message.parts[{i}].root.text提取: '{part.root.text}'")

            # 如果没有提取到消息，尝试其他方法
            if not message:
                print(f"DEBUG AgentExecutorWrapper: 主要方法未提取到消息，尝试备用方法")
                if hasattr(context, "request") and hasattr(context.request, "text"):
                    print(f"DEBUG AgentExecutorWrapper: 从context.request.text获取文本")
                    message = context.request.text
                elif hasattr(context, "params") and hasattr(context.params, "text"):
                    print(f"DEBUG AgentExecutorWrapper: 从context.params.text获取文本")
                    message = context.params.text

                # 尝试获取用户输入
                elif hasattr(context, "get_user_input") and callable(context.get_user_input):
                    try:
                        print(f"DEBUG AgentExecutorWrapper: 尝试调用context.get_user_input()")
                        user_input = context.get_user_input()
                        print(f"DEBUG AgentExecutorWrapper: 获取到用户输入: {user_input}")
                        if user_input:
                            message = user_input
                    except Exception as e:
                        print(f"DEBUG AgentExecutorWrapper: 调用get_user_input失败: {str(e)}")

                # 尝试从call_context获取
                elif hasattr(context, "call_context") and context.call_context:
                    print(f"DEBUG AgentExecutorWrapper: 检查call_context, 类型={type(context.call_context)}")
                    print(f"DEBUG AgentExecutorWrapper: call_context属性={dir(context.call_context)}")
                    if hasattr(context.call_context, "request") and context.call_context.request:
                        if hasattr(context.call_context.request, "params") and hasattr(
                                context.call_context.request.params, "message"):
                            user_msg = context.call_context.request.params.message
                            print(
                                f"DEBUG AgentExecutorWrapper: 从call_context.request.params.message获取, 类型={type(user_msg)}")
                            if hasattr(user_msg, "parts") and user_msg.parts:
                                for part in user_msg.parts:
                                    if hasattr(part, "root") and hasattr(part.root, "text"):
                                        message += part.root.text
                                        print(f"DEBUG AgentExecutorWrapper: 从call_context提取消息: '{part.root.text}'")

                # 输出context的完整内容以便进一步分析
                print(f"DEBUG AgentExecutorWrapper: 完整context内容:")
                for key in dir(context):
                    if not key.startswith("_") and key not in ["call_context", "get_user_input"]:
                        try:
                            value = getattr(context, key)
                            print(f"DEBUG AgentExecutorWrapper: context.{key} = {value}")
                        except Exception as e:
                            print(f"DEBUG AgentExecutorWrapper: 无法获取context.{key}: {e}")

            # 执行Agent逻辑
            if message:
                print(f"DEBUG AgentExecutorWrapper: 成功提取到消息: '{message}'")
                try:
                    # 使用Agent执行消息
                    try:
                        print(
                            f"DEBUG AgentExecutorWrapper: 准备调用Agent.arun，Agent类型: {type(self.agent).__name__}, 消息: {message[:50]}...")
                        print(f"DEBUG AgentExecutorWrapper: Agent对象信息: 属性={dir(self.agent)}")
                        print(
                            f"DEBUG AgentExecutorWrapper: 调用参数: message={message}, session_id={session_id}, stream=False")

                        run_response = await self.agent.arun(
                            message=message,
                            session_id=session_id,
                            stream=False
                        )
                        print(f"DEBUG AgentExecutorWrapper: Agent.arun调用成功")

                        # 从Agent响应中提取内容
                        print(
                            f"DEBUG AgentExecutorWrapper: run_response类型={type(run_response)}, 属性={dir(run_response)}")
                        if run_response and hasattr(run_response, "content"):
                            response_text = run_response.content
                            print(f"DEBUG AgentExecutorWrapper: 提取到内容: '{response_text}'")
                        else:
                            response_text = f"收到消息: {message}"
                            print(f"DEBUG AgentExecutorWrapper: 未提取到内容，使用默认回复: '{response_text}'")
                    except Exception as e:
                        print(f"DEBUG AgentExecutorWrapper: Agent.arun调用失败: {str(e)}")
                        traceback.print_exc()
                        # 如果Agent执行失败，创建一个错误消息
                        error_text = f"执行出错: {str(e)}"
                        print(f"DEBUG AgentExecutorWrapper: 创建错误消息: '{error_text}'")
                        response_message = Message(
                            messageId=str(uuid4()),
                            role=Role.agent,
                            parts=[Part(root=TextPart(text=error_text))]
                        )
                        print(f"DEBUG AgentExecutorWrapper: 入队错误消息并返回")
                        await event_queue.enqueue_event(response_message)
                        return

                    # 创建响应消息
                    print(f"DEBUG AgentExecutorWrapper: 创建正常响应消息: '{response_text}'")
                    response_message = Message(
                        messageId=str(uuid4()),
                        role=Role.agent,
                        parts=[Part(root=TextPart(text=response_text))]
                    )

                    # 入队响应消息
                    print(f"DEBUG AgentExecutorWrapper: 入队响应消息并返回")
                    await event_queue.enqueue_event(response_message)
                    return
                except Exception as e:
                    # 如果Agent执行失败，创建一个错误消息
                    print(f"DEBUG AgentExecutorWrapper: 执行出错(外层异常): {str(e)}")
                    error_text = f"执行出错: {str(e)}"
                    print(f"DEBUG AgentExecutorWrapper: 创建错误消息: '{error_text}'")
                    response_message = Message(
                        messageId=str(uuid4()),
                        role=Role.agent,
                        parts=[Part(root=TextPart(text=error_text))]
                    )
                    print(f"DEBUG AgentExecutorWrapper: 入队错误消息并返回")
                    await event_queue.enqueue_event(response_message)
                    return

            # 如果没有消息或执行失败，创建一个默认响应
            default_text = "收到空消息"
            print(f"DEBUG AgentExecutorWrapper: 没有提取到消息或执行失败，返回默认消息: '{default_text}'")
            response_message = Message(
                messageId=str(uuid4()),
                role=Role.agent,
                parts=[Part(root=TextPart(text=default_text))]
            )

            # 入队响应消息
            print(f"DEBUG AgentExecutorWrapper: 入队默认响应消息")
            await event_queue.enqueue_event(response_message)

        except Exception as e:
            # 创建错误消息
            print(f"DEBUG AgentExecutorWrapper: 最外层异常: {str(e)}")

            traceback.print_exc()
            error_message = Message(
                messageId=str(uuid4()),
                role=Role.agent,
                parts=[Part(root=TextPart(text=f"执行出错: {str(e)}"))]
            )

            # 入队错误消息
            print(f"DEBUG AgentExecutorWrapper: 入队最外层错误消息")
            await event_queue.enqueue_event(error_message)

    async def cancel(self, context, event_queue):
        """
        取消正在执行的任务
        
        Args:
            context: 请求上下文
            event_queue: 事件队列
        """

        # 创建取消消息
        cancel_message = Message(
            messageId=str(uuid4()),
            role=Role.agent,
            parts=[Part(root=TextPart(text="任务已被用户取消"))]
        )

        # 入队取消消息
        await event_queue.enqueue_event(cancel_message)


class AgentServer(BaseServer):
    """纯A2A协议的Agent服务"""

    def __init__(
            self,
            agent: Agent,
            host: str = "0.0.0.0",
            port: int = 8000
    ):
        """
        初始化AgentServer
        
        Args:
            agent: 要服务的Agent实例
            host: 服务器主机
            port: 服务器端口
        """
        super().__init__(
            host=host,
            port=port,
            name=agent.name or "Agent Server",
            description=agent.description or "A2A Agent Protocol Server"
        )
        self.agent = agent

    def create_agent_card(self) -> AgentCard:
        """
        创建AgentCard
        
        Returns:
            AgentCard: 包含Agent信息的卡片
        """
        # 获取Agent信息
        name = self.agent.name or "Unknown Agent"
        description = self.agent.description or self.agent.role or "An AI agent"

        # 获取工具信息（作为技能）
        skills = []
        if hasattr(self.agent, "get_tools"):
            # 使用临时会话ID获取工具列表
            tools = self.agent.get_tools(session_id="temp_session_id")
            if tools:
                for i, tool in enumerate(tools):
                    tool_name = getattr(tool, "name", None)
                    # 检查工具是否有description属性（agno框架的Function类）
                    if hasattr(tool, "description") and tool.description:
                        tool_description = tool.description
                    elif hasattr(tool, "__doc__") and tool.__doc__:
                        tool_description = tool.__doc__.strip()
                    else:
                        tool_description = f"Tool: {tool_name}"

                    if tool_name:
                        skills.append({
                            "id": f"tool_{i}_{tool_name}",
                            "name": tool_name,
                            "description": tool_description,
                            "tags": []
                        })

        # 如果没有工具，添加一个默认技能
        if not skills:
            skills.append({
                "id": "conversation",
                "name": "conversation",
                "description": "能够进行对话交流",
                "tags": []
            })

        # 创建AgentCard
        return AgentCard(
            name=name,
            description=description,
            url=f"http://{self.host}:{self.port}",
            version="1.0.0",
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            capabilities={
                # "streaming": self.agent.is_streamable,
                "streaming": True,
                "pushNotifications": False
            },
            skills=skills
        )

    def create_executor(self) -> AgentExecutor:
        """
        创建执行器
        
        Returns:
            AgentExecutor: 包装了Agent的执行器
        """
        return AgentExecutorWrapper(self.agent)
