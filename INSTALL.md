# Agents 安装指南

## 安装方式

### 1. 基础安装

安装核心功能：
```bash
pip install .
```

### 2. 开发环境安装

安装开发依赖：
```bash
pip install -e .[dev]
```

### 3. 开发环境安装

安装开发依赖：
```bash
pip install -e .[dev]
```

## 环境要求

- Python 3.8 或更高版本
- 推荐使用虚拟环境

## 创建虚拟环境

```bash
# 使用 conda
conda create -n agents python=3.10
conda activate agents

# 或使用 venv
python -m venv agents-env
source agents-env/bin/activate  # Linux/Mac
# agents-env\Scripts\activate  # Windows
```

## 验证安装

安装完成后，可以通过以下命令验证：

```bash
# 检查版本
python -c "import agents; print('Agents 安装成功')"

# 检查可用功能
python -c "from agents import Agent, Team; print('核心功能可用')"

# 运行示例
python examples/basic_agent.py
```

## 命令行工具

安装后可以使用以下命令行工具：

- `agents` - 启动代理服务
- `agents-api` - 启动API服务  
- `agents-team` - 启动团队服务

## 故障排除

### 常见问题

1. **依赖冲突**：
   ```bash
   pip install --upgrade pip
   pip install -e . --no-deps
   ```

2. **编译错误**：
   - 确保安装了开发工具
   - 在 macOS 上：`xcode-select --install`
   - 在 Ubuntu 上：`sudo apt-get install build-essential`

3. **权限问题**：
   ```bash
   pip install --user -e .
   ```

## 从源码安装

```bash
git clone https://github.com/ai-agents/ai-agents.git
cd ai-agents
pip install -e .
```

## 卸载

```bash
pip uninstall agents
``` 