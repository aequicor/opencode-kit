"""
Telemetry for agent executions.
Tracks timing, cost estimation, and success rates.
"""

import datetime
import json
from pathlib import Path
from typing import Optional


class AgentRun:
    __slots__ = (
        "agent_name",
        "task_id",
        "model",
        "start_time",
        "end_time",
        "status",
        "tokens_used",
        "files_changed",
        "error",
    )

    def __init__(
        self,
        agent_name: str,
        model: str,
        task_id: Optional[str] = None,
    ):
        self.agent_name = agent_name
        self.task_id = task_id
        self.model = model
        self.start_time = datetime.datetime.now(datetime.timezone.utc)
        self.end_time: Optional[datetime.datetime] = None
        self.status = "running"
        self.tokens_used = 0
        self.files_changed = 0
        self.error: Optional[str] = None

    def complete(self, tokens: int = 0, files: int = 0):
        self.end_time = datetime.datetime.now(datetime.timezone.utc)
        self.status = "success"
        self.tokens_used = tokens
        self.files_changed = files

    def fail(self, error: str):
        self.end_time = datetime.datetime.now(datetime.timezone.utc)
        self.status = "failed"
        self.error = error

    def duration_ms(self) -> int:
        if not self.end_time:
            return 0
        return int((self.end_time - self.start_time).total_seconds() * 1000)

    def to_dict(self) -> dict:
        return {
            "agent": self.agent_name,
            "task_id": self.task_id,
            "model": self.model,
            "start": self.start_time.isoformat(),
            "end": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms(),
            "status": self.status,
            "tokens_used": self.tokens_used,
            "files_changed": self.files_changed,
            "error": self.error,
        }


class TelemetryStore:
    def __init__(self, store_path: Optional[Path] = None):
        self._runs: list[AgentRun] = []
        self._store_path = store_path

    def add(self, run: AgentRun):
        self._runs.append(run)

    def save(self) -> Optional[Path]:
        if not self._store_path:
            return None
        data = [r.to_dict() for r in self._runs]
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        self._store_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return self._store_path

    def summary(self) -> dict:
        total = len(self._runs)
        if total == 0:
            return {"total_runs": 0}

        success = sum(1 for r in self._runs if r.status == "success")
        failed = sum(1 for r in self._runs if r.status == "failed")
        total_tokens = sum(r.tokens_used for r in self._runs)
        total_duration_ms = sum(r.duration_ms() for r in self._runs)
        total_files = sum(r.files_changed for r in self._runs)

        return {
            "total_runs": total,
            "success": success,
            "failed": failed,
            "success_rate": round(success / total * 100, 1) if total else 0,
            "total_tokens": total_tokens,
            "total_duration_ms": total_duration_ms,
            "total_files_changed": total_files,
            "avg_tokens_per_run": round(total_tokens / total) if total else 0,
            "avg_duration_ms": round(total_duration_ms / total) if total else 0,
        }

    def print_summary(self):
        s = self.summary()
        if s["total_runs"] == 0:
            return
        print("\n" + "\u2500" * 60)
        print("TELEMETRY SUMMARY")
        print("\u2500" * 60)
        print(f"  Runs: {s['total_runs']} ({s['success']} success, {s['failed']} failed)")
        print(f"  Success rate: {s['success_rate']}%")
        print(f"  Total tokens: {s['total_tokens']}")
        print(f"  Total duration: {s['total_duration_ms']}ms")
        print(f"  Files changed: {s['total_files_changed']}")
        print(f"  Avg tokens/run: {s['avg_tokens_per_run']}")
        print(f"  Avg duration/run: {s['avg_duration_ms']}ms")
        print()

    def agent_breakdown(self) -> dict:
        breakdown = {}
        for r in self._runs:
            if r.agent_name not in breakdown:
                breakdown[r.agent_name] = {
                    "runs": 0,
                    "success": 0,
                    "failed": 0,
                    "tokens": 0,
                    "duration_ms": 0,
                }
            breakdown[r.agent_name]["runs"] += 1
            if r.status == "success":
                breakdown[r.agent_name]["success"] += 1
            else:
                breakdown[r.agent_name]["failed"] += 1
            breakdown[r.agent_name]["tokens"] += r.tokens_used
            breakdown[r.agent_name]["duration_ms"] += r.duration_ms()
        return breakdown


_global_store: Optional[TelemetryStore] = None


def get_telemetry() -> TelemetryStore:
    global _global_store
    if _global_store is None:
        _global_store = TelemetryStore()
    return _global_store


def track_run(agent_name: str, model: str, task_id: Optional[str] = None) -> AgentRun:
    run = AgentRun(agent_name=agent_name, model=model, task_id=task_id)
    get_telemetry().add(run)
    return run
