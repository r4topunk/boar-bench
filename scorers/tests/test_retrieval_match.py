"""Pure test (no fixtures): gold titles vs library-prefixed pack titles (night 2026-10-01: recall@5 read 0.03 because
"Singapore" never matched "Wikivoyage: Singapore")."""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scorers.retrieval import _match


class TestGoldTitleMatch(unittest.TestCase):
    def test_bare_gold_matches_any_library(self):
        self.assertTrue(_match("Singapore", {"title": "Wikivoyage: Singapore"}))
        self.assertTrue(_match("Singapore", {"title": "Singapore"}))
        self.assertTrue(_match("EIP-1559", {"title": "Ethereum EIPs/ERCs: EIP-1559"}))

    def test_prefixed_gold_requires_its_library(self):
        self.assertTrue(_match("Wikivoyage: Singapore", {"title": "Wikivoyage: Singapore"}))
        self.assertFalse(_match("Wikivoyage: Singapore", {"title": "Singapore"}))

    def test_no_partial_or_subpage_match(self):
        self.assertFalse(_match("Singapore", {"title": "Wikivoyage: Singapore/Orchard"}))
        self.assertFalse(_match("Singapore", {"title": "History of Singapore"}))

    def test_section_still_required(self):
        self.assertTrue(_match("Singapore#Get in", {"title": "Wikivoyage: Singapore", "section": "Get in"}))
        self.assertFalse(_match("Singapore#Get in", {"title": "Wikivoyage: Singapore", "section": "Eat"}))


if __name__ == "__main__":
    unittest.main()
