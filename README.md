# opencode-kit

Reusable OpenCode AI agent configuration. Clone this kit or use the zero-clone AI Setup Prompt — either way, your project gets a full orchestrated AI development workflow with 9 specialized agents.

**Migrated to OpenCode v1.1.1+ syntax** — uses `permission` (not deprecated `tools`), `external_directory`, `doom_loop`, `small_model`, `compaction`, `formatter`.

## What you get

- **9 specialized AI agents**: Main (orchestrator), CodeWriter, CodeReviewer, BugFixer, debugger, QA, Designer, PromptEngineer, AutoApprover
- **Multi-model routing**: different models per role (orchestration vs coding vs review vs design) + `small_model` for lightweight tasks
- **MCP integrations**: context7 (library docs), serena (code navigation), KnowledgeOS (project vault)
- **Anti-loop guardrails**: circuit breakers, context discipline, token budget management, native `doom_loop` detection
- **Compaction & token budget**: auto-compaction with reserved buffer, 3-tier token budget (50%/75%/90%)
- **Session continuity**: checkpoint pattern via `.planning/CURRENT.md`
- **Documentation hierarchy**: per-module `requirements/spec/plans/reports` structure
- **6 slash commands**: `/new-feature`, `/resume`, `/checkpoint`, `/update`, `/approve`, `/review`
- **Human-in-the-loop or full automation**: `/approve` for manual confirmation; `AUTO_APPROVE=true` for zero-touch pipelines via `@AutoApprover`
- **Security perimeter**: `external_directory` permission, granular bash rules, destructive command denials

## Quick Start (5 minutes)

**Option A — Zero clone (AI agent does everything):** Copy the AI Setup Prompt below, paste it into any AI agent (Claude, GPT, etc.), and the agent will interview you and apply the kit. No git clone needed.

**Option B — Manual clone:**

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

**Option C — Remote apply (no clone, manual):**

```bash
# 1. Download apply_remote.py (self-contained — fetches templates from GitHub)
curl -sL https://raw.githubusercontent.com/aequicor/opencode-kit/main/scripts/apply_remote.py \
  -o apply_remote.py

# 2. Create your manifest (use a profile from GitHub as base, e.g.):
curl -sL https://raw.githubusercontent.com/aequicor/opencode-kit/main/profiles/generic.yaml \
  -o my-project.yaml
# Edit my-project.yaml — fill in project name, modules, provider, models

# 3. Dry run
python3 apply_remote.py --manifest my-project.yaml --target /path/to/your/project --dry-run

# 4. Apply
python3 apply_remote.py --manifest my-project.yaml --target /path/to/your/project

# 5. Clean up
rm apply_remote.py
```

## AI Setup Prompt

Paste this into **any** AI agent. The agent will fetch the full setup script from GitHub, interview you, build a manifest, and apply the kit — no git clone needed.

```
Fetch the full setup instructions from:
  https://raw.githubusercontent.com/aequicor/opencode-kit/main/docs/prompts/setup.md

Read that file completely, then follow every phase in it exactly.
Do not skip steps. Do not guess values.
```

## AI Update Prompt

Already using opencode-kit? Paste this into **any** AI agent. The agent will detect your current version, fetch the migration changelog, apply any breaking changes, and update your manifest — all in one session.

```
Fetch the full update instructions from:
  https://raw.githubusercontent.com/aequicor/opencode-kit/main/docs/prompts/update.md

Read that file completely, then follow every phase in it exactly.
Do not skip steps. Do not guess values.
```


## Agent Roster

| Agent | Role | Model class | Mode | Invoked by |
|-------|------|-------------|------|------------|
| Main | Orchestrator, single entry point | Default (best SWE) | Primary | PO directly |
| CodeWriter | Kotlin/code implementation, one stage at a time | Coder | All | @Main via task |
| CodeReviewer | Read-only code review | Reviewer | Subagent | @Main after CodeWriter |
| BugFixer | Root cause analysis + fix + regression test | Coder | All | @Main for bugs |
| debugger | Read-only investigation, produces failing test | Coder | All | @Main before BugFixer |
| QA | Test plan (Draft before, Final after implementation) | Coder | Subagent | @Main twice per feature |
| Designer | UI/UX description, read-only | Designer | Subagent | @Main for UI features |
| PromptEngineer | Maintains agent prompts and skills | Reviewer | Subagent | @Main for prompt work |
| AutoApprover | Automated plan gatekeeper — verifies plan completeness and spec alignment | Reviewer | Subagent | @Main in AUTO_APPROVE mode |

## Corner Case Analysis System

Every feature starts with a systematic corner case analysis during the **business requirements phase** — before a single line of spec or code is written. The system prevents late-cycle surprises by surfacing domain invariants, boundary conditions, failure modes, and concurrency scenarios at the business planning level.

### How it works

```
PO task → clarifying questions (incl. corner case exploration) →
  corner-case-refinement → corner case register →
    brainstorming / spec (MUST address Critical + High) →
      writing-plans (Critical = mandatory test task) →
        implementation (no corner case discovery here)
```

**6 analysis categories**, each framed at the business domain level:

| Category | Focus | Example question |
|----------|-------|-----------------|
| Input Integrity | Data entering the system | What if the mandatory field is left blank? |
| Business Process Integrity | Workflow ordering, idempotency, recovery | What if the system crashes mid-workflow? |
| Domain Invariants | Business rules that must never be violated | What if quantity goes negative? |
| External Dependency Failures | Third-party systems, payment gateways | What if the payment gateway is down for 30 minutes? |
| Scale & Capacity | Data volume, concurrency limits | What if 10,000 concurrent users trigger this flow? |
| Temporal & Concurrency | Race conditions, distributed consistency | What if two cashiers process the last item simultaneously? |

**Severity classification** at the business level:

| Severity | Definition | Enforcement |
|----------|-----------|-------------|
| **Critical** | Data loss, financial loss, security breach, regulatory violation | **Mandatory test task** in implementation plan |
| **High** | User-visible incorrect result, broken business process | **Explicit decision** required (test or defer) |
| Medium | Degraded experience, workaround exists | Listed for awareness |
| Low | Cosmetic, extreme edge | Documented for completeness |

**Output:** Corner case register at `.vault/concepts/<module>/plans/<feature>-corner-cases.md`.

**Hard rule:** Every Critical corner case MUST have a corresponding test task in the implementation plan. Specs written without a corner case register are rejected as incomplete. Corner cases discovered during implementation are a **planning failure** — the system catches this at the design level, not the code level.

## Profiles

| Profile | Stack | Pre-filled |
|---------|-------|-----------|
| `kotlin-multiplatform.yaml` | KMP: Compose Desktop + Android + iOS + Ktor | Gradle, detekt/ktlint, forbidden patterns, serena, kotlin-lsp |
| `kotlin-jvm-ktor.yaml` | Pure Kotlin/JVM Ktor backend | Gradle, detekt/ktlint, forbidden patterns, serena, kotlin-lsp |
| `generic.yaml` | Any language | Minimal — fill everything manually |
| `ollama-cloud.yaml` | Ollama cloud-hosted LLMs | DeepSeek V4 Pro + Qwen models, no Designer |
| `minecraft-paper-plugin.yaml` | Minecraft Paper plugin (Kotlin/Gradle KTS) | Multi-module, Paper API conventions, MiniMessage/component rules |

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
      └─► @Main (CLASSIFY → CLARIFY incl. corner cases → SEARCH → CORNER CASE ANALYSIS → DESIGN → SPEC → PLAN → QA DRAFT → CONFIRM → EXECUTE → QA FINAL → CLOSE)
                ├─► corner-case-refinement (business-phase analysis BEFORE spec)
                ├─► @Designer     (UI features)
                ├─► @CodeWriter   (implementation, one stage at a time)
                ├─► @CodeReviewer (after each stage)
                ├─► @BugFixer     (for bugs)
                ├─► @debugger     (complex bugs without stacktrace)
                ├─► @QA           (test plan draft + final)
                └─► @AutoApprover (at CONFIRM step when AUTO_APPROVE=true)

              At CONFIRM step, two modes:
              • Manual   — @Main pauses, PO reviews and types /approve to continue
              • Automated — PO adds AUTO_APPROVE=true to the task; @Main dispatches
                            @AutoApprover which checks plan/spec alignment and returns
                            APPROVED or NEEDS_CHANGES (max 2 fix cycles, then escalates)

/approve    → confirm pending plan and proceed to EXECUTE (manual mode)
/resume     → resume interrupted session from .planning/CURRENT.md
/checkpoint → update .planning/CURRENT.md with current state
/review     → code review of staged / unstaged / all changes
/update     → upgrade kit configuration to latest version
```

## Extending

**Add a profile**: copy `profiles/generic.yaml`, fill in your stack's build commands and code quality rules.

**Add a skill**: copy `kit/.opencode/skills/look-up/SKILL.md` as a template into `kit/.opencode/skills/your-skill/SKILL.md`.

**Customize an agent**: edit the agent file in `kit/.opencode/agents/` before applying, or edit it directly in the target project after applying.
