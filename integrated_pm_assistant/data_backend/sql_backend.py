"""
SQL backend — supports PostgreSQL, MySQL, and SQLite via SQLAlchemy.

Tables are auto-created on first write.  Connection string comes from
``config.yaml``:

    data_backend:
      type: sql
      sql:
        connection_string: "sqlite:///pm_data.db"

Note: Columns containing Python lists or dicts are automatically
serialised to JSON strings on write and deserialised on read.
"""

import json
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from data_backend.base import DataBackend


class SQLBackend(DataBackend):
    """Read/write data using a SQL database."""

    def __init__(self, connection_string: str, table_map: Optional[Dict[str, str]] = None):
        self._connection_string = connection_string
        self._engine: Engine = create_engine(connection_string)
        self.table_map = table_map or {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _normalize_table(self, table_name: str) -> str:
        """
        Map logical table name to physical if configured.
        SQL table names cannot contain hyphens or spaces.
        """
        mapped_name = self.table_map.get(table_name, table_name)
        tbl = mapped_name.replace("-", "_").replace(" ", "_").lower()

        # Extract DB name or host for logging
        db_info = self._connection_string.split("/")[-1]
        if "?" in db_info:
            db_info = db_info.split("?")[0]

        print(f"🗄️ [SQL] Dataset '{table_name}' -> DB: '{db_info}' | Table: '{tbl}'")
        return tbl

    @staticmethod
    def _is_text_dtype(dtype) -> bool:
        """Check if pandas dtype is object or string-like."""
        dt_str = str(dtype).lower()
        return dtype == object or "str" in dt_str or "string" in dt_str or "object" in dt_str

    @staticmethod
    def _serialize_df(df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert columns that contain lists or dicts to JSON strings
        so SQLite / other SQL DBs can store them.
        """
        df = df.copy()
        for col in df.columns:
            if SQLBackend._is_text_dtype(df[col].dtype):
                df[col] = df[col].apply(
                    lambda v: json.dumps(v) if isinstance(v, (list, dict)) else v
                )
        return df

    @staticmethod
    def _deserialize_df(df: pd.DataFrame) -> pd.DataFrame:
        """
        Try to parse columns that look like JSON arrays/objects back
        into Python lists/dicts.
        """
        def _try_parse(v):
            if isinstance(v, str):
                stripped = v.strip()
                if stripped.startswith(("[", "{")):
                    try:
                        return json.loads(stripped)
                    except (ValueError, TypeError):
                        pass
            return v

        df = df.copy()
        for col in df.columns:
            if SQLBackend._is_text_dtype(df[col].dtype):
                df[col] = df[col].apply(_try_parse)
        return df


    # ------------------------------------------------------------------
    # Interface implementation
    # ------------------------------------------------------------------

    def read(
        self,
        table_name: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        tbl = self._normalize_table(table_name)

        if not self.exists(table_name):
            raise FileNotFoundError(f"Table '{tbl}' does not exist")

        if filters:
            where_parts = []
            params: Dict[str, Any] = {}
            for i, (col, val) in enumerate(filters.items()):
                key = f"p{i}"
                where_parts.append(f'"{col}" = :{key}')
                params[key] = val
            where_clause = " AND ".join(where_parts)
            query = text(f'SELECT * FROM "{tbl}" WHERE {where_clause}')
            df = pd.read_sql(query, self._engine, params=params)
        else:
            df = pd.read_sql_table(tbl, self._engine)

        return self._deserialize_df(df)

    def write(
        self,
        table_name: str,
        df: pd.DataFrame,
        mode: str = "replace",
    ) -> None:
        tbl = self._normalize_table(table_name)
        if_exists = "replace" if mode == "replace" else "append"
        self._serialize_df(df).to_sql(tbl, self._engine, if_exists=if_exists, index=False)

    def append(self, table_name: str, df: pd.DataFrame) -> None:
        self.write(table_name, df, mode="append")

    def exists(self, table_name: str) -> bool:
        tbl = self._normalize_table(table_name)
        inspector = inspect(self._engine)
        return tbl in inspector.get_table_names()

    def update(
        self,
        table_name: str,
        df: pd.DataFrame,
        key_columns: List[str],
    ) -> None:
        tbl = self._normalize_table(table_name)

        if not self.exists(table_name):
            self._serialize_df(df).to_sql(tbl, self._engine, if_exists="replace", index=False)
            return

        existing = self._deserialize_df(pd.read_sql_table(tbl, self._engine))

        if key_columns:
            merge_keys = existing[key_columns].apply(tuple, axis=1)
            new_keys = df[key_columns].apply(tuple, axis=1)
            existing = existing[~merge_keys.isin(new_keys)]

        merged = pd.concat([existing, df], ignore_index=True)
        self._serialize_df(merged).to_sql(tbl, self._engine, if_exists="replace", index=False)
