# agent_server/servers/team.py
import json
from uuid import uuid4
import traceback

from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.types import AgentCard
from a2a.types import Message, Role, Part
from agno.run.team import TeamRunResponse
from agno.run.response import RunStatus
from agno.team.team import Team

from agno_a2a_ext.servers.base import BaseServer


class TeamExecutorWrapper(AgentExecutor):
    """将Team包装为A2A执行器"""
    
    def __init__(self, team: Team):
        """
        初始化执行器
        
        Args:
            team: 要包装的Team实例
        """
        self.team = team
    
    async def execute(self, context, event_queue):
        """
        执行Team并将结果放入事件队列
        
        Args:
            context: 请求上下文
            event_queue: 事件队列
        """

        
        try:
            # 提取消息和会话ID
            message = ""
            session_id = None
            
            # 详细记录context结构，帮助调试
            print(f"DEBUG TeamExecutorWrapper: 收到请求，context类型={type(context).__name__}")
            
            # 尝试直接从context中获取更多信息
            if hasattr(context, "__dict__"):
                print(f"DEBUG TeamExecutorWrapper: context属性={list(context.__dict__.keys())}")
            
            # 如果context是RequestContext类型，尝试更详细地分析
            if type(context).__name__ == "RequestContext":
                print("DEBUG TeamExecutorWrapper: 处理RequestContext类型")
                
                # 尝试从context.message获取信息
                if hasattr(context, "message"):
                    message_obj = context.message
                    print(f"DEBUG TeamExecutorWrapper: context.message类型={type(message_obj).__name__}")
                    
                    if hasattr(message_obj, "__dict__"):
                        print(f"DEBUG TeamExecutorWrapper: context.message属性={list(message_obj.__dict__.keys())}")
                    
                    # 打印message的字符串表示
                    print(f"DEBUG TeamExecutorWrapper: context.message={context.message}")
                    
                    # 如果message有parts属性
                    if hasattr(message_obj, "parts") and message_obj.parts:
                        print(f"DEBUG TeamExecutorWrapper: context.message.parts数量={len(message_obj.parts)}")
                        
                        # 遍历parts
                        for i, part in enumerate(message_obj.parts):
                            print(f"DEBUG TeamExecutorWrapper: part[{i}]类型={type(part).__name__}")
                            
                            # 打印part的所有属性
                            if hasattr(part, "__dict__"):
                                print(f"DEBUG TeamExecutorWrapper: part[{i}]属性={list(part.__dict__.keys())}")
                            
                            # 尝试从part.root.text提取
                            if hasattr(part, "root") and part.root:
                                print(f"DEBUG TeamExecutorWrapper: part[{i}].root类型={type(part.root).__name__}")
                                
                                # 打印root的所有属性
                                if hasattr(part.root, "__dict__"):
                                    print(f"DEBUG TeamExecutorWrapper: part[{i}].root属性={list(part.root.__dict__.keys())}")
                                
                                # 提取text
                                if hasattr(part.root, "text"):
                                    part_text = part.root.text
                                    message += part_text
                                    print(f"DEBUG TeamExecutorWrapper: 从part[{i}].root.text提取: '{part_text}'")
                            
                            # 尝试从part.text提取
                            elif hasattr(part, "text"):
                                part_text = part.text
                                message += part_text
                                print(f"DEBUG TeamExecutorWrapper: 从part[{i}].text提取: '{part_text}'")
                            
                            # 如果都没有，尝试打印part的完整结构
                            else:
                                try:
                                    print(f"DEBUG TeamExecutorWrapper: part[{i}]结构={json.dumps(part, default=str)}")
                                except:
                                    print(f"DEBUG TeamExecutorWrapper: part[{i}]无法序列化为JSON")
            
            # 如果从context.message无法提取，尝试从request.params中获取
            if not message and hasattr(context, "request") and context.request:
                print(f"DEBUG TeamExecutorWrapper: context.request类型={type(context.request).__name__}")
                
                # 打印request的所有属性
                if hasattr(context.request, "__dict__"):
                    print(f"DEBUG TeamExecutorWrapper: context.request属性={list(context.request.__dict__.keys())}")
                
                # 尝试从params中提取
                if hasattr(context.request, "params") and context.request.params:
                    params = context.request.params
                    print(f"DEBUG TeamExecutorWrapper: params类型={type(params).__name__}")
                    
                    # 打印params的所有属性
                    if hasattr(params, "__dict__"):
                        print(f"DEBUG TeamExecutorWrapper: params属性={list(params.__dict__.keys())}")
                    
                    # 提取message
                    if hasattr(params, "message") and params.message:
                        message_obj = params.message
                        print(f"DEBUG TeamExecutorWrapper: params.message类型={type(message_obj).__name__}")
                        
                        # 打印message_obj的所有属性
                        if hasattr(message_obj, "__dict__"):
                            print(f"DEBUG TeamExecutorWrapper: params.message属性={list(message_obj.__dict__.keys())}")
                        
                        # 如果message_obj是字符串，直接使用
                        if isinstance(message_obj, str):
                            message = message_obj
                            print(f"DEBUG TeamExecutorWrapper: 从params.message提取字符串: '{message}'")
                        
                        # 如果message_obj有parts属性
                        elif hasattr(message_obj, "parts") and message_obj.parts:
                            print(f"DEBUG TeamExecutorWrapper: params.message.parts数量={len(message_obj.parts)}")
                            
                            # 遍历parts
                            for i, part in enumerate(message_obj.parts):
                                print(f"DEBUG TeamExecutorWrapper: params.message.part[{i}]类型={type(part).__name__}")
                                
                                # 尝试从part.root.text提取
                                if hasattr(part, "root") and part.root:
                                    print(f"DEBUG TeamExecutorWrapper: params.message.part[{i}].root类型={type(part.root).__name__}")
                                    
                                    if hasattr(part.root, "text"):
                                        message += part.root.text
                                        print(f"DEBUG TeamExecutorWrapper: 从params.message.part[{i}].root.text提取: '{part.root.text}'")
                                
                                # 尝试从part.text提取
                                elif hasattr(part, "text"):
                                    message += part.text
                                    print(f"DEBUG TeamExecutorWrapper: 从params.message.part[{i}].text提取: '{part.text}'")
                    
                    # 提取会话ID
                    if hasattr(params, "session_id"):
                        session_id = params.session_id
                        print(f"DEBUG TeamExecutorWrapper: 从params提取session_id: {session_id}")
            
            # 如果没有提取到消息，使用默认消息
            if not message:
                message = "收到空消息"
                print(f"警告: 无法提取消息内容，使用默认消息: '{message}'")
                
            # 如果没有提取到会话ID，生成一个新的
            if not session_id:
                session_id = str(uuid4())
                
            print(f"DEBUG TeamExecutorWrapper: 提取的消息='{message}', 会话ID={session_id}")
            print(f"DEBUG TeamExecutorWrapper: 准备调用Team.arun，Team类型: {type(self.team).__name__}, 消息: {message[:50]}...")
                    
            try:
                # 修改：为团队创建一个安全的运行环境
                # 在调用 Team.arun 之前，先保存原始的 _update_team_media 方法

                original_update_team_media = Team._update_team_media
                
                # 创建一个安全的 _update_team_media 方法，处理 run_response 为 None 的情况
                def safe_update_team_media(self, run_response):
                    if run_response is None:
                        print("警告: 跳过 None run_response 的媒体更新")
                        return
                    return original_update_team_media(self, run_response)
                
                # 临时替换方法
                Team._update_team_media = safe_update_team_media
                
                # 同样，保存原始的 add_member_run 方法
                original_add_member_run = TeamRunResponse.add_member_run
                
                # 创建一个安全的 add_member_run 方法
                def safe_add_member_run(self, run_response):
                    if run_response is None:
                        print("警告: 跳过添加 None run_response")
                        return
                    return original_add_member_run(self, run_response)
                
                # 临时替换方法
                TeamRunResponse.add_member_run = safe_add_member_run
                
                # 调用Team.arun获取响应
                run_response = await self.team.arun(
                    message=message,
                    session_id=session_id,
                    stream=False
                )
                
                # 恢复原始方法
                Team._update_team_media = original_update_team_media
                TeamRunResponse.add_member_run = original_add_member_run
                
                # 检查run_response是否为None
                if run_response is None:
                    print(f"警告: Team.arun返回了None，创建一个空的响应")
                    run_response = TeamRunResponse(
                        content="收到空响应",
                        content_type="str",
                        team_id=self.team.team_id if hasattr(self.team, 'team_id') else None,
                        team_name=self.team.name if hasattr(self.team, 'name') else "未知团队",
                        session_id=session_id,
                        status=RunStatus.completed
                    )
                
                # 提取响应内容
                content = ""
                if hasattr(run_response, "content"):
                    content = run_response.content
                
                print(f"DEBUG TeamExecutorWrapper: Team.arun返回内容: '{content}'")
                
                # 创建A2A响应消息
                response_message = Message(
                    messageId=str(uuid4()),
                    role=Role.agent,
                    parts=[Part(text=content or "无响应内容")]
                )
                
                # 将响应放入事件队列
                if hasattr(event_queue, "enqueue_event"):
                    await event_queue.enqueue_event(response_message)
                    print(f"DEBUG TeamExecutorWrapper: 使用enqueue_event入队响应消息")
                elif hasattr(event_queue, "put"):
                    await event_queue.put(response_message)
                    print(f"DEBUG TeamExecutorWrapper: 使用put入队响应消息")
                else:
                    print(f"警告: 未知的事件队列类型: {type(event_queue).__name__}")
                
                print(f"DEBUG TeamExecutorWrapper: 响应处理完成")
                
            except Exception as e:
                print(f"DEBUG TeamExecutorWrapper: Team.arun调用出现异常: {str(e)}")
                traceback.print_exc()
                
                # 创建错误响应消息
                error_message = Message(
                    messageId=str(uuid4()),
                    role=Role.agent,
                    parts=[Part(text=f"执行错误: {str(e)}")]
                )
                
                # 将错误响应放入事件队列
                if hasattr(event_queue, "enqueue_event"):
                    await event_queue.enqueue_event(error_message)
                elif hasattr(event_queue, "put"):
                    await event_queue.put(error_message)
                else:
                    print(f"警告: 未知的事件队列类型: {type(event_queue).__name__}")
                
        except Exception as e:
            print(f"DEBUG TeamExecutorWrapper: 执行过程出现异常: {str(e)}")
            traceback.print_exc()
            
            # 创建错误响应消息
            error_message = Message(
                messageId=str(uuid4()),
                role=Role.agent,
                parts=[Part(text=f"执行错误: {str(e)}")]
            )
            
            # 将错误响应放入事件队列
            if hasattr(event_queue, "enqueue_event"):
                await event_queue.enqueue_event(error_message)
            elif hasattr(event_queue, "put"):
                await event_queue.put(error_message)
            else:
                print(f"警告: 未知的事件队列类型: {type(event_queue).__name__}")
    
    async def cancel(self, context, event_queue):
        """
        取消Team执行
        
        Args:
            context: 请求上下文
            event_queue: 事件队列
        """

        # 创建取消消息
        cancel_message = Message(
            messageId=str(uuid4()),
            role=Role.agent,
            parts=[Part(text="团队任务已被用户取消")]
        )
        
        # 将取消消息放入事件队列
        if hasattr(event_queue, "enqueue_event"):
            await event_queue.enqueue_event(cancel_message)
        elif hasattr(event_queue, "put"):
            await event_queue.put(cancel_message)
        else:
            print(f"警告: 未知的事件队列类型: {type(event_queue).__name__}")


class TeamServer(BaseServer):
    """纯A2A协议的Team服务"""
    
    def __init__(
        self,
        team: Team,
        host: str = "0.0.0.0",
        port: int = 9000
    ):
        """
        初始化TeamServer
        
        Args:
            team: 要服务的Team实例
            host: 服务器主机
            port: 服务器端口
        """
        super().__init__(
            host=host,
            port=port,
            name=team.name or "Team Server",
            description=team.description or "A2A Team Protocol Server"
        )
        self.team = team
    
    def create_agent_card(self) -> AgentCard:
        """
        创建AgentCard
        
        Returns:
            AgentCard: 包含Team信息的卡片
        """
        # 获取Team信息
        name = self.team.name or "Unknown Team"
        description = self.team.description or "A team of agent"
        
        # 获取成员信息
        member_skills = []
        if hasattr(self.team, "members"):
            for i, member in enumerate(self.team.members):
                member_name = getattr(member, "name", f"Member {i}")
                member_role = getattr(member, "role", "")
                member_skills.append({
                    "id": f"member-{i}",  # 添加必需的id字段
                    "name": member_name,
                    "description": member_role or f"Team member {i+1}",
                    "tags": ["team-member"]  # 添加必需的tags字段
                })
        
        # 如果没有成员技能，添加默认技能
        if not member_skills:
            member_skills = [{
                "id": "coordination",
                "name": "coordination",
                "description": "Team coordination",
                "tags": ["coordination"]
            }]
        
        # 创建AgentCard
        return AgentCard(
            name=name,
            description=description,
            url=f"http://{self.host}:{self.port}",
            version="1.0.0",
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            capabilities={
                "streaming": True,
                "pushNotifications": False
            },
            skills=member_skills
        )
    
    def create_executor(self) -> AgentExecutor:
        """
        创建执行器
        
        Returns:
            AgentExecutor: 包装了Team的执行器
        """
        return TeamExecutorWrapper(self.team)


async def main():
    """命令行入口点"""
    import argparse
    import asyncio
    from agno.agent.agent import Agent
    from agno.team.team import Team
    
    parser = argparse.ArgumentParser(description="启动A2A Team服务器")
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机地址")
    parser.add_argument("--port", type=int, default=9000, help="服务器端口")
    parser.add_argument("--name", default="Test Team", help="Team名称")
    parser.add_argument("--description", default="A team of agents", help="Team描述")
    
    args = parser.parse_args()
    
    # 创建测试Agent
    agent1 = Agent(
        name="Assistant 1",
        role="Assistant",
        instructions="我是第一个助手，负责回答问题。"
    )
    
    agent2 = Agent(
        name="Assistant 2", 
        role="Assistant",
        instructions="我是第二个助手，负责补充信息。"
    )
    
    # 创建Team
    team = Team(
        name=args.name,
        description=args.description,
        members=[agent1, agent2],
        instructions="我们是一个团队，协同工作来帮助用户。"
    )
    
    # 创建并启动服务器
    server = TeamServer(team, host=args.host, port=args.port)
    
    try:
        await server.start()
        print(f"Team服务器已启动: http://{args.host}:{args.port}")
        
        # 保持服务器运行
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
        await server.stop()
        print("服务器已停止")


if __name__ == "__main__":
    asyncio.run(main())