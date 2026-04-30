#!/usr/bin/env python3
"""
opencode-kit apply script.
Renders templates from kit/ and copies them into the target project.

Usage:
    python3 scripts/apply.py --manifest my-project.yaml --target /path/to/project
    python3 scripts/apply.py --manifest my-project.yaml --target /path/to/project --dry-run
    python3 scripts/apply.py --manifest my-project.yaml --target /path/to/project --merge
"""

import argparse
import datetime
import os
import re
import shutil
import sys
from pathlib import Path


# ─────────────────────────────────────────────
# YAML loading (with helpful error on missing pyyaml)
# ─────────────────────────────────────────────

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


# ─────────────────────────────────────────────
# CREDENTIAL CHECK
# ─────────────────────────────────────────────

_LOOKS_LIKE_KEY = re.compile(r'[A-Za-z0-9_\-]{32,}')

def _check_credentials(manifest: dict) -> None:
    """Abort if manifest contains what looks like a real API key value."""
    provider = manifest.get("provider", {})
    base_url = provider.get("base_url", "")
    api_key_env = provider.get("api_key_env", "")

    # api_key_env should be a short env var name, not a real key
    if api_key_env and _LOOKS_LIKE_KEY.match(api_key_env) and len(api_key_env) > 30:
        print(f"ERROR: provider.api_key_env looks like an actual API key: {api_key_env!r}")
        print("  Put the ENVIRONMENT VARIABLE NAME here, not the actual key.")
        print("  Example: api_key_env: ROUTERAI_OPENCODE")
        sys.exit(1)

    # Check MCP sections
    for mcp_name, mcp_cfg in manifest.get("mcp", {}).items():
        for field in ("api_key", "token", "secret", "password"):
            val = mcp_cfg.get(field, "")
            if val and _LOOKS_LIKE_KEY.match(str(val)) and len(str(val)) > 20:
                print(f"ERROR: mcp.{mcp_name}.{field} looks like a real secret: {str(val)[:8]}...")
                print("  Use api_key_env to reference an environment variable name instead.")
                sys.exit(1)


# ─────────────────────────────────────────────
# CONTEXT BUILDING
# ─────────────────────────────────────────────

def _build_module_table(modules: list) -> str:
    """Build the Markdown module table for _shared.md."""
    header = "| Module | Gradle module | Docs | Responsibility |\n"
    separator = "|--------|---------------|------|----------------|\n"
    rows = []
    for m in modules:
        gradle = m.get("gradle_module") or "—"
        rows.append(
            f"| `{m['name']}` | `{gradle}` | `{m['docs_path']}` | {m.get('responsibility', '')} |"
        )
    return header + separator + "\n".join(rows)


def _build_source_table(modules: list) -> str:
    """Build Gradle source roots table for FILE_STRUCTURE.md."""
    header = "| Module | Gradle task | Source root |\n"
    separator = "|--------|-------------|-------------|\n"
    rows = []
    for m in modules:
        gradle = m.get("gradle_module") or "—"
        rows.append(f"| {m['name']} | `{gradle}` | `{m['source_root']}` |")
    return header + separator + "\n".join(rows)


def _build_test_table(modules: list) -> str:
    """Build test roots table for FILE_STRUCTURE.md."""
    header = "| Module | Test root |\n"
    separator = "|--------|-----------|\n"
    rows = []
    for m in modules:
        rows.append(f"| `{m['name']}` | `{m['test_root']}` |")
    return header + separator + "\n".join(rows)


def _build_module_build_commands(modules: list, stack: dict) -> str:
    """Build module-specific build command examples for agent prompts."""
    build = stack.get("build_command", "./gradlew")
    lines = []
    for m in modules:
        gradle = m.get("gradle_module")
        if gradle:
            lines.append(f"{build} {gradle}:build")
        else:
            lines.append(f"# build command for {m['name']}: {build} build")
    return "\n".join(lines)


def _build_color_table(colors: list) -> str:
    """Build Designer color palette table."""
    if not colors:
        return "| Color | HEX | Purpose |\n|-------|-----|---------|\n| (fill in your project colors) | `#000000` | — |"
    header = "| Color | HEX | Purpose |\n"
    separator = "|-------|-----|------------------|\n"
    rows = [f"| {c['name']} | `{c['hex']}` | {c['purpose']} |" for c in colors]
    return header + separator + "\n".join(rows)


def _build_forbidden_list(patterns: list) -> str:
    """Build forbidden patterns bullet list for AGENTS.md."""
    return "\n".join(f"- {p}" for p in patterns)


def _build_lsp_block(lsp: dict) -> str:
    """Build the LSP JSON block for opencode.json."""
    if not lsp.get("enabled", False):
        return ""
    command = lsp.get("command", "")
    extensions = lsp.get("extensions", [])
    ext_json = ", ".join(f'"{e}"' for e in extensions)
    lang = command.replace("-lsp", "").replace("_lsp", "") or "default"
    return f'''  "lsp": {{
    "{lang}": {{
      "command": [
        "{command}"
      ],
      "extensions": [
        {ext_json}
      ]
    }}
  }},'''


def _build_module_docs_list(modules: list) -> str:
    """Build module docs paths list."""
    return "\n".join(f"- `{m['docs_path']}`" for m in modules)


def _build_module_names_list(modules: list) -> str:
    """Build comma-separated module names for agent prompts."""
    return " / ".join(m["name"] for m in modules)


def build_context(manifest: dict) -> dict:
    """Build the full rendering context from the manifest."""
    project = manifest.get("project", {})
    stack = manifest.get("stack", {})
    modules = manifest.get("modules", [])
    provider = manifest.get("provider", {})
    models = manifest.get("models", {})
    mcp = manifest.get("mcp", {})
    lsp = manifest.get("lsp", {})
    ui = manifest.get("ui", {})
    code_quality = manifest.get("code_quality", {})

    provider_name = provider.get("name", "routerai")
    # Provider ID for the JSON key: strip spaces, lowercase
    provider_id = provider_name.lower().replace(" ", "_").replace("-", "_")

    context7_cfg = mcp.get("context7", {})
    knowledge_cfg = mcp.get("knowledge", {})
    serena_cfg = mcp.get("serena", {})

    ui_framework = ui.get("framework") or ""
    colors = ui.get("colors", [])
    platforms = ui.get("platforms", [])

    default_model = models.get("default", "moonshotai/kimi-k2.6")
    coder_model = models.get("coder", "qwen/qwen3-coder-next")
    reviewer_model = models.get("reviewer", "deepseek/deepseek-v4-pro")
    designer_model = models.get("designer") or coder_model

    return {
        # Project
        "PROJECT_NAME": project.get("name", "My Project"),
        "PROJECT_DESCRIPTION": project.get("description", ""),

        # Stack
        "BUILD_COMMAND": stack.get("build_command", "./gradlew"),
        "COMPILE_COMMAND": stack.get("compile_command", "./gradlew compileKotlin"),
        "LINT_COMMAND": stack.get("lint_command", "./gradlew detekt ktlintCheck"),
        "TEST_COMMAND_TEMPLATE": stack.get("test_command", "./gradlew :[module]:test"),
        "STACK_DESCRIPTION": f"{project.get('name', 'Project')} — {stack.get('language', 'Kotlin')} stack",

        # Modules
        "MODULE_TABLE": _build_module_table(modules),
        "MODULE_SOURCE_TABLE": _build_source_table(modules),
        "MODULE_TEST_TABLE": _build_test_table(modules),
        "MODULE_BUILD_COMMANDS": _build_module_build_commands(modules, stack),
        "MODULE_NAMES_LIST": _build_module_names_list(modules),
        "MODULE_DOCS_LIST": _build_module_docs_list(modules),

        # Provider
        "PROVIDER_ID": provider_id,
        "PROVIDER_NAME": provider_name,
        "PROVIDER_BASE_URL": provider.get("base_url", "https://routerai.ru/api/v1"),
        "PROVIDER_API_KEY_ENV": provider.get("api_key_env", "PROVIDER_API_KEY"),

        # Models
        "DEFAULT_MODEL": default_model,
        "CODER_MODEL": coder_model,
        "REVIEWER_MODEL": reviewer_model,
        "DESIGNER_MODEL": designer_model,

        # Runtime
        "ISO_TIMESTAMP_PLACEHOLDER": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),

        # MCP
        "CONTEXT7_ENABLED": str(context7_cfg.get("enabled", True)).lower(),
        "CONTEXT7_API_KEY_ENV": context7_cfg.get("api_key_env", "CONTEXT7_API_KEY"),
        "KNOWLEDGE_ENABLED": str(knowledge_cfg.get("enabled", True)).lower(),
        "KNOWLEDGE_URL": knowledge_cfg.get("url", "http://localhost:8085/mcp"),
        "SERENA_ENABLED": str(serena_cfg.get("enabled", True)).lower(),

        # LSP
        "LSP_BLOCK": _build_lsp_block(lsp),

        # UI
        "UI_FRAMEWORK": ui_framework,
        "PLATFORMS": ", ".join(platforms),
        "COLOR_TABLE": _build_color_table(colors),

        # Code quality
        "FORBIDDEN_PATTERNS_LIST": _build_forbidden_list(
            code_quality.get("forbidden_patterns", [])
        ),
    }


# ─────────────────────────────────────────────
# TEMPLATE RENDERING
# ─────────────────────────────────────────────

def render(template_text: str, context: dict) -> str:
    """Replace all {{KEY}} placeholders with context values."""
    result = template_text
    for key, value in context.items():
        result = result.replace("{{" + key + "}}", str(value))
    return result


def check_unresolved(rendered: str, source_path: str) -> list:
    """Return list of unresolved {{PLACEHOLDER}} tokens."""
    return re.findall(r'\{\{[A-Z_]+\}\}', rendered)


# ─────────────────────────────────────────────
# FILE OPERATIONS
# ─────────────────────────────────────────────

def get_target_path(kit_file: Path, kit_root: Path, target_root: Path) -> Path:
    """
    Map kit/ path to target path, stripping .template suffix.
    kit/opencode.json.template → target/opencode.json
    kit/.opencode/agents/Main.md → target/.opencode/agents/Main.md
    """
    rel = kit_file.relative_to(kit_root)
    parts = list(rel.parts)
    # Strip .template from the last part
    if parts[-1].endswith(".template"):
        parts[-1] = parts[-1][: -len(".template")]
    return target_root / Path(*parts)


def collect_files(kit_root: Path) -> list:
    """Collect all files in kit/ (not directories)."""
    return [f for f in kit_root.rglob("*") if f.is_file()]


# ─────────────────────────────────────────────
# DOCS SCAFFOLD
# ─────────────────────────────────────────────

def create_docs_scaffold(modules: list, target: Path, dry_run: bool) -> list:
    """Create empty docs/<module>/{requirements,spec,guidelines,plans,reports} directories."""
    created = []
    subdirs = ["requirements", "spec", "guidelines", "plans", "reports", "documentation"]
    for m in modules:
        docs_path = m.get("docs_path", f"docs/{m['name']}/")
        for sub in subdirs:
            dir_path = target / docs_path / sub
            if not dir_path.exists():
                created.append(str(dir_path))
                if not dry_run:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    # Create a .gitkeep so git tracks empty dirs
                    (dir_path / ".gitkeep").touch()
    return created


# ─────────────────────────────────────────────
# MAIN APPLY LOGIC
# ─────────────────────────────────────────────

def apply(manifest_path: str, target_dir: str, dry_run: bool, merge: bool) -> None:
    kit_root = Path(__file__).parent.parent / "kit"
    target = Path(target_dir)
    manifest_file = Path(manifest_path)

    if not manifest_file.exists():
        print(f"ERROR: manifest not found: {manifest_path}")
        sys.exit(1)

    if not kit_root.exists():
        print(f"ERROR: kit/ directory not found at {kit_root}")
        sys.exit(1)

    # Load manifest
    with open(manifest_file) as f:
        manifest = yaml.safe_load(f)

    # Safety check
    _check_credentials(manifest)

    # Build rendering context
    context = build_context(manifest)

    # Collect files
    kit_files = collect_files(kit_root)

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Applying opencode-kit to: {target}")
    print(f"Manifest: {manifest_path}")
    print(f"Project: {context['PROJECT_NAME']}")
    print(f"Modules: {context['MODULE_NAMES_LIST']}")
    print()

    warnings = []
    actions = []

    for kit_file in sorted(kit_files):
        target_path = get_target_path(kit_file, kit_root, target)
        is_template = kit_file.name.endswith(".template")
        action = "RENDER" if is_template else "COPY"

        # Check for existing file
        if target_path.exists() and not merge:
            print(f"  SKIP (exists) {target_path.relative_to(target)}")
            continue
        elif target_path.exists() and merge:
            action = f"{action} (merge/overwrite)"

        actions.append((action, kit_file, target_path, is_template))
        print(f"  {action:20s} → {target_path.relative_to(target) if target.exists() else target_path}")

    # Create docs scaffold
    modules = manifest.get("modules", [])
    scaffold_dirs = create_docs_scaffold(modules, target, dry_run=True)
    if scaffold_dirs:
        print(f"\n  CREATE DIRS ({len(scaffold_dirs)} doc directories):")
        for d in scaffold_dirs[:10]:
            print(f"    {d}")
        if len(scaffold_dirs) > 10:
            print(f"    ... and {len(scaffold_dirs) - 10} more")

    if dry_run:
        print(f"\n[DRY RUN] {len(actions)} files would be written. Run without --dry-run to apply.")
        _print_checklist(context)
        return

    # Apply for real
    print("\nApplying...")
    unresolved_report = []

    for action, kit_file, target_path, is_template in actions:
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if is_template:
            text = kit_file.read_text(encoding="utf-8")
            rendered = render(text, context)
            unresolved = check_unresolved(rendered, str(kit_file))
            if unresolved:
                unresolved_report.append((str(target_path.relative_to(target)), unresolved))
            target_path.write_text(rendered, encoding="utf-8")
        else:
            shutil.copy2(kit_file, target_path)

    # Create docs scaffold for real
    create_docs_scaffold(modules, target, dry_run=False)

    print(f"\n✅ Done. {len(actions)} files written.")

    if unresolved_report:
        print("\n⚠️  Unresolved placeholders (fill these manually):")
        for file, tokens in unresolved_report:
            print(f"  {file}: {', '.join(tokens)}")

    _print_checklist(context)


def _print_checklist(context: dict) -> None:
    print("\n" + "─" * 60)
    print("POST-INSTALL CHECKLIST")
    print("─" * 60)
    print(f"\n1. Set environment variables before running opencode:")
    print(f"   export {context['PROVIDER_API_KEY_ENV']}=<your_api_key>")
    if context.get("CONTEXT7_ENABLED") == "true":
        print(f"   export {context['CONTEXT7_API_KEY_ENV']}=<your_context7_key>")
    print(f"\n2. Verify opencode.json — apiKey must use {{env:VAR}} syntax, NOT a real key")
    print(f"\n3. Check .opencode/_shared.md → Project Context section matches your project")
    print(f"\n4. Run compile to verify build works:")
    print(f"   {context['COMPILE_COMMAND']}")
    print(f"\n5. Add .env to .gitignore if not already there")
    if context.get("KNOWLEDGE_ENABLED") == "true":
        print(f"\n6. Start KnowledgeOS at {context['KNOWLEDGE_URL']} before running opencode")
    print()


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Apply opencode-kit to a target project")
    parser.add_argument("--manifest", required=True, help="Path to manifest YAML file")
    parser.add_argument("--target", required=True, help="Path to target project directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    parser.add_argument("--merge", action="store_true",
                        help="Overwrite existing files (default: skip existing)")
    args = parser.parse_args()

    apply(
        manifest_path=args.manifest,
        target_dir=args.target,
        dry_run=args.dry_run,
        merge=args.merge,
    )


if __name__ == "__main__":
    main()
