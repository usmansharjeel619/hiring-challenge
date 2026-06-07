import csv
import tempfile
import unittest
from pathlib import Path

from contact_finder.core import (
    CONFIDENCE_THRESHOLD,
    OUTPUT_FIELDS,
    email_matches_name,
    find_contact,
    names_agree,
    run,
)


class ContactFinderTests(unittest.TestCase):
    def test_agreeing_sources_emit_contact_above_threshold(self) -> None:
        result = find_contact(
            "Cedar Ridge Plumbing LLC",
            "4821 Maple Ave, Lincoln, NE 68504",
            {
                "registry": {
                    "name": "Daniel Ortega",
                    "role": "Owner",
                    "source_url": "mock://registry/ne/cedar-ridge-plumbing",
                },
                "listing": {
                    "name": "Daniel Ortega",
                    "phone": "+1-402-555-0148",
                    "source_url": "mock://listing/cedar-ridge-plumbing",
                },
                "enrichment": {
                    "email": "d.ortega@cedarridgeplumbing.com",
                    "phone": None,
                    "provider_confidence": 84,
                    "source_url": "mock://enrichment/cedar-ridge-plumbing",
                },
            },
        )

        self.assertGreaterEqual(result.confidence_score, CONFIDENCE_THRESHOLD)
        self.assertEqual(result.contact_name, "Daniel Ortega")
        self.assertEqual(result.contact_role, "Owner")
        self.assertEqual(result.contact_email_or_phone, "d.ortega@cedarridgeplumbing.com")
        self.assertFalse(result.needs_human_review)
        self.assertIn("registry:mock://registry/ne/cedar-ridge-plumbing", result.source)
        self.assertIn("listing:mock://listing/cedar-ridge-plumbing", result.source)
        self.assertIn("enrichment:mock://enrichment/cedar-ridge-plumbing", result.source)

    def test_below_threshold_blanks_contact_channel(self) -> None:
        result = find_contact(
            "Sunbelt Roofing Co",
            "7714 Desert Bloom Rd, Mesa, AZ 85207",
            {
                "listing": {
                    "name": None,
                    "phone": "+1-480-555-0133",
                    "source_url": "mock://listing/sunbelt-roofing",
                },
                "enrichment": {
                    "email": "office@sunbeltroofingaz.com",
                    "phone": "+1-480-555-0133",
                    "provider_confidence": 66,
                    "source_url": "mock://enrichment/sunbelt-roofing",
                },
            },
        )

        self.assertLess(result.confidence_score, CONFIDENCE_THRESHOLD)
        self.assertEqual(result.contact_name, "")
        self.assertEqual(result.contact_role, "")
        self.assertEqual(result.contact_email_or_phone, "")
        self.assertTrue(result.needs_human_review)
        self.assertIn("listing:mock://listing/sunbelt-roofing", result.source)

    def test_missing_mock_response_is_cannot_verify(self) -> None:
        result = find_contact("Redwood Cabinetry", "509 Timber Ct, Eugene, OR 97401", {})

        self.assertEqual(result.confidence_score, 0)
        self.assertEqual(result.source, "none")
        self.assertEqual(result.contact_email_or_phone, "")
        self.assertTrue(result.needs_human_review)

    def test_conflicting_names_stay_below_threshold(self) -> None:
        result = find_contact(
            "Coastal Breeze Pool Service",
            "233 Seagrape Way, Sarasota, FL 34236",
            {
                "registry": {
                    "name": "Tina Alvarez",
                    "role": "Manager",
                    "source_url": "mock://registry/fl/coastal-breeze-pool",
                },
                "listing": {
                    "name": "Marcus Webb",
                    "phone": "+1-941-555-0146",
                    "source_url": "mock://listing/coastal-breeze-pool",
                },
            },
        )

        self.assertLess(result.confidence_score, CONFIDENCE_THRESHOLD)
        self.assertEqual(result.contact_email_or_phone, "")
        self.assertTrue(result.needs_human_review)

    def test_name_and_email_matching_helpers_handle_common_variants(self) -> None:
        self.assertTrue(names_agree("Robert Kowalski", "Bob Kowalski"))
        self.assertTrue(names_agree("Sean Murphy", "S. Murphy"))
        self.assertTrue(email_matches_name("g.whitfield@tidewaterph.com", "George Whitfield"))

    def test_cli_run_writes_one_output_row_per_input_company(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "companies.csv"
            output_path = temp_path / "contacts.csv"
            mock_path = Path("challenge/mocks/enrichment_responses.json")
            input_path.write_text(
                "company_name,mailing_address\n"
                'Cedar Ridge Plumbing LLC,"4821 Maple Ave, Lincoln, NE 68504"\n'
                'Redwood Cabinetry,"509 Timber Ct, Eugene, OR 97401"\n',
                encoding="utf-8",
            )

            results = run(input_path=input_path, output_path=output_path, mock_path=mock_path)

            self.assertEqual(len(results), 2)
            with output_path.open(newline="", encoding="utf-8") as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(len(rows), 2)
            self.assertEqual(tuple(rows[0].keys()), OUTPUT_FIELDS)
            self.assertEqual(rows[0]["needs_human_review"], "false")
            self.assertEqual(rows[1]["needs_human_review"], "true")


if __name__ == "__main__":
    unittest.main()
