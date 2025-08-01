import time
import traceback
from typing import List, Literal, Optional

from agno.storage.base import Storage
from agno.storage.session import Session
from agno.storage.session.agent import AgentSession
from agno.storage.session.team import TeamSession
from agno.storage.session.workflow import WorkflowSession
from agno.utils.log import log_debug, log_info, log_warning, logger

try:
    from sqlalchemy.engine import Engine, create_engine
    from sqlalchemy.inspection import inspect
    from sqlalchemy.orm import scoped_session, sessionmaker
    from sqlalchemy.schema import Column, MetaData, Table
    from sqlalchemy.sql.expression import select, text
    from sqlalchemy.types import BigInteger, JSON, String
except ImportError:
    raise ImportError("`sqlalchemy` not installed. Please install it using `pip install sqlalchemy mysqlclient`")


class MySqlStorage(Storage):
    def __init__(
            self,
            table_name: str,
            schema: Optional[str] = None,
            db_url: Optional[str] = None,
            db_engine: Optional[Engine] = None,
            schema_version: int = 1,
            auto_upgrade_schema: bool = False,
            mode: Optional[Literal["agent", "team", "workflow"]] = "agent",
    ):
        """
        This class provides agent storage using a MySQL table.

        The following order is used to determine the database connection:
            1. Use the db_engine if provided
            2. Use the db_url
            3. Raise an error if neither is provided

        Args:
            table_name (str): Name of the table to store Agent sessions.
            schema (Optional[str]): The database to use for the table. Defaults to None.
            db_url (Optional[str]): The database URL to connect to.
            db_engine (Optional[Engine]): The SQLAlchemy database engine to use.
            schema_version (int): Version of the schema. Defaults to 1.
            auto_upgrade_schema (bool): Whether to automatically upgrade the schema.
            mode (Optional[Literal["agent", "team", "workflow"]]): The mode of the storage.
        Raises:
            ValueError: If neither db_url nor db_engine is provided.
        """
        super().__init__(mode)
        _engine: Optional[Engine] = db_engine
        if _engine is None and db_url is not None:
            _engine = create_engine(db_url)

        if _engine is None:
            raise ValueError("Must provide either db_url or db_engine")

        # Database attributes
        self.table_name: str = table_name
        self.schema: Optional[str] = schema
        self.db_url: Optional[str] = db_url
        self.db_engine: Engine = _engine
        self.metadata: MetaData = MetaData(schema=self.schema)
        self.inspector = inspect(self.db_engine)

        # Table schema version
        self.schema_version: int = schema_version
        # Automatically upgrade schema if True
        self.auto_upgrade_schema: bool = auto_upgrade_schema
        self._schema_up_to_date: bool = False

        # Database session
        self.Session: scoped_session = scoped_session(sessionmaker(bind=self.db_engine))
        # Database table for storage
        self.table: Table = self.get_table()
        log_debug(f"Created MySqlStorage: '{self.schema}.{self.table_name}'")

    @property
    def mode(self) -> Literal["agent", "team", "workflow"]:
        """Get the mode of the storage."""
        return super().mode

    @mode.setter
    def mode(self, value: Optional[Literal["agent", "team", "workflow"]]) -> None:
        """Set the mode and refresh the table if mode changes."""
        super(MySqlStorage, type(self)).mode.fset(self, value)  # type: ignore
        if value is not None:
            self.table = self.get_table()

    def get_table_v1(self) -> Table:
        """
        Define the table schema for version 1.

        Returns:
            Table: SQLAlchemy Table object representing the schema.
        """
        # Common columns for both agent and workflow modes
        common_columns = [
            Column("session_id", String(255), primary_key=True),
            Column("user_id", String(255), index=True),
            Column("memory", JSON, nullable=False, comment="Session memory"),
            Column("session_data", JSON, nullable=False, comment="Session data"),
            Column("extra_data", JSON, nullable=False, comment="Extra data"),
            Column("created_at", BigInteger, default=lambda: int(time.time())),
            Column("updated_at", BigInteger, default=lambda: int(time.time()), onupdate=lambda: int(time.time())),
        ]

        # Mode-specific columns
        specific_columns = []
        if self.mode == "agent":
            specific_columns = [
                Column("agent_id", String(255), index=True),
                Column("team_session_id", String(255), index=True, nullable=True),
                Column("agent_data", JSON, nullable=False, comment="Agent data"),
            ]
        elif self.mode == "team":
            specific_columns = [
                Column("team_id", String(255), index=True),
                Column("team_session_id", String(255), index=True, nullable=True),
                Column("team_data", JSON, nullable=False, comment="Team data"),
            ]
        elif self.mode == "workflow":
            specific_columns = [
                Column("workflow_id", String(255), index=True),
                Column("workflow_data", JSON, nullable=False, comment="Workflow data"),
            ]

        # Create table with all columns
        table = Table(
            self.table_name,
            self.metadata,
            *common_columns,
            *specific_columns,
            extend_existing=True,
            schema=self.schema,  # type: ignore
        )

        return table

    def get_table(self) -> Table:
        """
        Get the table schema based on the schema version.

        Returns:
            Table: SQLAlchemy Table object for the current schema version.

        Raises:
            ValueError: If an unsupported schema version is specified.
        """
        if self.schema_version == 1:
            return self.get_table_v1()
        else:
            raise ValueError(f"Unsupported schema version: {self.schema_version}")

    def table_exists(self) -> bool:
        """
        Check if the table exists in the database.

        Returns:
            bool: True if the table exists, False otherwise.
        """
        try:
            # Use a direct SQL query to check if the table exists
            with self.Session() as sess:
                if self.schema is not None:
                    exists_query = text(
                        "SELECT 1 FROM information_schema.tables WHERE table_schema = :schema AND table_name = :table"
                    )
                    exists = (
                            sess.execute(exists_query, {"schema": self.schema, "table": self.table_name}).scalar()
                            is not None
                    )
                else:
                    exists_query = text("SELECT 1 FROM information_schema.tables WHERE table_name = :table")
                    exists = sess.execute(exists_query, {"table": self.table_name}).scalar() is not None

            log_debug(f"Table '{self.table.fullname}' does{' not ' if not exists else ' '}exist")
            return exists

        except Exception as e:
            logger.error(f"Error checking if table exists: {e}")
            return False

    def create(self) -> None:
        """
        Create the table if it does not exist.
        """
        self.table = self.get_table()
        if not self.table_exists():
            try:
                with self.Session() as sess, sess.begin():
                    if self.schema is not None:
                        log_debug(f"Creating database: {self.schema}")
                        sess.execute(text(f"CREATE DATABASE IF NOT EXISTS {self.schema};"))

                log_debug(f"Creating table: {self.table_name}")

                # 使用自定义SQL创建表，因为SQLAlchemy生成的SQL可能有兼容性问题
                # 准备列定义
                with self.Session() as sess, sess.begin():
                    # 首先检查表是否已存在
                    exists_query = text(
                        "SELECT 1 FROM information_schema.tables WHERE table_schema = :schema AND table_name = :table"
                    )
                    exists = sess.execute(
                        exists_query,
                        {"schema": self.schema or sess.execute(text("SELECT DATABASE()")).scalar(),
                         "table": self.table_name}
                    ).scalar()

                    if not exists:
                        # u4f7fu7528u5143u7ec4u548cu5b57u7b26u4e32u683cu5f0fu5316u7b80u5316SQL
                        # u57fau7840u8868u7ed3u6784
                        base_columns = (
                            "    `session_id` VARCHAR(255) NOT NULL,\n"
                            "    `user_id` VARCHAR(255),\n"
                            "    `memory` JSON NOT NULL COMMENT 'Session memory',\n"
                            "    `session_data` JSON NOT NULL COMMENT 'Session data',\n"
                            "    `extra_data` JSON NOT NULL COMMENT 'Extra data',\n"
                            "    `created_at` BIGINT NOT NULL DEFAULT (UNIX_TIMESTAMP()),\n"
                            "    `updated_at` BIGINT NULL,\n"
                        )

                        # u6a21u5f0fu7279u5b9au5217
                        mode_columns = ""
                        if self.mode == "agent":
                            mode_columns = (
                                "    `agent_id` VARCHAR(255),\n"
                                "    `team_session_id` VARCHAR(255) NULL,\n"
                                "    `agent_data` JSON NOT NULL COMMENT 'Agent data',\n"
                            )
                        elif self.mode == "team":
                            mode_columns = (
                                "    `team_id` VARCHAR(255),\n"
                                "    `team_session_id` VARCHAR(255) NULL,\n"
                                "    `team_data` JSON NOT NULL COMMENT 'Team data',\n"
                            )
                        elif self.mode == "workflow":
                            mode_columns = (
                                "    `workflow_id` VARCHAR(255),\n"
                                "    `workflow_data` JSON NOT NULL COMMENT 'Workflow data',\n"
                            )

                        # u4e3bu952eu548cu8868u9009u9879
                        table_end = (
                            "    PRIMARY KEY (`session_id`)\n"
                            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
                        )

                        # u7ec4u5408u5b8cu6574SQL
                        create_table_sql = f"CREATE TABLE {('`' + self.schema + '`.' if self.schema else '')}`{self.table_name}` (\n" + base_columns + mode_columns + table_end

                        # u6267u884cu521bu5efau8868SQL
                        sess.execute(text(create_table_sql))
                        log_debug(f"Table {self.table_name} created successfully")

                # 创建索引
                existing_columns = [col.name for col in self.table.columns]
                for idx in self.table.indexes:
                    try:
                        if idx.name and 'PRIMARY' not in idx.name:
                            # u68c0u67e5u7d22u5f15u4e2du7684u6240u6709u5217u662fu5426u5b58u5728
                            idx_columns = [col.name for col in idx.columns]
                            all_columns_exist = all(col in existing_columns for col in idx_columns)

                            if not all_columns_exist:
                                log_debug(f"Skipping index {idx.name} because not all columns exist")
                                continue

                            idx_name = idx.name
                            log_debug(f"Creating index: {idx_name}")

                            # u68c0u67e5u7d22u5f15u662fu5426u5df2u5b58u5728
                            with self.Session() as sess:
                                if self.schema:
                                    exists_query = text(
                                        "SELECT 1 FROM information_schema.statistics WHERE table_schema = :schema AND index_name = :index_name AND table_name = :table_name"
                                    )
                                    exists = (
                                            sess.execute(exists_query, {
                                                "schema": self.schema,
                                                "index_name": idx_name,
                                                "table_name": self.table_name
                                            }).scalar()
                                            is not None
                                    )
                                else:
                                    exists_query = text(
                                        "SELECT 1 FROM information_schema.statistics WHERE index_name = :index_name AND table_name = :table_name"
                                    )
                                    exists = sess.execute(exists_query, {
                                        "index_name": idx_name,
                                        "table_name": self.table_name
                                    }).scalar() is not None

                            if not exists:
                                # u5bf9u4e8eu975eu4e3bu952eu7d22u5f15uff0cu5355u72ecu521bu5efa
                                with self.Session() as sess, sess.begin():
                                    # u83b7u53d6u5217u540d
                                    column_names = [col.name for col in idx.columns]
                                    column_str = ", ".join([f"`{col}`" for col in column_names])
                                    create_index_sql = f"CREATE INDEX `{idx_name}` ON {'`' + self.schema + '`.' if self.schema else ''}`{self.table_name}` ({column_str})"
                                    sess.execute(text(create_index_sql))
                                    log_debug(f"Index {idx_name} created successfully")
                            else:
                                log_debug(f"Index {idx_name} already exists, skipping creation")

                    except Exception as e:
                        # u8bb0u5f55u9519u8befu4f46u7ee7u7eedu5904u7406u5176u4ed6u7d22u5f15
                        logger.warning(f"Error creating index {idx.name}: {e}")

            except Exception as e:
                logger.error(f"Could not create table: '{self.table.fullname}': {e}")
                raise

    def read(self, session_id: str, user_id: Optional[str] = None) -> Optional[Session]:
        """
        Read an Session from the database.

        Args:
            session_id (str): ID of the session to read.
            user_id (Optional[str]): User ID to filter by. Defaults to None.

        Returns:
            Optional[Session]: Session object if found, None otherwise.
        """
        try:
            with self.Session() as sess:
                # 首先获取当前表的实际列
                inspector = inspect(self.db_engine)
                existing_columns = [col['name'] for col in inspector.get_columns(self.table_name, schema=self.schema)]

                # 根据实际存在的列构建查询
                query_columns = []
                for col in self.table.columns:
                    if col.name in existing_columns:
                        query_columns.append(col)
                    else:
                        log_debug(f"Column {col.name} not found in table, skipping in SELECT query")

                # 使用存在的列构建查询
                stmt = select(*query_columns).where(self.table.c.session_id == session_id)
                if user_id:
                    stmt = stmt.where(self.table.c.user_id == user_id)

                result = sess.execute(stmt).fetchone()

                if result is not None:
                    # 创建一个字典，包含所有返回的列
                    result_dict = dict(result._mapping)
                    log_debug(f"storage result_dict: " + str(result_dict))
                    # 如果是agent模式但缺少agent特有的列，添加默认值
                    if self.mode == "agent":
                        if "agent_id" not in result_dict:
                            result_dict["agent_id"] = None
                        if "agent_data" not in result_dict:
                            result_dict["agent_data"] = {}
                        if "team_session_id" not in result_dict:
                            result_dict["team_session_id"] = None
                        return AgentSession.from_dict(result_dict)
                    elif self.mode == "team":
                        if "team_id" not in result_dict:
                            result_dict["team_id"] = None
                        if "team_data" not in result_dict:
                            result_dict["team_data"] = {}
                        if "team_session_id" not in result_dict:
                            result_dict["team_session_id"] = None
                        return TeamSession.from_dict(result_dict)
                    elif self.mode == "workflow":
                        if "workflow_id" not in result_dict:
                            result_dict["workflow_id"] = None
                        if "workflow_data" not in result_dict:
                            result_dict["workflow_data"] = {}
                        return WorkflowSession.from_dict(result_dict)
                return None
        except Exception as e:
            if "doesn't exist" in str(e) or "Unknown table" in str(e) or "Unknown column" in str(e):
                log_debug(f"Table access error: {e}")
                log_debug("Creating table for future transactions")
                self.create()
            else:
                log_debug(f"Exception reading from table: {e}")
                log_debug(f"Table does not exist: {self.table.name}")
                log_debug(traceback.format_exc())
        return None

    def get_all_session_ids(self, user_id: Optional[str] = None, entity_id: Optional[str] = None) -> List[str]:
        """
        Get all session IDs, optionally filtered by user_id and/or entity_id.

        Args:
            user_id (Optional[str]): The ID of the user to filter by.
            entity_id (Optional[str]): The ID of the agent / workflow to filter by.

        Returns:
            List[str]: List of session IDs matching the criteria.
        """
        try:
            with self.Session() as sess, sess.begin():
                # 首先检查表中实际存在的列
                inspector = inspect(self.db_engine)
                existing_columns = [col['name'] for col in inspector.get_columns(self.table_name, schema=self.schema)]

                # 只选择session_id列
                stmt = select(self.table.c.session_id)

                # 添加user_id过滤条件（如果存在）
                if user_id is not None and "user_id" in existing_columns:
                    stmt = stmt.where(self.table.c.user_id == user_id)

                # 根据当前模式添加适当的entity_id过滤条件
                if entity_id is not None:
                    id_column = None
                    if self.mode == "agent" and "agent_id" in existing_columns:
                        id_column = self.table.c.agent_id
                    elif self.mode == "team" and "team_id" in existing_columns:
                        id_column = self.table.c.team_id
                    elif self.mode == "workflow" and "workflow_id" in existing_columns:
                        id_column = self.table.c.workflow_id

                    if id_column is not None:
                        stmt = stmt.where(id_column == entity_id)
                    else:
                        log_debug(f"ID column for mode {self.mode} not found in table, skipping entity_id filter")

                # 添加排序（如果created_at列存在）
                if "created_at" in existing_columns:
                    stmt = stmt.order_by(self.table.c.created_at.desc())

                # 执行查询
                rows = sess.execute(stmt).fetchall()
                return [row[0] for row in rows] if rows is not None else []
        except Exception as e:
            log_debug(f"Exception reading from table: {e}")
            if "doesn't exist" in str(e) or "Unknown table" in str(e):
                log_debug(f"Table does not exist: {self.table.name}")
                log_debug("Creating table for future transactions")
                self.create()
            else:
                log_debug(f"Error getting session IDs: {e}")
        return []

    def get_all_sessions(self, user_id: Optional[str] = None, entity_id: Optional[str] = None) -> List[Session]:
        """
        Get all sessions, optionally filtered by user_id and/or entity_id.

        Args:
            user_id (Optional[str]): The ID of the user to filter by.
            entity_id (Optional[str]): The ID of the agent / workflow to filter by.

        Returns:
            List[Session]: List of Session objects matching the criteria.
        """
        try:
            with self.Session() as sess, sess.begin():
                # 首先获取当前表的实际列
                inspector = inspect(self.db_engine)
                existing_columns = [col['name'] for col in inspector.get_columns(self.table_name, schema=self.schema)]

                # 根据实际存在的列构建查询
                query_columns = []
                for col in self.table.columns:
                    if col.name in existing_columns:
                        query_columns.append(col)

                # 使用存在的列构建查询
                stmt = select(*query_columns)

                if user_id is not None:
                    stmt = stmt.where(self.table.c.user_id == user_id)

                if entity_id is not None:
                    entity_id_col = None
                    if self.mode == "agent" and "agent_id" in existing_columns:
                        entity_id_col = self.table.c.agent_id
                    elif self.mode == "team" and "team_id" in existing_columns:
                        entity_id_col = self.table.c.team_id
                    elif self.mode == "workflow" and "workflow_id" in existing_columns:
                        entity_id_col = self.table.c.workflow_id

                    if entity_id_col is not None:
                        stmt = stmt.where(entity_id_col == entity_id)

                # order by created_at desc
                stmt = stmt.order_by(self.table.c.created_at.desc())

                # 执行查询
                rows = sess.execute(stmt).fetchall()
                sessions = []

                # 处理结果
                if rows is not None:
                    for row in rows:
                        # 创建一个字典，包含所有返回的列
                        result_dict = dict(row._mapping)

                        # 添加缺少的字段
                        if self.mode == "agent":
                            if "agent_id" not in result_dict:
                                result_dict["agent_id"] = None
                            if "agent_data" not in result_dict:
                                result_dict["agent_data"] = {}
                            if "team_session_id" not in result_dict:
                                result_dict["team_session_id"] = None
                            sessions.append(AgentSession.from_dict(result_dict))
                        elif self.mode == "team":
                            if "team_id" not in result_dict:
                                result_dict["team_id"] = None
                            if "team_data" not in result_dict:
                                result_dict["team_data"] = {}
                            if "team_session_id" not in result_dict:
                                result_dict["team_session_id"] = None
                            sessions.append(TeamSession.from_dict(result_dict))
                        else:
                            if "workflow_id" not in result_dict:
                                result_dict["workflow_id"] = None
                            if "workflow_data" not in result_dict:
                                result_dict["workflow_data"] = {}
                            sessions.append(WorkflowSession.from_dict(result_dict))
                return sessions
        except Exception as e:
            log_debug(f"Exception reading from table: {e}")
            log_debug(f"Table does not exist: {self.table.name}")
            log_debug("Creating table for future transactions")
            self.create()
        return []

    def upgrade_schema(self) -> None:
        """
        Upgrade the schema to the latest version.
        Currently handles adding the team_session_id column for agent mode.
        """
        if not self.auto_upgrade_schema:
            log_debug("Auto schema upgrade disabled. Skipping upgrade.")
            return

        try:
            if self.mode == "agent" and self.table_exists():
                with self.Session() as sess:
                    # Check if team_session_id column exists
                    column_exists_query = text(
                        """
                        SELECT 1 FROM information_schema.columns
                        WHERE table_schema = :schema AND table_name = :table
                        AND column_name = 'team_session_id'
                        """
                    )
                    column_exists = (
                            sess.execute(column_exists_query,
                                         {"schema": self.schema, "table": self.table_name}).scalar()
                            is not None
                    )

                    if not column_exists:
                        log_info(f"Adding 'team_session_id' column to {self.schema}.{self.table_name}")
                        alter_table_query = text(
                            f"ALTER TABLE {self.schema}.{self.table_name} ADD COLUMN team_session_id VARCHAR(255)"
                        )
                        sess.execute(alter_table_query)
                        sess.commit()
                        self._schema_up_to_date = True
                        log_info("Schema upgrade completed successfully")
        except Exception as e:
            logger.error(f"Error during schema upgrade: {e}")
            raise

    def upsert(self, session: Session, create_and_retry: bool = True) -> Optional[Session]:
        """
        Insert or update an Session in the database.

        Args:
            session (Session): The session data to upsert.
            create_and_retry (bool): Retry upsert if table does not exist.

        Returns:
            Optional[Session]: The upserted Session, or None if operation failed.
        """
        # Perform schema upgrade if auto_upgrade_schema is enabled
        if self.auto_upgrade_schema and not self._schema_up_to_date:
            self.upgrade_schema()

        try:
            with self.Session() as sess, sess.begin():
                # 检查表中存在的列
                inspector = inspect(self.db_engine)
                existing_columns = [col['name'] for col in inspector.get_columns(self.table_name, schema=self.schema)]

                # 检查记录是否存在
                exists_stmt = select(self.table.c.session_id).where(self.table.c.session_id == session.session_id)
                exists = sess.execute(exists_stmt).first() is not None

                current_time = int(time.time())

                # 确保JSON字段有值而不是None
                memory_data = session.memory or {}
                session_data = session.session_data or {}
                extra_data = session.extra_data or {}

                # 准备基本值字典，只包含存在的列
                values = {}

                # 添加通用字段（如果存在于表中）
                if "session_id" in existing_columns:
                    values["session_id"] = session.session_id
                if "user_id" in existing_columns:
                    values["user_id"] = session.user_id
                if "memory" in existing_columns:
                    values["memory"] = memory_data
                if "session_data" in existing_columns:
                    values["session_data"] = session_data
                if "extra_data" in existing_columns:
                    values["extra_data"] = extra_data
                if "updated_at" in existing_columns:
                    values["updated_at"] = current_time

                # 根据模式添加特定字段
                if self.mode == "agent":
                    if "agent_id" in existing_columns:
                        values["agent_id"] = session.agent_id  # type: ignore
                    if "team_session_id" in existing_columns:
                        values["team_session_id"] = session.team_session_id  # type: ignore
                    if "agent_data" in existing_columns:
                        values["agent_data"] = session.agent_data or {}  # type: ignore
                elif self.mode == "team":
                    if "team_id" in existing_columns:
                        values["team_id"] = session.team_id  # type: ignore
                    if "team_session_id" in existing_columns:
                        values["team_session_id"] = session.team_session_id  # type: ignore
                    if "team_data" in existing_columns:
                        values["team_data"] = session.team_data or {}  # type: ignore
                elif self.mode == "workflow":
                    if "workflow_id" in existing_columns:
                        values["workflow_id"] = session.workflow_id  # type: ignore
                    if "workflow_data" in existing_columns:
                        values["workflow_data"] = session.workflow_data or {}  # type: ignore

                if exists:
                    # 更新已有记录
                    update_stmt = self.table.update().where(self.table.c.session_id == session.session_id).values(
                        **values)
                    sess.execute(update_stmt)
                else:
                    # 插入新记录
                    insert_stmt = self.table.insert().values(**values)
                    sess.execute(insert_stmt)
        except Exception as e:
            if create_and_retry and not self.table_exists():
                log_debug(f"Table does not exist: {self.table.name}")
                log_debug("Creating table and retrying upsert")
                self.create()
                return self.upsert(session, create_and_retry=False)
            else:
                log_warning(f"Exception upserting into table: {e}")
                log_warning(
                    "A table upgrade might be required, please review these docs for more information: https://ai_agent.link/upgrade-schema"
                )
                return None
        return self.read(session_id=session.session_id)

    def delete_session(self, session_id: Optional[str] = None):
        """
        Delete a session from the database.

        Args:
            session_id (Optional[str], optional): ID of the session to delete. Defaults to None.

        Raises:
            Exception: If an error occurs during deletion.
        """
        if session_id is None:
            logger.warning("No session_id provided for deletion.")
            return

        try:
            with self.Session() as sess, sess.begin():
                # Delete the session with the given session_id
                delete_stmt = self.table.delete().where(self.table.c.session_id == session_id)
                result = sess.execute(delete_stmt)
                if result.rowcount == 0:
                    log_debug(f"No session found with session_id: {session_id}")
                else:
                    log_debug(f"Successfully deleted session with session_id: {session_id}")
        except Exception as e:
            logger.error(f"Error deleting session: {e}")

    def drop(self) -> None:
        """
        Drop the table from the database if it exists.
        """
        if self.table_exists():
            log_debug(f"Deleting table: {self.table_name}")
            # Drop with checkfirst=True to avoid errors if the table doesn't exist
            self.table.drop(self.db_engine, checkfirst=True)
            # Clear metadata to ensure indexes are recreated properly
            self.metadata = MetaData(schema=self.schema)
            self.table = self.get_table()

    def __deepcopy__(self, memo):
        """
        Create a deep copy of the MySqlStorage instance, handling unpickleable attributes.

        Args:
            memo (dict): A dictionary of objects already copied during the current copying pass.

        Returns:
            MySqlStorage: A deep-copied instance of MySqlStorage.
        """
        from copy import deepcopy

        # Create a new instance without calling __init__
        cls = self.__class__
        copied_obj = cls.__new__(cls)
        memo[id(self)] = copied_obj

        # Deep copy attributes
        for k, v in self.__dict__.items():
            if k in {"metadata", "table", "inspector"}:
                continue
            # Reuse db_engine and Session without copying
            elif k in {"db_engine", "SqlSession"}:
                setattr(copied_obj, k, v)
            else:
                setattr(copied_obj, k, deepcopy(v, memo))

        # Recreate metadata and table for the copied instance
        copied_obj.metadata = MetaData(schema=copied_obj.schema)
        copied_obj.inspector = inspect(copied_obj.db_engine)
        copied_obj.table = copied_obj.get_table()

        return copied_obj
