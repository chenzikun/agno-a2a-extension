# 数据库迁移系统使用指南

本项目使用Alembic作为数据库迁移工具，用于管理数据库结构的版本控制和变更。

## 环境要求

- Python 3.6+
- SQLAlchemy
- Alembic

## 迁移命令

我们提供了Makefile命令来简化迁移操作，可以直接使用以下命令：

### 基本命令

```bash
# 查看帮助信息
make

# 执行所有待应用的迁移
make migrate

# 查看迁移状态
make migrate-status

# 创建新的迁移文件
make migrate-create name="添加用户表"

# 自动生成迁移文件（基于模型变更）
make migrate-autogen name="更新用户字段"

# 回滚最近一次迁移
make migrate-rollback

# 回滚到指定版本
make migrate-rollback ver="20230501120000"
```

### 数据库管理命令（仅用于开发环境）

```bash
# 初始化数据库，创建所有表
make db-init

# 重置数据库，删除并重建所有表
make db-reset
```

### 指定数据库类型

```bash
# 默认使用MySQL
make migrate

```

## 原理说明

本项目使用了两套迁移系统：

1. **Alembic（推荐）**：标准的SQLAlchemy迁移工具，提供强大的自动迁移生成和版本管理功能
2. **自定义迁移引擎**：项目早期开发的迁移系统，用于兼容旧版本

默认情况下使用Alembic，如需使用旧版迁移引擎，可设置环境变量：

```bash
USE_ALEMBIC=0 make migrate
```

## 迁移文件结构

```
agent_api/migrations/
├── alembic/                # Alembic迁移环境
│   ├── versions/           # 迁移版本文件目录
│   ├── env.py              # 环境配置
│   └── script.py.mako      # 脚本模板
├── versions/               # 旧版迁移系统的版本文件
├── alembic.ini             # Alembic配置文件
├── alembic_wrapper.py      # Alembic命令包装器
├── cli.py                  # 旧版迁移系统CLI
├── config.py               # 数据库配置
├── engine.py               # 旧版迁移引擎
├── engine_cli.py           # 数据库引擎工具
└── migration_tool.py       # 统一入口脚本
```

## 最佳实践

1. **命名规范**：迁移文件名应清晰描述其功能，如"add_user_table"、"update_product_fields"
2. **小步迭代**：每个迁移应该只做一件事，避免大型迁移文件
3. **测试迁移**：在应用到生产环境前，先在开发/测试环境验证迁移脚本
4. **回滚计划**：确保每个迁移都有正确的回滚逻辑
5. **版本控制**：迁移文件应当纳入版本控制系统

## 常见问题

### Q: 如何处理迁移冲突？

A: 当多个开发人员同时创建迁移文件时可能发生冲突。解决方法：
   - 使用版本控制系统解决文件冲突
   - 确保每个迁移只修改相关的表/字段
   - 在合并代码前先应用团队其他成员的迁移

### Q: 如何在生产环境安全地应用迁移？

A: 生产环境迁移注意事项：
   - 先在测试环境验证迁移脚本
   - 备份生产数据库
   - 在低峰期执行迁移
   - 准备回滚计划

### Q: 自动生成的迁移文件是否可靠？

A: Alembic的自动生成功能很强大，但不是100%可靠：
   - 自动生成后，务必人工检查迁移文件
   - 注意某些复杂的变更（如重命名表/列）可能被识别为删除+新建
   - 补充自动生成可能遗漏的数据迁移逻辑 