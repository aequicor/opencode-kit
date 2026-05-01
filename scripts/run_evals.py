#!/usr/bin/env python3
"""
opencode-kit eval runner.
Runs evaluation suites against agent outputs.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.core.evaluation import load_suite


def run_evals(suites_dir: Path, output_dir: Path):
    if not suites_dir.exists():
        print(f"No eval suites found in {suites_dir}")
        sys.exit(1)

    suite_count = 0
    case_count = 0
    passed_count = 0

    all_results = []

    for yaml_file in sorted(suites_dir.glob("*.yaml")):
        suite = load_suite(yaml_file)
        if not suite:
            continue

        suite_count += 1
        results = suite.run()
        suite.print_report(results)

        case_count += len(results)
        passed_count += sum(1 for r in results if r.passed)

        all_results.extend(r.to_dict() for r in results)

    output_dir.mkdir(parents=True, exist_ok=True)

    import json

    report = {
        "suites": suite_count,
        "cases": case_count,
        "passed": passed_count,
        "failed": case_count - passed_count,
        "pass_rate": round(passed_count / case_count * 100, 1) if case_count else 0,
        "details": all_results,
    }

    import datetime

    report_file = output_dir / f"eval-report-{datetime.date.today().isoformat()}.json"
    report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nReport saved: {report_file}")
    print(f"Summary: {passed_count}/{case_count} passed ({report['pass_rate']}%)")


def main():
    parser = argparse.ArgumentParser(description="Run opencode-kit eval suites")
    parser.add_argument(
        "--suites", default="kit/.opencode/evals", help="Path to eval suites directory"
    )
    parser.add_argument(
        "--output", default=".opencode/metrics", help="Output directory for reports"
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    suites_path = project_root / args.suites
    output_path = project_root / args.output

    run_evals(suites_path, output_path)


if __name__ == "__main__":
    main()
