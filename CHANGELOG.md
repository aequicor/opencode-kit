# Changelog

All notable changes to opencode-kit will be documented in this file.

## [1.4.0] — 2026-05-02

### Added
- AI-driven requirements pipeline (`/requirements-pipeline` command + `requirements-pipeline` profile)
  - `@RequirementsPipeline` — orchestrator: BA → CCR loop → QA → CoverageChecker → SA → CCR loop → ConsistencyChecker → PO sign-off
  - `@BusinessAnalyst` — drafts and updates business requirements (DRAFT / UPDATE modes)
  - `@CornerCaseReviewer` — adversarial attacker for requirements (BUSINESS mode, 6 axes) and technical spec (TECHNICAL mode, 4 axes); loop-safe repeat-run handling
  - `@RequirementsQA` — generates requirements-phase test cases before spec exists (DRAFT / FIX modes)
  - `@CoverageChecker` — verifies every AC and Critical/High corner case has a test case; deferred note support
  - `@SystemAnalyst` — generates technical spec from requirements + test cases (DRAFT / UPDATE modes); handles CCR questions and ConsistencyChecker conflicts
  - `@ConsistencyChecker` — final gate: Spec vs Requirements (completeness + correctness) and test plan alignment
- `corner-case-refinement` skill: `Invocation Interface` section documenting input fields, output path, and final-version contract
- `@Main` FEATURE pipeline now dispatches `@RequirementsPipeline` as step 1 (fully automated requirements phase); requirements.md and spec.md are no longer written by @Main
- Pre-made requirements package detection at step 0.5 — skips @RequirementsPipeline when `/requirements-pipeline` was run standalone beforehand
- `_shared.md`: AI-driven requirements pipeline diagram, `@Main → @RequirementsPipeline` handoff protocol (Flow A integrated, Flow B standalone)

### Changed
- `@Main` FEATURE clarifying questions simplified — removed manual corner case axis exploration (handled by @RequirementsPipeline)
- `@Main` PLAN step no longer writes `requirements.md` or `spec.md` — these are produced by @RequirementsPipeline
- `new-feature.md` command updated to document the full 9-step pipeline including @RequirementsPipeline

## [1.3.0] — 2026-04-30

### Added
- Core module (`scripts/core/`) extracting shared logic from `apply.py` and `apply_remote.py`
- JSON Schema for manifest validation (`manifest.schema.json`)
- Structured output models for agent responses (Pydantic-compatible)
- Telemetry tracking for agent runs (timing, tokens, success rates)
- Prompt versioning infrastructure
- Pre-commit hooks configuration
- Integration tests covering full apply cycle
- `pyproject.toml` with dependencies and entry points

### Changed
- `apply.py` and `apply_remote.py` rewritten as thin wrappers over `core` module
- Tests restructured to cover both core and integration scenarios

## [1.2.0] — 2026-04-28

### Added
- Zero-clone AI Setup Prompt for remote kit application
- `apply_remote.py` — self-contained script fetching templates from GitHub
- `profiles/ollama-cloud.yaml` — Ollama cloud-hosted LLMs profile
- `profiles/minecraft-paper-plugin.yaml` — Minecraft Paper plugin profile

## [1.1.0] — 2026-04-25

### Added
- Migration to OpenCode v1.1.1+ permission syntax
- `external_directory` permission support
- `doom_loop` native detection
- `small_model` support
- Compaction configuration with reserved buffer
- Formatter configuration block

### Changed
- Deprecated `tools` field replaced by `permission` in all agent templates
- Agent modes updated: `primary` for orchestrator, `subagent` for executors

## [1.0.0] — 2026-04-20

### Added
- Initial release — 8 specialized AI agents
- Main orchestrator with FEATURE/BUG/TECH pipelines
- CodeWriter, CodeReviewer, BugFixer, debugger, QA, Designer, PromptEngineer agents
- Multi-model routing per agent role
- MCP integrations: context7, serena, KnowledgeOS
- Anti-loop guardrails and circuit breakers
- Session continuity via `.planning/CURRENT.md`
- Documentation hierarchy: requirements/spec/plans/reports
- 3 slash commands: `/new-feature`, `/resume`, `/checkpoint`
- Profile system: kotlin-multiplatform, kotlin-jvm-ktor, generic
- Template-based rendering with `{{PLACEHOLDER}}` substitution
- Credential safety checks (literal API key detection)
- CI/CD via GitHub Actions (pytest + ruff)
- Editor support: OpenCode/Claude Code, Cursor, GitHub Copilot
