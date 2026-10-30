"""Scan, classify, mask, process an erasure request and write the catalogue and memo: python -m governance.run"""
from __future__ import annotations

import time
from collections import Counter
from pathlib import Path

import yaml

from .classify import scan
from .erasure import erase
from .masking import create_views
from .warehouse import TRUTH, build

ROOT = Path(__file__).resolve().parent.parent
SENSITIVE = {"pii_direct", "pii_quasi", "financial", "pii_free_text"}


def run(out_dir: Path = ROOT / "output") -> dict:
    con = build()
    catalog = scan(con)
    correct = sum(TRUTH.get(c.column) == c.classification for c in catalog)
    views = create_views(con, catalog, ROOT / "policies.yml")

    analyst_sample = con.execute("select email, phone, date_of_birth from secure_analyst.customers limit 3").fetchall()
    analyst_ticket = con.execute(
        "select body from secure_analyst.tickets where body like '%[email]%' or body like '%[phone]%' limit 1").fetchone()

    subject = con.execute("""select c.customer_id from crm.customers c
                             join support.tickets t using (customer_id)
                             join marketing.events e on e.contact = c.email limit 1""").fetchone()[0]
    start = time.perf_counter()
    record = erase(con, catalog, subject, "DSR-2026-0142")
    elapsed = time.perf_counter() - start

    out_dir.mkdir(parents=True, exist_ok=True)
    retention = yaml.safe_load((ROOT / "policies.yml").read_text(encoding="utf-8"))["retention"]
    rows = "\n".join(f"| `{c.column}` | {c.data_type} | **{c.classification}** | {c.confidence} | {c.evidence} |"
                     for c in catalog)
    (out_dir / "data_catalog.md").write_text(
        "# Data catalogue: personal data classification\n\n| Column | Type | Class | Confidence | Evidence |\n"
        "|---|---|---|---|---|\n" + rows + "\n\n## Retention\n\n" +
        "\n".join(f"- `{k}`: {v}" for k, v in retention.items()) + "\n", encoding="utf-8")

    sensitive = [c for c in catalog if c.classification in SENSITIVE]
    unexpected = [c for c in sensitive if c.classification == "pii_free_text" or c.column.startswith("marketing.")]
    counts = Counter(c.classification for c in sensitive)
    actions = "\n".join(f"| {a['table']} | {a['action']} | {a['rows']} |" for a in record["actions"])
    (out_dir / "governance_memo.md").write_text(f"""# Personal data governance: summary for leadership

**Bottom line:** an automated scan found personal data in **{len(sensitive)} columns across
{len({c.column.rsplit('.', 1)[0] for c in sensitive})} tables**, including **{len(unexpected)} places nobody had
documented** ({", ".join(f"`{c.column}`" for c in unexpected)}). Analysts and marketing now see masked or
pseudonymised values by default, and a GDPR erasure request was completed in **{elapsed * 1000:.0f} ms** with a
verified audit record.

## What was found

| Class | Columns |
|---|---|
""" + "\n".join(f"| {k} | {v} |" for k, v in counts.most_common()) + f"""

Classification accuracy against a hand-labelled list: **{correct}/{len(catalog)}** columns.

## What each role now sees

{len(views)} secure views were generated from [`policies.yml`](../policies.yml). For example, an analyst sees:

| email | phone | date_of_birth |
|---|---|---|
""" + "\n".join(f"| {a} | {b} | {c} |" for a, b, c in analyst_sample) + f"""

and support ticket text with contact details removed: *"{analyst_ticket[0] if analyst_ticket else ''}"*

## Erasure request {record['request_id']}

| Table | Action | Rows |
|---|---|---|
{actions}

Verification scan after erasure: **{record['verification']}**. Order amounts were kept under a pseudonym because
financial records must be retained; everything else identifying the person was deleted.

## Asks

1. Make the `secure_*` views the only way analysts and marketing reach these tables (revoke raw table grants).
2. Add the classification scan to CI, so a new column with personal data cannot ship undocumented.
3. Agree the retention periods in `policies.yml` with Legal and schedule deletion jobs.
""", encoding="utf-8")
    return {"catalog": catalog, "accuracy": correct / len(catalog), "views": views, "erasure": record,
            "analyst_sample": analyst_sample, "analyst_ticket": analyst_ticket, "con": con}


if __name__ == "__main__":
    res = run()
    print(f"Classification accuracy {res['accuracy']:.0%}; {len(res['views'])} secure views")
    for c in res["catalog"]:
        if c.classification != TRUTH.get(c.column):
            print("MISS", c.column, c.classification, "expected", TRUTH.get(c.column))
    print("Erasure verification:", res["erasure"]["verification"])
    print("Analyst sees:", res["analyst_sample"][0], res["analyst_ticket"])
