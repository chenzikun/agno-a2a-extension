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
    """Wrap Team as an A2A executor"""
    
    def __init__(self, team: Team):
        """
        Initialize executor
        
        Args:
            team: Team instance to wrap
        """
        self.team = team
    
    async def execute(self, context, event_queue):
        """
        Execute Team and put results into event queue
        
        Args:
            context: Request context
            event_queue: Event queue
        """
        try:
            # Extract message and session ID
            message = ""
            session_id = None
            
            # Log context structure for debugging
            print(f"DEBUG TeamExecutorWrapper: Received request, context type={type(context).__name__}")
            
            # Try to get more info directly from context
            if hasattr(context, "__dict__"):
                print(f"DEBUG TeamExecutorWrapper: context attributes={list(context.__dict__.keys())}")
            
            # If context is RequestContext, analyze in detail
            if type(context).__name__ == "RequestContext":
                print("DEBUG TeamExecutorWrapper: Handling RequestContext type")
                
                # Try to get info from context.message
                if hasattr(context, "message"):
                    message_obj = context.message
                    print(f"DEBUG TeamExecutorWrapper: context.message type={type(message_obj).__name__}")
                    
                    if hasattr(message_obj, "__dict__"):
                        print(f"DEBUG TeamExecutorWrapper: context.message attributes={list(message_obj.__dict__.keys())}")
                    
                    print(f"DEBUG TeamExecutorWrapper: context.message={context.message}")
                    
                    # If message has parts attribute
                    if hasattr(message_obj, "parts") and message_obj.parts:
                        print(f"DEBUG TeamExecutorWrapper: context.message.parts count={len(message_obj.parts)}")
                        
                        # Iterate parts
                        for i, part in enumerate(message_obj.parts):
                            print(f"DEBUG TeamExecutorWrapper: part[{i}] type={type(part).__name__}")
                            
                            # Print all attributes of part
                            if hasattr(part, "__dict__"):
                                print(f"DEBUG TeamExecutorWrapper: part[{i}] attributes={list(part.__dict__.keys())}")
                            
                            # Try to extract from part.root.text
                            if hasattr(part, "root") and part.root:
                                print(f"DEBUG TeamExecutorWrapper: part[{i}].root type={type(part.root).__name__}")
                                if hasattr(part.root, "__dict__"):
                                    print(f"DEBUG TeamExecutorWrapper: part[{i}].root attributes={list(part.root.__dict__.keys())}")
                                if hasattr(part.root, "text"):
                                    part_text = part.root.text
                                    message += part_text
                                    print(f"DEBUG TeamExecutorWrapper: Extracted from part[{i}].root.text: '{part_text}'")
                            # Try to extract from part.text
                            elif hasattr(part, "text"):
                                part_text = part.text
                                message += part_text
                                print(f"DEBUG TeamExecutorWrapper: Extracted from part[{i}].text: '{part_text}'")
                            # If neither, try to print full structure
                            else:
                                try:
                                    print(f"DEBUG TeamExecutorWrapper: part[{i}] structure={json.dumps(part, default=str)}")
                                except:
                                    print(f"DEBUG TeamExecutorWrapper: part[{i}] cannot be serialized to JSON")
            # If not extracted from context.message, try from request.params
            if not message and hasattr(context, "request") and context.request:
                print(f"DEBUG TeamExecutorWrapper: context.request type={type(context.request).__name__}")
                if hasattr(context.request, "__dict__"):
                    print(f"DEBUG TeamExecutorWrapper: context.request attributes={list(context.request.__dict__.keys())}")
                if hasattr(context.request, "params") and context.request.params:
                    params = context.request.params
                    print(f"DEBUG TeamExecutorWrapper: params type={type(params).__name__}")
                    if hasattr(params, "__dict__"):
                        print(f"DEBUG TeamExecutorWrapper: params attributes={list(params.__dict__.keys())}")
                    # Extract message
                    if hasattr(params, "message") and params.message:
                        message_obj = params.message
                        print(f"DEBUG TeamExecutorWrapper: params.message type={type(message_obj).__name__}")
                        if hasattr(message_obj, "__dict__"):
                            print(f"DEBUG TeamExecutorWrapper: params.message attributes={list(message_obj.__dict__.keys())}")
                        if isinstance(message_obj, str):
                            message = message_obj
                            print(f"DEBUG TeamExecutorWrapper: Extracted string from params.message: '{message}'")
                        elif hasattr(message_obj, "parts") and message_obj.parts:
                            print(f"DEBUG TeamExecutorWrapper: params.message.parts count={len(message_obj.parts)}")
                            for i, part in enumerate(message_obj.parts):
                                print(f"DEBUG TeamExecutorWrapper: params.message.part[{i}] type={type(part).__name__}")
                                if hasattr(part, "root") and part.root:
                                    print(f"DEBUG TeamExecutorWrapper: params.message.part[{i}].root type={type(part.root).__name__}")
                                    if hasattr(part.root, "text"):
                                        message += part.root.text
                                        print(f"DEBUG TeamExecutorWrapper: Extracted from params.message.part[{i}].root.text: '{part.root.text}'")
                                elif hasattr(part, "text"):
                                    message += part.text
                                    print(f"DEBUG TeamExecutorWrapper: Extracted from params.message.part[{i}].text: '{part.text}'")
                    # Extract session_id
                    if hasattr(params, "session_id"):
                        session_id = params.session_id
                        print(f"DEBUG TeamExecutorWrapper: Extracted session_id from params: {session_id}")
            # If no message extracted, use default
            if not message:
                message = "Received empty message"
                print(f"WARNING: Could not extract message content, using default: '{message}'")
            # If no session_id, generate a new one
            if not session_id:
                session_id = str(uuid4())
            print(f"DEBUG TeamExecutorWrapper: Extracted message='{message}', session_id={session_id}")
            print(f"DEBUG TeamExecutorWrapper: Preparing to call Team.arun, Team type: {type(self.team).__name__}, message: {message[:50]}...")
            try:
                # Patch: create a safe run environment for the team
                # Save the original _update_team_media method before calling Team.arun
                original_update_team_media = Team._update_team_media
                # Create a safe _update_team_media method to handle None run_response
                def safe_update_team_media(self, run_response):
                    if run_response is None:
                        print("WARNING: Skipping media update for None run_response")
                        return
                    return original_update_team_media(self, run_response)
                # Temporarily replace the method
                Team._update_team_media = safe_update_team_media
                # Also save the original add_member_run method
                original_add_member_run = TeamRunResponse.add_member_run
                # Create a safe add_member_run method
                def safe_add_member_run(self, run_response):
                    if run_response is None:
                        print("WARNING: Skipping add_member_run for None run_response")
                        return
                    return original_add_member_run(self, run_response)
                # Temporarily replace the method
                TeamRunResponse.add_member_run = safe_add_member_run
                # Call Team.arun to get response
                run_response = await self.team.arun(
                    message=message,
                    session_id=session_id,
                    stream=False
                )
                # Restore original methods
                Team._update_team_media = original_update_team_media
                TeamRunResponse.add_member_run = original_add_member_run
                # Check if run_response is None
                if run_response is None:
                    print(f"WARNING: Team.arun returned None, creating an empty response")
                    run_response = TeamRunResponse(
                        content="Received empty response",
                        content_type="str",
                        team_id=self.team.team_id if hasattr(self.team, 'team_id') else None,
                        team_name=self.team.name if hasattr(self.team, 'name') else "Unknown Team",
                        session_id=session_id,
                        status=RunStatus.completed
                    )
                # Extract response content
                content = ""
                if hasattr(run_response, "content"):
                    content = run_response.content
                print(f"DEBUG TeamExecutorWrapper: Team.arun returned content: '{content}'")
                # Create A2A response message
                response_message = Message(
                    messageId=str(uuid4()),
                    role=Role.agent,
                    parts=[Part(text=content or "No response content")]
                )
                # Put response into event queue
                if hasattr(event_queue, "enqueue_event"):
                    await event_queue.enqueue_event(response_message)
                    print(f"DEBUG TeamExecutorWrapper: Used enqueue_event to enqueue response message")
                elif hasattr(event_queue, "put"):
                    await event_queue.put(response_message)
                    print(f"DEBUG TeamExecutorWrapper: Used put to enqueue response message")
                else:
                    print(f"WARNING: Unknown event queue type: {type(event_queue).__name__}")
                print(f"DEBUG TeamExecutorWrapper: Response handling complete")
            except Exception as e:
                print(f"DEBUG TeamExecutorWrapper: Exception during Team.arun call: {str(e)}")
                traceback.print_exc()
                # Create error response message
                error_message = Message(
                    messageId=str(uuid4()),
                    role=Role.agent,
                    parts=[Part(text=f"Execution error: {str(e)}")]
                )
                # Put error response into event queue
                if hasattr(event_queue, "enqueue_event"):
                    await event_queue.enqueue_event(error_message)
                elif hasattr(event_queue, "put"):
                    await event_queue.put(error_message)
                else:
                    print(f"WARNING: Unknown event queue type: {type(event_queue).__name__}")
        except Exception as e:
            print(f"DEBUG TeamExecutorWrapper: Exception during execution: {str(e)}")
            traceback.print_exc()
            # Create error response message
            error_message = Message(
                messageId=str(uuid4()),
                role=Role.agent,
                parts=[Part(text=f"Execution error: {str(e)}")]
            )
            # Put error response into event queue
            if hasattr(event_queue, "enqueue_event"):
                await event_queue.enqueue_event(error_message)
            elif hasattr(event_queue, "put"):
                await event_queue.put(error_message)
            else:
                print(f"WARNING: Unknown event queue type: {type(event_queue).__name__}")
    async def cancel(self, context, event_queue):
        """
        Cancel Team execution
        
        Args:
            context: Request context
            event_queue: Event queue
        """
        # Create cancel message
        cancel_message = Message(
            messageId=str(uuid4()),
            role=Role.agent,
            parts=[Part(text="Team task has been cancelled by user")]
        )
        # Put cancel message into event queue
        if hasattr(event_queue, "enqueue_event"):
            await event_queue.enqueue_event(cancel_message)
        elif hasattr(event_queue, "put"):
            await event_queue.put(cancel_message)
        else:
            print(f"WARNING: Unknown event queue type: {type(event_queue).__name__}")


class TeamServer(BaseServer):
    """Pure A2A protocol Team service"""
    
    def __init__(
        self,
        team: Team,
        host: str = "0.0.0.0",
        port: int = 9000
    ):
        """
        Initialize TeamServer
        
        Args:
            team: Team instance to serve
            host: Server host
            port: Server port
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
        Create AgentCard
        
        Returns:
            AgentCard: Card containing Team information
        """
        # Get Team information
        name = self.team.name or "Unknown Team"
        description = self.team.description or "A team of agent"
        # Get member information
        member_skills = []
        if hasattr(self.team, "members"):
            for i, member in enumerate(self.team.members):
                member_name = getattr(member, "name", f"Member {i}")
                member_role = getattr(member, "role", "")
                member_skills.append({
                    "id": f"member-{i}",  # Required id field
                    "name": member_name,
                    "description": member_role or f"Team member {i+1}",
                    "tags": ["team-member"]  # Required tags field
                })
        # If no member skills, add default
        if not member_skills:
            member_skills = [{
                "id": "coordination",
                "name": "coordination",
                "description": "Team coordination",
                "tags": ["coordination"]
            }]
        # Create AgentCard
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
        Create executor
        
        Returns:
            AgentExecutor: Executor wrapping the Team
        """
        return TeamExecutorWrapper(self.team)

async def main():
    """Command line entry point"""
    import argparse
    import asyncio
    from agno.agent.agent import Agent
    from agno.team.team import Team
    
    parser = argparse.ArgumentParser(description="Start A2A Team server")
    parser.add_argument("--host", default="0.0.0.0", help="Server host address")
    parser.add_argument("--port", type=int, default=9000, help="Server port")
    parser.add_argument("--name", default="Test Team", help="Team name")
    parser.add_argument("--description", default="A team of agents", help="Team description")
    
    args = parser.parse_args()
    
    # Create test Agents
    agent1 = Agent(
        name="Assistant 1",
        role="Assistant",
        instructions="I am the first assistant, responsible for answering questions."
    )
    agent2 = Agent(
        name="Assistant 2", 
        role="Assistant",
        instructions="I am the second assistant, responsible for providing additional information."
    )
    # Create Team
    team = Team(
        name=args.name,
        description=args.description,
        members=[agent1, agent2],
        instructions="We are a team working together to help users."
    )
    # Create and start the server
    server = TeamServer(team, host=args.host, port=args.port)
    try:
        await server.start()
        print(f"Team server started: http://{args.host}:{args.port}")
        # Keep the server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
        await server.stop()
        print("Server stopped")

if __name__ == "__main__":
    asyncio.run(main())