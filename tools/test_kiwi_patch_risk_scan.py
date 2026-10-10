#!/usr/bin/env python3
"""Unit tests for the legacy Kiwi patch risk scanner."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).with_name("kiwi_patch_risk_scan.py")
SPEC = importlib.util.spec_from_file_location("kiwi_patch_risk_scan", SCRIPT)
SCANNER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SCANNER)


class RiskScanTest(unittest.TestCase):
    def test_detects_unconditional_branch(self):
        findings = SCANNER.scan(
            "diff --git a/a.java b/a.java\n+++ b/a.java\n+if (true) return value;\n"
        )
        self.assertIn(
            ("Unconditional true branch", "a.java", "if (true) return value;"),
            findings,
        )

    def test_detects_boolean_override(self):
        findings = SCANNER.scan(
            "+++ b/feature.cc\n+return enabled || true;\n"
        )
        self.assertIn(
            ("Boolean override", "feature.cc", "return enabled || true;"),
            findings,
        )

    def test_ignores_removed_lines_and_diff_headers(self):
        findings = SCANNER.scan(
            "--- a/old.cc\n+++ b/new.cc\n-if (true) old();\n context();\n"
        )
        self.assertEqual(findings, [])

    def test_tracks_file_names(self):
        findings = SCANNER.scan(
            "+++ b/first.cc\n+GURL url;\n+++ b/second.cc\n+GURL url;\n"
        )
        self.assertEqual([item[1] for item in findings], ["first.cc", "second.cc"])


if __name__ == "__main__":
    unittest.main()
