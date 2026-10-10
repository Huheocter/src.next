#!/usr/bin/env python3
"""Report risky added lines in the legacy Kiwi integration patch.

This is a triage aid, not a vulnerability scanner. Every match needs human review.
"""
from pathlib import Path
import re
import subprocess

PATCH = "543d5c3b5be0dd6bd84b7f2fb05618093d0494f8"
OUT = Path("kiwi-patch-risk-scan.md")

RULES = (
    ("Unconditional true branch", re.compile(r"\bif\s*\(\s*true\s*\)")),
    ("Boolean override", re.compile(r"\|\|\s*true\b")),
    ("Disabled code block", re.compile(r"^\s*#if\s+0\b")),
    ("Permission / validation path", re.compile(r"permission|validat|allowlist|allow_list", re.I)),
    ("URL / request handling", re.compile(r"URLRequest|url_request|LoadUrlParams|GURL|request", re.I)),
    ("Build / feature gate", re.compile(r"\b(BUILD.gn|\.gni|base::Feature|FeatureList|ENABLE_\w+)\b")),
)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True, stderr=subprocess.STDOUT)


def scan(diff: str) -> list[tuple[str, str, str]]:
    path = "(unknown path)"
    findings = []
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        added = line[1:]
        for label, pattern in RULES:
            if pattern.search(added):
                findings.append((label, path, added.strip()))
    return findings


def main() -> None:
    git("cat-file", "-e", f"{PATCH}^{{commit}}")
    diff = git("diff", "--unified=0", f"{PATCH}^", PATCH)
    findings = scan(diff)
    lines = [
        "# Legacy Kiwi patch: risky-line triage",
        "",
        f"- Patch: {PATCH}",
        f"- Matches: **{len(findings)}**",
        "- Heuristic review queue only; matches are not proof of bugs or exploits.",
        "- Added lines only; inspect surrounding code before porting.",
        "",
        "| Risk flag | File | Added line |",
        "|---|---|---|",
    ]
    for label, path, added in findings:
        safe = added.replace("|", "\\|")
        lines.append(f"| {label} | {path} | {safe} |")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} with {len(findings)} review flags.")


if __name__ == "__main__":
    main()
