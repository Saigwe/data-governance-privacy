import pytest

from governance.classify import classify_column, scan
from governance.erasure import erase
from governance.masking import create_views
from governance.run import ROOT, run
from governance.warehouse import TRUTH, build


def test_value_based_detection_beats_column_names():
    # a column named innocuously but full of emails is still PII
    c = classify_column("x.t.notes_ref", "VARCHAR", ["a.b@example.com", "c.d@example.com"])
    assert c.classification == "pii_direct"
    t = classify_column("x.t.body", "VARCHAR", ["please email me at a.b@example.com about my order thanks",
                                                "the app is slow when loading the basket page today"])
    assert t.classification == "pii_free_text"


@pytest.fixture
def env():
    con = build(n_customers=200)
    catalog = scan(con)
    create_views(con, catalog, ROOT / "policies.yml")
    return con, catalog


def test_classifier_matches_ground_truth(env):
    _, catalog = env
    wrong = [c.column for c in catalog if TRUTH.get(c.column) != c.classification]
    assert not wrong


def test_analyst_view_has_no_raw_pii(env):
    con, _ = env
    emails = con.execute("select count(*) from secure_analyst.customers where email like '%@%'").fetchone()[0]
    assert emails == 0
    leaked = con.execute("select count(*) from secure_analyst.tickets where regexp_matches(body, '@|\\+\\d{2}')"
                         ).fetchone()[0]
    assert leaked == 0
    cols = [r[0] for r in con.execute("describe secure_analyst.customers").fetchall()]
    assert "iban" not in cols                                   # financial data denied to analysts


def test_hashing_keeps_joins_working(env):
    con, _ = env
    joined = con.execute("""select count(*) from secure_analyst.orders o
                            join secure_analyst.customers c using (customer_id)""").fetchone()[0]
    assert joined == con.execute("select count(*) from sales.orders").fetchone()[0]


def test_erasure_removes_everything_and_logs(env):
    con, catalog = env
    cid, email = con.execute("""select c.customer_id, c.email from crm.customers c
                                join marketing.events e on e.contact = c.email limit 1""").fetchone()
    orders_before = con.execute("select count(*) from sales.orders where customer_id = ?", [cid]).fetchone()[0]
    record = erase(con, catalog, cid, "DSR-TEST")
    assert record["verification"] == "no personal data found"
    assert con.execute("select count(*) from marketing.events where contact = ?", [email]).fetchone()[0] == 0
    assert con.execute("select count(*) from sales.orders where customer_id = ?", [record["subject"]]
                       ).fetchone()[0] == orders_before          # financial records retained under pseudonym
    assert con.execute("select count(*) from governance.erasure_log").fetchone()[0] == 1


def test_end_to_end_writes_memo(tmp_path):
    res = run(tmp_path)
    assert res["accuracy"] == 1.0
    memo = (tmp_path / "governance_memo.md").read_text(encoding="utf-8")
    assert "support.tickets.body" in memo and "marketing.events.contact" in memo
