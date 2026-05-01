#!/usr/bin/env python3
"""
opencode-kit remote apply script.
Downloads templates from GitHub and renders them into the target project.
No local clone required \u2014 this script is self-contained.

Usage:
    python3 apply_remote.py --manifest my-project.yaml --target /path/to/project
    python3 apply_remote.py --manifest my-project.yaml --target /path/to/project --dry-run
    python3 apply_remote.py --manifest my-project.yaml --target /path/to/project --merge

The manifest file must be local (created by the user or AI agent).
All kit templates are fetched from GitHub on the fly.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)

from core import (
    build_context,
    check_credentials,
    check_kit_version,
    check_unresolved,
    create_docs_scaffold,
    kit_path_to_target,
    print_postinstall_checklist,
    render,
    verify_output,
)
from core.context import _build_nested_context

KIT_REPO = "aequicor/opencode-kit"
KIT_BRANCH = "main"
KIT_RAW_BASE = f"https://raw.githubusercontent.com/{KIT_REPO}/{KIT_BRANCH}"
KIT_API_BASE = f"https://api.github.com/repos/{KIT_REPO}/git/trees/{KIT_BRANCH}?recursive=1"


def _fetch_url(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "opencode-kit-apply-remote/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError:
                print(
                    f"  WARNING: {url} returned non-UTF-8 content — reading with replacement chars"
                )
                return raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        print(f"ERROR: Failed to fetch {url} \u2014 HTTP {e.code}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"ERROR: Network error fetching {url} \u2014 {e.reason}")
        sys.exit(1)


def _fetch_kit_file_list(editors: list) -> list:
    try:
        data = _fetch_url(KIT_API_BASE)
        tree = json.loads(data)
        if "tree" not in tree:
            print("ERROR: Unexpected GitHub API response \u2014 no 'tree' key.")
            print("  You may be rate-limited. Wait a moment and try again.")
            sys.exit(1)
        all_paths = [
            entry["path"]
            for entry in tree["tree"]
            if entry["type"] == "blob" and entry["path"].startswith("kit/")
        ]
        return _filter_by_editors(all_paths, editors)
    except Exception as e:
        print(f"WARNING: Could not list kit files from GitHub API: {e}")
        print("  Falling back to hardcoded file list — your installation may be incomplete.")
        print("  Some recently added files may be missing. Check the repo for the full list:")
        print(f"  https://github.com/{KIT_REPO}")
        return _hardcoded_kit_files(editors)


def _filter_by_editors(paths: list, editors: list) -> list:
    result = []
    for path in paths:
        parts = path.split("/")
        if len(parts) >= 3 and parts[0] == "kit" and parts[1] == "editors":
            if parts[2] in editors:
                result.append(path)
        else:
            result.append(path)
    return result


def _hardcoded_kit_files(editors: list) -> list:
    base = [
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
        "kit/.vault/_templates/bug-report.md",
        "kit/.vault/_templates/test-plan.md",
        "kit/.vault/_templates/spec.md",
        "kit/.vault/_templates/requirements.md",
        "kit/.vault/_INDEX.md.template",
        "kit/nested/AGENTS.md.nested.template",
    ]
    editor_files = {
        "opencode": ["kit/editors/opencode/CLAUDE.md.template"],
        "cursor": ["kit/editors/cursor/.cursor/rules/conventions.mdc.template"],
        "copilot": ["kit/editors/copilot/.github/copilot-instructions.md.template"],
    }
    for editor in editors:
        base.extend(editor_files.get(editor, []))
    return base


def apply(manifest_path: str, target_dir: str, dry_run: bool, merge: bool) -> None:
    target = Path(target_dir)
    manifest_file = Path(manifest_path)

    if not manifest_file.exists():
        print(f"ERROR: manifest not found: {manifest_path}")
        sys.exit(1)

    if not target.exists():
        print(f"ERROR: target directory does not exist: {target}")
        sys.exit(1)

    with open(manifest_file, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    check_credentials(manifest)
    check_kit_version(manifest)
    context = build_context(manifest)

    editors = manifest.get("editors", ["opencode"])

    print("\nFetching kit file list from GitHub...")
    kit_files = _fetch_kit_file_list(editors)
    print(f"Found {len(kit_files)} kit files.")

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Applying opencode-kit to: {target}")
    print(f"Manifest: {manifest_path}")
    print(f"Project: {context['PROJECT_NAME']}")
    print(f"Modules: {context['MODULE_NAMES_LIST']}")
    print(f"Editors: {', '.join(editors)}")
    print()

    actions = []
    target_resolved = target.resolve()

    for kit_rel in sorted(kit_files):
        target_rel = kit_path_to_target(kit_rel)
        target_path = target / target_rel
        try:
            target_path.resolve().relative_to(target_resolved)
        except ValueError:
            print(f"  WARNING: Skipping {kit_rel!r} — resolved path escapes target directory")
            continue
        is_template = kit_rel.endswith(".template")
        action = "RENDER" if is_template else "COPY"

        if target_path.exists() and not merge:
            print(f"  SKIP (exists) {target_rel}")
            continue
        elif target_path.exists() and merge:
            action = f"{action} (merge/overwrite)"

        actions.append((action, kit_rel, target_path, target_rel, is_template))
        print(f"  {action:24s} -> {target_rel}")

    modules = manifest.get("modules", [])
    stack = manifest.get("stack", {})

    nested_template_url = f"{KIT_RAW_BASE}/kit/nested/AGENTS.md.nested.template"
    try:
        nested_template_text = _fetch_url(nested_template_url)
    except SystemExit:
        nested_template_text = None
    except Exception as e:
        print(f"  WARNING: Could not fetch nested template: {e} — skipping nested AGENTS.md")
        nested_template_text = None

    nested_actions = []
    if nested_template_text:
        for m in modules:
            src_root = m.get("source_root", "")
            if not src_root:
                continue
            nested_ctx = _build_nested_context(m, stack, context["PROJECT_NAME"])
            nested_ctx["PROJECT_NAME"] = context["PROJECT_NAME"]
            target_nested = target / src_root / "AGENTS.md"
            try:
                target_nested.resolve().relative_to(target_resolved)
            except ValueError:
                print(
                    f"  WARNING: Skipping module {m.get('name', '?')!r} — source_root {src_root!r} escapes target directory"
                )
                continue
            if target_nested.exists() and not merge:
                print(f"  SKIP (exists) {target_nested.relative_to(target)}")
                continue
            nested_actions.append((target_nested, nested_ctx))
            print(
                f"  NESTED AGENTS.md        \u2192 {target_nested.relative_to(target) if target.exists() else target_nested}"
            )

    scaffold_dirs = create_docs_scaffold(modules, target, dry_run=True)
    if scaffold_dirs:
        print(f"\n  CREATE DIRS ({len(scaffold_dirs)} doc directories):")
        for d in scaffold_dirs[:10]:
            print(f"    {d}")
        if len(scaffold_dirs) > 10:
            print(f"    ... and {len(scaffold_dirs) - 10} more")

    if dry_run:
        total = len(actions) + len(nested_actions)
        print(
            f"\n[DRY RUN] {total} files would be written ({len(actions)} base + {len(nested_actions)} nested). Run without --dry-run to apply."
        )
        print_postinstall_checklist(context)
        return

    print("\nDownloading and applying files...")
    unresolved_report = []

    for _action, kit_rel, target_path, target_rel, is_template in actions:
        url = f"{KIT_RAW_BASE}/{kit_rel}"
        print(f"  Fetching {url}")
        content = _fetch_url(url)

        target_path.parent.mkdir(parents=True, exist_ok=True)

        if is_template:
            try:
                rendered = render(content, context)
            except Exception as e:
                print(f"  ERROR: Failed to render {kit_rel}: {e}")
                sys.exit(1)
            unresolved = check_unresolved(rendered, kit_rel)
            if unresolved:
                unresolved_report.append((target_rel, unresolved))
            target_path.write_text(rendered, encoding="utf-8")
        else:
            target_path.write_text(content, encoding="utf-8")

    for target_nested, nested_ctx in nested_actions:
        target_nested.parent.mkdir(parents=True, exist_ok=True)
        try:
            rendered = render(nested_template_text, nested_ctx)
        except Exception as e:
            print(f"  ERROR: Failed to render nested AGENTS.md for {target_nested}: {e}")
            sys.exit(1)
        target_nested.write_text(rendered, encoding="utf-8")

    create_docs_scaffold(modules, target, dry_run=False)

    print(
        f"\n\u2705 Done. {len(actions)} base files + {len(nested_actions)} nested AGENTS.md written."
    )

    if unresolved_report:
        print("\nUnresolved placeholders (fill these manually):")
        for file, tokens in unresolved_report:
            print(f"  {file}: {', '.join(tokens)}")

    verify_warnings = verify_output(target, context)
    if verify_warnings:
        print("\n\u26a0\ufe0f  Post-install warnings:")
        for w in verify_warnings:
            print(f"  \u2717 {w}")
    else:
        print("\n\u2705 Post-install verification passed.")

    print_postinstall_checklist(context)


def main():
    parser = argparse.ArgumentParser(
        description="Apply opencode-kit to a target project (fetches templates from GitHub)"
    )
    parser.add_argument("--manifest", required=True, help="Path to manifest YAML file")
    parser.add_argument("--target", required=True, help="Path to target project directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
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
