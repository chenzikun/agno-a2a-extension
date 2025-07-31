"""
Alembic迁移引擎包装器

这个包装器将现有的CLI命令映射到Alembic命令，以便平滑过渡
"""
import os
import sys
import argparse
import subprocess
from typing import List, Tuple
from pathlib import Path

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 使用集中配置系统
from ai_agent.config import app_config, get_db_url

def run_alembic_command(command: List[str]) -> int:
    """
    运行Alembic命令

    Args:
        command: Alembic命令及参数
    
    Returns:
        命令执行的返回码
    """
    # 获取数据库URL并设置环境变量
    os.environ["ALEMBIC_DB_URL"] = get_db_url()
    
    # 获取Alembic配置文件路径
    alembic_ini = app_config.migration.alembic_ini
    
    # 构建完整命令
    alembic_command = ["alembic", "-c", alembic_ini] + command
    
    # 执行命令
    return subprocess.call(alembic_command)

def create_migration_file(name: str) -> Tuple[int, str]:
    """
    创建迁移文件
    
    Args:
        name: 迁移名称
    
    Returns:
        执行状态码和消息
    """
    # 运行alembic revision命令
    cmd = ["revision", "-m", name]
    exit_code = run_alembic_command(cmd)
    
    if exit_code == 0:
        return exit_code, f"创建迁移文件成功: {name}"
    else:
        return exit_code, f"创建迁移文件失败: {name}"

def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="数据库迁移工具 (Alembic包装器)")
    
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # migrate命令 (对应 alembic upgrade head)
    migrate_parser = subparsers.add_parser("migrate", help="执行迁移")
    
    # rollback命令 (对应 alembic downgrade)
    rollback_parser = subparsers.add_parser("rollback", help="回滚迁移")
    rollback_parser.add_argument("--version", help="回滚到指定版本")
    
    # status命令 (对应 alembic current 和 alembic history)
    status_parser = subparsers.add_parser("status", help="查看迁移状态")
    
    # create命令 (对应 alembic revision)
    create_parser = subparsers.add_parser("create", help="创建迁移文件")
    create_parser.add_argument("name", help="迁移名称")
    
    # init命令 (已经由 alembic init 完成)
    init_parser = subparsers.add_parser("init", help="初始化迁移表")
    
    # autogenerate命令 (新增，对应 alembic revision --autogenerate)
    autogen_parser = subparsers.add_parser("autogenerate", help="自动生成迁移文件")
    autogen_parser.add_argument("name", help="迁移名称")
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    if args.command == "migrate":
        print("执行迁移...")
        exit_code = run_alembic_command(["upgrade", "head"])
        if exit_code == 0:
            print("迁移完成")
        else:
            print("迁移失败")
            sys.exit(exit_code)
    
    elif args.command == "rollback":
        target = args.version if args.version else "-1"
        print(f"回滚迁移到 {target}...")
        exit_code = run_alembic_command(["downgrade", target])
        if exit_code == 0:
            print("回滚完成")
        else:
            print("回滚失败")
            sys.exit(exit_code)
    
    elif args.command == "status":
        print("当前迁移版本:")
        run_alembic_command(["current"])
        
        print("\n可用迁移历史:")
        run_alembic_command(["history"])
    
    elif args.command == "create":
        exit_code, message = create_migration_file(args.name)
        print(message)
        if exit_code != 0:
            sys.exit(exit_code)
    
    elif args.command == "autogenerate":
        print(f"自动生成迁移文件: {args.name}")
        exit_code = run_alembic_command(["revision", "--autogenerate", "-m", args.name])
        if exit_code == 0:
            print("迁移文件生成成功")
        else:
            print("迁移文件生成失败")
            sys.exit(exit_code)
    
    elif args.command == "init":
        print("Alembic环境已初始化，无需再次初始化")
        print("如需重新初始化，请手动运行: alembic init agent_api/migrations/alembic")

if __name__ == "__main__":
    main() 