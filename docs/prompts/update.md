You are upgrading an opencode-kit project to the latest version.
Your ONLY job is to follow this script exactly. Do not skip steps. Do not guess values.

KIT REPO: https://github.com/aequicor/opencode-kit
CHANGELOG: https://raw.githubusercontent.com/aequicor/opencode-kit/main/docs/migration/changelog.yaml

─── PHASE 0 — DETECT CURRENT VERSION ───

1. Find the manifest file in the project root (*.yaml or *.yml).
   If multiple → ask the user which one.
   If none → STOP. Tell user: "No manifest found. This project was not applied via opencode-kit."
2. Read kit_version from it. Example: kit_version: "1.2.0"
   If no kit_version field → treat as "1.0.0" (earliest). Ask user to confirm.

─── PHASE 1 — FETCH CHANGELOG ───

3. Fetch the migration changelog:
     CHANGELOG URL (see above)
   Parse as YAML. Extract the `versions` list.
4. Identify latest version = versions[0].version

5. If current_version == latest_version → "Already up to date." STOP.

6. Collect all versions between current (exclusive) and latest (inclusive),
   sorted chronologically (oldest first).

─── PHASE 2 — SHOW MIGRATION PLAN ───

7. Build a report:

## opencode-kit Update Plan
**Current:** <version>  →  **Target:** <target>
**Versions:** <list>

### Breaking Changes
<list from changelog — flag with ⚠️>

### New Manifest Fields
<list fields that will be added, with defaults>

### Files That Will Be Overwritten
- opencode.json
- .opencode/agents/* (all 9 agents)
- .opencode/_shared.md
- .opencode/FILE_STRUCTURE.md
- AGENTS.md
- AUTO_MEMORY.md
- .planning/CURRENT.md.template, .planning/DECISIONS.md.template
- .opencode/skills/* (all skills)
- .opencode/commands/* (all commands)
- .opencode/sessions/SESSIONS.md.template
- .opencode/evals/* (smoke + security eval suites)
- .opencode/i18n/en.yaml, .opencode/i18n/ru.yaml
- docs/_templates/*
- <editor files if enabled>

These files will be REWRITTEN. Customizations will be LOST.

8. Ask: "Proceed with update? (yes/no)"
   If no → STOP.

─── PHASE 3 — APPLY UPDATE ───

9. Download and run the remote apply script.
   apply_remote.py is self-contained — it fetches all kit templates from GitHub at runtime.
   It works regardless of how the kit was originally applied.

```bash
curl -sL https://raw.githubusercontent.com/aequicor/opencode-kit/main/scripts/apply_remote.py -o apply_remote.py
python3 apply_remote.py --manifest <manifest>.yaml --target . --merge
rm apply_remote.py
```

If curl is not available, use wget:
```bash
wget -q https://raw.githubusercontent.com/aequicor/opencode-kit/main/scripts/apply_remote.py -O apply_remote.py
python3 apply_remote.py --manifest <manifest>.yaml --target . --merge
rm apply_remote.py
```

If apply fails → report error and STOP.
If apply_remote.py fails with "PyYAML is required", run `pip install pyyaml` (or `pip3 install pyyaml`) and retry.

─── PHASE 4 — UPDATE MANIFEST ───

10. Update `kit_version` in the manifest to the latest version.

11. Add new manifest fields (from `manifest_changes.added_fields` across ALL migrated versions):
    For each field:
      - If not present → append with documented `default` value + comment "# NEW in vX.Y.Z"
      - If already present → skip (user may have customized it)

─── PHASE 5 — VERIFY ───

12. Read the updated opencode.json:
    - Verify `apiKey` uses `{env:VAR}` syntax, NOT a literal key.
    - If literal key found → SECURITY ERROR. Abort.

13. List .opencode/agents/ directory:
    - Verify agents are present (Main, CodeWriter, CodeReviewer, BugFixer, debugger, QA, Designer, PromptEngineer)
    - Designer may be absent if disabled in manifest.

14. Run compile and test commands from manifest:
    - Extract `stack.compile_command` and `stack.test_command` from the manifest.
    - Run compile (DRY RUN only — report result, don't fix):
      <compile_command from manifest> || echo "(compile check skipped — may need dependencies)"
    - Run tests if available:
      <test_command from manifest> || echo "(test check skipped)"

─── PHASE 6 — SUMMARY ───

15. Output:

═══════════════════════════════════════════════════
opencode-kit UPDATED SUCCESSFULLY
═══════════════════════════════════════════════════

Old version:  <old>
New version:  <new>

New capabilities:
  <list from changelog>

Breaking changes applied: <yes / none>

Next steps:
  1. Review changes:  git diff
  2. Restore customizations from git if needed
  3. Test:  <test_command>
  4. Commit: git add . && git commit -m "chore: update opencode-kit to <new>"

Report back a summary of what was done.
