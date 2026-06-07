# Usman Sharjeel — AgentCollect Contact Finder Submission

This branch implements the current plan-first Contact Finder challenge as a small Python CLI against the mocked providers in `challenge/mocks/`. It does not call real APIs, scrape real websites, or run the legacy Laravel challenge.

## Review path

- `PLAN.md` was committed first, before reading `challenge/CLARIFICATIONS.md` or the mock fixtures.
- `contact_finder/` contains the minimal Python slice.
- `ABOUT.md` contains the requested candidate reflection.
- `SUBMISSION.md` has the run command, test command, and process notes.

## Run

```bash
python -m contact_finder --input challenge/data/companies.csv --output contacts.csv
```

## Test

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The output keeps one row per input company. Contacts below the clarification threshold of `70` leave `contact_email_or_phone` empty and set `needs_human_review` to `true`.

---

# Respaid / AgentCollect — Hiring Challenge

Welcome. This challenge is **language-agnostic** and **plan-first**. We are not testing whether you know our stack (Laravel + React). We are testing **how you think**: do you plan and ask high-value questions before you build, or do you dive straight into code?

> **Use AI tools.** Claude Code, Cursor, Copilot — we expect and want it. We evaluate how you *direct* AI, not whether you use it.

## Start here → the Contact Finder challenge

Everything is in [`challenge/PROBLEM.md`](challenge/PROBLEM.md). It has two **gated** stages:

1. **Stage A — PLAN ONLY** (~20 min): commit a `PLAN.md` (architecture, sources, confidence/provenance/"cannot-verify", privacy, and clarifying questions) **before** you read the clarifications or write solution code. Template: [`challenge/PLAN.template.md`](challenge/PLAN.template.md).
2. **Stage B — CLARIFY + BUILD**: read [`challenge/CLARIFICATIONS.md`](challenge/CLARIFICATIONS.md), then build a minimal slice against the **mocked providers** in [`challenge/mocks/`](challenge/mocks/). No real scraping.

Dataset: [`challenge/data/companies.csv`](challenge/data/companies.csv).

## How to submit
- Your own repo (private is fine — add `wwwidr` as a collaborator), with `PLAN.md` committed **first** (git timestamps are part of the signal), then your slice.
- Process evidence: a screen recording link **or** a clean commit timeline (your choice — async, no webcam required).
- An `ABOUT.md` at the repo root — template: [`ABOUT.template.md`](ABOUT.template.md).

## How we score
See the rubric in [`challenge/PROBLEM.md`](challenge/PROBLEM.md#how-we-score-so-there-are-no-surprises). In short: plan & judgment 35%, clarifying questions 10%, adaptation 15%, slice 15%, AI-tool direction 15%, communication 10%. **Hard reject** if you dove into code with no plan, or faked precise contacts with no confidence/provenance handling.

## Conventions
[`CLAUDE.md`](CLAUDE.md) shows how we work. You don't need to follow our Laravel conventions for this language-agnostic challenge, but skim it — how we think about conventions matters.

---

### Legacy (optional, ignore unless asked)
The `tickets/` folder + the Laravel sandbox app are from our previous stack-specific challenge. The Contact Finder above is the current challenge. Do not do both.
