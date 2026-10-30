# Data catalogue: personal data classification

| Column | Type | Class | Confidence | Evidence |
|---|---|---|---|---|
| `crm.customers.customer_id` | VARCHAR | **identifier** | medium | column name 'customer_id' |
| `crm.customers.full_name` | VARCHAR | **pii_direct** | medium | column name 'full_name' |
| `crm.customers.email` | VARCHAR | **pii_direct** | high | 100% of values are emails |
| `crm.customers.phone` | VARCHAR | **pii_direct** | high | 100% of values are phones |
| `crm.customers.date_of_birth` | DATE | **pii_quasi** | high | column name 'date_of_birth' and a date type |
| `crm.customers.postcode` | VARCHAR | **pii_quasi** | high | values are postcodes |
| `crm.customers.iban` | VARCHAR | **financial** | high | 100% of values look like IBANs |
| `crm.customers.segment` | VARCHAR | **none** | medium | no personal-data signals |
| `crm.customers.country` | VARCHAR | **none** | medium | no personal-data signals |
| `marketing.events.contact` | VARCHAR | **pii_direct** | high | 100% of values are emails |
| `marketing.events.campaign` | VARCHAR | **none** | medium | no personal-data signals |
| `marketing.events.event` | VARCHAR | **none** | medium | no personal-data signals |
| `sales.orders.order_id` | VARCHAR | **identifier** | medium | column name 'order_id' |
| `sales.orders.customer_id` | VARCHAR | **identifier** | medium | column name 'customer_id' |
| `sales.orders.amount_eur` | DOUBLE | **none** | medium | no personal-data signals |
| `sales.orders.order_date` | DATE | **none** | medium | no personal-data signals |
| `support.tickets.ticket_id` | VARCHAR | **identifier** | medium | column name 'ticket_id' |
| `support.tickets.customer_id` | VARCHAR | **identifier** | medium | column name 'customer_id' |
| `support.tickets.body` | VARCHAR | **pii_free_text** | high | free text; 25% of sampled rows contain an email or phone number |
| `support.tickets.created_at` | DATE | **none** | medium | no personal-data signals |

## Retention

- `support.tickets`: 365 days
- `marketing.events`: 730 days
- `crm.customers`: account lifetime + 6 years (financial records)
