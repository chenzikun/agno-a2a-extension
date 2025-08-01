# ai_agent/agent/a2a_agent.py
from __future__ import annotations

from typing import Optional, Union, AsyncGenerator, AsyncIterator
from uuid import uuid4
import traceback

import httpx
from a2a.client import A2AClient
from a2a.types import (
    SendStreamingMessageRequest,
    SendMessageRequest,
    MessageSendParams,
    Message,
    Role,
    Part, TextPart
)
from agno.agent.agent import Agent
from agno.run.response import RunResponse, RunStatus


class A2AAgent(Agent):
    """
    A2A协议客户端代理，作为Team的成员连接到远程A2A服务
    
    该代理遵循Agent接口，但会将请求转发到远程A2A服务
    """

    def __init__(
            self,
            base_url: str,
            name: str,
            role: Optional[str] = None,
            timeout: float = 60.0,
            **kwargs
    ):
        """
        初始化A2AAgent
        
        Args:
            base_url: 远程A2A服务的基础URL
            name: 代理名称
            role: 代理角色（可选）
            timeout: 请求超时时间（秒）
            **kwargs: 传递给Agent父类的其他参数
        """
        super().__init__(
            name=name,
            role=role or name,
            **kwargs
        )
        self.base_url = base_url
        self.timeout = timeout
        self._client = None
        self._httpx_client = None

        # 添加流式响应支持标识
        self.is_streamable = True

    async def _ensure_client(self) -> A2AClient:
        """
        确保A2A客户端已初始化
        
        Returns:
            初始化好的A2A客户端
        """
        if self._client is None:
            print(f"DEBUG 初始化A2A客户端，base_url={self.base_url}")
            try:
                self._httpx_client = httpx.AsyncClient(timeout=self.timeout)
                self._client = await A2AClient.get_client_from_agent_card_url(
                    self._httpx_client, self.base_url
                )
                print(f"DEBUG A2A客户端初始化成功，client={self._client}")
            except Exception as e:
                print(f"ERROR 初始化A2A客户端失败: {str(e)}")
                traceback.print_exc()
                raise e
        return self._client

    async def arun(
            self,
            message: str,
            session_id: Optional[str] = None,
            stream: bool = False,
            **kwargs
    ) -> Union[RunResponse, AsyncGenerator[RunResponse, None]]:
        """
        异步运行代理，获取回复
        
        Args:
            message: 用户消息
            session_id: 会话ID
            stream: 是否流式响应
            **kwargs: 其他参数
            
        Returns:
            RunResponse或AsyncGenerator[RunResponse, None]: 运行响应或响应流
        """
        client = await self._ensure_client()
        if not session_id:
            session_id = self._generate_session_id()

        # 创建唯一请求ID
        request_id = str(uuid4())

        print(
            f"DEBUG A2AAgent 请求内容: message='{message}', session_id={session_id}, stream={stream}, request_id={request_id}")

        try:
            # 使用A2A标准接口发送消息
            if stream:
                print(
                    f"DEBUG A2AAgent 发送流式请求: URL={getattr(client, 'url', getattr(client, 'base_url', '未知URL'))}")

                # 使用标准接口发送流式请求

                # 构造消息对象
                message_obj = Message(
                    messageId=str(uuid4()),
                    role=Role.user,
                    parts=[Part(root=TextPart(kind="text", text=message))]
                )

                # 构造请求参数
                params = MessageSendParams(
                    message=message_obj,
                    session_id=session_id,
                    stream=True
                )

                # 构造流式请求
                request = SendStreamingMessageRequest(
                    id=request_id,
                    params=params
                )

                # 发送流式请求
                try:
                    response_stream = client.send_message_streaming(request)
                    return self._handle_stream_response(response_stream, request_id)
                except Exception as e:
                    print(f"流式请求失败: {str(e)}")
                    # 如果流式请求失败，回退到非流式请求
                    # 注意：这里应该返回RunResponse，而不是AsyncGenerator
                    try:
                        # 构造非流式请求

                        # 构造消息对象
                        message_obj = Message(
                            messageId=str(uuid4()),
                            role=Role.user,
                            parts=[Part(root=TextPart(kind="text", text=message))]
                        )

                        # 构造请求参数
                        params = MessageSendParams(
                            message=message_obj,
                            session_id=session_id,
                            stream=False
                        )

                        # 构造请求
                        fallback_request = SendMessageRequest(
                            id=request_id,
                            params=params
                        )

                        response = await client.send_message(fallback_request)
                        run_response = self._handle_nonstream_response(response)

                        # 设置run_response属性
                        self.run_response = run_response

                        return run_response
                    except Exception as fallback_error:
                        print(f"回退请求也失败: {str(fallback_error)}")
                        # 创建错误响应

                        error_response = RunResponse(
                            content=f"执行错误: {str(fallback_error)}",
                            content_type="str",
                            status=RunStatus.error
                        )
                        setattr(error_response, "event", "RunError")

                        # 设置run_response属性
                        self.run_response = error_response

                        return error_response
            else:
                # 非流式请求
                print(
                    f"DEBUG A2AAgent 发送普通请求: URL={getattr(client, 'url', getattr(client, 'base_url', '未知URL'))}")

                # 使用标准接口发送普通请求

                # 构造消息对象
                message_obj = Message(
                    messageId=str(uuid4()),
                    role=Role.user,
                    parts=[Part(root=TextPart(kind="text", text=message))]
                )

                # 构造请求参数
                params = MessageSendParams(
                    message=message_obj,
                    session_id=session_id,
                    stream=False
                )

                # 构造请求
                request = SendMessageRequest(
                    id=request_id,
                    params=params
                )

                # 发送请求
                response = await client.send_message(request)

                # 处理响应
                run_response = self._handle_nonstream_response(response)

                # 设置run_response属性，这样Team可以正确访问
                self.run_response = run_response

                return run_response

        except Exception as e:
            print(f"A2AAgent.arun 执行错误: {str(e)}")
            traceback.print_exc()

            # 创建错误响应
            error_response = RunResponse(
                content=f"执行错误: {str(e)}",
                content_type="str",
                status=RunStatus.error
            )
            setattr(error_response, "event", "RunError")

            # 设置run_response属性
            self.run_response = error_response

            return error_response

    async def _handle_nonstream_fallback(self, client, message, session_id, request_id):
        """当流式请求失败时的回退方法"""
        try:
            # 使用标准接口发送普通请求

            # 构造消息对象
            message_obj = Message(
                messageId=str(uuid4()),
                role=Role.user,
                parts=[Part(root=TextPart(kind="text", text=message))]
            )

            # 构造请求参数
            params = MessageSendParams(
                message=message_obj,
                session_id=session_id,
                stream=False
            )

            # 构造请求
            request = SendMessageRequest(
                id=request_id,
                params=params
            )

            # 发送请求
            response = await client.send_message(request)

            # 直接返回RunResponse对象，而不是异步生成器
            return self._handle_nonstream_response(response)

        except Exception as e:
            print(f"回退请求失败: {str(e)}")

            # 创建错误响应
            error_response = RunResponse(
                content=f"回退请求失败: {str(e)}",
                content_type="str",
                status=RunStatus.error
            )
            setattr(error_response, "event", "RunError")

            # 设置run_response属性
            self.run_response = error_response

            return error_response

    def _extract_content_from_response(self, response):
        """从A2A响应中提取内容"""
        content = ""

        # 调试输出
        print(f"DEBUG A2AAgent 提取响应内容: 响应类型={type(response).__name__}")

        # 如果response是TextPart类型
        if hasattr(response, "kind") and hasattr(response, "text") and getattr(response, "kind") == "text":
            content = response.text
            print(f"DEBUG A2AAgent 提取响应内容: 从TextPart.text直接提取: '{content}'")
            return content

        # 如果response是SendMessageSuccessResponse或其他包含root属性的对象
        if hasattr(response, "root"):
            print(f"DEBUG A2AAgent 提取响应内容: 从response.root提取, 类型={type(response.root).__name__}")

            # 如果root有result属性
            if hasattr(response.root, "result"):
                result = response.root.result
                print(f"DEBUG A2AAgent 提取响应内容: 从root.result提取, 类型={type(result).__name__}")

                # 如果result是Message并有parts属性
                if hasattr(result, "parts") and result.parts:
                    print(f"DEBUG A2AAgent 提取响应内容: 找到parts, 数量={len(result.parts)}")
                    for i, part in enumerate(result.parts):
                        print(f"DEBUG A2AAgent 提取响应内容: part[{i}]类型={type(part).__name__}")

                        # 从Part.root中提取文本
                        if hasattr(part, "root") and part.root:
                            if hasattr(part.root, "text"):
                                content += part.root.text
                                print(f"DEBUG A2AAgent 提取响应内容: 从part.root.text提取: '{part.root.text}'")
                        # 从Part中直接提取文本
                        elif hasattr(part, "text"):
                            content += part.text
                            print(f"DEBUG A2AAgent 提取响应内容: 从part.text提取: '{part.text}'")

        # 如果response直接有result属性
        elif hasattr(response, "result"):
            result = response.result
            print(f"DEBUG A2AAgent 提取响应内容: 从response.result提取, 类型={type(result).__name__}")

            # 如果result是Message并有parts属性
            if hasattr(result, "parts") and result.parts:
                print(f"DEBUG A2AAgent 提取响应内容: 找到parts, 数量={len(result.parts)}")
                for i, part in enumerate(result.parts):
                    print(f"DEBUG A2AAgent 提取响应内容: part[{i}]类型={type(part).__name__}")

                    # 从Part.root中提取文本
                    if hasattr(part, "root") and part.root:
                        if hasattr(part.root, "text"):
                            content += part.root.text
                            print(f"DEBUG A2AAgent 提取响应内容: 从part.root.text提取: '{part.root.text}'")
                    # 从Part中直接提取文本
                    elif hasattr(part, "text"):
                        content += part.text
                        print(f"DEBUG A2AAgent 提取响应内容: 从part.text提取: '{part.text}'")

        # 如果没有提取到内容，尝试直接访问content属性
        if not content and hasattr(response, "content"):
            content = response.content
            print(f"DEBUG A2AAgent 提取响应内容: 从response.content提取: '{content}'")

        # 如果仍然没有内容，记录警告
        if not content:
            print(f"警告: 无法从响应中提取内容: {response}")
            return "无响应内容"

        print(f"DEBUG A2AAgent 提取响应内容: 最终内容='{content}'")
        return content

    def _handle_nonstream_response(self, response):
        """处理非流式响应"""

        # 提取内容
        content = self._extract_content_from_response(response)

        # 确保内容不为空
        if not content or content == "无响应内容":
            content = "远程服务返回空响应"

        # 创建响应对象
        run_response = RunResponse(
            content=content,
            content_type="str",
            status=RunStatus.completed
        )

        # 设置事件类型
        setattr(run_response, "event", "RunCompleted")

        return run_response

    async def _handle_stream_response(
            self,
            response_stream: AsyncIterator,
            request_id: str
    ) -> AsyncGenerator[RunResponse, None]:
        """
        处理流式响应
        
        Args:
            response_stream: 响应流
            request_id: 请求ID
            
        Yields:
            RunResponse: 运行响应
        """

        try:
            # 跟踪当前的响应内容
            current_content = ""
            chunk_count = 0

            # 处理流中的每个响应
            async for chunk in response_stream:
                chunk_count += 1
                # 调试输出
                print(f"DEBUG A2AAgent 收到流式响应 #{chunk_count}: {chunk}")

                # 从响应中提取内容
                content = ""

                # 如果chunk有root属性（SendStreamingMessageSuccessResponse）
                if hasattr(chunk, "root"):
                    # 如果root有result属性
                    if hasattr(chunk.root, "result"):
                        result = chunk.root.result
                        # 如果result有parts属性
                        if hasattr(result, "parts") and result.parts:
                            for part in result.parts:
                                # 从Part.root中提取文本
                                if hasattr(part, "root") and hasattr(part.root, "text"):
                                    content += part.root.text
                                # 从Part中直接提取文本
                                elif hasattr(part, "text"):
                                    content += part.text

                # 如果chunk直接有result属性
                elif hasattr(chunk, "result"):
                    result = chunk.result
                    # 如果result有parts属性
                    if hasattr(result, "parts") and result.parts:
                        for part in result.parts:
                            # 从Part.root中提取文本
                            if hasattr(part, "root") and hasattr(part.root, "text"):
                                content += part.root.text
                            # 从Part中直接提取文本
                            elif hasattr(part, "text"):
                                content += part.text

                # 如果是字典（我们的手动处理方式）
                elif isinstance(chunk, dict):
                    content = chunk.get("content", "")

                # 更新当前内容
                if content:
                    current_content = content
                    print(f"DEBUG A2AAgent 提取流式内容: '{content}'")

                # 只在有内容时yield响应，避免重复
                if content:
                    # 创建运行中的响应
                    running_response = RunResponse(
                        content=current_content,
                        content_type="str",
                        status=RunStatus.running
                    )
                    setattr(running_response, "event", "RunResponse")
                    yield running_response

            # 发送最终完成响应（只有在有内容时才发送）
            if current_content:
                final_response = RunResponse(
                    content=current_content,
                    content_type="str",
                    status=RunStatus.completed
                )
                setattr(final_response, "event", "RunCompleted")
                yield final_response
            else:
                # 如果没有内容，发送错误响应
                error_response = RunResponse(
                    content="无响应内容",
                    content_type="str",
                    status=RunStatus.error
                )
                setattr(error_response, "event", "RunError")
                yield error_response

        except Exception as e:
            # 发生错误时，发送错误响应
            print(f"处理流式响应时出错: {str(e)}")
            traceback.print_exc()

            error_response = RunResponse(
                content=f"处理响应时出错: {str(e)}",
                content_type="str",
                status=RunStatus.error
            )
            setattr(error_response, "event", "RunError")
            yield error_response

    def _generate_session_id(self) -> str:
        """生成会话ID"""
        return f"a2a-agent-{id(self)}"

    async def close(self):
        """关闭客户端连接"""
        if self._httpx_client:
            await self._httpx_client.aclose()
            self._httpx_client = None
            self._client = None
