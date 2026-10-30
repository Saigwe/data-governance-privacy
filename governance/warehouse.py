"""Build a small DuckDB warehouse with personal data in expected and unexpected places."""
from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

import duckdb

FIRST = ["Ana", "Joao", "Maria", "Liam", "Emma", "Noah", "Olivia", "Tiago", "Sofia", "James", "Ines", "Rui"]
LAST = ["Silva", "Santos", "Murphy", "Smith", "Costa", "Walsh", "Ferreira", "Brown", "Pereira", "Kelly"]

# Ground truth for evaluating the classifier: table.column -> class
TRUTH = {
    "crm.customers.full_name": "pii_direct", "crm.customers.email": "pii_direct", "crm.customers.phone": "pii_direct",
    "crm.customers.date_of_birth": "pii_quasi", "crm.customers.postcode": "pii_quasi",
    "crm.customers.iban": "financial", "crm.customers.customer_id": "identifier",
    "crm.customers.segment": "none", "crm.customers.country": "none",
    "sales.orders.order_id": "identifier", "sales.orders.customer_id": "identifier",
    "sales.orders.amount_eur": "none", "sales.orders.order_date": "none",
    "support.tickets.ticket_id": "identifier", "support.tickets.customer_id": "identifier",
    "support.tickets.body": "pii_free_text", "support.tickets.created_at": "none",
    "marketing.events.contact": "pii_direct", "marketing.events.campaign": "none", "marketing.events.event": "none",
}


def build(path: str | Path = ":memory:", n_customers: int = 500, seed: int = 3) -> duckdb.DuckDBPyConnection:
    rng = random.Random(seed)
    con = duckdb.connect(str(path))
    for schema in ("crm", "sales", "support", "marketing"):
        con.execute(f"create schema if not exists {schema}")
    customers, orders, tickets, events = [], [], [], []
    for i in range(1, n_customers + 1):
        fn, ln = rng.choice(FIRST), rng.choice(LAST)
        email = f"{fn.lower()}.{ln.lower()}{i}@example.com"
        phone = rng.choice([f"+351 9{rng.randint(10, 39)} {rng.randint(100, 999)} {rng.randint(100, 999)}",
                            f"+44 7{rng.randint(100, 999)} {rng.randint(100000, 999999)}"])
        dob = date(1960, 1, 1) + timedelta(days=rng.randint(0, 15000))
        postcode = rng.choice([f"{rng.randint(1000, 9999)}-{rng.randint(100, 999)}", f"SW{rng.randint(1, 20)} {rng.randint(1, 9)}AB"])
        iban = f"PT50{rng.randint(10**20, 10**21 - 1)}"
        customers.append((f"C{i:05d}", f"{fn} {ln}", email, phone, dob, postcode, iban,
                          rng.choice(["consumer", "business"]), rng.choice(["PT", "UK", "IE"])))
        for k in range(rng.randint(0, 4)):
            orders.append((f"O{i:05d}{k}", f"C{i:05d}", round(rng.uniform(10, 300), 2),
                           date(2026, 1, 1) + timedelta(days=rng.randint(0, 290))))
        if rng.random() < 0.3:
            body = rng.choice([
                f"Hi, I can't log in. Please reply to {email}. Thanks, {fn}",
                f"Call me back on {phone} about my refund.",
                "The app crashes when I open my basket.",
                "Delivery was late again, very disappointed.",
            ])
            tickets.append((f"T{i:05d}", f"C{i:05d}", body, date(2026, 9, rng.randint(1, 30))))
        if rng.random() < 0.5:
            events.append((email, rng.choice(["autumn_sale", "loyalty"]), rng.choice(["open", "click"])))
    con.execute("create table crm.customers (customer_id varchar, full_name varchar, email varchar, phone varchar, "
                "date_of_birth date, postcode varchar, iban varchar, segment varchar, country varchar)")
    con.executemany("insert into crm.customers values (?, ?, ?, ?, ?, ?, ?, ?, ?)", customers)
    con.execute("create table sales.orders (order_id varchar, customer_id varchar, amount_eur double, order_date date)")
    con.executemany("insert into sales.orders values (?, ?, ?, ?)", orders)
    con.execute("create table support.tickets (ticket_id varchar, customer_id varchar, body varchar, created_at date)")
    con.executemany("insert into support.tickets values (?, ?, ?, ?)", tickets)
    con.execute("create table marketing.events (contact varchar, campaign varchar, event varchar)")
    con.executemany("insert into marketing.events values (?, ?, ?)", events)
    return con
