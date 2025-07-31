#!/usr/bin/env python
"""
数据库迁移工具入口脚本

这个脚本调用Alembic迁移工具执行数据库迁移操作
"""
import os
import sys
import warnings
from pathlib import Path

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def main():
    """主入口函数"""
    # 使用Alembic
    from agent_api.migrations.alembic_wrapper import main as alembic_main
    alembic_main()

if __name__ == "__main__":
    main() 