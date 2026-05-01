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
import shutil
import sys
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
    collect_base_files,
    collect_editor_files,
    create_docs_scaffold,
    get_target_path,
    print_postinstall_checklist,
    render,
    verify_output,
)
from core.context import _build_nested_context


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

    with open(manifest_file) as f:
        manifest = yaml.safe_load(f)

    check_credentials(manifest)
    check_kit_version(manifest)

    context = build_context(manifest)
    editors = manifest.get("editors", ["opencode"])
    kit_files = collect_base_files(kit_root) + collect_editor_files(kit_root, editors)

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Applying opencode-kit to: {target}")
    print(f"Manifest: {manifest_path}")
    print(f"Project: {context['PROJECT_NAME']}")
    print(f"Modules: {context['MODULE_NAMES_LIST']}")
    print(f"Editors: {', '.join(editors)}")
    print()

    nested_template = kit_root / "nested" / "AGENTS.md.nested.template"
    nested_template_text = (
        nested_template.read_text(encoding="utf-8") if nested_template.exists() else None
    )
    stack = manifest.get("stack", {})
    modules = manifest.get("modules", [])

    actions = []

    for kit_file in sorted(kit_files):
        target_path = get_target_path(kit_file, kit_root, target)
        is_template = kit_file.name.endswith(".template")
        action = "RENDER" if is_template else "COPY"

        if target_path.exists() and not merge:
            print(f"  SKIP (exists) {target_path.relative_to(target)}")
            continue
        elif target_path.exists() and merge:
            action = f"{action} (merge/overwrite)"

        actions.append((action, kit_file, target_path, is_template))
        print(
            f"  {action:24s} \u2192 {target_path.relative_to(target) if target.exists() else target_path}"
        )

    nested_actions = []
    if nested_template_text and not dry_run:
        for m in modules:
            src_root = m.get("source_root", "")
            if not src_root:
                continue
            nested_ctx = _build_nested_context(m, stack, context["PROJECT_NAME"])
            nested_ctx["PROJECT_NAME"] = context["PROJECT_NAME"]
            target_nested = target / src_root / "AGENTS.md"
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

    for target_nested, nested_ctx in nested_actions:
        target_nested.parent.mkdir(parents=True, exist_ok=True)
        rendered = render(nested_template_text, nested_ctx)
        target_nested.write_text(rendered, encoding="utf-8")

    create_docs_scaffold(modules, target, dry_run=False)

    print(
        f"\n\u2705 Done. {len(actions)} base files + {len(nested_actions)} nested AGENTS.md written."
    )

    if unresolved_report:
        print("\n\u26a0\ufe0f  Unresolved placeholders (fill these manually):")
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
    parser = argparse.ArgumentParser(description="Apply opencode-kit to a target project")
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
