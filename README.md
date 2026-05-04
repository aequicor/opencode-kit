# opencode-kit

AI agent configuration framework for [OpenCode](https://opencode.ai). Gives your project a full orchestrated development workflow — requirements, planning, coding, review, QA — driven by a team of specialized agents.

**Requires OpenCode v1.1.1+**

---

## Table of contents

- [Install](#install)
- [Set up credentials](#set-up-credentials)
- [First session](#first-session)
- [Daily workflow](#daily-workflow)
- [Usage scenarios](#usage-scenarios)
  - [1. Requirements pipeline](#1-requirements-pipeline)
  - [2. New feature](#2-new-feature)
  - [3. Testing](#3-testing)
  - [4. Bug fix](#4-bug-fix)
  - [5. Review](#5-review)
  - [6. Deploy](#6-deploy)
- [Choose profiles](#choose-profiles)
- [Agent roster](#agent-roster)
- [Requirements pipeline (optional)](#requirements-pipeline-optional)
- [Updating](#updating)
- [Extending](#extending)
- [Requirements](#requirements)

---

## Install

Three ways, pick one:

### Option 1 — AI Setup Prompt (recommended, zero clone)

Paste this into any AI agent (Claude, GPT, etc.). The agent interviews you, builds a manifest, and applies the kit automatically:

```
Fetch the full setup instructions from:
  https://raw.githubusercontent.com/aequicor/opencode-kit/main/docs/prompts/setup.md

Read that file completely, then follow every phase in it exactly.
Do not skip steps. Do not guess values.
```

### Option 2 — Remote apply (no clone, manual)

```bash
# Download the self-contained applier
curl -sL https://raw.githubusercontent.com/aequicor/opencode-kit/main/scripts/apply_remote.py \
  -o apply_remote.py

# Grab a profile for your stack as starting manifest
curl -sL https://raw.githubusercontent.com/aequicor/opencode-kit/main/profiles/generic.yaml \
  -o my-project.yaml
# Edit my-project.yaml — fill in project name, modules, profiles, provider, models

# Preview what will be created
python3 apply_remote.py --manifest my-project.yaml --target /path/to/your/project --dry-run

# Apply
python3 apply_remote.py --manifest my-project.yaml --target /path/to/your/project

rm apply_remote.py
```

### Option 3 — Clone and apply

```bash
git clone https://github.com/aequicor/opencode-kit.git
cd opencode-kit

cp manifest.example.yaml my-project.yaml
# Edit my-project.yaml

python3 scripts/apply.py --manifest my-project.yaml --target /path/to/your/project --dry-run
python3 scripts/apply.py --manifest my-project.yaml --target /path/to/your/project
```

---

## Set up credentials

**Never put API keys in the manifest.** Use environment variable names:

```yaml
# my-project.yaml
provider:
  name: ollama-cloud
  base_url: https://api.ollama.com/v1
  api_key_env: OLLAMA_CLOUD_API_KEY   # the env var name, not the key
```

Add to your shell profile (or CI secrets):

```bash
# Ollama Cloud (default)
export OLLAMA_CLOUD_API_KEY=sk-...
export CONTEXT7_API_KEY=ctx-...
```

Other providers use a different env var name — just set `api_key_env` to whatever name you choose:

```bash
# RouterAI / OpenRouter
export ROUTERAI_OPENCODE=sk-...
```

---

## First session

Open your project in OpenCode. **Select the `Main` agent** from the agent picker — all slash commands and tasks go through `@Main`, which then dispatches subagents automatically.

Start a new feature:

```
/new-feature Add user authentication with JWT tokens
```

`@Main` will clarify scope, plan stages, get your approval, then dispatch `@CodeWriter`, `@CodeReviewer`, and `@QA` automatically.

Fix a bug:

```
/fix Login throws 500 when email contains a plus sign
```

Review current changes:

```
/review
```

> **Note:** `@Main` is the only agent you select directly. All other agents (`@CodeWriter`, `@QA`, `@BugFixer`, `@BusinessAnalyst`, etc.) are subagents — invoked automatically by `@Main` and should not be selected manually.

---

## Daily workflow

| What you want to do | Command |
|---|---|
| Start a new feature or task | `/new-feature <description>` |
| Fix a bug | `/fix <description>` |
| Review staged/unstaged changes | `/review` |
| Approve a pending plan | `/approve` |
| Resume an interrupted session | `/resume` |
| Save progress mid-session | `/checkpoint` |
| Update dependencies | `/update-deps` |
| Deploy / publish | `/deploy` |
| Run linter and auto-fix | `/lint` |
| Run AI requirements pipeline | `/requirements-pipeline <description>` |
| Upgrade kit to latest version | `/update` |

---

## Usage scenarios

### 1. Requirements pipeline

**Goal:** generate a full reviewed requirements package (business requirements, corner cases, test plan, technical spec) before writing any code.

**When to use:** when you need a thorough, AI-reviewed spec for a complex feature — not a quick prototype.

**Profile:** add `requirements-pipeline` to `stack.profiles` in your manifest.

**Command:**

```
/requirements-pipeline "Users can reset their password via email link"
```

**What happens (full pipeline, orchestrated by `@Main`):**

1. **INTAKE** — `@Main` parses feature name and module from your description. If the module is ambiguous, it asks you to pick one.
2. **BA DRAFT** — `@BusinessAnalyst` generates a requirements document with user stories and acceptance criteria. Saved to `.vault/concepts/<module>/requirements/<feature>.md`.
3. **CC BUSINESS (loop)** — `@CornerCaseReviewer` attacks the requirements as an adversarial reviewer (max 3 iterations). If gaps are found, `@BusinessAnalyst` updates the requirements. Unresolved questions are surfaced to you.
4. **CORNER CASE REGISTER** — the `corner-case-refinement` skill runs a 6-category scan (input boundaries, process integrity, business rules, external dependencies, scale, concurrency). Results saved to `.vault/concepts/<module>/plans/<feature>-corner-cases.md` with severity ratings (Critical / High / Medium / Low).
5. **QA DRAFT** — `@RequirementsQA` generates test cases from requirements + corner cases.
6. **COVERAGE CHECK (loop)** — `@CoverageChecker` verifies every requirement and corner case has a test case (max 2 fix iterations).
7. **SA DRAFT** — `@SystemAnalyst` generates a technical spec (endpoints, data models, architecture) from requirements + test plan. Saved to `.vault/reference/<module>/spec/<feature>.md`.
8. **CC TECHNICAL (loop)** — `@CornerCaseReviewer` attacks the technical spec (max 3 iterations). If gaps remain, `@SystemAnalyst` updates the spec. Unresolved architectural decisions surfaced to you.
9. **CONSISTENCY CHECK (loop)** — `@ConsistencyChecker` verifies the spec does not contradict the requirements (max 2 iterations).
10. **SIGN-OFF** — the complete artifact package is presented to you:

```
### Artifacts

| Artifact              | File                                                       | Summary                              |
|-----------------------|------------------------------------------------------------|--------------------------------------|
| Business Requirements | .vault/concepts/<module>/requirements/<feature>.md         | N user stories, M acceptance criteria|
| Corner Case Register  | .vault/concepts/<module>/plans/<feature>-corner-cases.md   | Critical: N, High: M, Medium: K      |
| Requirements Test Plan| .vault/reference/<module>/spec/<feature>-test-plan.md      | T test cases                         |
| Technical Spec        | .vault/reference/<module>/spec/<feature>.md                | E endpoints, D data models           |
```

**After pipeline:**

- Type `/approve` to lock the artifacts and proceed to implementation.
- Type `reject: Step N` to discard artifacts from Step N onward and restart from that step.
- Then run `/new-feature` — `@Main` picks up the approved spec automatically and skips the planning phase.

**If the pipeline is blocked** (loop exhausted, unresolved questions), it pauses and asks you to provide answers. Type `/resume` to continue after responding.

**Typical session:**

```
> /requirements-pipeline "Users can reset their password via email link"

  Pipeline: INTAKE ✓ → BA DRAFT ✓ → CC BUSINESS (2 iter) ✓ → CORNER CASES ✓
           → QA DRAFT ✓ → COVERAGE ✓ → SA DRAFT ✓ → CC TECHNICAL (1 iter) ✓
           → CONSISTENCY ✓

  Sign-off package ready. Review artifacts above.
  → /approve
  → /new-feature "Password reset via email"
```

---

### 2. New feature

**Goal:** implement a new feature end-to-end — from planning through code, review, and QA.

**Command:**

```
/new-feature Add user authentication with JWT tokens
```

**What happens (orchestrated by `@Main`):**

1. **CLASSIFY & CLARIFY** — `@Main` asks minimal clarifying questions: which module, UI or backend, constraints.
2. **REQUIREMENTS PHASE** — if no pre-approved spec exists, `@Main` runs the requirements pipeline automatically (see scenario 1). If a spec is already approved in `.planning/CURRENT.md`, this step is skipped.
3. **SEARCH** — searches the knowledge base for existing code patterns and project guidelines.
4. **PLAN** — `@Main` creates an implementation plan broken into stages. Each stage is a self-contained unit of work. Plan saved to `.vault/concepts/<module>/plans/<feature>.md`.
5. **QA DRAFT** — `@QA` creates an implementation test plan.
6. **CONFIRM** — summary shown to you. Type `/approve` to proceed (or `@AutoApprover` handles it if `AUTO_APPROVE=true`).
7. **EXECUTE** — for each stage:
   - `@CodeWriter` implements the code.
   - `@CodeReviewer` reviews using the code-review-checklist (functionality, quality, architecture, security, performance).
   - If review finds CRITICAL/HIGH issues → `@CodeWriter` fixes them before moving on.
8. **QA FINAL** — `@QA` finalizes the test plan.
9. **CLOSE** — documentation updated, checkpoint written.

**Typical session with pre-approved spec:**

```
> /requirements-pipeline "User authentication with JWT"
  (pipeline runs, spec approved)

> /new-feature "User authentication with JWT"
  Main: Spec found — skipping requirements phase.
  Plan: 4 stages — [JWT service] → [Auth middleware] → [Login endpoint] → [Tests]
  → /approve

  CodeWriter: Stage 1/4 — JWT service ✓
  CodeReviewer: PASS
  CodeWriter: Stage 2/4 — Auth middleware ✓
  CodeReviewer: PASS
  ...
  QA: Final test plan ✓
  CLOSE ✓
```

**Typical session without pre-approved spec (simpler features):**

```
> /new-feature "Add rate-limiting header to API responses"
  Main: Clarify — which module? Backend? Any rate limit value?
  → "module: api, limit: 100 req/min"

  Main: Plan — 2 stages
  → /approve

  CodeWriter: Stage 1/2 — Rate limit middleware ✓
  CodeReviewer: PASS
  CodeWriter: Stage 2/2 — Header injection + tests ✓
  CodeReviewer: PASS
  QA: Final test plan ✓
  CLOSE ✓
```

---

### 3. Testing

**Goal:** walk through test cases interactively, log defects, and re-verify after fixes.

**When it activates:** `@Main` dispatches `@TestRunner` after implementation is complete (QA FINAL phase), or you can request a manual test walkthrough.

**Workflow:**

**GENERATE** — `@TestRunner` reads the spec, requirements, corner cases, and test plan to produce structured test cases:

```
.vault/reference/<module>/test-cases/<feature>-test-cases.md
```

Each test case includes: ID, priority (HIGH/MEDIUM/LOW), type (happy path / edge case / error / security / performance), preconditions, steps, and expected result.

**EXECUTE** — `@TestRunner` presents test cases to you one by one:

```
TC-001: User can log in with valid credentials (Priority: HIGH)
Steps:
  1. Navigate to /login
  2. Enter valid email and password
  3. Click "Sign In"
Expected: Dashboard loads with user greeting

Please enter result:
  ✅ Pass   ❌ Fail   ⏭️ Blocked   ⚠️ Partial   ⏭️ Skip
```

**Defect logging** — when a test fails, a defect is automatically created in the Defects Log:

```
DEF-001: Login returns 500 when email contains "+"
  Severity: HIGH | Related: TC-003 | Status: 🔴 Open
```

**RERUN** — after `@BugFixer` fixes a defect, `@TestRunner` re-presents the failing test cases for re-verification. Defects go through the lifecycle: 🔴 Open → 🟡 In Progress → 🟢 Fixed → verified.

**AMEND** — if requirements change mid-testing, `@TestRunner` adds, updates, or retires test cases with full transaction logging.

**Anti-loop safeguards:** max 3 rerun cycles per defect; max 20 test cases per feature (split by priority if exceeded); if defects exceed test case count, a systemic issue is flagged.

**Typical session:**

```
  @TestRunner: 12 test cases generated (4 happy, 5 edge, 3 error)

  TC-001: Login with valid credentials → ✅ Pass
  TC-002: Login with wrong password → ✅ Pass
  TC-003: Login with "+" in email → ❌ Fail
    → DEF-001 created (HIGH): Login returns 500 for emails with "+"
  TC-004: ... → ✅ Pass

  (after @BugFixer resolves DEF-001)

  @TestRunner: Rerun TC-003
  TC-003: Login with "+" in email → ✅ Pass
  DEF-001: 🔴 Open → 🟢 Fixed
```

---

### 4. Bug fix

**Goal:** root cause a bug, fix it, add a regression test, and prevent recurrence.

**Command:**

```
/fix Login throws 500 when email contains a plus sign
```

**What happens:**

1. **Classify** — `@Main` classifies the issue type:
   - Lint/style → fix directly (max 2 files, compile after each).
   - Compile error → read error, trace to source, fix (max 2 attempts).
   - Test failure → analyze, fix code or test (max 2 attempts).
2. **Fix** — `@BugFixer` performs root cause analysis and implements the fix.
3. **Verify** — after the fix: compile, lint, and affected tests are re-run.
4. **Report** — `Fixed: <what changed>. Build: pass/fail. Lint: pass/fail. Tests: pass/fail.`

**Stop rule:** if the same error persists after 2 attempts, `@BugFixer` escalates to you instead of retrying endlessly.

**Bug retrospective (automatic for systemic bugs):**

After a fix, if the bug points to a systemic issue (missing tests, guideline gap, architectural problem), the `bug-retro` skill runs:

1. **5 Whys** — root cause analysis down to the systemic gap.
2. **Classification** — missing tests, guideline gap, architectural problem, external dependency, human error, race condition, data issue.
3. **Action items** (priority order):
   - CRITICAL: write a regression test (prevents recurrence).
   - HIGH: update or create a project guideline.
   - MEDIUM: update spec or review checklist.
   - LOW: create a refactor task.
4. **Rule:** at least one test or guideline action must be completed before closing the bug.

Retrospective results are saved to `.vault/guidelines/<module>/reports/`.

**Typical session:**

```
> /fix Login throws 500 when email contains a plus sign

  BugFixer: Classified as compile error (URL decode missing)
  Attempt 1: Add URL decode to email parser
  Compile: ✓  Lint: ✓  Tests: ✓
  Fixed: Added URL decoding in EmailParser.parse()
  Build: pass. Lint: pass. Tests: pass.

  BugRetro: Root cause — no input validation guideline for user-supplied emails
  Actions:
    1. [CRITICAL] Regression test added: EmailParserTest.testPlusSignInEmail() ✅
    2. [HIGH] Guideline updated: .vault/guidelines/auth/input-validation.md ✅
```

---

### 5. Review

**Goal:** review code changes for correctness, security, and guideline adherence — without modifying files.

**Command:**

```
/review              (review staged changes)
/review unstaged     (review unstaged changes)
/review all          (review everything)
/review src/auth.rs  (review specific files)
```

**What happens:**

1. **Identify files** — based on scope: `git diff --cached --name-only` (staged), `git diff --name-only` (unstaged), or specified file paths.
2. **Read diffs + full files** — reads `git diff` for each file and the full file for context.
3. **Check against guidelines** — reviews code against `.vault/guidelines/<module>/` rules.
4. **Security check** — input validation, SQL injection, token handling, PII leaks.
5. **Structured report:**

```
# Code Review: staged
**Date:** 2026-05-04
**Files reviewed:** 5

## Issues

### CRITICAL (blocker)
| # | File       | Issue              | Suggestion             |
|---|------------|--------------------|------------------------|
| 1 | src/api.rs | SQL injection in /users/query | Use parameterized query |

### HIGH
| # | File       | Issue              | Suggestion             |
|---|------------|--------------------|------------------------|

### MEDIUM
| # | File       | Issue              | Suggestion             |
|---|------------|--------------------|------------------------|
| 1 | src/util.rs | Magic number 86400 | Use named constant SECONDS_PER_DAY |

## Positive notes
- Clean error handling in auth module
- Good test coverage on edge cases

## Verdict
❌ NEEDS FIXES
```

**Read-only.** The reviewer never edits files — it only reports. Fix issues yourself, or run `/fix` if needed. During `/new-feature`, `@CodeReviewer` uses the same checklist automatically after each `@CodeWriter` stage.

---

### 6. Deploy

**Goal:** safely deploy to staging or production with mandatory build/test gates and a human-in-the-loop confirmation.

**Command:**

```
/deploy staging
/deploy production
```

**What happens:**

1. **Pre-deployment checks (hard gate — no exceptions):**
   - `git status` — working tree must be clean (no uncommitted changes).
   - Compile — `{{COMPILE_COMMAND}}` must pass.
   - Tests — `{{TEST_COMMAND_TEMPLATE}}` all must pass.
   - Lint — `{{LINT_COMMAND}}` must pass.
   - If any check fails → STOP. Report failures. Deployment does not proceed.

2. **HITL gate (mandatory confirmation):**

```
═══════════════════════════════════════
DEPLOYMENT REQUEST
═══════════════════════════════════════
Target: production
Project: my-app
Branch: main
Last commit: a1b2c3f — feat: add JWT auth
Changes since last deploy: 12 commits
═══════════════════════════════════════

Proceed with deployment? (type "deploy now" to confirm)
```

3. **On confirmation:**
   - Build executed: `{{BUILD_COMMAND}}`.
   - Project-specific deploy script runs.
   - Smoke tests run after deploy.
   - Deploy log written to `.opencode/sessions/deploy-<timestamp>.md`.

4. **Report:** `Deployed to production: v2.1.0. Smoke tests: pass.`

**Safety rules:** the HITL gate is never skipped. Deployment never proceeds without a clean build + all tests + all lint checks passing. If you need to force-deploy a broken build, do it outside the kit — the deploy command is designed to prevent that.

**Typical session:**

```
> /deploy staging

  git status: clean ✓
  Compile: ✓
  Tests: 47/47 passed ✓
  Lint: ✓

  ═══ DEPLOYMENT REQUEST ═══
  Target: staging | Branch: feat/jwt | 3 commits
  Type "deploy now" to confirm:
  → deploy now

  Build: ✓  Deploy: ✓  Smoke tests: ✓
  Deployed to staging: feat/jwt-20260504
```

---

## Choose profiles

Combine stack and capability profiles in your manifest's `stack.profiles` list.
Profiles are merged left-to-right; your manifest values always win.

```yaml
stack:
  profiles: [kotlin-jvm-ktor, requirements-pipeline]
  language: kotlin          # from kotlin-jvm-ktor profile (override here if needed)
  build_command: "./gradlew"
  # ...
```

### Stack profiles (pick one)

| Profile | Stack |
|---|---|
| `generic` | Any language — fill everything manually |
| `kotlin-multiplatform` | KMP — Compose Desktop + Android + iOS + Ktor |
| `kotlin-jvm-ktor` | Pure Kotlin/JVM + Ktor backend |
| `java-spring` | Java + Spring Boot |
| `go-gin` | Go + Gin |
| `python-fastapi` | Python + FastAPI |
| `typescript-nextjs` | TypeScript + Next.js |
| `rust-actix` | Rust + Actix-web |
| `csharp-aspnet` | C# + ASP.NET Core |
| `minecraft-paper-plugin` | Minecraft Paper plugin (Kotlin/Gradle KTS) |

### Provider profiles (pick one)

| Profile | Provider |
|---|---|
| `ollama-cloud` | Ollama Cloud LLMs (kimi-k2, qwen3-coder, deepseek-v4) |

### Capability profiles (add any)

| Profile | Adds |
|---|---|
| `requirements-pipeline` | AI-driven requirements pipeline: BA → CCR → QA → SA → Consistency |

> **Backward compatible:** `stack.profile: kotlin-jvm-ktor` (single string) still works.

---

## Agent roster

### Core agents (all profiles)

| Agent | What it does |
|---|---|
| `@Main` | Orchestrator — your single entry point for every task |
| `@CodeWriter` | Implements code, one stage at a time |
| `@CodeReviewer` | Read-only review after each CodeWriter cycle |
| `@BugFixer` | Root cause analysis + fix + regression test |
| `@debugger` | Read-only investigation, produces a failing test |
| `@QA` | Generates implementation test plan (Draft then Final) |
| `@TestRunner` | Generates test cases, guides manual execution, logs defects, manages transactional updates |
| `@Designer` | UI/UX description for visual features (read-only) |
| `@PromptEngineer` | Maintains and improves agent prompts and skills |
| `@AutoApprover` | Automated plan gatekeeper when `AUTO_APPROVE=true` |

### Requirements pipeline subagents (`requirements-pipeline` profile)

Invoked automatically by `@Main` via the `requirements-pipeline` skill — not selected directly.

| Agent | What it does |
|---|---|
| `@BusinessAnalyst` | Drafts and iterates business requirements |
| `@CornerCaseReviewer` | Adversarial attacker — finds gaps in requirements and spec |
| `@RequirementsQA` | Generates test cases from requirements + corner cases |
| `@CoverageChecker` | Verifies every requirement has a test case |
| `@SystemAnalyst` | Generates technical spec from requirements + test plan |
| `@ConsistencyChecker` | Final gate — checks spec does not contradict requirements |

---

## Requirements pipeline (optional)

Use `/requirements-pipeline` before `/new-feature` to get AI-generated, reviewed requirements and a technical spec before writing any code:

```
/requirements-pipeline "Users can reset their password via email link"
```

The pipeline is executed by `@Main` via the `requirements-pipeline` skill: `@BusinessAnalyst` → `@CornerCaseReviewer` (adversarial loop) → `@RequirementsQA` → `@CoverageChecker` → `@SystemAnalyst` → `@ConsistencyChecker`.

When the pipeline finishes, run `/approve` to lock the artifacts, then `/new-feature` — `@Main` picks up the spec automatically and skips the planning phase.

Artifacts land in `.vault/concepts/<module>/` and `.vault/reference/<module>/spec/`.

---

## Updating

Paste this into any AI agent to upgrade an existing installation:

```
Fetch the full update instructions from:
  https://raw.githubusercontent.com/aequicor/opencode-kit/main/docs/prompts/update.md

Read that file completely, then follow every phase in it exactly.
Do not skip steps. Do not guess values.
```

---

## Extending

**Add a profile** — copy `profiles/generic.yaml`, fill in your stack's commands and rules. Add `_profile_name`, `_profile_description`, and `_profile_category: stack|provider|capability` metadata fields.

**Add a skill** — copy `kit/.opencode/skills/look-up/SKILL.md` into `kit/.opencode/skills/your-skill/SKILL.md`.

**Customize an agent** — edit the agent file in `kit/.opencode/agents/` before applying, or edit it directly in the target project after applying.

---

## Requirements

- [OpenCode](https://opencode.ai) v1.1.1+
- Python 3.9+ with PyYAML (`pip install pyyaml`)
- API key for your chosen provider (RouterAI, OpenRouter, etc.)
- Optional: KnowledgeOS running at configured URL for the vault MCP
