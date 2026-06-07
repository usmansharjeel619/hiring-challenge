# Contact Finder Plan

## Architecture

I would structure this as a small pipeline that turns a company CSV into auditable contact recommendations:

1. **Ingest** `company_name` and `mailing_address` from CSV, preserving the original row for traceability.
2. **Normalize company identity** by trimming names, standardizing business suffixes, parsing address locality/state when available, and creating a stable company key for matching.
3. **Query provider adapters** that represent different source types. Each adapter returns raw candidates plus source metadata, not final answers.
4. **Normalize candidates** into a common shape: contact name, role, email or phone, company match evidence, source, source-specific confidence, and provenance notes.
5. **Dedupe and merge evidence** across candidates by normalized company, contact channel, name, and role. Stronger multi-source evidence should merge into one candidate rather than produce duplicate outreach rows.
6. **Score and rank** candidates using role fit, company/address match strength, contact channel quality, source reliability, recency if available, and cross-source agreement.
7. **Emit one result row per input company** with the best verified candidate or a clear cannot-verify result. Every output value should be traceable to a source.

The system should keep provider logic isolated from scoring logic so we can add or remove sources without rewriting the confidence model.

## Sources & strategy

A single source is not reliable enough for payment outreach, so I would combine sources with different failure modes:

- **Business registry or official listing style sources** for entity identity, address, registered principals, and legal names. These are useful for company verification but can be stale or list legal contacts who are not payment decision-makers.
- **Company website or directory style sources** for current phone numbers, emails, staff pages, and office roles. These can be current but inconsistent and may expose generic inboxes instead of a named contact.
- **Contact enrichment style sources** for owner, finance, accounts payable, office manager, or operations contacts. These can improve recall but have higher false-positive risk and must be treated as evidence, not truth.
- **Domain/company metadata sources** for matching company names to web domains and validating whether an email domain belongs to the target company.

I would not guess emails from names and domains unless the business explicitly accepts that risk. For this challenge, the implementation should use only the mocked providers supplied in Stage B and should not scrape real sites.

## Quality

The scoring model should prefer honest uncertainty over precise-looking guesses.

- **Dedupe:** normalize email/phone, names, roles, company names, and addresses before comparing. Merge candidates when the contact channel matches or when name plus company plus role are strongly aligned.
- **Confidence scoring:** start from source reliability, then adjust for company/address match, target-role fit, direct contact channel quality, and cross-source agreement. Cap confidence when evidence comes from only one weak source, when the address does not match, or when the contact role is generic.
- **Provenance:** every output field should carry source evidence internally, and the final `source` field should identify which provider or providers supported the selected candidate.
- **Cannot verify:** if no candidate clears the threshold, output an explicit low-confidence result with empty contact fields where appropriate, attempted sources, and `needs_human_review=true`.
- **False-positive risk:** outreach to the wrong person is worse than missing a few accounts. I would bias toward human review for ambiguous company matches, stale-looking records, personal contact data without clear business relevance, or conflicting source evidence.

## Privacy / compliance

I would only use sources allowed by the business and only collect the minimum contact data needed for payment outreach.

- Do use public or contractually permitted business data sources and the mocked sources in this challenge.
- Do preserve provenance so a human can audit where a value came from.
- Do mark unverifiable or low-confidence contacts for review instead of inventing missing data.
- Do not scrape real websites, bypass access controls, use personal social profiles, infer private emails, or enrich beyond the stated business purpose without explicit approval.
- Do not store unnecessary personal data, sensitive notes, or data unrelated to the payment collection workflow.

## Clarifying questions

1. **Which decision-maker persona should win when multiple plausible contacts exist?**
   - Why it matters: role priority drives ranking. An owner, CFO, accounts payable manager, and office manager can all be reasonable, but the best outreach target depends on the business process.
   - Default assumption: prioritize owner, then CFO/finance, then accounts payable, then office manager, then generic business contact.
   - What changes if answered: role weights, acceptable fallback roles, and the human-review threshold for non-target roles would change.

2. **Which source types and contact channels are allowed for outreach?**
   - Why it matters: privacy and compliance boundaries determine which providers we can use and whether email, phone, generic inboxes, or named contacts are acceptable.
   - Default assumption: use only public or mocked business sources, no personal social scraping, no guessed emails, and no unverifiable personal phone numbers.
   - What changes if answered: provider adapters, channel filtering, provenance requirements, and confidence caps would change.

3. **What confidence threshold should gate automated outreach versus human review?**
   - Why it matters: the acceptable tradeoff between recall and false positives determines whether we send, review, or suppress a contact.
   - Default assumption: use a conservative threshold and send any below-threshold, missing, or conflicting result to human review.
   - What changes if answered: scoring cutoffs, `needs_human_review` behavior, and reporting of cannot-verify states would change.
