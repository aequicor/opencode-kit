"""
Enhanced observability system for agent executions.
Generates structured logs and metrics reports.
"""

import datetime
import json
from pathlib import Path
from typing import Optional


class MetricsCollector:
    def __init__(self, store_dir: Optional[Path] = None):
        self._dir = store_dir or Path(".opencode/metrics")
        self._events: list[dict] = []

    def log_event(self, event_type: str, agent: str, details: dict):
        self._events.append(
            {
                "type": event_type,
                "agent": agent,
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "details": details,
            }
        )

    def log_anti_loop(self, agent: str, symptom: str, action: str):
        self.log_event(
            "anti_loop",
            agent,
            {
                "symptom": symptom,
                "action_taken": action,
            },
        )

    def log_hitl(self, agent: str, gate: str, description: str, outcome: str):
        self.log_event(
            "hitl",
            agent,
            {
                "gate": gate,
                "description": description,
                "outcome": outcome,
            },
        )

    def log_error(self, agent: str, error_type: str, message: str, file: str = ""):
        self.log_event(
            "error",
            agent,
            {
                "error_type": error_type,
                "message": message,
                "file": file,
            },
        )

    def log_token_usage(self, agent: str, model: str, input_tokens: int, output_tokens: int):
        self.log_event(
            "token_usage",
            agent,
            {
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        )

    def save(self) -> Optional[Path]:
        if not self._dir:
            return None
        self._dir.mkdir(parents=True, exist_ok=True)
        today = datetime.date.today().isoformat()
        log_file = self._dir / f"events-{today}.json"

        existing = []
        if log_file.exists():
            existing = json.loads(log_file.read_text(encoding="utf-8"))

        existing.extend(self._events)
        log_file.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        self._events.clear()
        return log_file

    def generate_report(self, days: int = 7) -> str:
        if not self._dir or not self._dir.exists():
            return "# Metrics Report\n\nNo data collected yet."

        all_events = []
        for log_file in sorted(self._dir.glob("events-*.json")):
            all_events.extend(json.loads(log_file.read_text(encoding="utf-8")))

        cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        recent = [
            e for e in all_events if datetime.datetime.fromisoformat(e["timestamp"]) >= cutoff
        ]

        if not recent:
            return "# Metrics Report\n\nNo events in the last {days} days."

        anti_loops = [e for e in recent if e["type"] == "anti_loop"]
        hitls = [e for e in recent if e["type"] == "hitl"]
        errors = [e for e in recent if e["type"] == "error"]
        token_events = [e for e in recent if e["type"] == "token_usage"]

        total_input = sum(e["details"].get("input_tokens", 0) for e in token_events)
        total_output = sum(e["details"].get("output_tokens", 0) for e in token_events)

        lines = [
            f"# Metrics Report ({days} days)",
            f"**Generated:** {datetime.datetime.utcnow().isoformat()}",
            f"**Total events:** {len(recent)}",
            "",
            "## Token Usage",
            f"- Total input: {total_input:,} tokens",
            f"- Total output: {total_output:,} tokens",
            f"- Total: {total_input + total_output:,} tokens",
            "",
            "## Anti-Loop Events",
            f"- Count: {len(anti_loops)}",
        ]

        if anti_loops:
            for e in anti_loops[:10]:
                d = e["details"]
                lines.append(f"  - @{e['agent']}: {d['symptom']} → {d['action_taken']}")

        lines.extend(
            [
                "",
                "## HITL Events",
                f"- Count: {len(hitls)}",
            ]
        )
        if hitls:
            for e in hitls[:10]:
                d = e["details"]
                lines.append(f"  - {d['gate']}: {d['description']} → {d['outcome']}")

        lines.extend(
            [
                "",
                "## Errors",
                f"- Count: {len(errors)}",
            ]
        )
        if errors:
            for e in errors[:10]:
                d = e["details"]
                lines.append(f"  - @{e['agent']}: {d['error_type']} — {d['message']}")

        return "\n".join(lines)


_global_metrics: Optional[MetricsCollector] = None


def get_metrics(store_dir: Optional[Path] = None) -> MetricsCollector:
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = MetricsCollector(store_dir=store_dir)
    return _global_metrics
