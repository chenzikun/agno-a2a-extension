# AI-Agents Platform - Agno A2A Extension

A powerful AI agent framework for building, managing, and deploying intelligent agent applications. Based on the Agno framework and A2A protocol, providing complete agent-to-agent communication and team collaboration capabilities.

## Features

- **A2A Protocol Support**: Agent-to-agent communication based on A2A protocol
- **Multi-Agent Teams**: Support for creating and managing multi-agent teams
- **RESTful API**: Complete REST API interface
- **Streaming Responses**: Real-time streaming response support
- **Multiple Database Support**: Support for MySQL, PostgreSQL, MongoDB, etc.
- **Web Interface**: Modern web testing interface

## Quick Start


```bash
# set examples/.env; then quick start

bash quick_start.sh
```

### Basic Usage

#### 1. Start Agent Server

### Programming Usage

#### Create Agent Server

```python
from agno_a2a_ext import AgentServer
from agno.agent.agent import Agent

# Create Agent
agent = Agent(
    name="My Agent",
    role="Assistant",
    instructions="I am an AI assistant that can help users solve problems."
)

# Create server
server = AgentServer(agent, host="0.0.0.0", port=8000)

# Start server
await server.start()
```

#### Create Team Server

```python
from agno_a2a_ext import TeamServer
from agno.agent.agent import Agent
from agno.team.team import Team

# Create team members
agent1 = Agent(name="Assistant 1", role="Assistant")
agent2 = Agent(name="Assistant 2", role="Developer")

# Create Team
team = Team(
    name="Development Team",
    members=[agent1, agent2],
    instructions="We are a development team working together to help users."
)

# Create server
server = TeamServer(team, host="0.0.0.0", port=9000)

# Start server
await server.start()
```

#### Create API Server

```python
from agno_a2a_ext import ServerAPI
from agno.agent.agent import Agent
from agno.team.team import Team

# Create Agent and Team
agent = Agent(name="General Assistant", role="Assistant")
team = Team(name="Development Team", members=[agent])

# Create API server
api_server = ServerAPI(
    agents=[agent],
    teams=[team],
    host="0.0.0.0",
    port=8080
)

# Start server
await api_server.start()
```

#### Use A2A Client Agent

```python
from agno_a2a_ext import A2AAgent

# Create A2A client agent
a2a_agent = A2AAgent(
    base_url="http://localhost:8000",
    name="Remote Agent",
    role="Assistant"
)

# Use agent
response = await a2a_agent.arun("Hello, please introduce yourself")
print(response.content)
```

#### Use Factory Pattern Management

```python
from agno_a2a_ext import AIFactory

# Create factory instance
factory = AIFactory()

# Register Agent
agent = Agent(name="My Agent", role="Assistant")
factory.register(agent)

# Get Agent
retrieved_agent = factory.get_agent_by_id(agent.id)

# Get all Agents
all_agents = factory.get_all_agents()
```

## API Documentation

After starting the API server, you can access the following endpoints:

- **API Documentation**: `http://localhost:8080/docs`
- **Health Check**: `http://localhost:8080/health`
- **Status Check**: `http://localhost:8080/status`

### Main API Endpoints

#### Agent Related
- `GET /playground/agents` - Get all Agents
- `POST /playground/agents/{agent_id}/runs` - Run Agent
- `GET /playground/agents/{agent_id}/sessions` - Get Agent sessions

#### Team Related
- `GET /playground/teams` - Get all Teams
- `POST /playground/teams/{team_id}/runs` - Run Team
- `GET /playground/teams/{team_id}/sessions` - Get Team sessions

## Configuration

### Environment Variables

```bash
# Database configuration
DATABASE_URL=mysql://user:password@localhost/dbname

# API keys
OPENAI_API_KEY=your_openai_api_key

# Server configuration
HOST=0.0.0.0
PORT=8080
```

### Database Migration

```bash
# Execute migration
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Add new table"
```

## Development

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black agno_a2a_ext/
isort agno_a2a_ext/
```

## License

MIT License

## Contributing

Welcome to submit Issues and Pull Requests!

## Changelog

### v1.0.0
- Initial version release
- A2A protocol support
- Agent and Team servers
- Complete REST API
- Web testing interface 