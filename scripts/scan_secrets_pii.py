"""Automated Secret and PII Scanner for CI/CD and pre-commit checks.
Ensures no API keys, tokens, or raw PII are committed to the repository.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

IGNORED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".idea", ".vscode"}
IGNORED_FILES = {".env", "logs_baseline.jsonl", "expected_answers.jsonl", "sample_queries.jsonl"}
# Note: sample_queries.jsonl is the input benchmark that contains synthetic test PII to test redaction.

SECRET_PATTERNS = {
    "langfuse_secret": re.compile(r"sk-lf-[a-zA-Z0-9_-]{20,}"),
    "langfuse_public": re.compile(r"pk-lf-[a-zA-Z0-9_-]{20,}"),
    "openai_api_key": re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    "openrouter_key": re.compile(r"sk-or-v1-[a-zA-Z0-9]{32,}"),
    "generic_secret_assignment": re.compile(r"""(?i)(?:secret|token|password|api_key)\s*=\s*['"][a-zA-Z0-9_=-]{16,}['"]"""),
}

PII_PATTERNS = {
    "raw_email": re.compile(r"\b[A-Za-z0-9._%+-]+@(?!vinuni\.edu\.vn)[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"),
    "raw_phone_vn": re.compile(r"(?<!\d)(?:\+84|0)(?:[ .-]?\d){9}(?!\d)"),
    "raw_cccd": re.compile(r"\b\d{12}\b"),
    "raw_credit_card": re.compile(r"\b(?:\d{4}[- ]?){3}\d{4}\b"),
}


def scan_file(file_path: Path) -> list[str]:
    violations = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    # Check secrets
    for name, pattern in SECRET_PATTERNS.items():
        if pattern.search(content):
            violations.append(f"Secret detected ({name}) in {file_path.relative_to(REPO_ROOT)}")

    # In production logs, check for unredacted PII
    if file_path.name == "logs.jsonl":
        for name, pattern in PII_PATTERNS.items():
            matches = pattern.findall(content)
            # Filter out already redacted tokens like [REDACTED_...]
            real_matches = [m for m in matches if "[REDACTED" not in str(m)]
            if real_matches:
                violations.append(f"Raw PII detected ({name}) in {file_path.relative_to(REPO_ROOT)}")

    return violations


def scan_repo() -> int:
    print("--- Scanning repository for secrets and PII leaks ---")
    total_files = 0
    all_violations = []

    for path in REPO_ROOT.rglob("*"):
        if path.is_file():
            if any(part in IGNORED_DIRS for part in path.parts):
                continue
            if path.name in IGNORED_FILES or path.name.endswith(".pyc") or path.suffix in {".png", ".jpg", ".jpeg"}:
                continue
            total_files += 1
            file_violations = scan_file(path)
            if file_violations:
                all_violations.extend(file_violations)

    print(f"Scanned {total_files} repository files.")
    if all_violations:
        print(f"FAILED: Found {len(all_violations)} violations:")
        for v in all_violations:
            print(f"  - {v}")
        return 1

    print("PASSED: No secrets or raw PII leaks detected.")
    return 0


def main() -> None:
    sys.exit(scan_repo())


if __name__ == "__main__":
    main()
