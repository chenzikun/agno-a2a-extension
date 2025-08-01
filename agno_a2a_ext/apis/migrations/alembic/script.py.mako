"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Tuple, Optional

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# 修订版本标识符，由Alembic使用
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}

# 迁移描述信息
description = "${message}"


def upgrade() -> None:
    """升级数据库结构"""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """回滚数据库结构"""
    ${downgrades if downgrades else "pass"} 