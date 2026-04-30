#!/usr/bin/env python3
"""
opencode-kit remote apply script.
Downloads templates from GitHub and renders them into the target project.
No local clone required — this script is self-contained.

Usage:
    python3 apply_remote.py --manifest my-project.yaml --target /path/to/project
    python3 apply_remote.py --manifest my-project.yaml --target /path/to/project --dry-run
    python3 apply_remote.py --manifest my-project.yaml --target /path/to/project --merge

The manifest file must be local (created by the user or AI agent).
All kit templates are fetched from GitHub on the fly.
"""

import argparse
import datetime
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.request
import urllib.error
from pathlib import Path

KIT_REPO = "aequicor/opencode-kit"
KIT_BRANCH = "main"
KIT_RAW_BASE = f"https://raw.githubusercontent.com/{KIT_REPO}/{KIT_BRANCH}"
KIT_API_BASE = (
    f"https://api.github.com/repos/{KIT_REPO}/git/trees/{KIT_BRANCH}?recursive=1"
)

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


_LOOKS_LIKE_KEY = re.compile(r"[A-Za-z0-9_\-]{32,}")


def _check_credentials(manifest: dict) -> None:
    provider = manifest.get("provider", {})
    api_key_env = provider.get("api_key_env", "")
    if api_key_env and _LOOKS_LIKE_KEY.match(api_key_env) and len(api_key_env) > 30:
        print(
            f"ERROR: provider.api_key_env looks like an actual API key: {api_key_env!r}"
        )
        print("  Put the ENVIRONMENT VARIABLE NAME here, not the actual key.")
        print("  Example: api_key_env: ROUTERAI_OPENCODE")
        sys.exit(1)
    for mcp_name, mcp_cfg in manifest.get("mcp", {}).items():
        for field in ("api_key", "token", "secret", "password"):
            val = mcp_cfg.get(field, "")
            if val and _LOOKS_LIKE_KEY.match(str(val)) and len(str(val)) > 20:
                print(
                    f"ERROR: mcp.{mcp_name}.{field} looks like a real secret: {str(val)[:8]}..."
                )
                print(
                    "  Use api_key_env to reference an environment variable name instead."
                )
                sys.exit(1)


def _fetch_url(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(
        url, headers={"User-Agent": "opencode-kit-apply-remote/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"ERROR: Failed to fetch {url} — HTTP {e.code}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"ERROR: Network error fetching {url} — {e.reason}")
        sys.exit(1)


def _fetch_kit_file_list() -> list:
    try:
        data = _fetch_url(KIT_API_BASE)
        tree = json.loads(data)
        if "tree" not in tree:
            print("ERROR: Unexpected GitHub API response — no 'tree' key.")
            print("  You may be rate-limited. Wait a moment and try again.")
            sys.exit(1)
        return [
            entry["path"]
            for entry in tree["tree"]
            if entry["type"] == "blob" and entry["path"].startswith("kit/")
        ]
    except Exception as e:
        print(f"ERROR: Could not list kit files from GitHub API: {e}")
        print("  Falling back to hardcoded file list.")
        return _hardcoded_kit_files()


def _hardcoded_kit_files() -> list:
    return [
        "kit/opencode.json.template",
        "kit/AGENTS.md.template",
        "kit/.opencode/_shared.md.template",
        "kit/.opencode/FILE_STRUCTURE.md.template",
        "kit/.opencode/agents/Main.md.template",
        "kit/.opencode/agents/CodeWriter.md.template",
        "kit/.opencode/agents/CodeReviewer.md.template",
        "kit/.opencode/agents/BugFixer.md.template",
        "kit/.opencode/agents/debugger.md.template",
        "kit/.opencode/agents/QA.md.template",
        "kit/.opencode/agents/Designer.md.template",
        "kit/.opencode/agents/PromptEngineer.md.template",
        "kit/.opencode/commands/new-feature.md",
        "kit/.opencode/commands/resume.md",
        "kit/.opencode/commands/checkpoint.md",
        "kit/.opencode/skills/look-up/SKILL.md",
        "kit/.opencode/skills/bug-retro/SKILL.md",
        "kit/.planning/CURRENT.md.template",
        "kit/.planning/DECISIONS.md.template",
        "kit/docs/_templates/bug-report.md",
        "kit/docs/_templates/test-plan.md",
        "kit/docs/_templates/spec.md",
        "kit/docs/_templates/requirements.md",
    ]


def _build_module_table(modules: list) -> str:
    header = "| Module | Gradle module | Docs | Responsibility |\n"
    separator = "|--------|---------------|------|----------------|\n"
    rows = []
    for m in modules:
        gradle = m.get("gradle_module") or "\u2014"
        rows.append(
            f"| `{m['name']}` | `{gradle}` | `{m['docs_path']}` | {m.get('responsibility', '')} |"
        )
    return header + separator + "\n".join(rows)


def _build_source_table(modules: list) -> str:
    header = "| Module | Gradle task | Source root |\n"
    separator = "|--------|-------------|-------------|\n"
    rows = []
    for m in modules:
        gradle = m.get("gradle_module") or "\u2014"
        rows.append(f"| {m['name']} | `{gradle}` | `{m['source_root']}` |")
    return header + separator + "\n".join(rows)


def _build_test_table(modules: list) -> str:
    header = "| Module | Test root |\n"
    separator = "|--------|----------|\n"
    rows = []
    for m in modules:
        rows.append(f"| `{m['name']}` | `{m['test_root']}` |")
    return header + separator + "\n".join(rows)


def _build_module_build_commands(modules: list, stack: dict) -> str:
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
    if not colors:
        return "| Color | HEX | Purpose |\n|-------|-----|---------|\n| (fill in your project colors) | `#000000` | \u2014 |"
    header = "| Color | HEX | Purpose |\n"
    separator = "|-------|-----|------------------|\n"
    rows = [f"| {c['name']} | `{c['hex']}` | {c['purpose']} |" for c in colors]
    return header + separator + "\n".join(rows)


def _build_forbidden_list(patterns: list) -> str:
    return "\n".join(f"- {p}" for p in patterns)


def _build_formatter_block(stack: dict, formatter_cfg: dict) -> str:
    if not formatter_cfg.get("enabled", False):
        return ""
    fmt_name = formatter_cfg.get("name", stack.get("language", "default") + "-fmt")
    command = formatter_cfg.get("command", [stack.get("build_command", ""), "lint"])
    extensions = formatter_cfg.get("extensions", [])
    ext_json = ", ".join(f'"{e}"' for e in extensions)
    env_block = ""
    if formatter_cfg.get("environment"):
        env_items = []
        for k, v in formatter_cfg.get("environment", {}).items():
            env_items.append(f'        "{k}": "{v}"')
        env_block = ',\n      "environment": {\n' + ",\n".join(env_items) + "\n      }"
    cmd_json = ", ".join(f'"{c}"' for c in command)
    return f'''  "formatter": {{
    "{fmt_name}": {{
      "command": [{cmd_json}],
      "extensions": [{ext_json}]{env_block}
    }}
  }},'''


def _build_lsp_block(lsp: dict) -> str:
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
    return "\n".join(f"- `{m['docs_path']}`" for m in modules)


def _build_module_names_list(modules: list) -> str:
    return " / ".join(m["name"] for m in modules)


def build_context(manifest: dict) -> dict:
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
        "PROJECT_NAME": project.get("name", "My Project"),
        "PROJECT_DESCRIPTION": project.get("description", ""),
        "BUILD_COMMAND": stack.get("build_command", "./gradlew"),
        "COMPILE_COMMAND": stack.get("compile_command", "./gradlew compileKotlin"),
        "LINT_COMMAND": stack.get("lint_command", "./gradlew detekt ktlintCheck"),
        "TEST_COMMAND_TEMPLATE": stack.get("test_command", "./gradlew :[module]:test"),
        "STACK_DESCRIPTION": f"{project.get('name', 'Project')} \u2014 {stack.get('language', 'Kotlin')} stack",
        "MODULE_TABLE": _build_module_table(modules),
        "MODULE_SOURCE_TABLE": _build_source_table(modules),
        "MODULE_TEST_TABLE": _build_test_table(modules),
        "MODULE_BUILD_COMMANDS": _build_module_build_commands(modules, stack),
        "MODULE_NAMES_LIST": _build_module_names_list(modules),
        "MODULE_DOCS_LIST": _build_module_docs_list(modules),
        "PROVIDER_ID": provider_id,
        "PROVIDER_NAME": provider_name,
        "PROVIDER_BASE_URL": provider.get("base_url", "https://routerai.ru/api/v1"),
        "PROVIDER_API_KEY_ENV": provider.get("api_key_env", "PROVIDER_API_KEY"),
        "DEFAULT_MODEL": default_model,
        "CODER_MODEL": coder_model,
        "REVIEWER_MODEL": reviewer_model,
        "DESIGNER_MODEL": designer_model,
        "SMALL_MODEL": models.get("small", coder_model),
        "ISO_TIMESTAMP_PLACEHOLDER": datetime.datetime.utcnow().strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "CONTEXT7_ENABLED": str(context7_cfg.get("enabled", True)).lower(),
        "CONTEXT7_API_KEY_ENV": context7_cfg.get("api_key_env", "CONTEXT7_API_KEY"),
        "KNOWLEDGE_ENABLED": str(knowledge_cfg.get("enabled", True)).lower(),
        "KNOWLEDGE_URL": knowledge_cfg.get("url", "http://localhost:8085/mcp"),
        "SERENA_ENABLED": str(serena_cfg.get("enabled", True)).lower(),
        "LSP_BLOCK": _build_lsp_block(lsp),
        "UI_FRAMEWORK": ui_framework,
        "PLATFORMS": ", ".join(platforms),
        "COLOR_TABLE": _build_color_table(colors),
        "FORBIDDEN_PATTERNS_LIST": _build_forbidden_list(
            code_quality.get("forbidden_patterns", [])
        ),
        "FORMATTER_BLOCK": _build_formatter_block(stack, manifest.get("formatter", {})),
    }


def render(template_text: str, context: dict) -> str:
    result = template_text
    for key, value in context.items():
        result = result.replace("{{" + key + "}}", str(value))
    return result


def check_unresolved(rendered: str, source_path: str) -> list:
    return re.findall(r"\{\{[A-Z_]+\}\}", rendered)


def _kit_path_to_target(kit_rel_path: str) -> str:
    parts = kit_rel_path.split("/")
    if parts[0] == "kit":
        parts = parts[1:]
    if parts[-1].endswith(".template"):
        parts[-1] = parts[-1][: -len(".template")]
    return str(Path(*parts))


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


def apply(manifest_path: str, target_dir: str, dry_run: bool, merge: bool) -> None:
    target = Path(target_dir)
    manifest_file = Path(manifest_path)

    if not manifest_file.exists():
        print(f"ERROR: manifest not found: {manifest_path}")
        sys.exit(1)

    if not target.exists():
        print(f"ERROR: target directory does not exist: {target}")
        sys.exit(1)

    with open(manifest_file) as f:
        manifest = yaml.safe_load(f)

    _check_credentials(manifest)
    context = build_context(manifest)

    print(f"\nFetching kit file list from GitHub...")
    kit_files = _fetch_kit_file_list()
    print(f"Found {len(kit_files)} kit files.")

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Applying opencode-kit to: {target}")
    print(f"Manifest: {manifest_path}")
    print(f"Project: {context['PROJECT_NAME']}")
    print(f"Modules: {context['MODULE_NAMES_LIST']}")
    print()

    actions = []

    for kit_rel in sorted(kit_files):
        target_rel = _kit_path_to_target(kit_rel)
        target_path = target / target_rel
        is_template = kit_rel.endswith(".template")
        action = "RENDER" if is_template else "COPY"

        if target_path.exists() and not merge:
            print(f"  SKIP (exists) {target_rel}")
            continue
        elif target_path.exists() and merge:
            action = f"{action} (merge/overwrite)"

        actions.append((action, kit_rel, target_path, target_rel, is_template))
        print(f"  {action:20s} -> {target_rel}")

    modules = manifest.get("modules", [])
    scaffold_dirs = create_docs_scaffold(modules, target, dry_run=True)
    if scaffold_dirs:
        print(f"\n  CREATE DIRS ({len(scaffold_dirs)} doc directories):")
        for d in scaffold_dirs[:10]:
            print(f"    {d}")
        if len(scaffold_dirs) > 10:
            print(f"    ... and {len(scaffold_dirs) - 10} more")

    if dry_run:
        print(
            f"\n[DRY RUN] {len(actions)} files would be written. Run without --dry-run to apply."
        )
        _print_checklist(context)
        return

    print("\nDownloading and applying files...")
    unresolved_report = []

    for action, kit_rel, target_path, target_rel, is_template in actions:
        url = f"{KIT_RAW_BASE}/{kit_rel}"
        print(f"  Fetching {url}")
        content = _fetch_url(url)

        target_path.parent.mkdir(parents=True, exist_ok=True)

        if is_template:
            rendered = render(content, context)
            unresolved = check_unresolved(rendered, kit_rel)
            if unresolved:
                unresolved_report.append((target_rel, unresolved))
            target_path.write_text(rendered, encoding="utf-8")
        else:
            target_path.write_text(content, encoding="utf-8")

    create_docs_scaffold(modules, target, dry_run=False)

    print(f"\nDone. {len(actions)} files written.")

    if unresolved_report:
        print("\nUnresolved placeholders (fill these manually):")
        for file, tokens in unresolved_report:
            print(f"  {file}: {', '.join(tokens)}")

    _print_checklist(context)


def _print_checklist(context: dict) -> None:
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


def main():
    parser = argparse.ArgumentParser(
        description="Apply opencode-kit to a target project (fetches templates from GitHub)"
    )
    parser.add_argument("--manifest", required=True, help="Path to manifest YAML file")
    parser.add_argument(
        "--target", required=True, help="Path to target project directory"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without writing files"
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Overwrite existing files (default: skip existing)",
    )
    args = parser.parse_args()

    apply(
        manifest_path=args.manifest,
        target_dir=args.target,
        dry_run=args.dry_run,
        merge=args.merge,
    )


if __name__ == "__main__":
    main()
