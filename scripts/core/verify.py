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
                json.load(f)
        except json.JSONDecodeError as e:
            warnings.append(f"INVALID JSON in opencode.json: {e}")

        content = opencode_json.read_text(encoding="utf-8")
        if looks_like_key(content):
            env_var = context.get("PROVIDER_API_KEY_ENV", "")
            if env_var and f"env:{env_var}" not in content:
                warnings.append(
                    "opencode.json may contain a literal API key \u2014 verify it uses {env:VAR} syntax"
                )

    return warnings
