#!/usr/bin/env python3
"""Unit tests for the legacy Kiwi patch inventory categorizer."""

import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).with_name("kiwi_port_inventory.py")
SPEC = importlib.util.spec_from_file_location("kiwi_port_inventory", SCRIPT)
INVENTORY = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(INVENTORY)


class ClassifyPathTest(unittest.TestCase):
    def test_blink_and_network_are_high_risk(self):
        self.assertEqual(
            INVENTORY.classify("third_party/blink/renderer/core/foo.cc"),
            "Blink / network behavior (high risk)",
        )
        self.assertEqual(
            INVENTORY.classify("net/url_request/request.cc"),
            "Blink / network behavior (high risk)",
        )

    def test_extensions_are_security_sensitive(self):
        self.assertEqual(
            INVENTORY.classify("extensions/browser/api/foo.cc"),
            "Extensions support (high priority, security-sensitive)",
        )
        self.assertEqual(
            INVENTORY.classify("chrome/browser/extensions/foo.cc"),
            "Extensions support (high priority, security-sensitive)",
        )

    def test_android_ui_paths(self):
        self.assertEqual(
            INVENTORY.classify("chrome/android/java/Foo.java"),
            "Android UI / settings",
        )
        self.assertEqual(
            INVENTORY.classify("components/browser_ui/foo.cc"),
            "Android UI / settings",
        )

    def test_core_and_base_paths(self):
        self.assertEqual(
            INVENTORY.classify("content/browser/foo.cc"),
            "Browser core / navigation / rendering",
        )
        self.assertEqual(INVENTORY.classify("base/foo.cc"), "Base API compatibility")

    def test_build_resources_and_unknown_paths(self):
        self.assertEqual(
            INVENTORY.classify("chrome/app/generated_resources.grd"),
            "Build wiring / resources / strings",
        )
        self.assertEqual(INVENTORY.classify("unclassified/file.txt"), "Other / requires manual review")


if __name__ == "__main__":
    unittest.main()
