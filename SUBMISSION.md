# Submission Notes

## Process

- Commit 1 adds `PLAN.md` only, before reading `challenge/CLARIFICATIONS.md` or the mock provider fixtures.
- Commit 2 adds the Python contact finder slice against the mocked providers.
- Commit 3 adds `ABOUT.md`, README usage notes, and this submission note.

## Run

```bash
python -m contact_finder --input challenge/data/companies.csv --output contacts.csv
```

The command writes one output row per input company. Rows below the clarification threshold of `70` leave `contact_email_or_phone` empty and set `needs_human_review` to `true`.

## Test

```bash
python -m unittest discover -s tests -p "test_*.py"
```

No real APIs are called and no real scraping is performed. The implementation reads only `challenge/mocks/enrichment_responses.json`.
