---
description: Run lint and code-style checks across the project. No arguments — just runs the configured linter and reports results.
---

Run the project lint command and report results:

1. Run: `{{LINT_COMMAND}}`
2. If lint passes → report "Lint: PASSED. No issues."
3. If lint fails with errors:
   - List failed rules and affected files
   - Categorize: style / correctness / warnings
   - Ask: "Auto-fix style issues? (yes/no)"
   - If yes → dispatch @CodeWriter with fix instructions
   - If no → write issues to `.planning/lint_report.md`

**Do not modify code without confirmation.**
