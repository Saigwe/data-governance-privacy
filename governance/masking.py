"""Generate role-specific secure views from the classification and the policy file."""
from __future__ import annotations

from pathlib import Path

import duckdb
import yaml

from .classify import Classification

REDACT_EMAIL = r"[\w.+-]+@[\w-]+\.[\w.]+"
REDACT_PHONE = r"\+\d{2,3}[\s\d]{8,14}\d"


def expression(col: str, data_type: str, action: str) -> str | None:
    c = f'"{col}"'
    if action == "clear":
        return c
    if action == "deny":
        return None
    if action == "hash":
        return f"'h_' || left(md5(cast({c} as varchar)), 12)"
    if action == "mask":
        if "email" in col or "contact" in col:
            return f"left({c}, 1) || '***@' || split_part({c}, '@', 2)"
        return f"repeat('*', greatest(length(cast({c} as varchar)) - 4, 0)) || right(cast({c} as varchar), 4)"
    if action == "generalise":
        if "date" in data_type.lower():
            return f"year({c})"
        return f"split_part(cast({c} as varchar), ' ', 1)"  # e.g. postcode district only
    if action == "redact":
        return (f"regexp_replace(regexp_replace({c}, '{REDACT_EMAIL}', '[email]', 'g'), "
                f"'{REDACT_PHONE}', '[phone]', 'g')")
    raise ValueError(f"unknown action {action}")


def create_views(con: duckdb.DuckDBPyConnection, catalog: list[Classification], policy_path: Path) -> list[str]:
    policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))["roles"]
    by_table: dict[str, list[Classification]] = {}
    for c in catalog:
        by_table.setdefault(c.column.rsplit(".", 1)[0], []).append(c)
    created = []
    for role, rules in policy.items():
        con.execute(f"create schema if not exists secure_{role}")
        for table, cols in by_table.items():
            exprs = []
            for c in cols:
                col = c.column.rsplit(".", 1)[1]
                e = expression(col, c.data_type, rules.get(c.classification, "clear"))
                if e:
                    exprs.append(f'{e} as "{col}"')
            view = f"secure_{role}.{table.split('.')[1]}"
            con.execute(f"create or replace view {view} as select {', '.join(exprs)} from {table}")
            created.append(view)
    return created
