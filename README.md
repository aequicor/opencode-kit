# opencode-kit

AI agent configuration framework for [OpenCode](https://opencode.ai). Gives your project a full orchestrated development workflow — requirements, planning, coding, review, QA — driven by a team of specialized agents.

**Requires OpenCode v1.1.1+**

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
# Edit my-project.yaml — fill in project name, modules, provider, models

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

> **Note:** Only `@Main` and `@RequirementsPipeline` are meant to be selected directly by you. All other agents (`@CodeWriter`, `@QA`, `@BugFixer`, etc.) are subagents — they are invoked automatically and should not be selected manually.

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

## Choose a profile

Pick the profile closest to your stack when creating your manifest:

| Profile | Stack |
|---|---|
| `ollama-cloud.yaml` | **Default** — Ollama Cloud LLMs (kimi-k2, qwen3-coder, deepseek-v4) |
| `generic.yaml` | Any language — fill everything manually |
| `kotlin-multiplatform.yaml` | KMP — Compose Desktop + Android + iOS + Ktor |
| `kotlin-jvm-ktor.yaml` | Pure Kotlin/JVM + Ktor backend |
| `java-spring.yaml` | Java + Spring Boot |
| `go-gin.yaml` | Go + Gin |
| `python-fastapi.yaml` | Python + FastAPI |
| `typescript-nextjs.yaml` | TypeScript + Next.js |
| `rust-actix.yaml` | Rust + Actix-web |
| `csharp-aspnet.yaml` | C# + ASP.NET Core |
| `minecraft-paper-plugin.yaml` | Minecraft Paper plugin (Kotlin/Gradle KTS) |
| `requirements-pipeline.yaml` | Any language + AI-driven requirements pipeline |

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
| `@Designer` | UI/UX description for visual features (read-only) |
| `@PromptEngineer` | Maintains and improves agent prompts and skills |
| `@AutoApprover` | Automated plan gatekeeper when `AUTO_APPROVE=true` |

### Requirements pipeline agents (`requirements-pipeline` profile)

| Agent | What it does |
|---|---|
| `@RequirementsPipeline` | Orchestrates the full BA → spec pipeline |
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

The pipeline runs: `@BusinessAnalyst` → `@CornerCaseReviewer` (adversarial loop) → `@RequirementsQA` → `@CoverageChecker` → `@SystemAnalyst` → `@ConsistencyChecker`.

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

**Add a profile** — copy `profiles/generic.yaml`, fill in your stack's commands and rules.

**Add a skill** — copy `kit/.opencode/skills/look-up/SKILL.md` into `kit/.opencode/skills/your-skill/SKILL.md`.

**Customize an agent** — edit the agent file in `kit/.opencode/agents/` before applying, or edit it directly in the target project after applying.

---

## Requirements

- [OpenCode](https://opencode.ai) v1.1.1+
- Python 3.9+ with PyYAML (`pip install pyyaml`)
- API key for your chosen provider (RouterAI, OpenRouter, etc.)
- Optional: KnowledgeOS running at configured URL for the vault MCP
