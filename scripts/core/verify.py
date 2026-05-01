import json
from pathlib import Path

from .credentials import looks_like_key


def verify_output(target: Path, context: dict) -> list:
    warnings = []

    agents_dir = target / ".opencode" / "agents"
    expected_agents = [
        "Main.md",
        "CodeWriter.md",
        "CodeReviewer.md",
        "BugFixer.md",
        "debugger.md",
        "QA.md",
        "Designer.md",
        "PromptEngineer.md",
        "AutoApprover.md",
    ]
    for agent in expected_agents:
        if not (agents_dir / agent).exists():
            warnings.append(f"MISSING agent: .opencode/agents/{agent}")

    opencode_json = target / "opencode.json"
    if opencode_json.exists():
        try:
            with open(opencode_json, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            warnings.append(f"INVALID JSON in opencode.json: {e}")
            data = None

        if data is not None:

            def _scan_values(obj, path: str = "$") -> list[str]:
                found = []
                if isinstance(obj, str):
                    if looks_like_key(obj):
                        found.append(f"{path}: {obj[:20]}{'...' if len(obj) > 20 else ''}")
                elif isinstance(obj, dict):
                    for k, v in obj.items():
                        if k.lower() in ("apikey", "api_key", "key", "token", "secret", "password"):
                            continue
                        found.extend(_scan_values(v, f"{path}.{k}"))
                elif isinstance(obj, list):
                    for i, v in enumerate(obj):
                        found.extend(_scan_values(v, f"{path}[{i}]"))
                return found

            leaked = _scan_values(data)
            for entry in leaked:
                warnings.append(
                    f"opencode.json may contain a literal API key at {entry} \u2014 verify it uses {{env:VAR}} syntax"
                )

    return warnings
