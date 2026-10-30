# 3-minute walkthrough: Data Governance & Privacy

A timed script for a Loom recording of about 3 minutes (screen plus camera bubble, 1080p). Say it in your own words; the lines are a guide, not a teleprompter.

**Open these tabs before you press record:** README, `governance/classify.py`, `policies.yml`, `governance/masking.py`, `governance/erasure.py`, `output/data_catalog.md`, `output/governance_memo.md`, `tests/test_governance.py`, GitHub Actions.

| Time | On screen | What to say |
|---|---|---|
| 0:00–0:20 | Portfolio card, then the README headline | Most privacy policies live in a PDF. Here governance runs as code: it found personal data in 8 columns, including 2 places nobody had documented, and handles a GDPR erasure end to end. |
| 0:20–0:50 | `governance/classify.py` | Every column is classified from its name and a sample of its values, as direct PII, quasi-identifier, financial, free text, identifier or none. That's how emails hidden inside support-ticket text are found. 20 out of 20 correct against a hand-labelled list. |
| 0:50–1:15 | `policies.yml` | One policy file maps each role and class to an action: clear, mask, hash, generalise, redact or deny. |
| 1:15–1:40 | `governance/masking.py` and a secure view | Twelve secure views are generated from it. Analysts get stable hashes, so joins still work, birth years instead of birth dates, ticket text with emails and phones redacted, and no IBANs. |
| 1:40–2:10 | `governance/erasure.py` | Right to erasure: delete the customer, their tickets and their marketing events, which are only matched by email, found through classification. Order amounts are kept under a pseudonym because financial records must be retained. A verification scan confirms nothing identifying is left, and it's logged. |
| 2:10–2:30 | `output/data_catalog.md` | The catalogue lists every column's class, the evidence and the retention period. |
| 2:30–2:45 | `output/governance_memo.md` | Leadership gets the findings, what each role now sees, the erasure audit and three asks. |
| 2:45–3:00 | `tests/`, then the README top | Six tests: value-based detection beats names alone, no raw PII in analyst views, hashed keys still join, and erasure removes everything it should. Links are under the video. |

## Recording checklist
- Close email, chat and notifications. Zoom the browser to 125% so code is readable.
- Run `python -m governance.run` once before recording so the outputs are fresh.
- Keep to one take per section; Loom lets you trim. Aim for 2:45 to 3:10.
- Show real numbers on screen as you say them; never estimate on camera.
- Say "simulated warehouse" when you introduce the data. This is a skills demonstration, not a rebuild of client work.

## After recording
1. Copy the Loom share link.
2. In `README.md`, replace the walkthrough line with `- [x] [3-minute Loom walkthrough](<your Loom link>)` and add the link under the title.
3. Add the link to this project's card on saigwe.github.io.
