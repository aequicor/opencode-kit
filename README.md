# opencode-kit

Reusable OpenCode AI agent configuration. Clone this kit, fill in a manifest, run `apply.py`, and your project gets a full orchestrated AI development workflow with 8 specialized agents.

## What you get

- **8 specialized AI agents**: Main (orchestrator), CodeWriter, CodeReviewer, BugFixer, debugger, QA, Designer, PromptEngineer
- **Multi-model routing**: different models per role (orchestration vs coding vs review vs design)
- **MCP integrations**: context7 (library docs), serena (code navigation), KnowledgeOS (project vault)
- **Anti-loop guardrails**: circuit breakers, context discipline, token budget management
- **Session continuity**: checkpoint pattern via `.planning/CURRENT.md`
- **Documentation hierarchy**: per-module `requirements/spec/plans/reports` structure
- **3 slash commands**: `/new-feature`, `/resume`, `/checkpoint`

## Quick Start (5 minutes)

```bash
# 1. Clone the kit
git clone <this-repo> opencode-kit
cd opencode-kit

# 2. Copy and fill the manifest
cp manifest.example.yaml my-project.yaml
# Edit my-project.yaml — fill in project name, modules, provider, models

# 3. Dry run — preview what will be created
python3 scripts/apply.py --manifest my-project.yaml --target /path/to/your/project --dry-run

# 4. Apply
python3 scripts/apply.py --manifest my-project.yaml --target /path/to/your/project

# 5. Set environment variables (see post-install output)
export ROUTERAI_OPENCODE=your_key_here
export CONTEXT7_API_KEY=your_key_here
```

## AI Setup Prompt

Paste this to an AI agent to apply the kit autonomously:

```
You are applying opencode-kit to a new project.

Kit location: /path/to/opencode-kit
Target project: /path/to/target/project
Project name: My Project
Stack profile: kotlin-multiplatform  # or: kotlin-jvm-ktor | generic

## Step 1 — Fill manifest
Read manifest.example.yaml from the kit. Create my-project.yaml by copying it and filling in:
- project.name and project.description
- stack.profile (choose the closest match from profiles/ directory)
- modules: list all modules from the project's build files (settings.gradle.kts or equivalent)
  For each module: name, gradle_module, source_root, test_root, docs_path, responsibility
- provider.base_url and provider.api_key_env (the env var NAME only — never the actual key)
- models: adjust if using different provider/models
- mcp.knowledge.url: set to actual KnowledgeOS URL (or set enabled: false if not using it)
- ui.colors: if this project has a design system, list the colors. If unknown, use generic profile.

If any field is unclear, leave the default and add a comment: # TODO: verify this

## Step 2 — Dry run
Run: python3 scripts/apply.py --manifest my-project.yaml --target /path/to/target/project --dry-run
Review output. Verify no existing files will be overwritten unintentionally.
If .opencode/ or opencode.json already exist, add --merge flag.

## Step 3 — Apply
Run without --dry-run.

## Step 4 — Verify
1. Open opencode.json — confirm apiKey uses {env:VAR_NAME} syntax, NOT a real key.
2. Confirm all 8 agent files exist in .opencode/agents/
3. Run the compile command to confirm the build works.
4. Read .opencode/_shared.md → verify the Project Context section matches the actual project.

## Step 5 — Set env vars
The following must be set before running opencode:
- The provider API key env var (see opencode.json apiKey field)
- CONTEXT7_API_KEY (if context7 MCP is enabled)

## Report back
- Which files were created/modified
- Any TODO fields remaining
- Any errors encountered
```

## Agent Roster

| Agent | Role | Model class | Invoked by |
|-------|------|-------------|------------|
| Main | Orchestrator, single entry point | Default (best SWE) | PO directly |
| CodeWriter | Kotlin/code implementation, one stage at a time | Coder | @Main via task |
| CodeReviewer | Read-only code review | Reviewer | @Main after CodeWriter |
| BugFixer | Root cause analysis + fix + regression test | Coder | @Main for bugs |
| debugger | Read-only investigation, produces failing test | Coder | @Main before BugFixer |
| QA | Test plan (Draft before, Final after implementation) | Coder | @Main twice per feature |
| Designer | UI/UX description for Compose Multiplatform | Designer | @Main for UI features |
| PromptEngineer | Maintains agent prompts and skills | Reviewer | @Main for prompt work |

## Profiles

| Profile | Stack | Pre-filled |
|---------|-------|-----------|
| `kotlin-multiplatform.yaml` | KMP: Compose Desktop + Android + iOS + Ktor | Gradle, detekt/ktlint, forbidden patterns, serena, kotlin-lsp |
| `kotlin-jvm-ktor.yaml` | Pure Kotlin/JVM Ktor backend | Gradle, detekt/ktlint, forbidden patterns, serena, kotlin-lsp |
| `generic.yaml` | Any language | Minimal — fill everything manually |

## Requirements

- [opencode](https://opencode.ai) installed
- Python 3.8+ with PyYAML (`pip install pyyaml`)
- API key for your chosen provider (RouterAI, OpenRouter, etc.)
- Optional: KnowledgeOS running at configured URL for the vault MCP

## Credentials

**Never put actual API keys in manifest.yaml.** Use `api_key_env` fields — they store the *name* of the environment variable, not the value:

```yaml
provider:
  api_key_env: ROUTERAI_OPENCODE  # The env var name, not the key itself
```

The generated `opencode.json` will have:
```json
"apiKey": "{env:ROUTERAI_OPENCODE}"
```

OpenCode reads the key from your environment at runtime. Add to your shell profile:
```bash
export ROUTERAI_OPENCODE=sk-...
export CONTEXT7_API_KEY=ctx-...
```

For CI/CD, inject as secrets. Never commit `.env` files — add to `.gitignore`.

## Workflow

```
PO → /new-feature <description>
      └─► @Main (CLASSIFY → CLARIFY → SEARCH → PLAN → QA DRAFT → CONFIRM → EXECUTE → QA FINAL → CLOSE)
               ├─► @Designer   (UI features)
               ├─► @CodeWriter (implementation, one stage at a time)
               ├─► @CodeReviewer (after each stage)
               ├─► @BugFixer  (for bugs)
               ├─► @debugger  (complex bugs without stacktrace)
               └─► @QA        (test plan draft + final)

/resume  → resume interrupted session from .planning/CURRENT.md
/checkpoint → update .planning/CURRENT.md with current state
```

## Extending

**Add a profile**: copy `profiles/generic.yaml`, fill in your stack's build commands and code quality rules.

**Add a skill**: copy `kit/.opencode/skills/look-up/SKILL.md` as a template into `kit/.opencode/skills/your-skill/SKILL.md`.

**Customize an agent**: edit the agent file in `kit/.opencode/agents/` before applying, or edit it directly in the target project after applying.
