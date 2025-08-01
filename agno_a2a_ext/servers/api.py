# agent_server/servers/api.py
import asyncio
import json
from time import time
from typing import Dict, Optional, Any, List, AsyncGenerator, cast
from uuid import uuid4
from io import BytesIO
import traceback

import uvicorn
from fastapi import FastAPI, Request, HTTPException, File, Form, Query, UploadFile, APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from agno.agent.agent import Agent, RunResponse
from agno.media import Audio, Image, Video
from agno.media import File as FileMedia
from agno.memory.agent import AgentMemory
from agno.memory.v2 import Memory
from agno.run.response import RunStatus
from agno.storage.session.agent import AgentSession
from agno.storage.session.team import TeamSession
from agno.team.team import Team

from agno_a2a_ext.apis.playground.operator import get_session_title_from_team_session, get_session_title
from agno_a2a_ext.servers.schemas import (
    AgentGetResponse,
    AgentModel,
    AgentRenameRequest,
    AgentSessionsResponse,
    MemoryResponse,
    TeamGetResponse,
    TeamRenameRequest,
    TeamSessionResponse
)
from agno_a2a_ext.servers.utils import process_audio, process_document, process_image, process_video, format_tools


async def chat_response_streamer(
        agent: Agent,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        images: Optional[List[Image]] = None,
        audio: Optional[List[Audio]] = None,
        videos: Optional[List[Video]] = None,
) -> AsyncGenerator:
    import json  # 导入json模块
    try:
        print(f"DEBUG: 开始流式请求，agent={agent.name}, message='{message}'")
        run_response = await agent.arun(
            message=message,
            session_id=session_id,
            user_id=user_id,
            images=images,
            audio=audio,
            videos=videos,
            stream=True,
            stream_intermediate_steps=True,
        )

        if hasattr(run_response, "__aiter__"):
            print(f"DEBUG: agent.arun返回了异步迭代器")
            chunk_count = 0
            async for run_response_chunk in run_response:
                chunk_count += 1
                print(f"DEBUG: 收到流式响应块 #{chunk_count}, 类型={type(run_response_chunk).__name__}")

                # 确保我们有一个字典
                response_dict = {}
                if hasattr(run_response_chunk, "to_dict"):
                    response_dict = run_response_chunk.to_dict()
                else:
                    # 手动构建字典
                    for attr in ["content", "content_type", "status", "images", "videos", "audio", "created_at"]:
                        if hasattr(run_response_chunk, attr):
                            value = getattr(run_response_chunk, attr)
                            if attr in ["images", "videos", "audio"] and value is None:
                                value = []
                            response_dict[attr] = value

                # 确保有event字段
                if "event" not in response_dict:
                    if hasattr(run_response_chunk, "event"):
                        response_dict["event"] = getattr(run_response_chunk, "event")
                    elif "status" in response_dict:
                        status = response_dict["status"]
                        if status == "RUNNING" or status == RunStatus.running:
                            response_dict["event"] = "RunResponse"
                        elif status == "COMPLETED" or status == RunStatus.completed:
                            response_dict["event"] = "RunCompleted"
                        elif status == "ERROR" or status == RunStatus.error:
                            response_dict["event"] = "RunError"
                        else:
                            response_dict["event"] = "RunResponse"
                    else:
                        # 默认为RunResponse
                        response_dict["event"] = "RunResponse"

                # 确保基本字段存在
                if "content" not in response_dict:
                    response_dict["content"] = ""
                if "content_type" not in response_dict:
                    response_dict["content_type"] = "str"
                if "created_at" not in response_dict:
                    import time
                    response_dict["created_at"] = int(time.time())
                for media in ["images", "videos", "audio"]:
                    if media not in response_dict:
                        response_dict[media] = []

                # 序列化并发送
                json_str = json.dumps(response_dict)
                print(f"DEBUG: 发送JSON块: {json_str[:100]}...")
                yield f"data: {json_str}\n\n"

            print(f"DEBUG: 流式响应完成，共发送 {chunk_count} 个块")
        else:
            print(f"DEBUG: agent.arun返回了非流式响应")
            # 处理非流式响应
            response_dict = {}
            if hasattr(run_response, "to_dict"):
                response_dict = run_response.to_dict()
            else:
                # 手动构建字典
                for attr in ["content", "content_type", "status", "images", "videos", "audio", "created_at"]:
                    if hasattr(run_response, attr):
                        value = getattr(run_response, attr)
                        if attr in ["images", "videos", "audio"] and value is None:
                            value = []
                        response_dict[attr] = value

            # 添加事件字段
            response_dict["event"] = "RunCompleted"

            # 确保基本字段存在
            if "content" not in response_dict:
                response_dict["content"] = ""
            if "content_type" not in response_dict:
                response_dict["content_type"] = "str"
            if "created_at" not in response_dict:
                import time
                response_dict["created_at"] = int(time.time())
            for media in ["images", "videos", "audio"]:
                if media not in response_dict:
                    response_dict[media] = []

            # 序列化并发送
            json_str = json.dumps(response_dict)
            print(f"DEBUG: 发送非流式JSON响应: {json_str[:100]}...")
            yield f"data: {json_str}\n\n"

    except Exception as e:
        print(f"ERROR: 流式处理错误: {str(e)}")
        traceback.print_exc()

        # 创建错误响应
        import time
        error_dict = {
            "content": f"流式处理错误: {str(e)}",
            "content_type": "str",
            "status": "ERROR",
            "event": "RunError",
            "images": [],
            "videos": [],
            "audio": [],
            "created_at": int(time.time())
        }

        # 序列化并发送
        json_str = json.dumps(error_dict)
        print(f"DEBUG: 发送错误JSON响应: {json_str[:100]}...")
        yield f"data: {json_str}\n\n"


async def team_chat_response_streamer(
        team: Team,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        images: Optional[List[Image]] = None,
        audio: Optional[List[Audio]] = None,
        videos: Optional[List[Video]] = None,
        files: Optional[List[FileMedia]] = None,
) -> AsyncGenerator:
    import json  # 导入json模块
    try:
        print(f"DEBUG: 开始团队流式请求，team={team.name}, message='{message}'")

        # 设置流式参数
        stream_params = {
            "stream": True,
            "stream_intermediate_steps": True,
            "stream_member_events": True
        }

        # 执行团队运行
        run_response_stream = await team.arun(
            message=message,
            session_id=session_id,
            user_id=user_id,
            images=images,
            audio=audio,
            videos=videos,
            files=files,
            **stream_params
        )

        # 处理流式响应
        chunk_count = 0
        buffer = ""
        last_response_dict = None
        content_chunks_count = 0

        # 用于存储非内容事件的响应
        events_to_send = []

        async for run_response_chunk in run_response_stream:
            chunk_count += 1
            print(f"DEBUG: 接收流式响应块 #{chunk_count}, 类型={type(run_response_chunk).__name__}")

            # 准备响应字典
            response_dict = {}

            # 如果有to_dict方法，使用它
            if hasattr(run_response_chunk, "to_dict"):
                response_dict = run_response_chunk.to_dict()
                print(f"DEBUG: 使用to_dict()方法提取响应内容")
            else:
                # 手动提取属性
                print(f"DEBUG: 手动提取响应属性")
                for attr in ["content", "content_type", "status", "images", "videos", "audio", "created_at", "team_id",
                             "team_name"]:
                    if hasattr(run_response_chunk, attr):
                        value = getattr(run_response_chunk, attr)
                        if attr in ["images", "videos", "audio"] and value is None:
                            value = []
                        response_dict[attr] = value

            # 确定事件类型
            if "event" not in response_dict:
                # 检查是否有event属性
                if hasattr(run_response_chunk, "event"):
                    response_dict["event"] = getattr(run_response_chunk, "event")
                else:
                    # 根据对象类型确定事件类型
                    event_type = type(run_response_chunk).__name__
                    print(f"DEBUG: 根据类型确定事件: {event_type}")

                    if "RunResponseStarted" in event_type or "RunStarted" in event_type:
                        response_dict["event"] = "TeamRunStarted"
                    elif "RunResponseContent" in event_type:
                        response_dict["event"] = "TeamRunResponseContent"
                    elif "RunCompleted" in event_type or "RunResponseCompleted" in event_type:
                        response_dict["event"] = "TeamRunCompleted"
                    elif "RunError" in event_type:
                        response_dict["event"] = "TeamRunError"
                    elif "status" in response_dict:
                        # 根据状态确定事件类型
                        status = response_dict["status"]
                        if status == "RUNNING" or status == RunStatus.running:
                            response_dict["event"] = "TeamRunResponseContent"
                        elif status == "COMPLETED" or status == RunStatus.completed:
                            response_dict["event"] = "TeamRunCompleted"
                        elif status == "ERROR" or status == RunStatus.error:
                            response_dict["event"] = "TeamRunError"
                        else:
                            # 默认为内容事件
                            response_dict["event"] = "TeamRunResponseContent"
                    else:
                        # 默认为内容事件
                        response_dict["event"] = "TeamRunResponseContent"

            # 确保基本字段存在
            if "content" not in response_dict:
                response_dict["content"] = ""
            if "content_type" not in response_dict:
                response_dict["content_type"] = "str"
            if "created_at" not in response_dict:
                import time
                response_dict["created_at"] = int(time.time())
            if "team_id" not in response_dict and hasattr(team, "team_id"):
                response_dict["team_id"] = team.team_id
            if "team_name" not in response_dict:
                response_dict["team_name"] = team.name
            for media in ["images", "videos", "audio"]:
                if media not in response_dict:
                    response_dict[media] = []

            # 根据事件类型处理
            event = response_dict["event"]

            # 对于开始和完成事件，直接发送
            if event == "TeamRunStarted":
                # 直接发送开始事件
                json_str = json.dumps(response_dict)
                print(f"DEBUG: 发送开始事件: {json_str[:100]}...")
                yield f"data: {json_str}\n\n"
                continue

            elif event == "TeamRunCompleted":
                # 如果有缓冲区内容，先发送缓冲区
                if buffer:
                    # 复制最后一个响应字典并更新内容
                    buffer_response = response_dict.copy()
                    buffer_response["event"] = "TeamRunResponseContent"
                    buffer_response["content"] = buffer
                    json_str = json.dumps(buffer_response)
                    print(f"DEBUG: 发送最终缓冲区内容: {json_str[:100]}...")
                    yield f"data: {json_str}\n\n"
                    buffer = ""

                # 发送完成事件
                json_str = json.dumps(response_dict)
                print(f"DEBUG: 发送完成事件: {json_str[:100]}...")
                yield f"data: {json_str}\n\n"
                continue

            elif event == "TeamRunError":
                # 直接发送错误事件
                json_str = json.dumps(response_dict)
                print(f"DEBUG: 发送错误事件: {json_str[:100]}...")
                yield f"data: {json_str}\n\n"
                continue

            # 对于内容事件，累积到缓冲区
            elif event == "TeamRunResponseContent":
                content = response_dict.get("content", "")
                if content:
                    buffer += content
                    last_response_dict = response_dict
                    content_chunks_count += 1

                    # 检查是否应该发送缓冲区
                    # 1. 如果内容包含句号、问号或感叹号，可能是句子结束
                    # 2. 如果累积了足够多的块（例如10个）
                    # 3. 如果缓冲区太大（例如超过500个字符）
                    if (any(char in buffer for char in ['.', '?', '!', '。', '？', '！', '\n']) or
                            content_chunks_count >= 10 or
                            len(buffer) > 500):
                        # 复制最后一个响应字典并更新内容
                        buffer_response = last_response_dict.copy()
                        buffer_response["content"] = buffer
                        json_str = json.dumps(buffer_response)
                        print(f"DEBUG: 发送缓冲区内容: {json_str[:100]}...")
                        yield f"data: {json_str}\n\n"
                        buffer = ""
                        content_chunks_count = 0

        print(f"DEBUG: 团队流式响应完成，共接收 {chunk_count} 个块")

    except Exception as e:
        print(f"ERROR: 团队流式处理错误: {str(e)}")
        traceback.print_exc()

        # 创建错误响应
        import time
        error_dict = {
            "content": f"团队流式处理错误: {str(e)}",
            "content_type": "str",
            "status": "ERROR",
            "event": "TeamRunError",
            "team_id": getattr(team, "team_id", None),
            "team_name": getattr(team, "name", "未知团队"),
            "images": [],
            "videos": [],
            "audio": [],
            "created_at": int(time.time())
        }

        # 序列化并发送
        json_str = json.dumps(error_dict)
        print(f"DEBUG: 发送错误JSON响应: {json_str[:100]}...")
        yield f"data: {json_str}\n\n"


class ServerAPI:
    """HTTP API服务，类似agent_api的实现"""

    def __init__(
            self,
            agents: List[Agent] = None,
            teams: List[Team] = None,
            workflows: Dict[str, Any] = None,
            host: str = "0.0.0.0",
            port: int = 8080,
            title: str = "Agent API",
            description: str = "Agent and Team API",
            cors_origins: List[str] = None
    ):
        """
        初始化ServerAPI
        
        Args:
            agents: 代理实例列表
            teams: 团队实例列表
            workflows: 工作流实例字典，键为工作流ID
            host: 服务器主机
            port: 服务器端口
            title: API标题
            description: API描述
            cors_origins: CORS允许的源列表
        """
        # 将列表转换为字典，使用对象自身的ID作为键
        self.agents = {}
        if agents:
            for agent in agents:
                agent_id = getattr(agent, "agent_id", None)
                if not agent_id:
                    agent_id = str(uuid4())  # 始终使用UUID格式的agent_id
                    setattr(agent, "agent_id", agent_id)  # 设置agent_id属性
                self.agents[agent_id] = agent
                print(f"DEBUG ServerAPI初始化: 注册agent id={agent_id}, name={agent.name}, 类型={type(agent).__name__}")

        self.teams = {}
        if teams:
            for team in teams:
                team_id = getattr(team, "team_id", None) or team.name
                print(f"team_id: {team_id}")
                self.teams[team_id] = team

        self.workflows = workflows or {}
        self.host = host
        self.port = port
        self.title = title
        self.description = description
        self.cors_origins = cors_origins or ["*"]

        self._server = None
        self._task = None
        self._app = None

    def get_agent(self, agent_id: str) -> Agent:
        """获取代理，如果不存在则抛出异常"""
        print(f"DEBUG 尝试获取agent_id={agent_id}, 可用agents={list(self.agents.keys())}")
        if agent_id not in self.agents:
            raise HTTPException(
                status_code=404,
                detail=f"Agent {agent_id} not found"
            )
        agent = self.agents[agent_id]
        print(f"DEBUG 找到agent: {agent.name}, 类型={type(agent).__name__}")
        return agent

    def get_team(self, team_id: str) -> Team:
        """获取团队，如果不存在则抛出异常"""
        print(self.teams)
        print(team_id)
        if team_id not in self.teams:
            raise HTTPException(
                status_code=404,
                detail=f"Team {team_id} not found"
            )
        return self.teams[team_id]

    def get_workflow(self, workflow_id: str) -> Any:
        """获取工作流，如果不存在则抛出异常"""
        if workflow_id not in self.workflows:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow {workflow_id} not found"
            )
        return self.workflows[workflow_id]

    def create_app(self) -> FastAPI:
        """
        创建FastAPI应用
        
        Returns:
            FastAPI: 配置好的FastAPI应用
        """
        app = FastAPI(
            title=self.title,
            description=self.description
        )

        # 添加CORS中间件
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )

        v1_router = APIRouter(prefix="/v1")

        # 系统路由
        @v1_router.get("/health")
        async def health_check():
            """健康检查"""
            return {"status": "healthy"}

        @v1_router.get("/status")
        async def api_status():
            """API状态"""
            return {
                "playground": "available",
                "status": "available",
                "agent": len(self.agents),
                "teams": len(self.teams),
                "workflows": len(self.workflows)
            }

        # Playground状态
        @v1_router.get("/playground/status")
        async def playground_status():
            """Playground状态"""
            return {"playground": "available"}

        # Agent相关路由
        @v1_router.get("/playground/agents", response_model=List[AgentGetResponse])
        async def get_agents():
            """列出所有代理"""
            agent_list = []

            for agent_id, agent in self.agents.items():
                # 获取工具信息
                agent_tools = agent.get_tools(str(uuid4()))
                formatted_tools = format_tools(agent_tools)

                # 获取模型信息
                name = agent.model.name or agent.model.__class__.__name__ if agent.model else None
                provider = agent.model.provider or agent.model.__class__.__name__ if agent.model else ""
                model_id = agent.model.id if agent.model else None

                if provider and model_id:
                    provider = f"{provider} {model_id}"
                elif name and model_id:
                    provider = f"{name} {model_id}"
                elif model_id:
                    provider = model_id
                else:
                    provider = ""

                # 获取记忆信息
                memory_dict = None
                if agent.memory:
                    if isinstance(agent.memory, AgentMemory) and agent.memory.db:
                        memory_dict = {"name": agent.memory.db.__class__.__name__}
                    elif isinstance(agent.memory, Memory) and agent.memory.db:
                        memory_dict = {"name": "Memory"}
                        if agent.memory.model is not None:
                            memory_dict["model"] = AgentModel(
                                name=agent.memory.model.name,
                                model=agent.memory.model.id,
                                provider=agent.memory.model.provider,
                            )
                        if agent.memory.db is not None:
                            memory_dict["db"] = agent.memory.db.__dict__()  # type: ignore

                agent_list.append(
                    AgentGetResponse(
                        agent_id=agent_id,
                        name=agent.name,
                        model=AgentModel(
                            name=name,
                            model=model_id,
                            provider=provider,
                        ),
                        add_context=agent.add_context,
                        tools=formatted_tools,
                        memory=memory_dict,
                        storage={"name": agent.storage.__class__.__name__} if agent.storage else None,
                        knowledge={"name": agent.knowledge.__class__.__name__} if agent.knowledge else None,
                        description=agent.description,
                        instructions=agent.instructions,
                    )
                )

            return agent_list

        @v1_router.post("/playground/agents/{agent_id}/runs")
        async def create_agent_run(
                agent_id: str,
                message: str = Form(...),
                stream: bool = Form(True),
                monitor: bool = Form(False),
                session_id: Optional[str] = Form(None),
                user_id: Optional[str] = Form(None),
                files: Optional[List[UploadFile]] = File(None),
        ):
            """运行代理"""
            print(f"DEBUG /playground/agent/{agent_id}/runs: 收到请求，message={message}")
            agent = self.get_agent(agent_id)
            print(f"DEBUG 已找到agent: {agent.name}, 类型={type(agent).__name__}")

            if not session_id:
                session_id = str(uuid4())

            if monitor:
                agent.monitoring = True
            else:
                agent.monitoring = False

            # 处理媒体文件
            base64_images: List[Image] = []
            base64_audios: List[Audio] = []
            base64_videos: List[Video] = []

            if files:
                for file in files:
                    try:
                        if file.content_type in ["image/png", "image/jpeg", "image/jpg", "image/webp"]:
                            base64_image = await process_image(file)
                            base64_images.append(base64_image)
                        elif file.content_type in ["audio/wav", "audio/mp3", "audio/mpeg"]:
                            base64_audio = await process_audio(file)
                            base64_audios.append(base64_audio)
                        elif file.content_type in [
                            "video/x-flv", "video/quicktime", "video/mpeg", "video/mp4",
                            "video/webm", "video/wmv", "video/3gpp"
                        ]:
                            base64_video = await process_video(file)
                            base64_videos.append(base64_video)
                        elif file.content_type in [
                            "application/pdf", "text/csv",
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            "text/plain", "application/json"
                        ]:
                            # 检查知识库
                            if agent.knowledge is None:
                                raise HTTPException(status_code=404, detail="KnowledgeBase not found")

                            # 处理文档
                            if file.content_type == "application/pdf":
                                from agno.document.reader.pdf_reader import PDFReader
                                contents = await file.read()
                                pdf_file = BytesIO(contents)
                                pdf_file.name = file.filename
                                file_content = PDFReader().read(pdf_file)
                                agent.knowledge.load_documents(file_content)
                            elif file.content_type == "text/csv":
                                from agno.document.reader.csv_reader import CSVReader
                                contents = await file.read()
                                csv_file = BytesIO(contents)
                                csv_file.name = file.filename
                                file_content = CSVReader().read(csv_file)
                                agent.knowledge.load_documents(file_content)
                            elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                                from agno.document.reader.docx_reader import DocxReader
                                contents = await file.read()
                                docx_file = BytesIO(contents)
                                docx_file.name = file.filename
                                file_content = DocxReader().read(docx_file)
                                agent.knowledge.load_documents(file_content)
                            elif file.content_type == "text/plain":
                                from agno.document.reader.text_reader import TextReader
                                contents = await file.read()
                                text_file = BytesIO(contents)
                                text_file.name = file.filename
                                file_content = TextReader().read(text_file)
                                agent.knowledge.load_documents(file_content)
                            elif file.content_type == "application/json":
                                from agno.document.reader.json_reader import JSONReader
                                contents = await file.read()
                                json_file = BytesIO(contents)
                                json_file.name = file.filename
                                file_content = JSONReader().read(json_file)
                                agent.knowledge.load_documents(file_content)
                        else:
                            raise HTTPException(status_code=400, detail="Unsupported file type")
                    except Exception as e:
                        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

            # 运行代理
            if stream and hasattr(agent, 'is_streamable') and agent.is_streamable:
                return StreamingResponse(
                    chat_response_streamer(
                        agent,
                        message,
                        session_id=session_id,
                        user_id=user_id,
                        images=base64_images if base64_images else None,
                        audio=base64_audios if base64_audios else None,
                        videos=base64_videos if base64_videos else None,
                    ),
                    media_type="text/event-stream",
                )
            else:
                run_response = cast(
                    RunResponse,
                    await agent.arun(
                        message=message,
                        session_id=session_id,
                        user_id=user_id,
                        images=base64_images if base64_images else None,
                        audio=base64_audios if base64_audios else None,
                        videos=base64_videos if base64_videos else None,
                        stream=False,
                    ),
                )
                return run_response.to_dict()

        @v1_router.get("/playground/agents/{agent_id}/sessions")
        async def get_all_agent_sessions(agent_id: str, user_id: Optional[str] = Query(None)):
            """获取代理所有会话"""
            agent = self.get_agent(agent_id)

            if agent.storage is None:
                return JSONResponse(status_code=404, content="Agent does not have storage enabled.")

            agent_sessions = []
            all_agent_sessions: List[AgentSession] = agent.storage.get_all_sessions(user_id=user_id)

            for session in all_agent_sessions:
                title = get_session_title(session)
                agent_sessions.append(
                    AgentSessionsResponse(
                        title=title,
                        session_id=session.session_id,
                        session_name=session.session_data.get("session_name") if session.session_data else None,
                        created_at=session.created_at,
                    )
                )

            return agent_sessions

        @v1_router.get("/playground/agents/{agent_id}/sessions/{session_id}")
        async def get_agent_session(agent_id: str, session_id: str, user_id: Optional[str] = Query(None)):
            """获取代理特定会话"""
            agent = self.get_agent(agent_id)

            if agent.storage is None:
                return JSONResponse(status_code=404, content="Agent does not have storage enabled.")

            agent_session: Optional[AgentSession] = agent.storage.read(session_id, user_id)
            if agent_session is None:
                return JSONResponse(status_code=404, content="Session not found.")

            agent_session_dict = agent_session.to_dict()
            if agent_session.memory is not None:
                runs = agent_session.memory.get("runs")
                if runs is not None:
                    first_run = runs[0]
                    if "content" in first_run:
                        agent_session_dict["runs"] = []

                        for run in runs:
                            first_user_message = None
                            for msg in run.get("messages", []):
                                if msg.get("role") == "user" and msg.get("from_history", False) is False:
                                    first_user_message = msg
                                    break
                            run.pop("memory", None)
                            agent_session_dict["runs"].append(
                                {
                                    "message": first_user_message,
                                    "response": run,
                                }
                            )

            return agent_session_dict

        @v1_router.post("/playground/agents/{agent_id}/sessions/{session_id}/rename")
        async def rename_agent_session(agent_id: str, session_id: str, body: AgentRenameRequest):
            """重命名代理会话"""
            agent = self.get_agent(agent_id)

            if agent.storage is None:
                return JSONResponse(status_code=404, content="Agent does not have storage enabled.")

            all_agent_sessions: List[AgentSession] = agent.storage.get_all_sessions(user_id=body.user_id)
            for session in all_agent_sessions:
                if session.session_id == session_id:
                    agent.rename_session(body.name, session_id=session_id)
                    return JSONResponse(content={"message": f"successfully renamed session {session.session_id}"})

            return JSONResponse(status_code=404, content="Session not found.")

        @v1_router.delete("/playground/agents/{agent_id}/sessions/{session_id}")
        async def delete_agent_session(agent_id: str, session_id: str, user_id: Optional[str] = Query(None)):
            """删除代理会话"""
            agent = self.get_agent(agent_id)

            if agent.storage is None:
                return JSONResponse(status_code=404, content="Agent does not have storage enabled.")

            all_agent_sessions: List[AgentSession] = agent.storage.get_all_sessions(user_id=user_id)
            for session in all_agent_sessions:
                if session.session_id == session_id:
                    agent.delete_session(session_id)
                    return JSONResponse(content={"message": f"successfully deleted session {session_id}"})

            return JSONResponse(status_code=404, content="Session not found.")

        @v1_router.get("/playground/agents/{agent_id}/memories")
        async def get_agent_memories(agent_id: str, user_id: str = Query(...)):
            """获取代理记忆"""
            agent = self.get_agent(agent_id)

            if agent.memory is None:
                return JSONResponse(status_code=404, content="Agent does not have memory enabled.")

            if isinstance(agent.memory, Memory):
                memories = agent.memory.get_user_memories(user_id=user_id)
                return [
                    MemoryResponse(memory=memory.memory, topics=memory.topics, last_updated=memory.last_updated)
                    for memory in memories
                ]
            else:
                return []

        # Team相关路由
        @v1_router.get("/playground/teams")
        async def get_teams():
            """列出所有团队"""
            return [TeamGetResponse.from_team(team) for team in self.teams.values()]

        @v1_router.get("/playground/teams/{team_id}")
        async def get_team(team_id: str):
            """获取特定团队"""
            team = self.get_team(team_id)
            return TeamGetResponse.from_team(team)

        @v1_router.post("/playground/teams/{team_id}/runs")
        async def create_team_run(
                team_id: str,
                message: str = Form(...),
                stream: bool = Form(True),
                monitor: bool = Form(True),
                session_id: Optional[str] = Form(None),
                user_id: Optional[str] = Form(None),
                files: Optional[List[UploadFile]] = File(None),
        ):
            """
            创建团队运行
            
            Args:
                team_id: 团队ID
                message: 用户消息
                stream: 是否流式响应
                monitor: 是否监控
                session_id: 会话ID
                user_id: 用户ID
                files: 文件列表
                
            Returns:
                流式响应或普通响应
            """
            # 获取团队
            team = self.get_team(team_id)

            if not session_id:
                session_id = str(uuid4())

            if monitor:
                team.monitoring = True
            else:
                team.monitoring = False

            # 处理媒体文件
            base64_images: List[Image] = []
            base64_audios: List[Audio] = []
            base64_videos: List[Video] = []
            document_files: List[FileMedia] = []

            if files:
                for file in files:
                    try:
                        if file.content_type in ["image/png", "image/jpeg", "image/jpg", "image/webp"]:
                            base64_image = await process_image(file)
                            base64_images.append(base64_image)
                        elif file.content_type in ["audio/wav", "audio/mp3", "audio/mpeg"]:
                            base64_audio = await process_audio(file)
                            base64_audios.append(base64_audio)
                        elif file.content_type in [
                            "video/x-flv", "video/quicktime", "video/mpeg", "video/mp4",
                            "video/webm", "video/wmv", "video/3gpp"
                        ]:
                            base64_video = await process_video(file)
                            base64_videos.append(base64_video)
                        elif file.content_type in [
                            "application/pdf", "text/csv",
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            "text/plain", "application/json"
                        ]:
                            document_file = await process_document(file)
                            if document_file is not None:
                                document_files.append(document_file)
                        else:
                            raise HTTPException(status_code=400, detail="Unsupported file type")
                    except Exception as e:
                        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

            print(f"DEBUG: 尝试使用流式响应，stream={stream}")

            try:
                # 尝试流式响应
                if stream:
                    return StreamingResponse(
                        team_chat_response_streamer(
                            team, message, session_id=session_id, user_id=user_id,
                            images=base64_images, audio=base64_audios, videos=base64_videos, files=document_files
                        ),
                        media_type="text/event-stream",
                    )
                else:
                    # 非流式响应
                    run_response = await team.arun(
                        message=message, session_id=session_id, user_id=user_id,
                        images=base64_images, audio=base64_audios, videos=base64_videos, files=document_files,
                        stream=False
                    )

                    # 确保有正确的响应格式
                    response_dict = {}
                    if hasattr(run_response, "to_dict"):
                        response_dict = run_response.to_dict()
                    else:
                        # 手动构建字典
                        for attr in ["content", "content_type", "status", "images", "videos", "audio", "created_at",
                                     "team_id", "team_name"]:
                            if hasattr(run_response, attr):
                                value = getattr(run_response, attr)
                                if attr in ["images", "videos", "audio"] and value is None:
                                    value = []
                                response_dict[attr] = value

                    # 添加事件字段
                    response_dict["event"] = "TeamRunCompleted"

                    # 确保基本字段存在
                    if "content" not in response_dict:
                        response_dict["content"] = ""
                    if "content_type" not in response_dict:
                        response_dict["content_type"] = "str"
                    if "created_at" not in response_dict:
                        import time
                        response_dict["created_at"] = int(time.time())
                    if "team_id" not in response_dict:
                        response_dict["team_id"] = team_id
                    if "team_name" not in response_dict:
                        response_dict["team_name"] = team.name
                    for media in ["images", "videos", "audio"]:
                        if media not in response_dict:
                            response_dict[media] = []

                    return response_dict

            except Exception as e:
                print(f"ERROR: 团队运行错误: {str(e)}")
                traceback.print_exc()

                # 如果流式响应失败，尝试非流式响应
                if stream:
                    print("尝试回退到非流式响应")
                    try:
                        run_response = await team.arun(
                            message=message, session_id=session_id, user_id=user_id,
                            images=base64_images, audio=base64_audios, videos=base64_videos, files=document_files,
                            stream=False
                        )
                        return run_response.to_dict()
                    except Exception as e2:
                        print(f"非流式响应也失败: {str(e2)}")
                        raise HTTPException(status_code=500, detail=f"Team run failed: {str(e2)}")

                raise HTTPException(status_code=500, detail=f"Team run failed: {str(e)}")

        @v1_router.get("/playground/teams/{team_id}/sessions", response_model=List[TeamSessionResponse])
        async def get_all_team_sessions(team_id: str, user_id: Optional[str] = Query(None)):
            """获取团队所有会话"""
            team = self.get_team(team_id)

            if team.storage is None:
                raise HTTPException(status_code=404, detail="Team does not have storage enabled")

            try:
                all_team_sessions: List[TeamSession] = team.storage.get_all_sessions(user_id=user_id, entity_id=team_id)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error retrieving sessions: {str(e)}")

            team_sessions: List[TeamSessionResponse] = []
            for session in all_team_sessions:
                title = get_session_title_from_team_session(session)
                team_sessions.append(
                    TeamSessionResponse(
                        title=title,
                        session_id=session.session_id,
                        session_name=session.session_data.get("session_name") if session.session_data else None,
                        created_at=session.created_at,
                    )
                )

            return team_sessions

        @v1_router.get("/playground/teams/{team_id}/sessions/{session_id}")
        async def get_team_session(team_id: str, session_id: str, user_id: Optional[str] = Query(None)):
            """获取团队特定会话"""
            team = self.get_team(team_id)

            if team.storage is None:
                raise HTTPException(status_code=404, detail="Team does not have storage enabled")

            try:
                team_session: Optional[TeamSession] = team.storage.read(session_id, user_id)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error retrieving session: {str(e)}")

            if not team_session:
                raise HTTPException(status_code=404, detail="Session not found")

            team_session_dict = team_session.to_dict()
            if team_session.memory is not None:
                runs = team_session.memory.get("runs")
                if runs is not None:
                    first_run = runs[0]
                    if "content" in first_run:
                        team_session_dict["runs"] = []
                        for run in runs:
                            first_user_message = None
                            for msg in run.get("messages", []):
                                if msg.get("role") == "user" and msg.get("from_history", False) is False:
                                    first_user_message = msg
                                    break
                            team_session_dict.pop("memory", None)
                            team_session_dict["runs"].append(
                                {
                                    "message": first_user_message,
                                    "response": run,
                                }
                            )

            return team_session_dict

        @v1_router.post("/playground/teams/{team_id}/sessions/{session_id}/rename")
        async def rename_team_session(team_id: str, session_id: str, body: TeamRenameRequest):
            """重命名团队会话"""
            team = self.get_team(team_id)

            if team.storage is None:
                raise HTTPException(status_code=404, detail="Team does not have storage enabled")

            all_team_sessions: List[TeamSession] = team.storage.get_all_sessions(user_id=body.user_id,
                                                                                 entity_id=team_id)
            for session in all_team_sessions:
                if session.session_id == session_id:
                    team.rename_session(body.name, session_id=session_id)
                    return JSONResponse(content={"message": f"successfully renamed team session {body.name}"})

            raise HTTPException(status_code=404, detail="Session not found")

        @v1_router.delete("/playground/teams/{team_id}/sessions/{session_id}")
        async def delete_team_session(team_id: str, session_id: str, user_id: Optional[str] = Query(None)):
            """删除团队会话"""
            team = self.get_team(team_id)

            if team.storage is None:
                raise HTTPException(status_code=404, detail="Team does not have storage enabled")

            all_team_sessions: List[TeamSession] = team.storage.get_all_sessions(user_id=user_id, entity_id=team_id)
            for session in all_team_sessions:
                if session.session_id == session_id:
                    team.delete_session(session_id)
                    return JSONResponse(content={"message": f"successfully deleted team session {session_id}"})

            raise HTTPException(status_code=404, detail="Session not found")

        @v1_router.get("/playground/teams/{team_id}/memories")
        async def get_team_memories(team_id: str, user_id: str = Query(...)):
            """获取团队记忆"""
            team = self.get_team(team_id)

            if team.memory is None:
                return JSONResponse(status_code=404, content="Team does not have memory enabled.")

            if isinstance(team.memory, Memory):
                memories = team.memory.get_user_memories(user_id=user_id)
                return [
                    MemoryResponse(memory=memory.memory, topics=memory.topics, last_updated=memory.last_updated)
                    for memory in memories
                ]
            else:
                return []

        # 简化的API（兼容旧版）
        @v1_router.get("/agents")
        async def list_agents():
            """列出所有代理"""
            return {
                "agent": [
                    {"id": agent_id, "name": agent.name}
                    for agent_id, agent in self.agents.items()
                ]
            }

        @v1_router.post("/agents/{agent_id}/run")
        async def run_agent(agent_id: str, request: Request):
            """运行代理（非流式）"""
            print(f"DEBUG ServerAPI: 收到agent_id={agent_id}的运行请求")
            agent = self.get_agent(agent_id)
            print(f"DEBUG ServerAPI: 已获取agent，类型={type(agent).__name__}")
            data = await request.json()

            message = data.get("message", "")
            session_id = data.get("session_id", str(uuid4()))
            print(f"DEBUG ServerAPI: 将运行agent，消息='{message}'")

            try:
                response = await agent.arun(
                    message=message,
                    session_id=session_id,
                    stream=False
                )
                print(
                    f"DEBUG ServerAPI: agent.arun完成，响应内容='{response.content if hasattr(response, 'content') else None}'")

                # 返回完整的RunResponse格式
                if hasattr(response, 'to_dict'):
                    result = response.to_dict()
                else:
                    # 手动构建完整的响应格式
                    result = {
                        "content": response.content if hasattr(response, 'content') else "",
                        "content_type": getattr(response, 'content_type', 'str'),
                        "model": getattr(response, 'model', None),
                        "model_provider": getattr(response, 'model_provider', None),
                        "run_id": getattr(response, 'run_id', str(uuid4())),
                        "agent_id": getattr(response, 'agent_id', agent_id),
                        "agent_name": getattr(response, 'agent_name', agent.name if hasattr(agent, 'name') else None),
                        "session_id": getattr(response, 'session_id', session_id),
                        "created_at": getattr(response, 'created_at', int(time())),
                        "status": getattr(response, 'status', 'RUNNING'),
                        "messages": getattr(response, 'messages', []),
                        "metrics": getattr(response, 'metrics', {}),
                        "tools": getattr(response, 'tools', [])
                    }

                return result
            except Exception as e:
                print(f"DEBUG ServerAPI: agent.arun出错: {str(e)}")
                traceback.print_exc()
                return {
                    "content": f"处理请求时出错: {str(e)}",
                    "error": str(e),
                    "content_type": "str",
                    "status": "ERROR"
                }

        @v1_router.post("/agents/{agent_id}/stream")
        async def stream_agent(agent_id: str, request: Request):
            """运行代理（流式）"""
            agent = self.get_agent(agent_id)
            data = await request.json()

            message = data.get("message", "")
            session_id = data.get("session_id", str(uuid4()))

            async def generate():
                async for chunk in agent.arun(
                        message=message,
                        session_id=session_id,
                        stream=True
                ):
                    if isinstance(chunk, str):
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                    elif hasattr(chunk, 'content'):
                        yield f"data: {json.dumps({'content': chunk.content})}\n\n"

            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )

        @v1_router.get("/teams")
        async def list_teams():
            """列出所有团队"""
            return {
                "teams": [
                    {"id": team_id, "name": team.name}
                    for team_id, team in self.teams.items()
                ]
            }

        @v1_router.post("/teams/{team_id}/run")
        async def run_team(team_id: str, request: Request):
            """运行团队（非流式）"""
            team = self.get_team(team_id)
            data = await request.json()

            message = data.get("message", "")
            session_id = data.get("session_id", str(uuid4()))

            try:
                response = await team.arun(
                    message=message,
                    session_id=session_id,
                    stream=False
                )

                # 返回完整的RunResponse格式
                if hasattr(response, 'to_dict'):
                    result = response.to_dict()
                else:
                    # 手动构建完整的响应格式
                    result = {
                        "content": response.content if hasattr(response, 'content') else "",
                        "content_type": getattr(response, 'content_type', 'str'),
                        "model": getattr(response, 'model', None),
                        "model_provider": getattr(response, 'model_provider', None),
                        "run_id": getattr(response, 'run_id', str(uuid4())),
                        "team_id": getattr(response, 'team_id', team_id),
                        "team_name": getattr(response, 'team_name', team.name if hasattr(team, 'name') else None),
                        "session_id": getattr(response, 'session_id', session_id),
                        "created_at": getattr(response, 'created_at', int(time())),
                        "status": getattr(response, 'status', 'RUNNING'),
                        "messages": getattr(response, 'messages', []),
                        "metrics": getattr(response, 'metrics', {}),
                        "tools": getattr(response, 'tools', [])
                    }

                # 添加团队成员运行记录（如果有）
                if hasattr(response, 'member_runs') and response.member_runs:
                    result["member_runs"] = [
                        {
                            "agent_id": run.agent_id if hasattr(run, 'agent_id') else None,
                            "content": run.content if hasattr(run, 'content') else None
                        }
                        for run in response.member_runs
                    ]

                return result
            except Exception as e:
                print(f"DEBUG ServerAPI: team.arun出错: {str(e)}")
                traceback.print_exc()
                return {
                    "content": f"处理请求时出错: {str(e)}",
                    "error": str(e),
                    "content_type": "str",
                    "status": "ERROR"
                }

        @v1_router.post("/teams/{team_id}/stream")
        async def stream_team(team_id: str, request: Request):
            """运行团队（流式）"""
            team = self.get_team(team_id)
            data = await request.json()

            message = data.get("message", "")
            session_id = data.get("session_id", str(uuid4()))

            async def generate():
                async for chunk in team.arun(
                        message=message,
                        session_id=session_id,
                        stream=True
                ):
                    if isinstance(chunk, str):
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                    elif hasattr(chunk, 'content'):
                        yield f"data: {json.dumps({'content': chunk.content})}\n\n"

            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )

        app.include_router(v1_router)
        self._app = app

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
        print(f"ServerAPI已启动：http://{self.host}:{self.port}")

    async def stop(self):
        """停止服务器"""
        if self._server:
            self._server.should_exit = True

            if self._task and not self._task.done():
                self._task.cancel()

            self._server = None
            self._task = None
            self._app = None
            print("ServerAPI已停止")


async def main():
    """命令行入口点"""
    import argparse
    import asyncio
    from agno.agent.agent import Agent
    from agno.team.team import Team
    
    parser = argparse.ArgumentParser(description="启动AI-Agents API服务器")
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机地址")
    parser.add_argument("--port", type=int, default=8080, help="服务器端口")
    parser.add_argument("--title", default="AI-Agents API", help="API标题")
    parser.add_argument("--description", default="AI-Agents API服务器", help="API描述")
    
    args = parser.parse_args()
    
    # 创建测试Agent
    agent1 = Agent(
        name="General Assistant",
        role="Assistant",
        instructions="我是一个通用助手，可以帮助用户解决各种问题。"
    )
    
    agent2 = Agent(
        name="Code Assistant",
        role="Developer",
        instructions="我是一个代码助手，专门帮助用户解决编程问题。"
    )
    
    # 创建测试Team
    team = Team(
        name="Development Team",
        description="一个开发团队，包含多个专业助手",
        members=[agent1, agent2],
        instructions="我们是一个开发团队，协同工作来帮助用户解决技术问题。"
    )
    
    # 创建API服务器
    api_server = ServerAPI(
        agents=[agent1, agent2],
        teams=[team],
        host=args.host,
        port=args.port,
        title=args.title,
        description=args.description
    )
    
    try:
        await api_server.start()
        print(f"API服务器已启动: http://{args.host}:{args.port}")
        print(f"API文档: http://{args.host}:{args.port}/docs")
        
        # 保持服务器运行
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
        await api_server.stop()
        print("服务器已停止")


if __name__ == "__main__":
    asyncio.run(main())
