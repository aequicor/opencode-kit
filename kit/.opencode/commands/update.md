---
description: Update opencode-kit configuration to the latest version. Reads current kit_version from manifest, fetches changelog, applies migrations and re-renders templates.
---

# /update — Kit Configuration Upgrade

You are upgrading an opencode-kit configuration to the latest version.

## MANDATORY: Read current version first

1. Find the manifest file in the project root (`*.yaml` or `*.yml`). READ it.
   If multiple manifests exist → ask the user which one to use.
   If none → STOP. Tell user: "No manifest found. This project may not have been applied via opencode-kit."
2. Extract `kit_version` from it. This is the CURRENT version.
3. If no `kit_version` field is found:
   - Search for `kit_version` in all `.yaml`/`.yml` files in the project root.
   - If truly absent → treat as "1.0.0" (earliest version).
   - Tell user: "No kit_version found — assuming 1.0.0. Continue? (yes/no)"

## Fetch migration changelog

4. Fetch the machine-readable changelog:
   ```
   https://raw.githubusercontent.com/aequicor/opencode-kit/main/docs/migration/changelog.yaml
   ```
   If fetch fails → use webfetch on `https://github.com/aequicor/opencode-kit/blob/main/docs/migration/changelog.yaml`
   If both fail → STOP. Report: "Cannot reach changelog. Check internet connection."

## Determine migration path

5. Parse changelog. Find the current version entry. Collect ALL versions between current (exclusive) and latest (inclusive) in chronological order (oldest first).

6. Build a migration report:

```
## opencode-kit Update Report
**Project:** <read from manifest: project.name>
**Current version:** <current>
**Target version:** <latest, e.g. 1.3.0>
**Versions to migrate through:** <list>

### Breaking Changes
<list any entries where breaking: true — with descriptions>

### Manifest Fields to Add
<list new manifest fields from all versions being migrated, with defaults>

### Files That Will Be Updated
<list common files_changed across all migratable versions>
```

7. Ask: "Proceed with update? (yes/no)"
   If no → STOP.

## Execute migration

8. **Run the remote apply script.**

   The `apply_remote.py` script is self-contained — it fetches all kit templates from GitHub at runtime. It works regardless of how the kit was originally applied (local clone or remote).

   ```bash
   curl -sL https://raw.githubusercontent.com/aequicor/opencode-kit/main/scripts/apply_remote.py -o apply_remote.py
   python3 apply_remote.py --manifest <manifest>.yaml --target . --merge
   rm apply_remote.py
   ```

   If curl is not available:
   ```bash
   wget -q https://raw.githubusercontent.com/aequicor/opencode-kit/main/scripts/apply_remote.py -O apply_remote.py
   python3 apply_remote.py --manifest <manifest>.yaml --target . --merge
   rm apply_remote.py
   ```

   If apply_remote.py fails with "PyYAML is required", run `pip install pyyaml` and retry.
   If apply_remote.py fails with any other error, report it to the user and STOP.

## Post-migration

12. **Update kit_version in manifest:**
    - Edit the manifest YAML: set `kit_version` to the latest version (e.g. `"1.3.0"`).

13. **Add new manifest fields** (from `manifest_changes.added_fields` across all migrated versions):
    - For each added field: if not present in user's manifest, append it with the documented `default` value and a `# NEW: ` comment.

14. **Validate manifest** (if validation tooling available):
    ```bash
    python3 -c "from scripts.core.schema import validate_manifest; validate_manifest('<manifest>.yaml')" 2>/dev/null || echo "Schema validation skipped (no core module available)"
    ```

## Final checklist

15. Output:

```
═══════════════════════════════════════════════
opencode-kit UPDATED SUCCESSFULLY
═══════════════════════════════════════════════

Old version: <old>
New version: <new>

Files updated:
- <list of changed files>

New capabilities unlocked:
- <list from changelog>

Next steps:
  1. Review changed files: git diff
  2. If any customizations were overwritten → restore them from git history
  3. Run compile to verify: <read compile_command from manifest>
  4. Run lint to verify: <read lint_command from manifest>
  5. Commit: git add . && git commit -m "chore: update opencode-kit to <new_version>"

Breaking changes applied: <yes / none>
```

## SAFETY RULES

- **NEVER modify files outside the project root** (no writes to `/`, `/etc`, `~/.config`, etc.)
- **NEVER delete user files** — `--merge` overwrites kit-managed files only (agents, skills, templates, opencode.json, AGENTS.md, _shared.md, FILE_STRUCTURE.md, .planning/ templates)
- **NEVER touch `.vault/` files created by users** — kit only writes `.vault/_templates/` and `.vault/_INDEX.md` which are in `kit/.vault/`
- **ALWAYS preserve `kit_version`** in the updated manifest
- **If manifest.api_key_env contains a literal key** (32+ chars with dashes) → STOP and warn: "Security: manifest contains a real API key in api_key_env. Fix manually before proceeding."
