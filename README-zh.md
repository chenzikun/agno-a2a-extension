# AI-Agents 平台 - Agno A2A 扩展

一个强大的AI代理框架，用于构建、管理和部署智能代理应用。基于Agno框架和A2A协议，提供完整的代理间通信和团队协作功能。

## 功能特性

- **A2A协议支持**: 基于A2A协议的代理间通信
- **多代理团队**: 支持创建和管理多代理团队
- **RESTful API**: 提供完整的REST API接口
- **流式响应**: 支持实时流式响应
- **多种数据库支持**: 支持MySQL、PostgreSQL、MongoDB等
- **Web界面**: 提供现代化的Web测试界面

## 快速开始

```bash
# set examples/.env; then quick start

bash quick_start.sh
```

### 编程使用

#### 创建Agent服务器

```python
from agno_a2a_ext import AgentServer
from agno.agent.agent import Agent

# 创建Agent
agent = Agent(
    name="My Agent",
    role="Assistant",
    instructions="我是一个AI助手，可以帮助用户解决问题。"
)

# 创建服务器
server = AgentServer(agent, host="0.0.0.0", port=8000)

# 启动服务器
await server.start()
```

#### 创建Team服务器

```python
from agno_a2a_ext import TeamServer
from agno.agent.agent import Agent
from agno.team.team import Team

# 创建团队成员
agent1 = Agent(name="Assistant 1", role="Assistant")
agent2 = Agent(name="Assistant 2", role="Developer")

# 创建Team
team = Team(
    name="Development Team",
    members=[agent1, agent2],
    instructions="我们是一个开发团队，协同工作来帮助用户。"
)

# 创建服务器
server = TeamServer(team, host="0.0.0.0", port=9000)

# 启动服务器
await server.start()
```

#### 创建API服务器

```python
from agno_a2a_ext import ServerAPI
from agno.agent.agent import Agent
from agno.team.team import Team

# 创建Agent和Team
agent = Agent(name="General Assistant", role="Assistant")
team = Team(name="Development Team", members=[agent])

# 创建API服务器
api_server = ServerAPI(
    agents=[agent],
    teams=[team],
    host="0.0.0.0",
    port=8080
)

# 启动服务器
await api_server.start()
```

#### 使用A2A客户端代理

```python
from agno_a2a_ext import A2AAgent

# 创建A2A客户端代理
a2a_agent = A2AAgent(
    base_url="http://localhost:8000",
    name="Remote Agent",
    role="Assistant"
)

# 使用代理
response = await a2a_agent.arun("你好，请介绍一下你自己")
print(response.content)
```

#### 使用工厂模式管理

```python
from agno_a2a_ext import AIFactory

# 创建工厂实例
factory = AIFactory()

# 注册Agent
agent = Agent(name="My Agent", role="Assistant")
factory.register(agent)

# 获取Agent
retrieved_agent = factory.get_agent_by_id(agent.id)

# 获取所有Agent
all_agents = factory.get_all_agents()
```

## API文档

启动API服务器后，可以访问以下端点：

- **API文档**: `http://localhost:8080/docs`
- **健康检查**: `http://localhost:8080/health`
- **状态检查**: `http://localhost:8080/status`

### 主要API端点

#### Agent相关
- `GET /playground/agents` - 获取所有Agent
- `POST /playground/agents/{agent_id}/runs` - 运行Agent
- `GET /playground/agents/{agent_id}/sessions` - 获取Agent会话

#### Team相关
- `GET /playground/teams` - 获取所有Team
- `POST /playground/teams/{team_id}/runs` - 运行Team
- `GET /playground/teams/{team_id}/sessions` - 获取Team会话

## 配置

### 环境变量

```bash
# 数据库配置
DATABASE_URL=mysql://user:password@localhost/dbname

# API密钥
OPENAI_API_KEY=your_openai_api_key

# 服务器配置
HOST=0.0.0.0
PORT=8080
```

### 数据库迁移

```bash
# 执行迁移
alembic upgrade head

# 创建新迁移
alembic revision --autogenerate -m "Add new table"
```

## 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black agno_a2a_ext/
isort agno_a2a_ext/
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 更新日志

### v1.0.0
- 初始版本发布
- 支持A2A协议
- 提供Agent和Team服务器
- 完整的REST API
- Web测试界面 