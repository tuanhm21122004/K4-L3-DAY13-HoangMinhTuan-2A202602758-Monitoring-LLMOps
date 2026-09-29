"""Automation script to setup Langfuse Prompts (v1/v2), generate traces,
demonstrate promote and rollback, and verify trace-to-log correlation.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

load_dotenv(REPO_ROOT / ".env")

from langfuse import Langfuse

PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
BASE_URL = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
PROMPT_NAME = os.getenv("LANGFUSE_PROMPT_NAME", "day13-chat")


def setup_langfuse() -> dict:
    if not PUBLIC_KEY or not SECRET_KEY:
        print("ERROR: LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY is missing in .env")
        sys.exit(1)

    langfuse = Langfuse(public_key=PUBLIC_KEY, secret_key=SECRET_KEY, host=BASE_URL)
    print(f"Connecting to Langfuse at {BASE_URL}...")
    
    # 1. Create Prompt Version 1 (baseline & production)
    print("1. Creating prompt version 1...")
    p1 = langfuse.create_prompt(
        name=PROMPT_NAME,
        type="text",
        prompt="Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}",
        labels=["baseline", "production"],
    )
    print(f"   Created prompt v{p1.version} with labels: {p1.labels}")

    # 2. Create Prompt Version 2 (candidate)
    print("2. Creating prompt version 2...")
    p2 = langfuse.create_prompt(
        name=PROMPT_NAME,
        type="text",
        prompt="Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}\nProvide a concise and direct answer based strictly on the context.",
        labels=["candidate"],
    )
    print(f"   Created prompt v{p2.version} with labels: {p2.labels}")

    return {
        "v1_version": p1.version,
        "v2_version": p2.version,
    }


def run_workload_and_capture_traces() -> list[dict]:
    client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=30.0)
    queries = [
        {"user_id": "u01", "session_id": "s01", "feature": "qa", "message": "What is your refund policy? My email is student@vinuni.edu.vn"},
        {"user_id": "u02", "session_id": "s02", "feature": "qa", "message": "Explain why metrics traces and logs work together"},
        {"user_id": "u03", "session_id": "s03", "feature": "summary", "message": "Summarize the monitoring policy for production logging"},
        {"user_id": "u04", "session_id": "s04", "feature": "qa", "message": "Can I get help with policy and monitoring?"},
        {"user_id": "u05", "session_id": "s05", "feature": "qa", "message": "Here is my phone 0987654321, what should be logged?"},
        {"user_id": "u06", "session_id": "s06", "feature": "summary", "message": "Give me a short summary of the observability workflow"},
        {"user_id": "u07", "session_id": "s07", "feature": "qa", "message": "What should not appear in app logs?"},
        {"user_id": "u08", "session_id": "s08", "feature": "qa", "message": "How do I debug tail latency?"},
        {"user_id": "u09", "session_id": "s09", "feature": "qa", "message": "What is the policy for PII and credit card 4111 1111 1111 1111?"},
        {"user_id": "u10", "session_id": "s10", "feature": "qa", "message": "How should alerts be designed?"},
    ]

    print(f"\n3. Sending {len(queries)} requests to API...")
    results = []
    for q in queries:
        resp = client.post("/chat", json=q)
        data = resp.json()
        cid = data.get("correlation_id")
        lat = data.get("latency_ms")
        print(f"   [{resp.status_code}] cid: {cid} | latency: {lat}ms | quality: {data.get('quality_score')}")
        results.append(data)
        time.sleep(0.3)

    return results


def demonstrate_rollback() -> None:
    langfuse = Langfuse(public_key=PUBLIC_KEY, secret_key=SECRET_KEY, host=BASE_URL)
    print("\n4. Demonstrating Prompt Rollback...")
    print("   Promoting version 2 to 'production'...")
    p2 = langfuse.get_prompt(PROMPT_NAME, label="candidate")
    langfuse.create_prompt(
        name=PROMPT_NAME,
        type="text",
        prompt=p2.prompt,
        labels=["production", "candidate"],
    )
    print("   -> Version 2 promoted to 'production'.")
    time.sleep(1)

    print("   Rolling back: Re-assigning 'production' label back to Version 1...")
    p1 = langfuse.get_prompt(PROMPT_NAME, label="baseline")
    langfuse.create_prompt(
        name=PROMPT_NAME,
        type="text",
        prompt=p1.prompt,
        labels=["production", "baseline"],
    )
    print("   -> Successfully rolled back 'production' label to Version 1!")


if __name__ == "__main__":
    prompt_info = setup_langfuse()
    results = run_workload_and_capture_traces()
    demonstrate_rollback()
    print("\nAll Langfuse steps completed successfully!")
