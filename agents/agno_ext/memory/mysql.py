import time
from typing import List, Optional

from sqlalchemy import BigInteger

try:
    from sqlalchemy.engine import Engine, create_engine
    from sqlalchemy.inspection import inspect
    from sqlalchemy.orm import scoped_session, sessionmaker
    from sqlalchemy.schema import Column, MetaData, Table
    from sqlalchemy.sql.expression import delete, select, text
    from sqlalchemy.types import DateTime, String, JSON
except ImportError:
    raise ImportError("`sqlalchemy` not installed.  Please install using `pip install sqlalchemy mysqlclient`")

from agno.memory.db import MemoryDb
from agno.memory.row import MemoryRow
from agno.utils.log import log_debug, logger


class MySqlMemoryDb(MemoryDb):
    def __init__(
            self,
            table_name: str,
            schema: Optional[str] = None,
            db_url: Optional[str] = None,
            db_engine: Optional[Engine] = None,
    ):
        """
        This class provides a memory store backed by a MySQL table.

        The following order is used to determine the database connection:
            1. Use the db_engine if provided
            2. Use the db_url to create the engine

        Args:
            table_name (str): The name of the table to store memory rows.
            schema (Optional[str]): The database name to store the table in. Defaults to None.
            db_url (Optional[str]): The database URL to connect to. Defaults to None.
            db_engine (Optional[Engine]): The database engine to use. Defaults to None.
        """
        _engine: Optional[Engine] = db_engine
        if _engine is None and db_url is not None:
            _engine = create_engine(db_url)

        if _engine is None:
            raise ValueError("Must provide either db_url or db_engine")

        self.table_name: str = table_name
        self.schema: Optional[str] = schema
        self.db_url: Optional[str] = db_url
        self.db_engine: Engine = _engine
        self.inspector = inspect(self.db_engine)
        self.metadata: MetaData = MetaData(schema=self.schema)
        self.Session: scoped_session = scoped_session(sessionmaker(bind=self.db_engine))
        self.table: Table = self.get_table()

    def get_table(self) -> Table:
        return Table(
            self.table_name,
            self.metadata,
            Column("id", String(255), primary_key=True),
            Column("user_id", String(255)),
            Column("memory", JSON, server_default=text("'{}'"), nullable=False),
            Column("created_at", BigInteger, default=lambda: int(time.time())),
            Column("updated_at", BigInteger, default=lambda: int(time.time()), onupdate=lambda: int(time.time())),
            extend_existing=True,
        )

    def create(self) -> None:
        if not self.table_exists():
            try:
                with self.Session() as sess, sess.begin():
                    if self.schema is not None:
                        log_debug(f"Creating database if not exists: {self.schema}")
                        sess.execute(text(f"CREATE DATABASE IF NOT EXISTS {self.schema};"))

                log_debug(f"Creating table: {self.table_name}")

                with self.Session() as sess, sess.begin():
                    exists_query = text(
                        "SELECT 1 FROM information_schema.tables WHERE table_schema = :schema AND table_name = :table"
                    )
                    exists = sess.execute(
                        exists_query,
                        {"schema": self.schema or sess.execute(text("SELECT DATABASE()")).scalar(),
                         "table": self.table_name}
                    ).scalar()

                    if not exists:
                        # u4f7fu7528u5143u7ec4u548cu5b57u7b26u4e32u683cu5f0fu5316u7b80u5316u591au884cu5b57u7b26u4e32u7684u521bu5efa
                        create_table_sql = (
                            f"CREATE TABLE {('`' + self.schema + '`.' if self.schema else '')}`{self.table_name}` (\n"
                            "    `id` VARCHAR(255) NOT NULL PRIMARY KEY,\n"
                            "    `user_id` VARCHAR(255),\n"
                            "    `memory` JSON NOT NULL,\n"
                            "    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,\n"
                            "    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\n"
                            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
                        )

                        sess.execute(text(create_table_sql))

                        sess.execute(text(
                            f"CREATE INDEX `idx_user_id` ON {'`' + self.schema + '`.' if self.schema else ''}`{self.table_name}` (`user_id`)"))

                        log_debug(f"Table {self.table_name} created successfully")
            except Exception as e:
                logger.error(f"Error creating table '{self.table.fullname}': {e}")
                raise

    def memory_exists(self, memory: MemoryRow) -> bool:
        columns = [self.table.c.id]
        with self.Session() as sess, sess.begin():
            stmt = select(*columns).where(self.table.c.id == memory.id)
            result = sess.execute(stmt).first()
            return result is not None

    def read_memories(
            self, user_id: Optional[str] = None, limit: Optional[int] = None, sort: Optional[str] = None
    ) -> List[MemoryRow]:
        memories: List[MemoryRow] = []
        try:
            with self.Session() as sess, sess.begin():
                stmt = select(self.table)
                if user_id is not None:
                    stmt = stmt.where(self.table.c.user_id == user_id)
                if limit is not None:
                    stmt = stmt.limit(limit)

                if sort == "asc":
                    stmt = stmt.order_by(self.table.c.created_at.asc())
                else:
                    stmt = stmt.order_by(self.table.c.created_at.desc())

                rows = sess.execute(stmt).fetchall()
                for row in rows:
                    if row is not None:
                        memories.append(MemoryRow.model_validate(row))
        except Exception as e:
            log_debug(f"Exception reading from table: {e}")
            log_debug(f"Table does not exist: {self.table.name}")
            log_debug("Creating table for future transactions")
            # self.create()
        return memories

    def upsert_memory(self, memory: MemoryRow, create_and_retry: bool = True) -> None:
        """Create a new memory if it does not exist, otherwise update the existing memory"""

        try:
            with self.Session() as sess, sess.begin():
                # Check if record exists
                exists = self.memory_exists(memory)

                # u786eu4fddmemoryu5b57u6bb5u59cbu7ec8u6709u6548uff0cu4e0du4e3aNoneu6216u7a7au5b57u5178
                memory_data = memory.memory or {}

                if exists:
                    # Update existing record
                    stmt = self.table.update().where(self.table.c.id == memory.id).values(
                        user_id=memory.user_id,
                        memory=memory_data,
                    )
                else:
                    # Insert new record
                    stmt = self.table.insert().values(
                        id=memory.id,
                        user_id=memory.user_id,
                        memory=memory_data,
                    )

                sess.execute(stmt)
        except Exception as e:
            log_debug(f"Exception upserting into table: {e}")
            log_debug(f"Table does not exist: {self.table.name}")
            log_debug("Creating table for future transactions")
            self.create()
            if create_and_retry:
                return self.upsert_memory(memory, create_and_retry=False)
            return None

    def delete_memory(self, id: str) -> None:
        with self.Session() as sess, sess.begin():
            stmt = delete(self.table).where(self.table.c.id == id)
            sess.execute(stmt)

    def drop_table(self) -> None:
        if self.table_exists():
            log_debug(f"Deleting table: {self.table_name}")
            self.table.drop(self.db_engine)

    def table_exists(self) -> bool:
        log_debug(f"Checking if table exists: {self.table.name}")
        try:
            return inspect(self.db_engine).has_table(self.table.name, schema=self.schema)
        except Exception as e:
            logger.error(e)
            return False

    def clear(self) -> bool:
        with self.Session() as sess, sess.begin():
            stmt = delete(self.table)
            sess.execute(stmt)
            return True

    def __deepcopy__(self, memo):
        """
        Create a deep copy of the MySqlMemoryDb instance, handling unpickleable attributes.

        Args:
            memo (dict): A dictionary of objects already copied during the current copying pass.

        Returns:
            MySqlMemoryDb: A deep-copied instance of MySqlMemoryDb.
        """
        from copy import deepcopy

        # Create a new instance without calling __init__
        cls = self.__class__
        copied_obj = cls.__new__(cls)
        memo[id(self)] = copied_obj

        # Deep copy attributes
        for k, v in self.__dict__.items():
            if k in {"metadata", "table"}:
                continue
            # Reuse db_engine and Session without copying
            elif k in {"db_engine", "Session"}:
                setattr(copied_obj, k, v)
            else:
                setattr(copied_obj, k, deepcopy(v, memo))

        # Recreate metadata and table for the copied instance
        copied_obj.metadata = MetaData(schema=copied_obj.schema)
        copied_obj.table = copied_obj.get_table()

        return copied_obj
