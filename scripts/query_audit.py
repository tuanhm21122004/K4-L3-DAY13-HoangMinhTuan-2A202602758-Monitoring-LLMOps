"""Audit Log Query and Verification CLI.
Allows filtering, searching, and cryptographic tamper-detection of audit logs.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.audit import calculate_hash


def load_audit_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def verify_integrity(records: list[dict]) -> tuple[bool, str]:
    if not records:
        return True, "No records to verify."
    prev_hash = None
    for idx, rec in enumerate(records):
        expected_prev = rec.get("prev_hash")
        if expected_prev != prev_hash:
            return False, f"Broken chain at index {idx}: expected prev_hash={prev_hash}, found={expected_prev}"
        stored_hash = rec.get("record_hash")
        computed_hash = calculate_hash(rec)
        if stored_hash != computed_hash:
            return False, f"Tampered record at index {idx}: stored={stored_hash}, computed={computed_hash}"
        prev_hash = stored_hash
    return True, f"All {len(records)} audit records verified successfully (SHA-256 chain intact)."


def main() -> None:
    parser = argparse.ArgumentParser(description="Query and verify LLMOps Audit Trail")
    parser.add_argument("--audit-file", type=Path, default=Path("data/audit.jsonl"))
    parser.add_argument("--verify", action="store_true", help="Verify cryptographic integrity of audit chain")
    parser.add_argument("--event", type=str, help="Filter by event_type")
    parser.add_argument("--severity", type=str, help="Filter by severity (INFO, WARNING, CRITICAL)")
    parser.add_argument("--limit", type=int, default=20, help="Maximum number of records to display")
    args = parser.parse_args()

    records = load_audit_records(args.audit_file)
    print(f"Total audit records found: {len(records)}")

    if args.verify:
        valid, msg = verify_integrity(records)
        status = "PASSED" if valid else "FAILED"
        print(f"[{status}] Integrity Check: {msg}")
        if not valid:
            sys.exit(1)

    filtered = records
    if args.event:
        filtered = [r for r in filtered if r.get("event_type") == args.event]
    if args.severity:
        filtered = [r for r in filtered if r.get("severity") == args.severity]

    print(f"Matching records ({len(filtered)}):")
    for r in filtered[-args.limit:]:
        print(f"[{r.get('ts')}] {r.get('severity')} | {r.get('event_type')} | {r.get('action')} | Actor: {r.get('actor', {}).get('user_id_hash')} | Cid: {r.get('correlation_id')}")


if __name__ == "__main__":
    main()
