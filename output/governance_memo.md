# Personal data governance: summary for leadership

**Bottom line:** an automated scan found personal data in **8 columns across
3 tables**, including **2 places nobody had
documented** (`marketing.events.contact`, `support.tickets.body`). Analysts and marketing now see masked or
pseudonymised values by default, and a GDPR erasure request was completed in **13 ms** with a
verified audit record.

## What was found

| Class | Columns |
|---|---|
| pii_direct | 4 |
| pii_quasi | 2 |
| financial | 1 |
| pii_free_text | 1 |

Classification accuracy against a hand-labelled list: **20/20** columns.

## What each role now sees

12 secure views were generated from [`policies.yml`](../policies.yml). For example, an analyst sees:

| email | phone | date_of_birth |
|---|---|---|
| h_8b42eba2d17d | h_2425d962e272 | 1987 |
| h_0e7eb6b461cd | h_dd173c083be3 | 1977 |
| h_f90414db7b63 | h_7aa4bcd7d72e | 1991 |

and support ticket text with contact details removed: *"Call me back on [phone] about my refund."*

## Erasure request DSR-2026-0142

| Table | Action | Rows |
|---|---|---|
| sales.orders | pseudonymised customer_id (retained for tax law) | 3 |
| support.tickets | deleted | 1 |
| marketing.events | deleted (matched on contact) | 1 |
| crm.customers | deleted | 1 |

Verification scan after erasure: **no personal data found**. Order amounts were kept under a pseudonym because
financial records must be retained; everything else identifying the person was deleted.

## Asks

1. Make the `secure_*` views the only way analysts and marketing reach these tables (revoke raw table grants).
2. Add the classification scan to CI, so a new column with personal data cannot ship undocumented.
3. Agree the retention periods in `policies.yml` with Legal and schedule deletion jobs.
