You are applying opencode-kit to a project.
Your ONLY job is to follow this script exactly. Do not skip steps. Do not guess values.

KIT REPO: https://github.com/aequicor/opencode-kit
KIT RAW BASE: https://raw.githubusercontent.com/aequicor/opencode-kit/main

You do NOT need to clone the kit. All template files are fetched from GitHub automatically
by apply_remote.py. You only need to:
  1. Ask the user questions and create a local manifest YAML file.
  2. Download apply_remote.py and run it — it fetches kit templates from GitHub.

──────────────────────────────────────────────────
PHASE 1 — COLLECT ALL REQUIRED VARIABLES
──────────────────────────────────────────────────

You MUST ask the user EVERY question below. Present them as a numbered list.
Wait for the user to answer ALL of them before proceeding.
If the user leaves an answer blank, use the [default] shown.

Do NOT proceed to Phase 2 until you have an answer (or explicit blank acceptance) for every question.

## 1. TARGET
   Q1. Target project absolute path: [no default — REQUIRED]
       Directory must exist. The kit will be applied INTO this directory.

## 2. PROJECT
   Q2. Project name: [default: "My Project"]
   Q3. One-line project description: [default: ""]

## 3. STACK PROFILE
   Read this file to list available profiles:
     https://raw.githubusercontent.com/aequicor/opencode-kit/main/profiles/
   Available profiles:
     • kotlin-multiplatform — KMP: Compose Desktop + Android + iOS + Ktor
     • kotlin-jvm-ktor    — Pure Kotlin/JVM Ktor backend
     • generic             — Any language (minimal defaults)
     • ollama-cloud        — DeepSeek V4 Pro + Qwen models via ollama-cloud

   Q4. Which profile? [default: kotlin-multiplatform]
       If the user says "unsure" or gives no answer, ask what language the project uses
       and recommend the best match:
         Kotlin + Multiplatform → kotlin-multiplatform
         Kotlin JVM backend only  → kotlin-jvm-ktor
         Anything else            → generic

## 4. BUILD COMMANDS
   (Only if profile is "generic" OR user wants overrides)
   Q5. Build command:    [default from profile]
   Q6. Compile command:  [default from profile]
   Q7. Lint command:     [default from profile]
   Q8. Test command:     [default from profile]
       If using Gradle, test command must contain [module]
       as a literal placeholder. Example: ./gradlew :[module]:test

## 5. MODULES
   Explain: "A module is a logical unit with its own source root and test root.
   I need this info for each module: name, gradle_module, source_root, test_root,
   docs_path, responsibility."

   Q9. How many modules does your project have? [default: 2]
   For each module, ask:
     a) Module name (short identifier, e.g. "server", "client", "shared"):
        [no default — REQUIRED]
     b) Gradle module path (e.g. ":server", ":composeApp")
        Write "null" if NOT using Gradle. [default: ":<name>"]
     c) Source root (e.g. "server/src/main/kotlin/com/example/"):
        [no default — REQUIRED]
     d) Test root (e.g. "server/src/test/kotlin/com/example/"):
        [no default — REQUIRED]
     e) Docs path (e.g. "docs/server/"): [default: "docs/<name>/"]
     f) Responsibility (one-line): [default: ""]

   If the target project has a settings.gradle.kts or build.gradle.kts,
   read it and extract module names automatically, then confirm with the user.

## 6. PROVIDER
   Q10. Provider name: [default: routerai]
        Display name in opencode.json.
   Q11. Provider base URL (OpenAI-compatible endpoint):
        [default: https://routerai.ru/api/v1]
   Q12. API key ENVIRONMENT VARIABLE NAME — the NAME of the env var,
        NEVER the actual key value:
        [default: ROUTERAI_OPENCODE]

## 7. MODELS (model IDs as recognized by your provider)
   Q13. Default model (orchestrator / @Main):
        [default: moonshotai/kimi-k2.6]
   Q14. Coder model (@CodeWriter, @BugFixer, @debugger, @QA):
        [default: qwen/qwen3-coder-next]
   Q15. Reviewer model (@CodeReviewer, @PromptEngineer):
        [default: deepseek/deepseek-v4-pro]
   Q16. Designer model (@Designer):
        [default: openai/gpt-5.4]
        Set to "null" to omit Designer agent entirely.
   Q17. Small model (lightweight tasks — title/summary):
        [default: same as coder model]

## 8. MCP INTEGRATIONS
   Q18. Enable context7? (external library docs, rate-limited):
        [default: yes]  If yes → Q19. Context7 API key env var NAME: [default: CONTEXT7_API_KEY]
   Q19. Enable KnowledgeOS? (project vault at configured URL):
        [default: yes]  If yes → Q20. KnowledgeOS MCP URL: [default: http://localhost:8085/mcp]
   Q20. Enable serena? (semantic code navigation, JVM-focused):
        [default: yes for Kotlin profiles, no for generic]

## 9. LSP
   Q21. Enable LSP? [default: from profile]
        If yes → Q22. LSP command: [default: kotlin-lsp for Kotlin profiles]
        Q23. File extensions (comma-separated): [default: .kt, .kts for Kotlin]

## 10. UI / DESIGNER
   Q24. UI framework (e.g. "Compose Multiplatform", "React", "SwiftUI"):
        [default: from profile]
        Set to "null" to omit Designer agent entirely.
   Q25. Target platforms (comma-separated):
        [default: from profile, e.g. "Desktop, Android, iOS"]
   Q26. Color palette:
        "Do you have a design system with specific colors?"
        If yes → ask for each color: Name, HEX code (#RRGGBB), Purpose.
        Ask "How many colors?" then ask for each one.
        If no → use profile defaults (with #REPLACE_ME placeholders).

## 11. CODE QUALITY
   Q27. Forbidden patterns:
        "The kit ships with default forbidden patterns for your stack:
          <list defaults from profile>
        Do you want to use these defaults?"
        If yes → keep them.
        If no → ask the user to list their forbidden patterns one at a time.

## 12. FORMATTER
   Q28. Enable auto-formatter? [default: from profile]
        If yes → Q29. Formatter name: [default: from profile]
        Q30. Formatter command (as a list): [default: from profile]
        Q31. File extensions for formatting (comma-separated): [default: from profile]

──────────────────────────────────────────────────
PHASE 2 — CREATE THE MANIFEST FILE
──────────────────────────────────────────────────

1. Read the chosen profile YAML from GitHub:
     https://raw.githubusercontent.com/aequicor/opencode-kit/main/profiles/<chosen-profile>.yaml
   This gives you all the profile defaults (build commands, forbidden patterns, etc.).

2. Read manifest.example.yaml from GitHub:
     https://raw.githubusercontent.com/aequicor/opencode-kit/main/manifest.example.yaml
   This gives you the structure and comments.

3. Create a file named "<project-slug>.yaml" **in the target project directory**.
   Write it using the EXACT structure from manifest.example.yaml.
   Merge: profile defaults + user's answers.
   User answers ALWAYS override profile defaults.

   CRITICAL RULES:
   - api_key_env must contain ONLY the env var NAME (e.g. "ROUTERAI_OPENCODE"),
     never an actual key. If what was provided looks like a key (long string
     with dashes/underscores), REJECT it and re-ask Q12.
   - context7 api_key_env: same rule — env var NAME only.
   - model IDs: use the EXACT string the user provided (or default).
   - designer model: if user said "null", write `designer: null`.
   - ui.framework: if user said "null", write `framework: null`.
   - gradle_module: if user said "null", write `gradle_module: null`.
   - For every field you are unsure about, add: `# TODO: verify this`

4. Show the completed manifest to the user and ask:
   "Does this look correct? (yes/no/edit X)"
   If the user says "edit X", go back and change that field.
   Repeat until the user confirms.

──────────────────────────────────────────────────
PHASE 3 — APPLY THE KIT (NO CLONE NEEDED)
──────────────────────────────────────────────────

The apply_remote.py script is self-contained — it downloads all kit templates from GitHub
at runtime. You do NOT need to clone the repository.

1. Download the apply script into the target project directory:
     curl -sL https://raw.githubusercontent.com/aequicor/opencode-kit/main/scripts/apply_remote.py \
       -o <target-path>/apply_remote.py
   (If curl is not available, use wget:
     wget -q https://raw.githubusercontent.com/aequicor/opencode-kit/main/scripts/apply_remote.py \
       -O <target-path>/apply_remote.py
   )

2. Make sure PyYAML is installed:
     pip install pyyaml
   (If pip is not found, try pip3 install pyyaml)

3. Dry run — preview what will be created:
     python3 <target-path>/apply_remote.py --manifest <target-path>/<manifest>.yaml --target <target-path> --dry-run

   If python3 is not found, try python instead.

4. Show the dry-run output to the user.
   Ask: "Proceed with apply? (yes/no)"

5. If user says yes, run the same command WITHOUT --dry-run:
     python3 <target-path>/apply_remote.py --manifest <target-path>/<manifest>.yaml --target <target-path>

   If the script reports SKIP for any files because they already exist,
   STOP and ask the user: "Some files already exist. Use --merge to overwrite? (yes/no)"
   If yes, re-run with --merge flag.
   If no, abort.

6. If apply_remote.py fails with "PyYAML is required", run `pip install pyyaml` and retry.
   If apply_remote.py fails with any other error, report it to the user and STOP.

7. After successful apply, clean up:
     rm <target-path>/apply_remote.py

──────────────────────────────────────────────────
PHASE 4 — VERIFY THE OUTPUT
──────────────────────────────────────────────────

1. Read the generated <target>/opencode.json.
   Verify: apiKey field contains "{env:VAR_NAME}" syntax, NOT a literal key.
   If it contains a literal key, this is a SECURITY ERROR — abort and fix the manifest.

2. List all files in <target>/.opencode/agents/.
   Verify exactly 9 agent files exist:
     Main.md, CodeWriter.md, CodeReviewer.md, BugFixer.md,
     debugger.md, QA.md, Designer.md, PromptEngineer.md, AutoApprover.md
   If Designer was disabled, Designer.md may be absent — that's OK.
   Report which agents are present.

3. Read <target>/.opencode/_shared.md.
   Verify the Project Context section at the top reflects the actual project.
   Check that the MODULE TABLE contains the correct modules.
   Report any mismatches.

4. Run the compile command from the manifest (e.g. ./gradlew compileKotlin)
   FROM THE TARGET DIRECTORY.
   Report success or failure.

──────────────────────────────────────────────────
PHASE 5 — ENVIRONMENT VARIABLES REMINDER
──────────────────────────────────────────────────

Print EXACTLY this message:

  ═══════════════════════════════════════════════
  KIT APPLIED SUCCESSFULLY
  ═══════════════════════════════════════════════

  Files created in <target>:
    <list of files created>

  Before running opencode, set these environment variables:
    export <PROVIDER_API_KEY_ENV>=<your_api_key>
    export <CONTEXT7_API_KEY_ENV>=<your_context7_key>   (if context7 enabled)

  Quick start:
    cd <target>
    export <PROVIDER_API_KEY_ENV>=<your_api_key>
    opencode         # launches with @Main orchestrator

  To add to your shell profile permanently:
    echo 'export <PROVIDER_API_KEY_ENV>=<your_api_key>' >> ~/.zshrc

  If any TODO fields remain in the manifest, fix them before relying on agents.

  Report back a summary of what was done.
