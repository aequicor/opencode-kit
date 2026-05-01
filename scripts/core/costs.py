"""
Cost tracking and budget management for agent executions.
Tracks token usage, estimates costs, enforces per-session budgets.
"""

import datetime
from pathlib import Path
from typing import Optional


class ModelPricing:
    def __init__(self, input_per_1k: float, output_per_1k: float):
        self.input_per_1k = input_per_1k
        self.output_per_1k = output_per_1k

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (input_tokens / 1000) * self.input_per_1k + (
            output_tokens / 1000
        ) * self.output_per_1k


DEFAULT_PRICING = {
    "moonshotai/kimi-k2.6": ModelPricing(2.0, 8.0),
    "qwen/qwen3-coder-next": ModelPricing(0.5, 2.0),
    "deepseek/deepseek-v4-pro": ModelPricing(1.0, 4.0),
    "openai/gpt-5.4": ModelPricing(3.0, 15.0),
    "openai/gpt-5.1": ModelPricing(2.5, 10.0),
}


SESSION_BUDGET = 5.0
COST_BREACH_THRESHOLD = 5.0


class CostEntry:
    __slots__ = ("agent_name", "model", "input_tokens", "output_tokens", "cost", "timestamp")

    def __init__(self, agent_name: str, model: str, input_tokens: int, output_tokens: int):
        self.agent_name = agent_name
        self.model = model
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        pricing = DEFAULT_PRICING.get(model, ModelPricing(1.0, 4.0))
        self.cost = pricing.estimate_cost(input_tokens, output_tokens)
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)

    def to_dict(self) -> dict:
        return {
            "agent": self.agent_name,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": round(self.cost, 6),
            "timestamp": self.timestamp.isoformat(),
        }


class CostTracker:
    def __init__(self, budget: float = SESSION_BUDGET, store_path: Optional[Path] = None):
        self._entries: list[CostEntry] = []
        self._budget = budget
        self._store_path = store_path

    def record(
        self, agent_name: str, model: str, input_tokens: int, output_tokens: int
    ) -> CostEntry:
        entry = CostEntry(agent_name, model, input_tokens, output_tokens)
        self._entries.append(entry)
        return entry

    def total_cost(self) -> float:
        return sum(e.cost for e in self._entries)

    def remaining_budget(self) -> float:
        return max(0.0, self._budget - self.total_cost())

    def is_over_budget(self) -> bool:
        return self.total_cost() >= self._budget

    def cost_by_agent(self) -> dict:
        breakdown = {}
        for e in self._entries:
            breakdown[e.agent_name] = breakdown.get(e.agent_name, 0.0) + e.cost
        return breakdown

    def cost_by_model(self) -> dict:
        breakdown = {}
        for e in self._entries:
            breakdown[e.model] = breakdown.get(e.model, 0.0) + e.cost
        return breakdown

    def summary(self) -> dict:
        return {
            "total_cost": round(self.total_cost(), 4),
            "budget": self._budget,
            "remaining": round(self.remaining_budget(), 4),
            "entries": len(self._entries),
            "by_agent": {k: round(v, 4) for k, v in self.cost_by_agent().items()},
            "by_model": {k: round(v, 4) for k, v in self.cost_by_model().items()},
        }

    def print_summary(self):
        s = self.summary()
        print("\n" + "\u2500" * 60)
        print("COST TRACKER")
        print("\u2500" * 60)
        print(f"  Budget: ${s['budget']:.2f}")
        print(f"  Spent:  ${s['total_cost']:.4f}")
        print(f"  Remaining: ${s['remaining']:.4f}")
        print(f"  Operations: {s['entries']}")
        if s["by_agent"]:
            print("\n  By Agent:")
            for agent, cost in sorted(s["by_agent"].items(), key=lambda x: -x[1]):
                print(f"    {agent}: ${cost:.4f}")
        if s["by_model"]:
            print("\n  By Model:")
            for model, cost in sorted(s["by_model"].items(), key=lambda x: -x[1]):
                print(f"    {model}: ${cost:.4f}")
        if self.is_over_budget():
            print(f"\n  \u26a0\ufe0f  BUDGET EXCEEDED (\u2265 ${self._budget:.2f})")
        print()

    def save(self) -> Optional[Path]:
        if not self._store_path:
            return None
        data = {
            "summary": self.summary(),
            "history": [e.to_dict() for e in self._entries],
            "saved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        import json

        self._store_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return self._store_path


_global_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker(budget: float = SESSION_BUDGET) -> CostTracker:
    global _global_cost_tracker
    if _global_cost_tracker is None:
        _global_cost_tracker = CostTracker(budget=budget)
    return _global_cost_tracker
