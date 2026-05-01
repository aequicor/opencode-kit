"""
Agent evaluation framework — benchmark prompts against defined tasks.
"""

import time
from pathlib import Path
from typing import Optional


class EvalCase:
    def __init__(
        self,
        id: str,
        description: str,
        agent: str,
        input: str,
        expected_patterns: list[str],
        forbidden_patterns: Optional[list[str]] = None,
        max_steps: int = 10,
        weight: float = 1.0,
    ):
        self.id = id
        self.description = description
        self.agent = agent
        self.input = input
        self.expected_patterns = expected_patterns
        self.forbidden_patterns = forbidden_patterns or []
        self.max_steps = max_steps
        self.weight = weight


class EvalResult:
    def __init__(self, case: EvalCase):
        self.case = case
        self.passed = False
        self.score = 0.0
        self.duration_ms = 0
        self.output = ""
        self.details: list[str] = []

    def to_dict(self) -> dict:
        return {
            "case_id": self.case.id,
            "agent": self.case.agent,
            "passed": self.passed,
            "score": self.score,
            "duration_ms": self.duration_ms,
            "details": self.details,
        }


class EvalSuite:
    def __init__(self, name: str, cases: list[EvalCase]):
        self.name = name
        self.cases = cases

    def run(self, agent_runner=None) -> list[EvalResult]:
        results = []
        total_weight = sum(c.weight for c in self.cases)

        for case in self.cases:
            result = EvalResult(case)
            start = time.time()

            if agent_runner:
                try:
                    output = agent_runner(case)
                    result.output = output

                    all_matched = True
                    for pattern in case.expected_patterns:
                        if pattern not in output:
                            all_matched = False
                            result.details.append(f"Expected pattern not found: {pattern}")
                    for pattern in case.forbidden_patterns:
                        if pattern in output:
                            all_matched = False
                            result.details.append(f"Forbidden pattern found: {pattern}")

                    result.passed = all_matched
                    result.score = (case.weight / total_weight * 100) if all_matched else 0.0
                except Exception as e:
                    result.details.append(f"Error: {e}")
            else:
                result.details.append("No agent runner provided — dry evaluation")

            result.duration_ms = int((time.time() - start) * 1000)
            results.append(result)

        return results

    def print_report(self, results: list[EvalResult]):
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        total_score = sum(r.score for r in results)

        print(f"\nEvaluation Suite: {self.name}")
        print("=" * 60)
        print(f"  Total: {len(results)} | Passed: {passed} | Failed: {failed}")
        print(f"  Score: {total_score:.1f}%")
        print(f"  Duration: {sum(r.duration_ms for r in results)}ms")
        print()

        for r in results:
            status = "PASS" if r.passed else "FAIL"
            print(f"  [{status}] {r.case.id} — {r.case.description}")
            for d in r.details:
                print(f"    {d}")
        print()


def load_suite(suite_file: Path) -> Optional[EvalSuite]:
    if not suite_file.exists():
        return None

    try:
        import yaml

        with open(suite_file) as f:
            data = yaml.safe_load(f)

        cases = []
        for c in data.get("cases", []):
            cases.append(
                EvalCase(
                    id=c.get("id", "unnamed"),
                    description=c.get("description", ""),
                    agent=c.get("agent", "Main"),
                    input=c.get("input", ""),
                    expected_patterns=c.get("expected_patterns", []),
                    forbidden_patterns=c.get("forbidden_patterns", []),
                    max_steps=c.get("max_steps", 10),
                    weight=c.get("weight", 1.0),
                )
            )

        return EvalSuite(name=data.get("name", "Unnamed Suite"), cases=cases)
    except Exception as e:
        print(f"ERROR loading suite {suite_file}: {e}")
        return None
