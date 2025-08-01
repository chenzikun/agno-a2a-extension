from uuid import uuid4
import traceback

from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.types import AgentCard
from a2a.types import Message, Role, Part, TextPart
from agno.agent.agent import Agent

from agno_a2a_ext.servers.base import BaseServer


class AgentExecutorWrapper(AgentExecutor):
    """Wrapper to convert Agent to A2A executor"""

    def __init__(self, agent: Agent):
        """
        Initialize executor
        
        Args:
            agent: Agent instance to wrap
        """
        self.agent = agent

    async def execute(self, context, event_queue):
        """
        Execute Agent and put results into event queue
        
        Args:
            context: Request context
            event_queue: Event queue
        """

        try:
            # Extract message from request
            message = ""
            session_id = None
            stream = True  # Enable streaming by default

            # Try to get information from context, handle different structures
            if hasattr(context, "request") and context.request:
                print(f"DEBUG AgentExecutorWrapper: Getting info from context.request, request type={type(context.request)}")
                if hasattr(context.request, "message") and context.request.message:
                    print(f"DEBUG AgentExecutorWrapper: Found message, type={type(context.request.message)}")
                    print(f"DEBUG AgentExecutorWrapper: message attributes={dir(context.request.message)}")
                    # Extract text from message parts
                    if hasattr(context.request.message, "parts"):
                        print(f"DEBUG AgentExecutorWrapper: Found parts, count={len(context.request.message.parts)}")
                        for i, part in enumerate(context.request.message.parts):
                            print(f"DEBUG AgentExecutorWrapper: Processing part[{i}], type={type(part)}, attributes={dir(part)}")
                            if hasattr(part, "root") and hasattr(part.root, "text"):
                                print(f"DEBUG AgentExecutorWrapper: Getting text from part.root.text: '{part.root.text}'")
                                message += part.root.text
                            elif hasattr(part, "text"):
                                print(f"DEBUG AgentExecutorWrapper: Getting text from part.text: '{part.text}'")
                                message += part.text
                            else:
                                print(f"DEBUG AgentExecutorWrapper: Cannot get text from part")
                if hasattr(context.request, "configuration") and context.request.configuration:
                    print(f"DEBUG AgentExecutorWrapper: Found configuration")
                    session_id = context.request.configuration.sessionId
                    print(f"DEBUG AgentExecutorWrapper: session_id = {session_id}")
            elif hasattr(context, "params") and context.params:
                print(f"DEBUG AgentExecutorWrapper: Getting info from context.params, params type={type(context.params)}")
                # Try to get information from params
                if hasattr(context.params, "message") and context.params.message:
                    print(f"DEBUG AgentExecutorWrapper: Found message, type={type(context.params.message)}")
                    # Extract text from message parts
                    if hasattr(context.params.message, "parts"):
                        print(f"DEBUG AgentExecutorWrapper: Found parts, count={len(context.params.message.parts)}")
                        for i, part in enumerate(context.params.message.parts):
                            print(f"DEBUG AgentExecutorWrapper: Processing part[{i}], type={type(part)}, attributes={dir(part)}")
                            if hasattr(part, "root") and hasattr(part.root, "text"):
                                print(f"DEBUG AgentExecutorWrapper: Getting text from part.root.text: '{part.root.text}'")
                                message += part.root.text
                            elif hasattr(part, "text"):
                                print(f"DEBUG AgentExecutorWrapper: Getting text from part.text: '{part.text}'")
                                message += part.text
                            else:
                                print(f"DEBUG AgentExecutorWrapper: Cannot get text from part")
                if hasattr(context.params, "configuration") and context.params.configuration:
                    print(f"DEBUG AgentExecutorWrapper: Found configuration")
                    session_id = context.params.configuration.sessionId
                    print(f"DEBUG AgentExecutorWrapper: session_id = {session_id}")

            # Try to extract message directly from context
            if not message and hasattr(context, "message"):
                print(f"DEBUG AgentExecutorWrapper: Trying to get info from context.message, type={type(context.message)}")
                if context.message:
                    print(f"DEBUG AgentExecutorWrapper: context.message={context.message}")
                    if isinstance(context.message, str):
                        message = context.message
                        print(f"DEBUG AgentExecutorWrapper: Directly getting string message: '{message}'")
                    elif hasattr(context.message, "parts") and context.message.parts:
                        print(
                            f"DEBUG AgentExecutorWrapper: Extracting from context.message.parts, count={len(context.message.parts)}")
                        for i, part in enumerate(context.message.parts):
                            if hasattr(part, "root") and hasattr(part.root, "text"):
                                message += part.root.text
                                print(
                                    f"DEBUG AgentExecutorWrapper: Extracting from message.parts[{i}].root.text: '{part.root.text}'")

            # If no message extracted, try alternative methods
            if not message:
                print(f"DEBUG AgentExecutorWrapper: Primary methods failed to extract message, trying fallback methods")
                if hasattr(context, "request") and hasattr(context.request, "text"):
                    print(f"DEBUG AgentExecutorWrapper: Getting text from context.request.text")
                    message = context.request.text
                elif hasattr(context, "params") and hasattr(context.params, "text"):
                    print(f"DEBUG AgentExecutorWrapper: Getting text from context.params.text")
                    message = context.params.text

                # Try to get user input
                elif hasattr(context, "get_user_input") and callable(context.get_user_input):
                    try:
                        print(f"DEBUG AgentExecutorWrapper: Trying to call context.get_user_input()")
                        user_input = context.get_user_input()
                        print(f"DEBUG AgentExecutorWrapper: Got user input: {user_input}")
                        if user_input:
                            message = user_input
                    except Exception as e:
                        print(f"DEBUG AgentExecutorWrapper: Failed to call get_user_input: {str(e)}")

                # Try to get from call_context
                elif hasattr(context, "call_context") and context.call_context:
                    print(f"DEBUG AgentExecutorWrapper: Checking call_context, type={type(context.call_context)}")
                    print(f"DEBUG AgentExecutorWrapper: call_context attributes={dir(context.call_context)}")
                    if hasattr(context.call_context, "request") and context.call_context.request:
                        if hasattr(context.call_context.request, "params") and hasattr(
                                context.call_context.request.params, "message"):
                            user_msg = context.call_context.request.params.message
                            print(
                                f"DEBUG AgentExecutorWrapper: Getting from call_context.request.params.message, type={type(user_msg)}")
                            if hasattr(user_msg, "parts") and user_msg.parts:
                                for part in user_msg.parts:
                                    if hasattr(part, "root") and hasattr(part.root, "text"):
                                        message += part.root.text
                                        print(f"DEBUG AgentExecutorWrapper: Extracted message from call_context: '{part.root.text}'")

                # Output complete context content for further analysis
                print(f"DEBUG AgentExecutorWrapper: Complete context content:")
                for key in dir(context):
                    if not key.startswith("_") and key not in ["call_context", "get_user_input"]:
                        try:
                            value = getattr(context, key)
                            print(f"DEBUG AgentExecutorWrapper: context.{key} = {value}")
                        except Exception as e:
                            print(f"DEBUG AgentExecutorWrapper: Cannot get context.{key}: {e}")

            # Execute Agent logic
            if message:
                print(f"DEBUG AgentExecutorWrapper: Successfully extracted message: '{message}'")
                try:
                    # Use Agent to execute message
                    try:
                        print(
                            f"DEBUG AgentExecutorWrapper: Preparing to call Agent.arun, Agent type: {type(self.agent).__name__}, message: {message[:50]}...")
                        print(f"DEBUG AgentExecutorWrapper: Agent object info: attributes={dir(self.agent)}")
                        print(
                            f"DEBUG AgentExecutorWrapper: Call parameters: message={message}, session_id={session_id}, stream=False")

                        run_response = await self.agent.arun(
                            message=message,
                            session_id=session_id,
                            stream=False
                        )
                        print(f"DEBUG AgentExecutorWrapper: Agent.arun call successful")

                        # Extract content from Agent response
                        print(
                            f"DEBUG AgentExecutorWrapper: run_response type={type(run_response)}, attributes={dir(run_response)}")
                        if run_response and hasattr(run_response, "content"):
                            response_text = run_response.content
                            print(f"DEBUG AgentExecutorWrapper: Extracted content: '{response_text}'")
                        else:
                            response_text = f"Received message: {message}"
                            print(f"DEBUG AgentExecutorWrapper: No content extracted, using default reply: '{response_text}'")
                    except Exception as e:
                        print(f"DEBUG AgentExecutorWrapper: Agent.arun call failed: {str(e)}")
                        traceback.print_exc()
                        # If Agent execution fails, create an error message
                        error_text = f"Execution error: {str(e)}"
                        print(f"DEBUG AgentExecutorWrapper: Creating error message: '{error_text}'")
                        response_message = Message(
                            messageId=str(uuid4()),
                            role=Role.agent,
                            parts=[Part(root=TextPart(text=error_text))]
                        )
                        print(f"DEBUG AgentExecutorWrapper: Enqueuing error message and returning")
                        await event_queue.enqueue_event(response_message)
                        return

                    # Create response message
                    print(f"DEBUG AgentExecutorWrapper: Creating normal response message: '{response_text}'")
                    response_message = Message(
                        messageId=str(uuid4()),
                        role=Role.agent,
                        parts=[Part(root=TextPart(text=response_text))]
                    )

                    # Enqueue response message
                    print(f"DEBUG AgentExecutorWrapper: Enqueuing response message and returning")
                    await event_queue.enqueue_event(response_message)
                    return
                except Exception as e:
                    # If Agent execution fails, create an error message
                    print(f"DEBUG AgentExecutorWrapper: Execution error (outer exception): {str(e)}")
                    error_text = f"Execution error: {str(e)}"
                    print(f"DEBUG AgentExecutorWrapper: Creating error message: '{error_text}'")
                    response_message = Message(
                        messageId=str(uuid4()),
                        role=Role.agent,
                        parts=[Part(root=TextPart(text=error_text))]
                    )
                    print(f"DEBUG AgentExecutorWrapper: Enqueuing error message and returning")
                    await event_queue.enqueue_event(response_message)
                    return

            # If no message or execution failed, create a default response
            default_text = "Received empty message"
            print(f"DEBUG AgentExecutorWrapper: No message extracted or execution failed, returning default message: '{default_text}'")
            response_message = Message(
                messageId=str(uuid4()),
                role=Role.agent,
                parts=[Part(root=TextPart(text=default_text))]
            )

            # Enqueue response message
            print(f"DEBUG AgentExecutorWrapper: Enqueuing default response message")
            await event_queue.enqueue_event(response_message)

        except Exception as e:
            # Create error message
            print(f"DEBUG AgentExecutorWrapper: Outermost exception: {str(e)}")

            traceback.print_exc()
            error_message = Message(
                messageId=str(uuid4()),
                role=Role.agent,
                parts=[Part(root=TextPart(text=f"Execution error: {str(e)}"))]
            )

            # Enqueue error message
            print(f"DEBUG AgentExecutorWrapper: Enqueuing outermost error message")
            await event_queue.enqueue_event(error_message)

    async def cancel(self, context, event_queue):
        """
        Cancel the currently executing task
        
        Args:
            context: Request context
            event_queue: Event queue
        """

        # Create cancel message
        cancel_message = Message(
            messageId=str(uuid4()),
            role=Role.agent,
            parts=[Part(root=TextPart(text="Task has been cancelled by user"))]
        )

        # Enqueue cancel message
        await event_queue.enqueue_event(cancel_message)


class AgentServer(BaseServer):
    """Pure A2A protocol Agent service"""

    def __init__(
            self,
            agent: Agent,
            host: str = "0.0.0.0",
            port: int = 8000
    ):
        """
        Initialize AgentServer
        
        Args:
            agent: Agent instance to serve
            host: Server host
            port: Server port
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
        Create AgentCard
        
        Returns:
            AgentCard: Card containing Agent information
        """
        # Get Agent information
        name = self.agent.name or "Unknown Agent"
        description = self.agent.description or self.agent.role or "An AI agent"

        # Get tool information (as skills)
        skills = []
        if hasattr(self.agent, "get_tools"):
            # Use a temporary session ID to get tool list
            tools = self.agent.get_tools(session_id="temp_session_id")
            if tools:
                for i, tool in enumerate(tools):
                    tool_name = getattr(tool, "name", None)
                    # Check if tool has a description attribute (Agno Function class)
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

        # If no tools, add a default skill
        if not skills:
            skills.append({
                "id": "conversation",
                "name": "conversation",
                "description": "Able to conduct conversation.",
                "tags": []
            })

        # Create AgentCard
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
        Create executor
        
        Returns:
            AgentExecutor: Executor wrapping the Agent
        """
        return AgentExecutorWrapper(self.agent)


async def main():
    """Command line entry point"""
    import argparse
    import asyncio
    from agno.agent.agent import Agent
    
    parser = argparse.ArgumentParser(description="Start A2A Agent server")
    parser.add_argument("--host", default="0.0.0.0", help="Server host address")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--name", default="Test Agent", help="Agent name")
    parser.add_argument("--role", default="Assistant", help="Agent role")
    
    args = parser.parse_args()
    
    # Create a simple test Agent
    agent = Agent(
        name=args.name,
        role=args.role,
        instructions="I am an AI assistant that can help users solve problems."
    )
    
    # Create and start the server
    server = AgentServer(agent, host=args.host, port=args.port)
    
    try:
        await server.start()
        print(f"Agent server started: http://{args.host}:{args.port}")
        
        # Keep the server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
        await server.stop()
        print("Server stopped")


if __name__ == "__main__":
    asyncio.run(main())
