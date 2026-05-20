"""
Odoo ERP backend — connects via XML-RPC (``xmlrpc.client``).

Requires:

    data_backend:
      type: odoo
      odoo:
        url: "https://your-odoo.com"
        db: "mydb"
        username: "admin"
        api_key: "your-api-key"
        model_map:           # logical name → Odoo model
          employees: "hr.employee"
          tasks: "project.task"
          meetings: "calendar.event"
"""

import xmlrpc.client
from typing import Any, Dict, List, Optional

import pandas as pd

from data_backend.base import DataBackend


class OdooBackend(DataBackend):
    """Read/write data using the Odoo XML-RPC API."""

    def __init__(
        self,
        url: str,
        db: str,
        username: str,
        api_key: str,
        model_map: Optional[Dict[str, str]] = None,
    ):
        self._url = url.rstrip("/")
        self._db = db
        self._username = username
        self._api_key = api_key
        self._model_map: Dict[str, str] = model_map or {}

        # Authenticate
        common = xmlrpc.client.ServerProxy(f"{self._url}/xmlrpc/2/common")
        self._uid = common.authenticate(self._db, self._username, self._api_key, {})

        if not self._uid:
            raise ConnectionError("Odoo authentication failed")

        self._models = xmlrpc.client.ServerProxy(f"{self._url}/xmlrpc/2/object")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _model_for(self, table_name: str) -> str:
        """Resolve logical table name to Odoo model name."""
        base = table_name.lower().split("_")[-1]  # e.g. "MyProj_Tasks" → "tasks"
        model = self._model_map.get(table_name) or self._model_map.get(base)
        if not model:
            raise ValueError(
                f"No Odoo model mapping for '{table_name}'. "
                f"Add it in config.yaml → data_backend.odoo.model_map"
            )
        return model

    def _execute(self, model: str, method: str, *args, **kwargs):
        return self._models.execute_kw(
            self._db, self._uid, self._api_key,
            model, method, list(args), kwargs,
        )

    # ------------------------------------------------------------------
    # Interface implementation
    # ------------------------------------------------------------------

    def read(
        self,
        table_name: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        model = self._model_for(table_name)

        domain: list = []
        if filters:
            for col, val in filters.items():
                domain.append((col, "=", val))

        # First get field names
        fields_info = self._execute(model, "fields_get", attributes=["string", "type"])
        field_names = list(fields_info.keys())

        ids = self._execute(model, "search", domain)

        if not ids:
            return pd.DataFrame()

        records = self._execute(model, "read", ids, {"fields": field_names})

        return pd.DataFrame(records)

    def write(
        self,
        table_name: str,
        df: pd.DataFrame,
        mode: str = "replace",
    ) -> None:
        model = self._model_for(table_name)

        if mode == "replace":
            # Delete all existing records first
            existing_ids = self._execute(model, "search", [])
            if existing_ids:
                self._execute(model, "unlink", existing_ids)

        # Create new records
        records = df.to_dict(orient="records")
        for record in records:
            # Remove id/None keys that Odoo won't accept
            clean = {k: v for k, v in record.items() if v is not None and k != "id"}
            self._execute(model, "create", clean)

    def append(self, table_name: str, df: pd.DataFrame) -> None:
        self.write(table_name, df, mode="append")

    def exists(self, table_name: str) -> bool:
        try:
            model = self._model_for(table_name)
            count = self._execute(model, "search_count", [])
            return count > 0
        except Exception:
            return False

    def update(
        self,
        table_name: str,
        df: pd.DataFrame,
        key_columns: List[str],
    ) -> None:
        model = self._model_for(table_name)
        records = df.to_dict(orient="records")

        for record in records:
            # Build domain from key columns
            domain = [(col, "=", record[col]) for col in key_columns if col in record]
            existing_ids = self._execute(model, "search", domain)

            clean = {k: v for k, v in record.items() if v is not None and k != "id"}

            if existing_ids:
                self._execute(model, "write", existing_ids, clean)
            else:
                self._execute(model, "create", clean)
