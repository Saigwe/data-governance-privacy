"""Scan every column and classify it from its name and a sample of its values."""
from __future__ import annotations

import re
from dataclasses import dataclass

import duckdb

PATTERNS = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "phone": re.compile(r"\+\d{2,3}[\s\d]{8,14}"),
    "iban": re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"),
    "postcode": re.compile(r"^(\d{4}-\d{3}|[A-Z]{1,2}\d{1,2}[A-Z]? ?\d[A-Z]{2})$"),
}
NAME_HINTS = {
    "pii_direct": ["name", "email", "phone", "mobile", "contact", "address"],
    "pii_quasi": ["birth", "dob", "postcode", "zip", "gender"],
    "financial": ["iban", "card", "account_number", "sort_code"],
    "identifier": ["_id"],
}


@dataclass(frozen=True)
class Classification:
    column: str          # schema.table.column
    data_type: str
    classification: str  # pii_direct | pii_quasi | financial | pii_free_text | identifier | none
    confidence: str      # high | medium
    evidence: str


def _value_matches(values: list[str]) -> dict[str, float]:
    if not values:
        return {}
    return {k: sum(bool(p.search(v)) for v in values) / len(values) for k, p in PATTERNS.items()}


def classify_column(fqcn: str, data_type: str, sample: list) -> Classification:
    name = fqcn.split(".")[-1].lower()
    values = [str(v) for v in sample if v is not None]
    hits = _value_matches(values)
    long_text = values and sum(len(v) for v in values) / len(values) > 40

    if hits.get("iban", 0) > 0.8:
        return Classification(fqcn, data_type, "financial", "high", f"{hits['iban']:.0%} of values look like IBANs")
    if hits.get("email", 0) > 0.8 or hits.get("phone", 0) > 0.8:
        kind = "email" if hits.get("email", 0) > 0.8 else "phone"
        return Classification(fqcn, data_type, "pii_direct", "high", f"{hits[kind]:.0%} of values are {kind}s")
    if long_text and (hits.get("email", 0) > 0 or hits.get("phone", 0) > 0):
        share = max(hits.get("email", 0), hits.get("phone", 0))
        return Classification(fqcn, data_type, "pii_free_text", "high",
                              f"free text; {share:.0%} of sampled rows contain an email or phone number")
    if hits.get("postcode", 0) > 0.8:
        return Classification(fqcn, data_type, "pii_quasi", "high", "values are postcodes")
    for cls, hints in NAME_HINTS.items():
        if any(h in name for h in hints) and not (cls == "identifier" and not name.endswith("_id")):
            if cls == "pii_quasi" and "date" in data_type.lower():
                return Classification(fqcn, data_type, cls, "high", f"column name '{name}' and a date type")
            return Classification(fqcn, data_type, cls, "medium", f"column name '{name}'")
    return Classification(fqcn, data_type, "none", "medium", "no personal-data signals")


def scan(con: duckdb.DuckDBPyConnection, sample_rows: int = 200) -> list[Classification]:
    cols = con.execute("""select table_schema, table_name, column_name, data_type from information_schema.columns
                          where table_schema not in ('information_schema', 'pg_catalog', 'main')
                            and table_name not like 'v_%' order by 1, 2, ordinal_position""").fetchall()
    out = []
    for schema, table, column, dtype in cols:
        sample = [r[0] for r in con.execute(
            f'select "{column}" from {schema}.{table} using sample {sample_rows} rows').fetchall()]
        out.append(classify_column(f"{schema}.{table}.{column}", dtype, sample))
    return out
