"""Vendored files are byte-identical to what vendor/SOURCE.md records."""
import hashlib, re, unittest

from scorers.tests.helpers import REPO

VENDOR = REPO / "scorers" / "vendor"


class Vendor(unittest.TestCase):
    def test_hashes(self):
        rows = re.findall(r"^\| `([^`]+)` \| [^|]*\| `([0-9a-f]{64})` \|$|^\| `([^`]+)` \| same lib dir \| `([0-9a-f]{64})` \|$",
                          (VENDOR / "SOURCE.md").read_text(), re.M)
        pairs = [(a or c, b or d) for a, b, c, d in rows]
        self.assertEqual(len(pairs), 10)
        for rel, h in pairs:
            self.assertEqual(hashlib.sha256((VENDOR / rel).read_bytes()).hexdigest(), h, rel)


if __name__ == "__main__":
    unittest.main(verbosity=2)
