"""Tests for the series consistency detection logic."""

import unittest

from series_checker.detector import (
    detect_all,
    detect_characters,
    detect_places,
    detect_timeline,
)


class CharacterTests(unittest.TestCase):
    def test_catches_name_variants(self):
        text = "Jon Snow went to the market. John Snow came home."
        findings = detect_characters(text)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].kind, "character")
        self.assertIn("Jon Snow", findings[0].detail)
        self.assertIn("John Snow", findings[0].detail)

    def test_no_conflict_for_consistent_names(self):
        text = "Arya Stark walked to the gate. Arya Stark drew her sword."
        self.assertEqual(detect_characters(text), [])

    def test_close_spelling_flagged(self):
        text = "Daenarys Targaryen ruled. Daenerys Targaryen conquered."
        findings = detect_characters(text)
        self.assertEqual(len(findings), 1)


class PlaceTests(unittest.TestCase):
    def test_catches_place_variants(self):
        text = "She was born in Londdon. She died in London."
        findings = detect_places(text)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].kind, "place")
        self.assertIn("Londdon", findings[0].detail)
        self.assertIn("London", findings[0].detail)

    def test_no_conflict_for_consistent_places(self):
        text = "Winterfell is cold. Winterfell is far north."
        self.assertEqual(detect_places(text), [])


class TimelineTests(unittest.TestCase):
    def test_catches_out_of_order_dates(self):
        text = "In 2024 she left the city. In 2020 she had arrived."
        findings = detect_timeline(text)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].kind, "timeline")
        self.assertIn("2020", findings[0].detail)

    def test_chronological_dates_are_ok(self):
        text = "In 2020 she arrived. In 2024 she left."
        self.assertEqual(detect_timeline(text), [])

    def test_repeated_date_is_not_a_conflict(self):
        text = "In 2020 she arrived. In 2020 she stayed."
        self.assertEqual(detect_timeline(text), [])


class AllTests(unittest.TestCase):
    def test_detect_all_runs_every_check(self):
        text = (
            "Jon Snow left in 2024. John Snow arrived in 2020. "
            "She lived in Londdon and loved London."
        )
        findings = detect_all(text)
        kinds = {f.kind for f in findings}
        self.assertIn("character", kinds)
        self.assertIn("place", kinds)
        self.assertIn("timeline", kinds)

    def test_no_duplicate_across_categories(self):
        text = (
            "Jon Snow left in 2024. John Snow arrived in 2020. "
            "She lived in Londdon and loved London."
        )
        details = [f.detail for f in detect_all(text)]
        self.assertEqual(len(details), len(set(details)))


if __name__ == "__main__":
    unittest.main()
