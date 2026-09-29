"""Dashboard visualizer for Day 13 Monitoring & LLMOps.
Reads data/logs.jsonl and renders a 6-panel overview chart matching config/dashboard.yaml.
Saves image directly to submission/evidence/11-dashboard-overview.png.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np


def load_logs(log_path: Path) -> list[dict]:
    if not log_path.exists():
        return []
    records = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def generate_dashboard(
    log_path: Path = Path("data/logs.jsonl"),
    output_path: Path = Path("submission/evidence/11-dashboard-overview.png"),
) -> None:
    records = load_logs(log_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Filter events
    requests = [r for r in records if r.get("event") == "request_received"]
    responses = [r for r in records if r.get("event") == "response_sent"]
    failures = [r for r in records if r.get("event") == "request_failed"]

    # Calculate metrics
    latencies = [r["latency_ms"] for r in responses if "latency_ms" in r]
    ttfts = [r["ttft_ms"] for r in responses if "ttft_ms" in r]
    costs = [r["cost_usd"] for r in responses if "cost_usd" in r]
    tokens_in = [r["tokens_in"] for r in responses if "tokens_in" in r]
    tokens_out = [r["tokens_out"] for r in responses if "tokens_out" in r]
    qualities = [r["quality_score"] for r in responses if "quality_score" in r]

    # Retrieval success
    retrieval_events = [
        r for r in records if r.get("tool_name") == "retrieval" and "tool_success" in r
    ]
    retrieval_success_count = sum(1 for r in retrieval_events if r.get("tool_success") is True)
    retrieval_total = len(retrieval_events) or 1
    retrieval_rate = (retrieval_success_count / retrieval_total) * 100

    total_reqs = len(requests) or (len(responses) + len(failures)) or 1
    total_failures = len(failures)
    error_rate = (total_failures / total_reqs) * 100

    p50_lat = np.percentile(latencies, 50) if latencies else 0.0
    p95_lat = np.percentile(latencies, 95) if latencies else 0.0
    p99_lat = np.percentile(latencies, 99) if latencies else 0.0
    p95_ttft = np.percentile(ttfts, 95) if ttfts else 0.0
    total_cost = sum(costs)
    avg_quality = np.mean(qualities) if qualities else 0.0

    # Set up dark/clean monitoring theme
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.patch.set_facecolor("#0f172a")

    title_color = "#f8fafc"
    subtitle_color = "#94a3b8"
    grid_color = "#334155"
    text_color = "#e2e8f0"

    fig.suptitle(
        "K4-L3A Day 13 Monitoring & LLMOps — System Health Dashboard (Last 60m)",
        fontsize=18,
        fontweight="bold",
        color=title_color,
        y=0.98,
    )

    for row in axes:
        for ax in row:
            ax.set_facecolor("#1e293b")
            ax.tick_params(colors=text_color, labelsize=9)
            ax.grid(True, linestyle="--", alpha=0.4, color=grid_color)
            for spine in ax.spines.values():
                spine.set_color("#475569")

    # Panel 1: Latency & TTFT
    ax1 = axes[0, 0]
    metrics_labels = ["P50 Lat", "P95 Lat", "P99 Lat", "TTFT P95"]
    metrics_vals = [p50_lat, p95_lat, p99_lat, p95_ttft]
    bars1 = ax1.bar(metrics_labels, metrics_vals, color=["#38bdf8", "#818cf8", "#c084fc", "#f472b6"], width=0.55)
    ax1.axhline(3000, color="#ef4444", linestyle="--", linewidth=1.5, label="SLO Threshold (3000ms)")
    ax1.set_title("1. Latency percentiles & TTFT (ms)", color=title_color, fontsize=12, fontweight="semibold")
    ax1.set_ylabel("Latency (ms)", color=subtitle_color, fontsize=10)
    ax1.legend(loc="upper right", facecolor="#1e293b", edgecolor="#475569", labelcolor=text_color, fontsize=8)
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, yval + 10, f"{yval:.1f}ms", ha="center", va="bottom", color=text_color, fontsize=9, fontweight="bold")
    ax1.set_ylim(0, max(max(metrics_vals, default=100) * 1.3, 3500))

    # Panel 2: Traffic
    ax2 = axes[0, 1]
    traffic_labels = ["Total Requests", "Successful (200)", "Failed (500)"]
    traffic_vals = [total_reqs, len(responses), len(failures)]
    bars2 = ax2.bar(traffic_labels, traffic_vals, color=["#0ea5e9", "#10b981", "#ef4444"], width=0.5)
    ax2.axhline(1, color="#eab308", linestyle="--", linewidth=1.5, label="Min Traffic Threshold (1 req/min)")
    ax2.set_title("2. Request Traffic (Volume & Status)", color=title_color, fontsize=12, fontweight="semibold")
    ax2.set_ylabel("Requests", color=subtitle_color, fontsize=10)
    ax2.legend(loc="upper right", facecolor="#1e293b", edgecolor="#475569", labelcolor=text_color, fontsize=8)
    for bar in bars2:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2, yval + 0.1, f"{int(yval)}", ha="center", va="bottom", color=text_color, fontsize=9, fontweight="bold")
    ax2.set_ylim(0, max(traffic_vals, default=10) * 1.35)

    # Panel 3: Errors & Retrieval Success
    ax3 = axes[0, 2]
    categories = ["Error Rate (%)", "Retrieval Success (%)"]
    values = [error_rate, retrieval_rate]
    colors = ["#ef4444" if error_rate > 2.0 else "#10b981", "#10b981" if retrieval_rate >= 90.0 else "#f59e0b"]
    bars3 = ax3.bar(categories, values, color=colors, width=0.45)
    ax3.axhline(2.0, color="#ef4444", linestyle="--", linewidth=1.2, label="Error Max (2%)")
    ax3.axhline(90.0, color="#3b82f6", linestyle=":", linewidth=1.2, label="Retrieval Min (90%)")
    ax3.set_title("3. Errors & Retrieval Success Rate (%)", color=title_color, fontsize=12, fontweight="semibold")
    ax3.set_ylabel("Percentage (%)", color=subtitle_color, fontsize=10)
    ax3.set_ylim(0, 115)
    ax3.legend(loc="lower right", facecolor="#1e293b", edgecolor="#475569", labelcolor=text_color, fontsize=8)
    for bar in bars3:
        yval = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2, yval + 1.5, f"{yval:.1f}%", ha="center", va="bottom", color=text_color, fontsize=9, fontweight="bold")

    # Panel 4: Cost
    ax4 = axes[1, 0]
    cum_costs = np.cumsum(costs) if costs else [0]
    ax4.plot(range(1, len(cum_costs) + 1), cum_costs, marker="o", color="#10b981", linewidth=2, label="Cumulative Cost ($)")
    ax4.axhline(2.5, color="#ef4444", linestyle="--", linewidth=1.5, label="Budget Limit ($2.50)")
    ax4.set_title("4. Cost Over Time (USD)", color=title_color, fontsize=12, fontweight="semibold")
    ax4.set_xlabel("Request Sequence", color=subtitle_color, fontsize=10)
    ax4.set_ylabel("USD ($)", color=subtitle_color, fontsize=10)
    ax4.legend(loc="upper left", facecolor="#1e293b", edgecolor="#475569", labelcolor=text_color, fontsize=8)
    ax4.text(
        0.95, 0.15,
        f"Total: ${total_cost:.4f}\nAvg: ${np.mean(costs) if costs else 0:.4f}",
        transform=ax4.transAxes,
        ha="right", va="bottom",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#0f172a", edgecolor="#475569"),
        color=text_color, fontsize=9,
    )
    ax4.set_ylim(0, max(2.8, max(cum_costs, default=0) * 1.3))

    # Panel 5: Tokens
    ax5 = axes[1, 1]
    tot_in = sum(tokens_in)
    tot_out = sum(tokens_out)
    token_bars = ax5.bar(["Tokens In", "Tokens Out", "Total Tokens"], [tot_in, tot_out, tot_in + tot_out], color=["#60a5fa", "#a78bfa", "#34d399"], width=0.5)
    ax5.axhline(50000, color="#ef4444", linestyle="--", linewidth=1.5, label="Threshold (50,000)")
    ax5.set_title("5. Input & Output Tokens (Total)", color=title_color, fontsize=12, fontweight="semibold")
    ax5.set_ylabel("Tokens", color=subtitle_color, fontsize=10)
    ax5.legend(loc="upper right", facecolor="#1e293b", edgecolor="#475569", labelcolor=text_color, fontsize=8)
    for bar in token_bars:
        yval = bar.get_height()
        ax5.text(bar.get_x() + bar.get_width()/2, yval + 10, f"{int(yval):,}", ha="center", va="bottom", color=text_color, fontsize=9, fontweight="bold")
    ax5.set_ylim(0, max(tot_in + tot_out + 500, 2000) * 1.3)

    # Panel 6: Quality
    ax6 = axes[1, 2]
    if qualities:
        ax6.plot(range(1, len(qualities) + 1), qualities, marker="s", color="#38bdf8", linewidth=1.8, label="Score per Req")
        ax6.axhline(avg_quality, color="#a78bfa", linestyle="-.", linewidth=1.5, label=f"Mean: {avg_quality:.2f}")
    ax6.axhline(0.75, color="#f59e0b", linestyle="--", linewidth=1.5, label="Quality Guardrail (0.75)")
    ax6.set_title("6. Quality Proxy Score (0.0 – 1.0)", color=title_color, fontsize=12, fontweight="semibold")
    ax6.set_xlabel("Request Sequence", color=subtitle_color, fontsize=10)
    ax6.set_ylabel("Quality Score", color=subtitle_color, fontsize=10)
    ax6.set_ylim(0, 1.15)
    ax6.legend(loc="lower right", facecolor="#1e293b", edgecolor="#475569", labelcolor=text_color, fontsize=8)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(output_path, dpi=160, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"Dashboard saved successfully: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate 6-panel monitoring dashboard")
    parser.add_argument("--logs", type=Path, default=Path("data/logs.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("submission/evidence/11-dashboard-overview.png"))
    args = parser.parse_args()
    generate_dashboard(args.logs, args.output)


if __name__ == "__main__":
    main()
