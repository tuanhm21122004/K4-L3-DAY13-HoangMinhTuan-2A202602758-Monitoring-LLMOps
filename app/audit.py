"""Audit logging system for security, compliance, and governance.
Provides tamper-evident hash chaining and structured compliance recording.
"""
from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_LOG_PATH = Path(os.getenv("AUDIT_LOG_PATH", "data/audit.jsonl"))
_LAST_RECORD_HASH: str | None = None


def _get_last_hash() -> str | None:
    global _LAST_RECORD_HASH
    if _LAST_RECORD_HASH is not None:
        return _LAST_RECORD_HASH
    if not AUDIT_LOG_PATH.exists():
        return None
    lines = [line.strip() for line in AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return None
    try:
        last = json.loads(lines[-1])
        _LAST_RECORD_HASH = last.get("record_hash")
        return _LAST_RECORD_HASH
    except Exception:
        return None


def calculate_hash(record_dict: dict[str, Any]) -> str:
    # Hash everything except record_hash
    clean = {k: v for k, v in record_dict.items() if k != "record_hash"}
    encoded = json.dumps(clean, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def emit_audit_event(
    event_type: str,
    severity: str,
    actor: dict[str, str],
    action: str,
    resource: dict[str, Any],
    status: str = "SUCCESS",
    correlation_id: str | None = None,
    compliance_tags: list[str] | None = None,
) -> dict[str, Any]:
    global _LAST_RECORD_HASH
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    prev_hash = _get_last_hash()

    record = {
        "audit_id": f"aud-{uuid.uuid4().hex[:12]}",
        "ts": datetime.now(timezone.utc).isoformat(),
        "correlation_id": correlation_id,
        "event_type": event_type,
        "severity": severity,
        "actor": actor,
        "action": action,
        "resource": resource,
        "status": status,
        "compliance_tags": compliance_tags or ["Decree13-VN-Art9", "GDPR-Art6"],
        "prev_hash": prev_hash,
    }
    record_hash = calculate_hash(record)
    record["record_hash"] = record_hash
    _LAST_RECORD_HASH = record_hash

    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record


def audit_pii_detected(
    user_id_hash: str,
    client_ip: str,
    correlation_id: str,
    pii_types: list[str],
) -> dict[str, Any]:
    return emit_audit_event(
        event_type="pii_detected_and_redacted",
        severity="WARNING",
        actor={"user_id_hash": user_id_hash, "role": "end_user", "client_ip": client_ip},
        action="REDACT",
        resource={
            "type": "user_prompt",
            "id": correlation_id,
            "details": {"detected_pii_categories": pii_types},
        },
        status="SUCCESS",
        correlation_id=correlation_id,
        compliance_tags=["Decree13-VN-Art9-PII-Protection", "PCI-DSS-Req3-Cardholder-Data"],
    )


def audit_incident_toggle(
    incident_name: str,
    action: str,  # "ENABLE" or "DISABLE"
    actor_id: str = "operator",
    client_ip: str = "127.0.0.1",
) -> dict[str, Any]:
    return emit_audit_event(
        event_type="incident_state_changed",
        severity="WARNING",
        actor={"user_id_hash": actor_id, "role": "admin", "client_ip": client_ip},
        action=action,
        resource={"type": "incident_injector", "id": incident_name},
        status="SUCCESS",
        compliance_tags=["SOC2-CC7.2-Security-Configuration"],
    )
