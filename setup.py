#!/usr/bin/env python3
"""
AI-Agents 平台 - Agno A2A 扩展安装脚本

一个强大的AI代理框架，用于构建、管理和部署智能代理应用。
基于Agno框架和A2A协议，提供完整的代理间通信和团队协作功能。
"""

import os
import sys
from setuptools import setup, find_packages
from pathlib import Path

# 读取README文件作为长描述
def read_readme():
    readme_path = Path(__file__).parent / "README.md"
    if readme_path.exists():
        return readme_path.read_text(encoding="utf-8")
    return ""

# 读取requirements文件
def read_requirements(filename):
    requirements_path = Path(__file__).parent / filename
    if requirements_path.exists():
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

# 项目基本信息
PROJECT_NAME = "agno_a2a_ext"
PROJECT_VERSION = "1.0.0"
PROJECT_DESCRIPTION = "基于Agno框架和A2A协议的AI代理扩展，提供完整的代理间通信和团队协作功能"
PROJECT_LONG_DESCRIPTION = read_readme()
PROJECT_AUTHOR = "AI-Agents Team"
PROJECT_AUTHOR_EMAIL = "team@ai-agents.com"
PROJECT_URL = "https://github.com/ai-agents/agno-a2a-extension"
PROJECT_LICENSE = "MIT"
PROJECT_CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Software Development :: Libraries :: Application Frameworks",
    "Topic :: Communications :: Chat",
    "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
]

# 核心依赖
INSTALL_REQUIRES = [
    "a2a>=0.44",
    "agno>=1.7.6",
    "fastapi>=0.116.0",
    "openai>=1.93.3",
    "a2a-sdk>=0.2.16",
    "uvicorn>=0.35.0",
    "httpx>=0.24.0",
    "pydantic>=2.0.0",
    "alembic>=1.12.0",
    "sqlalchemy>=2.0.0",
    "python-multipart>=0.0.6",
    "python-dotenv==1.0.1"
]

# 可选依赖
EXTRAS_REQUIRE = {
    "dev": [
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.0.0",
        "black>=23.0.0",
        "isort>=5.12.0",
        "flake8>=6.0.0",
        "mypy>=1.0.0",
        "pre-commit>=3.0.0",

    ],
    "mysql": [
        "mysqlclient>=2.1.0",
        "pymysql>=1.0.0",
    ],
    "postgresql": [
        "psycopg2-binary>=2.9.0",
    ],
    "mongo": [
        "pymongo>=4.0.0",
    ],
}

# 包配置
PACKAGES = find_packages(include=["agno_a2a_ext", "agno_a2a_ext.*"])

# 数据文件
PACKAGE_DATA = {
    "agno_a2a_ext": ["*.md", "*.txt", "*.json", "*.yaml", "*.yml"],
}

# 入口点
ENTRY_POINTS = {
    # "console_scripts": [
    #     "agno-agent=agno_a2a_ext.servers.agent:main",
    #     "agno-team=agno_a2a_ext.servers.team:main",
    #     "agno-api=agno_a2a_ext.servers.api:main",
    # ],
}

def main():
    """主安装函数"""
    setup(
        name=PROJECT_NAME,
        version=PROJECT_VERSION,
        description=PROJECT_DESCRIPTION,
        long_description=PROJECT_LONG_DESCRIPTION,
        long_description_content_type="text/markdown",
        author=PROJECT_AUTHOR,
        author_email=PROJECT_AUTHOR_EMAIL,
        url=PROJECT_URL,
        license=PROJECT_LICENSE,
        classifiers=PROJECT_CLASSIFIERS,
        packages=PACKAGES,
        package_data=PACKAGE_DATA,
        include_package_data=True,
        install_requires=INSTALL_REQUIRES,
        extras_require=EXTRAS_REQUIRE,
        entry_points=ENTRY_POINTS,
        python_requires=">=3.8",
        zip_safe=False,
        keywords=[
            "ai", "agno", "a2a", "artificial-intelligence", "machine-learning",
            "llm", "chatbot", "automation", "workflow", "api", "fastapi",
            "agent", "team", "communication", "protocol"
        ],
        project_urls={
            "Bug Reports": f"{PROJECT_URL}/issues",
            "Source": PROJECT_URL,
            "Documentation": f"{PROJECT_URL}/docs",
            "Changelog": f"{PROJECT_URL}/blob/main/CHANGELOG.md",
        },
    )

if __name__ == "__main__":
    main() 