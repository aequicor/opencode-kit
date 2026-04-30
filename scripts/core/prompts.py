"""
Prompt versioning — tracks prompt changes with version tags and changelog.
"""

import datetime
from pathlib import Path
from typing import Optional

PROMPT_REGISTRY = {
    "agents": ".opencode/agents/",
    "skills": ".opencode/skills/",
    "shared": ".opencode/_shared.md",
    "commands": ".opencode/commands/",
    "planning": ".planning/",
    "agm": "AGENTS.md",
    "claude": "CLAUDE.md",
}


class PromptVersion:
    def __init__(
        self,
        name: str,
        version: str,
        date: str,
        author: str,
        changes: list[str],
        file_path: str,
    ):
        self.name = name
        self.version = version
        self.date = date
        self.author = author
        self.changes = changes
        self.file_path = file_path

    def to_changelog_entry(self) -> str:
        lines = [
            f"### [{self.version}] — {self.name} — {self.date}",
            f"- **File:** `{self.file_path}`",
            f"- **Author:** {self.author}",
        ]
        for change in self.changes:
            lines.append(f"  - {change}")
        return "\n".join(lines)


def get_current_prompt_versions(kit_root: Path) -> dict[str, str]:
    versions = {}
    version_file = kit_root / ".opencode" / "prompts" / "VERSIONS.md"
    if not version_file.exists():
        return versions

    current_section = None
    for line in version_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("## "):
            current_section = line[3:]
        elif line.startswith("- ") and ": " in line and current_section:
            key, val = line[2:].split(": ", 1)
            versions[f"{current_section}/{key.strip()}"] = val.strip()
    return versions


def bump_prompt_version(
    kit_root: Path,
    prompt_name: str,
    changes: list[str],
    author: str = "PromptEngineer",
) -> PromptVersion:
    version_file = kit_root / ".opencode" / "prompts" / "VERSIONS.md"
    version_file.parent.mkdir(parents=True, exist_ok=True)

    current_versions = get_current_prompt_versions(kit_root)
    current = current_versions.get(prompt_name, "0.0.0")

    parts = [int(x) for x in current.split(".")]
    parts[-1] += 1
    new_version = ".".join(str(p) for p in parts)

    date = datetime.date.today().isoformat()

    mapping = {
        "agm": "AGENTS.md",
        "claude": "CLAUDE.md",
    }

    for section, path in PROMPT_REGISTRY.items():
        if prompt_name.startswith(section + "/"):
            name = prompt_name[len(section) + 1 :]
            file_path = f"{path}{name}.md" if section in ("agents", "skills", "commands") else path
            break
    else:
        file_path = prompt_name

    if prompt_name in mapping:
        file_path = mapping[prompt_name]

    return PromptVersion(
        name=prompt_name,
        version=new_version,
        date=date,
        author=author,
        changes=changes,
        file_path=file_path,
    )
