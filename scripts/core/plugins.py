"""
Plugin system for opencode-kit.
Allows loading custom agent configurations from external sources.
"""

from pathlib import Path
from typing import Optional

_loaded_plugins: list[dict] = []


class KitPlugin:
    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        agents: Optional[list[Path]] = None,
        skills: Optional[list[Path]] = None,
        commands: Optional[list[Path]] = None,
        profile: Optional[Path] = None,
    ):
        self.name = name
        self.version = version
        self.description = description
        self.agents = agents or []
        self.skills = skills or []
        self.commands = commands or []
        self.profile = profile

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "agents": [str(p) for p in self.agents],
            "skills": [str(p) for p in self.skills],
            "commands": [str(p) for p in self.commands],
            "profile": str(self.profile) if self.profile else None,
        }


def discover_plugins(kit_root: Path) -> list[KitPlugin]:
    plugins_dir = kit_root / ".opencode" / "plugins"
    if not plugins_dir.exists():
        return []

    plugins = []
    for yaml_file in sorted(plugins_dir.glob("*.yaml")):
        try:
            import yaml
            with open(yaml_file) as f:
                data = yaml.safe_load(f)

            if not data or not data.get("name"):
                print(f"  WARNING: skipping invalid plugin: {yaml_file}")
                continue

            plugins.append(
                KitPlugin(
                    name=data["name"],
                    version=data.get("version", "0.0.0"),
                    description=data.get("description", ""),
                    agents=[plugins_dir / a for a in data.get("agents", [])],
                    skills=[plugins_dir / s for s in data.get("skills", [])],
                    commands=[plugins_dir / c for c in data.get("commands", [])],
                    profile=plugins_dir / data["profile"] if data.get("profile") else None,
                )
            )
        except Exception as e:
            print(f"  WARNING: failed to load plugin {yaml_file}: {e}")

    return plugins


def merge_plugin_files(
    kit_root: Path,
    plugin: KitPlugin,
    target: Path,
    dry_run: bool = False,
) -> list[str]:
    created = []
    base = kit_root / ".opencode"

    for agent_path in plugin.agents:
        dest = base / "agents" / agent_path.name
        if not dest.exists() and not dry_run:
            import shutil
            shutil.copy2(agent_path, dest)
            created.append(str(dest))

    for skill_path in plugin.skills:
        skill_dir = skill_path.parent
        dest_dir = base / "skills" / skill_dir.name
        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
            import shutil
            for f in skill_dir.rglob("*"):
                if f.is_file():
                    shutil.copy2(f, dest_dir / f.name)
            created.append(str(dest_dir))

    for cmd_path in plugin.commands:
        dest = base / "commands" / cmd_path.name
        if not dest.exists() and not dry_run:
            import shutil
            shutil.copy2(cmd_path, dest)
            created.append(str(dest))

    return created
