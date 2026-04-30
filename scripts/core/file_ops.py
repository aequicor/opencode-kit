import re
from pathlib import Path


def render(template_text: str, context: dict) -> str:
    result = template_text
    for key, value in context.items():
        result = result.replace("{{" + key + "}}", str(value))
    return result


def check_unresolved(rendered: str, source_path: str = "") -> list:
    return re.findall(r"\{\{[A-Z_]+\}\}", rendered)


def get_target_path(kit_file: Path, kit_root: Path, target_root: Path) -> Path:
    rel = kit_file.relative_to(kit_root)
    parts = list(rel.parts)

    if parts[-1].endswith(".template"):
        parts[-1] = parts[-1][: -len(".template")]

    if len(parts) >= 2 and parts[0] == "editors":
        parts = parts[2:]

    return target_root / Path(*parts)


def kit_path_to_target(kit_rel_path: str) -> str:
    parts = kit_rel_path.split("/")
    if parts[0] == "kit":
        parts = parts[1:]
    if len(parts) >= 2 and parts[0] == "editors":
        parts = parts[2:]
    if parts[-1].endswith(".template"):
        parts[-1] = parts[-1][: -len(".template")]
    return str(Path(*parts))


def collect_base_files(kit_root: Path) -> list:
    editors_dir = kit_root / "editors"
    nested_dir = kit_root / "nested"
    return [
        f
        for f in kit_root.rglob("*")
        if f.is_file()
        and not str(f).startswith(str(editors_dir))
        and not str(f).startswith(str(nested_dir))
    ]


def collect_editor_files(kit_root: Path, editors: list) -> list:
    files = []
    editors_root = kit_root / "editors"
    for editor in editors:
        editor_dir = editors_root / editor
        if editor_dir.exists():
            files.extend(f for f in editor_dir.rglob("*") if f.is_file())
        else:
            print(f"  WARNING: no editor templates found for '{editor}' (skipping)")
    return files


def create_docs_scaffold(modules: list, target: Path, dry_run: bool) -> list:
    created = []
    subdirs = [
        "requirements",
        "spec",
        "guidelines",
        "plans",
        "reports",
        "documentation",
    ]
    for m in modules:
        docs_path = m.get("docs_path", f"docs/{m['name']}/")
        for sub in subdirs:
            dir_path = target / docs_path / sub
            if not dir_path.exists():
                created.append(str(dir_path))
                if not dry_run:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    (dir_path / ".gitkeep").touch()
    return created


def print_postinstall_checklist(context: dict) -> None:
    print("\n" + "\u2500" * 60)
    print("POST-INSTALL CHECKLIST")
    print("\u2500" * 60)
    print(f"\n1. Set environment variables before running opencode:")
    print(f"   export {context['PROVIDER_API_KEY_ENV']}=<your_api_key>")
    if context.get("CONTEXT7_ENABLED") == "true":
        print(f"   export {context['CONTEXT7_API_KEY_ENV']}=<your_context7_key>")
    print(
        f"\n2. Verify opencode.json \u2014 apiKey must use {{env:VAR}} syntax, NOT a real key"
    )
    print(
        f"\n3. Check .opencode/_shared.md \u2192 Project Context section matches your project"
    )
    print(f"\n4. Run compile to verify build works:")
    print(f"   {context['COMPILE_COMMAND']}")
    print(f"\n5. Add .env to .gitignore if not already there")
    if context.get("KNOWLEDGE_ENABLED") == "true":
        print(
            f"\n6. Start KnowledgeOS at {context['KNOWLEDGE_URL']} before running opencode"
        )
    print()
