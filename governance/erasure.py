"""GDPR right to erasure (Article 17): remove a person's personal data everywhere, keep what the law requires,
and leave an audit trail."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import duckdb

from .classify import Classification


def erase(con: duckdb.DuckDBPyConnection, catalog: list[Classification], customer_id: str,
          request_id: str) -> dict:
    email, phone = con.execute("select email, phone from crm.customers where customer_id = ?",
                               [customer_id]).fetchone() or (None, None)
    token = "erased_" + hashlib.sha256(customer_id.encode()).hexdigest()[:10]
    actions = []

    # Financial records (orders) must be kept for tax law: pseudonymise the link, keep the amounts.
    n = con.execute("update sales.orders set customer_id = ? where customer_id = ?", [token, customer_id]).fetchone()[0]
    actions.append({"table": "sales.orders", "action": "pseudonymised customer_id (retained for tax law)", "rows": n})
    # Support tickets contain free-text PII: delete them.
    n = con.execute("delete from support.tickets where customer_id = ?", [customer_id]).fetchone()[0]
    actions.append({"table": "support.tickets", "action": "deleted", "rows": n})
    # Marketing events are keyed by email only: found through the classification, not a customer_id join.
    contact_cols = [c.column for c in catalog if c.column.startswith("marketing.") and c.classification == "pii_direct"]
    for col in contact_cols:
        table, column = col.rsplit(".", 1)
        n = con.execute(f'delete from {table} where "{column}" = ?', [email]).fetchone()[0]
        actions.append({"table": table, "action": f"deleted (matched on {column})", "rows": n})
    # The customer record itself.
    n = con.execute("delete from crm.customers where customer_id = ?", [customer_id]).fetchone()[0]
    actions.append({"table": "crm.customers", "action": "deleted", "rows": n})

    # Verify: scan every text column for the person's email and phone.
    leftovers = []
    for c in catalog:
        if "VARCHAR" not in c.data_type.upper():
            continue
        table, column = c.column.rsplit(".", 1)
        hits = con.execute(f'select count(*) from {table} where "{column}" like ? or "{column}" like ?',
                           [f"%{email}%", f"%{phone}%"]).fetchone()[0]
        if hits:
            leftovers.append({"column": c.column, "rows": hits})

    record = {"request_id": request_id, "subject": token, "completed_at": datetime.now(timezone.utc).isoformat(),
              "actions": actions, "verification": "no personal data found" if not leftovers else leftovers}
    con.execute("create schema if not exists governance")
    con.execute("create table if not exists governance.erasure_log (request_id varchar, record json)")
    con.execute("insert into governance.erasure_log values (?, ?)", [request_id, json.dumps(record)])
    return record
