#!/usr/bin/env python3
"""Generate a reproducible inventory of the legacy Kiwi patch without applying it."""

from collections import defaultdict
from pathlib import Path
import subprocess

PATCH = "543d5c3b5be0dd6bd84b7f2fb05618093d0494f8"
OUT = Path("kiwi-port-inventory.md")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True, stderr=subprocess.STDOUT)


def classify(path: str) -> str:
    if path.startswith("third_party/blink/") or path.startswith("net/url_request/"):
        return "Blink / network behavior (high risk)"
    if path.startswith("extensions/") or path.startswith("chrome/browser/extensions/"):
        return "Extensions support (high priority, security-sensitive)"
    if path.startswith("chrome/android/") or path.startswith("chrome/browser/ui/android/") or path.startswith("components/browser_ui/"):
        return "Android UI / settings"
    if path.startswith("chrome/browser/") or path.startswith("chrome/renderer/") or path.startswith("content/"):
        return "Browser core / navigation / rendering"
    if path.startswith("base/"):
        return "Base API compatibility"
    if path.endswith((".grd", ".grdp", ".gni", ".gn")) or "/res_" in path or "/drawable-" in path or "/mipmap-" in path:
        return "Build wiring / resources / strings"
    return "Other / requires manual review"


def main() -> None:
    git("cat-file", "-e", f"{PATCH}^{{commit}}")
    rows = [line.split("\\t", 1) for line in git("diff", "--name-status", f"{PATCH}^", PATCH).splitlines()]
    groups = defaultdict(list)
    for row in rows:
        status, path = row[0], row[-1]
        groups[classify(path)].append((status, path))

    lines = [
        "# Kiwi to Chromium 155 patch inventory",
        "",
        f"- Legacy patch: {PATCH}",
        f"- Changed paths: **{len(rows)}**",
        "- Inventory only: this script does not apply code, build Chromium, or claim an APK is available.",
        "",
        "## Summary by area",
        "",
        "| Area | Files |",
        "|---|---:|",
    ]
    for area, files in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0])):
        lines.append(f"| {area} | {len(files)} |")
    for area, files in sorted(groups.items(), key=lambda item: item[0]):
        lines += ["", f"## {area}", ""]
        for status, path in sorted(files, key=lambda item: item[1]):
            lines.append(f"- {status} {path}")
    OUT.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
    print(f"Wrote {OUT} with {len(rows)} changed paths across {len(groups)} areas.")


if __name__ == "__main__":
    main()
