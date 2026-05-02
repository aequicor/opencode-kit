# opencode-kit

Reusable OpenCode AI agent configuration. Clone this kit or use the zero-clone AI Setup Prompt — either way, your project gets a full orchestrated AI development workflow.

**Requires OpenCode v1.1.1+** — uses `permission` (not deprecated `tools`), `external_directory`, `doom_loop`, `small_model`, `compaction`, `formatter`.

## What you get

- **9 core AI agents**: Main (orchestrator), CodeWriter, CodeReviewer, BugFixer, debugger, QA, Designer, PromptEngineer, AutoApprover
- **+7 requirements pipeline agents** *(optional, `requirements-pipeline` profile)*: RequirementsPipeline, BusinessAnalyst, CornerCaseReviewer, RequirementsQA, CoverageChecker, SystemAnalyst, ConsistencyChecker
- **Multi-model routing**: different models per role (orchestration vs coding vs review vs design) + `small_model` for lightweight tasks
- **MCP integrations**: context7 (library docs), serena (code navigation), KnowledgeOS (project vault)
- **Anti-loop guardrails**: circuit breakers, context discipline, token budget management, native `doom_loop` detection
- **Compaction & token budget**: auto-compaction with reserved buffer, 3-tier token budget (50%/75%/90%)
- **Session continuity**: checkpoint pattern via `.planning/CURRENT.md`
- **Documentation hierarchy**: per-module `requirements/spec/plans/reports` structure in `.vault/`
- **11 slash commands**: `/new-feature`, `/requirements-pipeline`, `/approve`, `/resume`, `/checkpoint`, `/review`, `/update`, `/update-deps`, `/deploy`, `/fix`, `/lint`
- **Human-in-the-loop or full automation**: `/approve` for manual confirmation; `AUTO_APPROVE=true` for zero-touch pipelines via `@AutoApprover`
- **Security perimeter**: `external_directory` permission, granular bash rules, destructive command denials

## Quick Start (5 minutes)

**Option A — Zero clone (AI agent does everything):** Copy the AI Setup Prompt below, paste it into any AI agent (Claude, GPT, etc.), and the agent will interview you and apply the kit. No git clone needed.

**Option B — Manual clone:**

```bash
# 1. Clone the kit
git clone https://github.com/aequicor/opencode-kit.git
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

### Core agents (all profiles)

| Agent | Role | Model class | Mode | Invoked by |
|-------|------|-------------|------|------------|
| Main | Orchestrator, single entry point | Default (best SWE) | Primary | PO directly |
| CodeWriter | Code implementation, one stage at a time | Coder | All | @Main via task |
| CodeReviewer | Read-only code review | Reviewer | Subagent | @Main after CodeWriter |
| BugFixer | Root cause analysis + fix + regression test | Coder | All | @Main for bugs |
| debugger | Read-only investigation, produces failing test | Coder | All | @Main before BugFixer |
| QA | Implementation test plan (Draft + Final) | Coder | Subagent | @Main twice per feature |
| Designer | UI/UX description, read-only | Designer | Subagent | @Main for UI features |
| PromptEngineer | Maintains agent prompts and skills | Reviewer | Subagent | @Main for prompt work |
| AutoApprover | Automated plan gatekeeper — verifies plan completeness | Reviewer | Subagent | @Main in AUTO_APPROVE mode |

### Requirements pipeline agents (`requirements-pipeline` profile)

| Agent | Role | Model class | Mode | Invoked by |
|-------|------|-------------|------|------------|
| RequirementsPipeline | Requirements orchestrator — chains BA → CCR → QA → SA → consistency | Default | Primary | PO via /requirements-pipeline, or @Main step 1 |
| BusinessAnalyst | Drafts and updates business requirements (DRAFT / UPDATE) | Default | Subagent | @RequirementsPipeline |
| CornerCaseReviewer | Adversarial attacker — finds gaps in requirements (BUSINESS) and spec (TECHNICAL) | Default | Subagent | @RequirementsPipeline |
| RequirementsQA | Generates test cases from requirements + corner cases (pre-spec) | Coder | Subagent | @RequirementsPipeline |
| CoverageChecker | Verifies all requirements and corner cases have test cases | Default | Subagent | @RequirementsPipeline |
| SystemAnalyst | Generates technical spec from requirements + test cases | Default | Subagent | @RequirementsPipeline |
| ConsistencyChecker | Final gate — verifies spec does not contradict requirements | Default | Subagent | @RequirementsPipeline |

## Corner Case Analysis System

Every feature starts with a systematic corner case analysis during the **business requirements phase** — before a single line of spec or code is written. The system prevents late-cycle surprises by surfacing domain invariants, boundary conditions, failure modes, and concurrency scenarios at the business planning level.

### How it works (full pipeline — `requirements-pipeline` profile)

```
PO: /requirements-pipeline "description"   (or automatically as @Main step 1)
  @BusinessAnalyst    — drafts requirements
        ↕ loop (max 3 iterations)
  @CornerCaseReviewer — attacks requirements across 6 categories, @BusinessAnalyst answers
  corner-case-refinement skill — formalizes findings into corner case register
  @RequirementsQA     — generates test cases from requirements + register (pre-spec)
        ↕ loop (max 2 iterations)
  @CoverageChecker    — verifies all ACs and Critical/High corner cases have test cases
  @SystemAnalyst      — generates technical spec from requirements + test cases
        ↕ loop (max 3 iterations)
  @CornerCaseReviewer — attacks spec across 4 technical axes, @SystemAnalyst answers
        ↕ loop (max 2 iterations)
  @ConsistencyChecker — final consistency gate (spec vs requirements vs test plan)
  PO: /approve → artifacts ready
PO: /new-feature → @Main reads artifacts, proceeds to implementation planning
```

**6 analysis categories** (business domain level):

| Category | Focus | Example question |
|----------|-------|-----------------|
| Input Integrity | Data entering the system | What if the mandatory field is left blank? |
| Business Process Integrity | Workflow ordering, idempotency, recovery | What if the system crashes mid-workflow? |
| Domain Invariants | Business rules that must never be violated | What if quantity goes negative? |
| External Dependency Failures | Third-party systems, payment gateways | What if the payment gateway is down for 30 minutes? |
| Scale & Capacity | Data volume, concurrency limits | What if 10,000 concurrent users trigger this flow? |
| Temporal & Concurrency | Race conditions, distributed consistency | What if two users act on the same record simultaneously? |

**Severity classification**:

| Severity | Definition | Enforcement |
|----------|-----------|-------------|
| **Critical** | Data loss, financial loss, security breach, regulatory violation | Mandatory test case — cannot be deferred |
| **High** | User-visible incorrect result, broken business process | Test case required or explicit deferred note |
| Medium | Degraded experience, workaround exists | Listed for awareness |
| Low | Cosmetic, extreme edge | Documented for completeness |

**Artifacts produced:**
- `.vault/concepts/<module>/requirements/<feature>.md` — business requirements
- `.vault/concepts/<module>/plans/<feature>-corner-cases.md` — corner case register
- `.vault/reference/<module>/spec/<feature>-requirements-test-plan.md` — requirements test plan
- `.vault/reference/<module>/spec/<feature>.md` — technical spec

## Profiles

| Profile | Stack | Pre-filled |
|---------|-------|-----------|
| `kotlin-multiplatform.yaml` | KMP: Compose Desktop + Android + iOS + Ktor | Gradle, detekt/ktlint, forbidden patterns, serena, kotlin-lsp |
| `kotlin-jvm-ktor.yaml` | Pure Kotlin/JVM Ktor backend | Gradle, detekt/ktlint, forbidden patterns, serena, kotlin-lsp |
| `java-spring.yaml` | Java Spring Boot | Maven/Gradle, Spring conventions, serena |
| `go-gin.yaml` | Go + Gin | Go modules, golangci-lint |
| `python-fastapi.yaml` | Python + FastAPI | pip/uv, ruff/mypy |
| `typescript-nextjs.yaml` | TypeScript + Next.js | npm, ESLint, Prettier |
| `rust-actix.yaml` | Rust + Actix-web | Cargo, clippy |
| `csharp-aspnet.yaml` | C# + ASP.NET Core | dotnet, roslyn analyzers |
| `minecraft-paper-plugin.yaml` | Minecraft Paper plugin (Kotlin/Gradle KTS) | Multi-module, Paper API conventions, MiniMessage/component rules |
| `ollama-cloud.yaml` | Ollama cloud-hosted LLMs | DeepSeek V4 Pro + Qwen models, no Designer |
| `requirements-pipeline.yaml` | Any language + AI-driven requirements pipeline | All 7 requirements agents, generic stack baseline |
| `generic.yaml` | Any language | Minimal — fill everything manually |

## Requirements

- [opencode](https://opencode.ai) v1.1.1 or later installed
- Python 3.9+ with PyYAML (`pip install pyyaml`)
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

### With `requirements-pipeline` profile

```
PO → /requirements-pipeline <description>
      └─► @RequirementsPipeline (automated BA → CCR → QA → SA → consistency pipeline)
              └─► PO: /approve → artifacts written to .planning/CURRENT.md

PO → /new-feature <description>
      └─► @Main
            ├─► step 0.5: detect pre-made package in .planning/CURRENT.md → skip step 1
            │             (OR: no pre-made package → dispatch @RequirementsPipeline as step 1)
            ├─► step 2:   SEARCH existing code patterns and guidelines
            ├─► step 3:   @Designer (UI features only)
            ├─► step 4:   lookup skill (new library)
            ├─► step 5:   writing-plans (plan + stage files — requirements/spec already exist)
            ├─► step 5a:  @QA DRAFT (implementation-level test plan)
            ├─► step 6:   CONFIRM — PO /approve (or @AutoApprover if AUTO_APPROVE=true)
            ├─► step 7:   @CodeWriter + @CodeReviewer cycles (per stage)
            ├─► step 7a:  @QA FINAL
            └─► step 8:   CLOSE
```

### Without requirements pipeline (generic and other profiles)

```
PO → /new-feature <description>
      └─► @Main
            ├─► step 0:   CLASSIFY & CLARIFY (minimal questions to PO)
            ├─► step 1:   corner-case-refinement skill + writing-plans for requirements + spec
            ├─► step 2:   SEARCH
            ├─► step 3:   @Designer (UI features only)
            ├─► step 4:   lookup skill (new library)
            ├─► step 5:   writing-plans (plan + stage files)
            ├─► step 5a:  @QA DRAFT
            ├─► step 6:   CONFIRM — PO /approve (or @AutoApprover if AUTO_APPROVE=true)
            ├─► step 7:   @CodeWriter + @CodeReviewer cycles (per stage)
            ├─► step 7a:  @QA FINAL
            └─► step 8:   CLOSE
```

### Slash commands

| Command | Description |
|---------|-------------|
| `/new-feature` | Start a new feature, bug fix, or tech task via @Main |
| `/requirements-pipeline` | Run the AI-driven requirements pipeline (requirements-pipeline profile only) |
| `/approve` | Confirm pending plan or requirements package |
| `/resume` | Resume interrupted session from `.planning/CURRENT.md` |
| `/checkpoint` | Write current state to `.planning/CURRENT.md` |
| `/review` | Code review of staged / unstaged / all changes |
| `/update` | Upgrade kit configuration to latest version |
| `/update-deps` | Update project dependencies |
| `/deploy` | Deploy / publish the project (requires PO confirmation) |
| `/fix` | Quick bug fix with inline context |
| `/lint` | Run linter and fix issues |

## Extending

**Add a profile**: copy `profiles/generic.yaml`, fill in your stack's build commands and code quality rules.

**Add a skill**: copy `kit/.opencode/skills/look-up/SKILL.md` as a template into `kit/.opencode/skills/your-skill/SKILL.md`.

**Customize an agent**: edit the agent file in `kit/.opencode/agents/` before applying, or edit it directly in the target project after applying.
