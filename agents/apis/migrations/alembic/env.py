"""
Alembic迁移环境配置

此文件在执行alembic命令时会被加载，用于配置数据库连接和迁移执行环境
"""
from logging.config import fileConfig
import os
import sys
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 确保能够导入应用模块
project_root = str(Path(__file__).parent.parent.parent.parent)
sys.path.insert(0, project_root)

# 导入集中配置系统
from ai_agent.config import app_config

# 导入ORM模型基类和相关模型
from agent_api.models import Base

# 提供目标元数据
target_metadata = Base.metadata

# 配置Alembic日志系统
fileConfig(context.config.config_file_name)

def get_url() -> str:
    """
    获取数据库URL，优先从环境变量获取
    
    Returns:
        数据库URL字符串
    """
    # 优先从环境变量获取
    url = os.environ.get("ALEMBIC_DB_URL")
    if url:
        return url
    
    # 从配置系统获取MySQL URL
    return app_config.get_db_url()

def run_migrations_offline() -> None:
    """
    在"离线"模式下运行迁移
    
    离线模式下，不会建立数据库连接，而是生成SQL脚本
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """
    在"在线"模式下运行迁移
    
    在线模式下，会直接连接数据库并执行迁移
    """
    # 获取数据库URL并更新配置
    config = context.config
    section = config.config_ini_section
    config.set_section_option(section, "sqlalchemy.url", get_url())
    
    # 创建引擎
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            # 自动生成迁移脚本时，使用数据库表名的大小写匹配
            compare_type=True,
            # 启用服务器默认值比较
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

# 根据执行模式选择相应的迁移函数
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online() 