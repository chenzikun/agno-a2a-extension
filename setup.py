#!/usr/bin/env python3
"""
AI-Agents 平台安装脚本

一个强大的AI代理框架，用于构建、管理和部署智能代理应用。
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
PROJECT_NAME = "agents"
PROJECT_VERSION = "1.0.0"
PROJECT_DESCRIPTION = "一个强大的AI代理框架，用于构建、管理和部署智能代理应用"
PROJECT_LONG_DESCRIPTION = read_readme()
PROJECT_AUTHOR = "AI-Agents Team"
PROJECT_AUTHOR_EMAIL = "team@ai-agents.com"
PROJECT_URL = "https://github.com/ai-agents/ai-agents"
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
]

# 核心依赖
INSTALL_REQUIRES = [
    "a2a==0.44",
    "agno==1.7.6",
    "fastapi==0.116.0",
    "openai==1.93.3",
    "a2a-sdk==0.2.16",
    "uvicorn==0.35.0",
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
}

# 包配置
PACKAGES = ["agents"]

# 数据文件
PACKAGE_DATA = {
    "": ["*.md", "*.txt", "*.json", "*.yaml", "*.yml"],
}

# 入口点
ENTRY_POINTS = {
    "console_scripts": [
        "agents=servers.agent:main",
        "agents-api=servers.api:main",
        "agents-team=servers.team:main",
    ],
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
            "ai", "agents", "artificial-intelligence", "machine-learning",
            "llm", "chatbot", "automation", "workflow", "api", "fastapi"
        ],
        project_urls={
            "Bug Reports": f"{PROJECT_URL}/issues",
            "Source": PROJECT_URL,
            "Documentation": f"{PROJECT_URL}/docs",
        },
    )

if __name__ == "__main__":
    main() 