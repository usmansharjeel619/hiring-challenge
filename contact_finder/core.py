from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


CONFIDENCE_THRESHOLD = 70
PROVIDER_ORDER = ("registry", "listing", "enrichment")
OUTPUT_FIELDS = (
    "company_name",
    "mailing_address",
    "contact_name",
    "contact_role",
    "contact_email_or_phone",
    "confidence_score",
    "source",
    "needs_human_review",
)

GENERIC_EMAIL_PREFIXES = {
    "admin",
    "billing",
    "contact",
    "hello",
    "info",
    "office",
    "sales",
    "support",
}

NAME_ALIASES = {
    "bob": "robert",
    "rob": "robert",
    "dan": "daniel",
}

TITLE_OR_ROLE_TOKENS = {
    "dr",
    "mr",
    "mrs",
    "ms",
    "manager",
    "owner",
}


@dataclass(frozen=True)
class ContactResult:
    company_name: str
    mailing_address: str
    contact_name: str
    contact_role: str
    contact_email_or_phone: str
    confidence_score: int
    source: str
    needs_human_review: bool

    def as_csv_row(self) -> dict[str, str | int]:
        return {
            "company_name": self.company_name,
            "mailing_address": self.mailing_address,
            "contact_name": self.contact_name,
            "contact_role": self.contact_role,
            "contact_email_or_phone": self.contact_email_or_phone,
            "confidence_score": self.confidence_score,
            "source": self.source,
            "needs_human_review": "true" if self.needs_human_review else "false",
        }


class MockProvider:
    def __init__(self, responses: Mapping[str, Mapping[str, Any]]) -> None:
        self._responses = responses

    @classmethod
    def from_path(cls, path: Path) -> "MockProvider":
        with path.open(encoding="utf-8") as file:
            responses = json.load(file)
        return cls(responses)

    def lookup(self, company_name: str) -> Mapping[str, Any]:
        response = self._responses.get(company_name)
        if isinstance(response, Mapping):
            return response
        return {}


def find_contact(
    company_name: str,
    mailing_address: str,
    evidence: Mapping[str, Any],
    threshold: int = CONFIDENCE_THRESHOLD,
) -> ContactResult:
    score = score_evidence(evidence)
    source = source_summary(evidence)
    needs_review = score < threshold

    if needs_review:
        return ContactResult(
            company_name=company_name,
            mailing_address=mailing_address,
            contact_name="",
            contact_role="",
            contact_email_or_phone="",
            confidence_score=score,
            source=source,
            needs_human_review=True,
        )

    registry = _provider(evidence, "registry")
    listing = _provider(evidence, "listing")
    enrichment = _provider(evidence, "enrichment")

    return ContactResult(
        company_name=company_name,
        mailing_address=mailing_address,
        contact_name=_best_name(registry, listing),
        contact_role=_best_role(registry, listing),
        contact_email_or_phone=_best_contact_channel(enrichment, listing),
        confidence_score=score,
        source=source,
        needs_human_review=False,
    )


def score_evidence(evidence: Mapping[str, Any]) -> int:
    present_sources = [
        provider_name
        for provider_name in PROVIDER_ORDER
        if _provider(evidence, provider_name)
    ]
    if not present_sources:
        return 0

    registry = _provider(evidence, "registry")
    listing = _provider(evidence, "listing")
    enrichment = _provider(evidence, "enrichment")

    score = 0
    conflict = False

    registry_name = _clean(registry.get("name"))
    registry_role = _clean(registry.get("role"))
    listing_name = _clean(listing.get("name"))
    listing_phone = _clean(listing.get("phone"))
    enrichment_email = _clean(enrichment.get("email"))
    enrichment_phone = _clean(enrichment.get("phone"))
    provider_confidence = _int_or_zero(enrichment.get("provider_confidence"))

    if registry_name:
        score += 25
        score += _role_weight(registry_role)

    if listing_name:
        score += 10
        score += _role_weight(_listing_role(listing_name))

    if listing_phone:
        score += 20

    if enrichment_email or enrichment_phone:
        score += round(provider_confidence * 0.35)
        if provider_confidence >= 80:
            score += 12
        elif provider_confidence >= 70:
            score += 8
        elif provider_confidence < 50:
            score -= 5

    if len(present_sources) >= 3:
        score += 14
    elif len(present_sources) == 2:
        score += 8

    if registry_name and listing_name:
        if names_agree(registry_name, listing_name):
            score += 15
        else:
            score -= 12
            conflict = True

    if listing_phone and enrichment_phone and _normalize_phone(listing_phone) == _normalize_phone(enrichment_phone):
        score += 10

    best_name = _best_name(registry, listing)
    if enrichment_email and best_name and email_matches_name(enrichment_email, best_name):
        score += 6

    if enrichment_email and is_generic_email(enrichment_email) and not best_name:
        score -= 12

    score = _apply_confidence_caps(score, set(present_sources), provider_confidence, conflict, listing_name)
    return max(0, min(100, score))


def names_agree(left: str, right: str) -> bool:
    left_tokens = _name_tokens(left)
    right_tokens = _name_tokens(right)
    if not left_tokens or not right_tokens:
        return False
    if left_tokens == right_tokens:
        return True

    left_first, left_last = left_tokens[0], left_tokens[-1]
    right_first, right_last = right_tokens[0], right_tokens[-1]
    if left_last != right_last:
        return False

    return left_first == right_first or left_first[0] == right_first[0]


def email_matches_name(email: str, name: str) -> bool:
    local_part = email.split("@", 1)[0].lower()
    local_tokens = [token for token in re.split(r"[^a-z]+", local_part) if token]
    name_tokens = _name_tokens(name)
    if not local_tokens or not name_tokens:
        return False

    first_name = name_tokens[0]
    last_name = name_tokens[-1]
    return (
        first_name in local_tokens
        or last_name in local_tokens
        or any(token.startswith(first_name[0]) for token in local_tokens)
        and last_name in local_tokens
    )


def is_generic_email(email: str) -> bool:
    prefix = email.split("@", 1)[0].lower()
    return prefix in GENERIC_EMAIL_PREFIXES


def source_summary(evidence: Mapping[str, Any]) -> str:
    sources: list[str] = []
    for provider_name in PROVIDER_ORDER:
        provider_data = _provider(evidence, provider_name)
        source_url = _clean(provider_data.get("source_url"))
        if source_url:
            sources.append(f"{provider_name}:{source_url}")
    return "; ".join(sources) if sources else "none"


def run(input_path: Path, output_path: Path, mock_path: Path) -> list[ContactResult]:
    provider = MockProvider.from_path(mock_path)
    results: list[ContactResult] = []

    with input_path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        for row in reader:
            company_name = _clean(row.get("company_name"))
            mailing_address = _clean(row.get("mailing_address"))
            results.append(
                find_contact(
                    company_name=company_name,
                    mailing_address=mailing_address,
                    evidence=provider.lookup(company_name),
                )
            )

    if output_path.parent != Path("."):
        output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(result.as_csv_row() for result in results)

    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Find traceable B2B contacts from mocked providers.")
    parser.add_argument("--input", required=True, type=Path, help="Input companies CSV path.")
    parser.add_argument("--output", required=True, type=Path, help="Output contacts CSV path.")
    parser.add_argument(
        "--mocks",
        default=Path("challenge/mocks/enrichment_responses.json"),
        type=Path,
        help="Mock provider response JSON path.",
    )
    args = parser.parse_args(argv)

    results = run(input_path=args.input, output_path=args.output, mock_path=args.mocks)
    reviewed = sum(1 for result in results if result.needs_human_review)
    print(f"Wrote {len(results)} rows to {args.output} ({reviewed} need human review).")
    return 0


def _apply_confidence_caps(
    score: int,
    present_sources: set[str],
    provider_confidence: int,
    conflict: bool,
    listing_name: str,
) -> int:
    if len(present_sources) == 1:
        return min(score, 55)

    if present_sources == {"listing", "enrichment"} and (provider_confidence < 70 or not listing_name):
        score = min(score, 68)

    if conflict:
        score = min(score, 68)

    if present_sources == {"registry", "listing"}:
        score = min(score, 74)

    if present_sources == {"registry", "enrichment"}:
        score = min(score, 84)

    return score


def _provider(evidence: Mapping[str, Any], provider_name: str) -> Mapping[str, Any]:
    provider_data = evidence.get(provider_name)
    if isinstance(provider_data, Mapping):
        return provider_data
    return {}


def _best_name(registry: Mapping[str, Any], listing: Mapping[str, Any]) -> str:
    registry_role = _clean(registry.get("role")).lower()
    registry_name = _clean(registry.get("name"))
    listing_name = _clean(listing.get("name"))

    if registry_name and registry_role != "registered agent":
        return registry_name
    return _clean_listing_name(listing_name) or registry_name


def _best_role(registry: Mapping[str, Any], listing: Mapping[str, Any]) -> str:
    registry_role = _clean(registry.get("role"))
    if registry_role and registry_role.lower() != "registered agent":
        return registry_role

    listing_role = _listing_role(_clean(listing.get("name")))
    return listing_role if listing_role != "Unknown" else "Business contact"


def _best_contact_channel(enrichment: Mapping[str, Any], listing: Mapping[str, Any]) -> str:
    return (
        _clean(enrichment.get("email"))
        or _clean(enrichment.get("phone"))
        or _clean(listing.get("phone"))
    )


def _listing_role(name: str) -> str:
    if "manager" in name.lower():
        return "Manager"
    return "Unknown"


def _role_weight(role: str) -> int:
    normalized = role.lower()
    if "accounts payable" in normalized or normalized == "ap" or "ap manager" in normalized:
        return 18
    if any(word in normalized for word in ("owner", "founder", "president", "principal")):
        return 14
    if any(word in normalized for word in ("cfo", "finance", "controller", "bookkeeper")):
        return 12
    if "office manager" in normalized:
        return 8
    if normalized == "manager":
        return 6
    return 0


def _name_tokens(name: str) -> list[str]:
    without_parentheticals = re.sub(r"\([^)]*\)", " ", name.lower())
    raw_tokens = re.split(r"[^a-z]+", without_parentheticals)
    tokens = []
    for token in raw_tokens:
        if not token or token in TITLE_OR_ROLE_TOKENS:
            continue
        tokens.append(NAME_ALIASES.get(token, token))
    return tokens


def _clean_listing_name(name: str) -> str:
    return re.sub(r"\s*\([^)]*\)", "", _clean(name)).strip()


def _normalize_phone(phone: str) -> str:
    return re.sub(r"\D+", "", phone)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
