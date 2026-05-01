import datetime


def _build_module_table(modules: list) -> str:
    header = "| Module | Gradle module | Docs | Responsibility |\n"
    separator = "|--------|---------------|------|----------------|\n"
    rows = []
    for m in modules:
        gradle = m.get("gradle_module") or "\u2014"
        rows.append(
            f"| `{m['name']}` | `{gradle}` | `{m['docs_path']}` | {m.get('responsibility', '')} |"
        )
    return header + separator + "\n".join(rows)


def _build_source_table(modules: list) -> str:
    header = "| Module | Gradle task | Source root |\n"
    separator = "|--------|-------------|-------------|\n"
    rows = []
    for m in modules:
        gradle = m.get("gradle_module") or "\u2014"
        rows.append(f"| {m['name']} | `{gradle}` | `{m['source_root']}` |")
    return header + separator + "\n".join(rows)


def _build_test_table(modules: list) -> str:
    header = "| Module | Test root |\n"
    separator = "|--------|----------|\n"
    rows = []
    for m in modules:
        rows.append(f"| `{m['name']}` | `{m['test_root']}` |")
    return header + separator + "\n".join(rows)


def _build_module_build_commands(modules: list, stack: dict) -> str:
    build = stack.get("build_command", "./gradlew")
    lines = []
    for m in modules:
        gradle = m.get("gradle_module")
        if gradle:
            lines.append(f"{build} {gradle}:build")
        else:
            lines.append(f"# build command for {m['name']}: {build} build")
    return "\n".join(lines)


def _build_color_table(colors: list) -> str:
    if not colors:
        return "| Color | HEX | Purpose |\n|-------|-----|---------|\n| (fill in your project colors) | `#000000` | \u2014 |"
    header = "| Color | HEX | Purpose |\n"
    separator = "|-------|-----|------------------|\n"
    rows = [f"| {c['name']} | `{c['hex']}` | {c['purpose']} |" for c in colors]
    return header + separator + "\n".join(rows)


def _build_forbidden_list(patterns: list) -> str:
    return "\n".join(f"- {p}" for p in patterns)


def _build_formatter_block(stack: dict, formatter_cfg: dict) -> str:
    if not formatter_cfg.get("enabled", False):
        return ""
    fmt_name = formatter_cfg.get("name", stack.get("language", "default") + "-fmt")
    command = formatter_cfg.get("command", [stack.get("build_command", ""), "lint"])
    extensions = formatter_cfg.get("extensions", [])
    ext_json = ", ".join(f'"{e}"' for e in extensions)
    env_block = ""
    if formatter_cfg.get("environment"):
        env_items = []
        for k, v in formatter_cfg.get("environment", {}).items():
            env_items.append(f'        "{k}": "{v}"')
        env_block = ',\n      "environment": {\n' + ",\n".join(env_items) + "\n      }"
    cmd_json = ", ".join(f'"{c}"' for c in command)
    return f'''  "formatter": {{
    "{fmt_name}": {{
      "command": [{cmd_json}],
      "extensions": [{ext_json}]{env_block}
    }}
  }},'''


def _build_lsp_block(lsp: dict) -> str:
    if not lsp.get("enabled", False):
        return ""
    command = lsp.get("command", "")
    extensions = lsp.get("extensions", [])
    ext_json = ", ".join(f'"{e}"' for e in extensions)
    lang = command.replace("-lsp", "").replace("_lsp", "") or "default"
    return f'''  "lsp": {{
    "{lang}": {{
      "command": [
        "{command}"
      ],
      "extensions": [
        {ext_json}
      ]
    }}
  }},'''


def _build_module_docs_list(modules: list) -> str:
    return "\n".join(f"- `{m['docs_path']}`" for m in modules)


def _build_module_names_list(modules: list) -> str:
    return " / ".join(m["name"] for m in modules)


def _build_cursor_globs(lsp: dict, stack: dict) -> str:
    extensions = lsp.get("extensions", [])
    if extensions:
        globs = [f'"**/*{ext}"' for ext in extensions]
    else:
        lang = stack.get("language", "generic")
        lang_globs = {
            "kotlin": ['"**/*.kt"', '"**/*.kts"'],
            "typescript": ['"**/*.ts"', '"**/*.tsx"', '"**/*.js"', '"**/*.jsx"'],
            "python": ['"**/*.py"'],
            "go": ['"**/*.go"'],
            "rust": ['"**/*.rs"'],
        }
        globs = lang_globs.get(lang, ['"**/*"'])
    return ", ".join(globs)


def _build_formatter_hook(formatter_cfg: dict) -> str:
    if not formatter_cfg.get("enabled", False):
        return ""
    return " ".join(formatter_cfg.get("command", []))


def _build_deps_files(stack: dict) -> str:
    lang = stack.get("language", "generic")
    deps_map = {
        "kotlin": "- `gradle/libs.versions.toml` (if exists) or `build.gradle.kts` deps",
        "python": "- `requirements.txt` / `pyproject.toml` dependencies",
        "typescript": "- `package.json` dependencies + devDependencies",
        "go": "- `go.mod` dependencies",
        "rust": "- `Cargo.toml` dependencies",
        "java": "- `gradle/libs.versions.toml` (if exists) or `build.gradle.kts` deps",
    }
    return deps_map.get(lang, "- Primary dependency manifest file")


def _build_module_dependency_list(modules: list) -> str:
    if not modules:
        return "(none — no modules defined)"
    lines = []
    for m in modules:
        deps = m.get("module_dependencies", "")
        lines.append(f"- `{m['name']}`: {deps}" if deps else f"- `{m['name']}`: (none specified)")
    return "\n".join(lines)


def _build_module_gradle_line(module: dict) -> str:
    gradle = module.get("gradle_module")
    if gradle:
        return f"**Gradle module:** `{gradle}`"
    return "**Gradle:** (not a Gradle project)"


def _build_module_build_table(module: dict, stack: dict) -> str:
    build = stack.get("build_command", "./gradlew")
    compile_cmd = stack.get("compile_command", "./gradlew compileKotlin")
    gradle = module.get("gradle_module")
    if gradle:
        return (
            f"| `{build} {gradle}:build` | Build this module |\n"
            f"| `{build} {gradle}:test` | Run tests |\n"
            f"| `{build} {gradle}:compileKotlin` | Quick compile |"
        )
    return (
        f"| `{build}` | Build project |\n"
        f"| `{stack.get('test_command', build + ' test')}` | Run tests |\n"
        f"| `{compile_cmd}` | Quick compile |"
    )


def _build_eval_template(agent_name: str, project_name: str) -> str:
    eval_id = agent_name.lower().replace("@", "")
    return f"""---
id: eval-{eval_id}-001
description: Basic smoke test for @{agent_name} — classification loop
agent: {agent_name}
input: "Classify this task: add a login endpoint to the server module"
expected_patterns:
  - "CLARIFY"
  - "Which module"
forbidden_patterns:
  - "I don't know how"
max_steps: 5
weight: 1.0
---
"""


def _build_eval_globs(lsp: dict) -> str:
    extensions = lsp.get("extensions", [])
    if extensions:
        return ", ".join(f'"{ext}"' for ext in extensions)
    return '"*"'


def _build_nested_context(module: dict, stack: dict, project_name: str) -> dict:
    return {
        "MODULE_NAME": module.get("name", ""),
        "MODULE_SOURCE_ROOT": module.get("source_root", ""),
        "MODULE_TEST_ROOT": module.get("test_root", ""),
        "MODULE_RESPONSIBILITY": module.get("responsibility", ""),
        "MODULE_GRADLE_LINE": _build_module_gradle_line(module),
        "MODULE_BUILD_TABLE": _build_module_build_table(module, stack),
        "MODULE_CONVENTIONS": module.get(
            "conventions", "(use project-default conventions from root AGENTS.md)"
        ),
        "MODULE_DEPENDENCIES": _build_module_dependency_list([module]),
        "MODULE_DOCS_PATH": module.get("docs_path", f"docs/{module.get('name', '')}/"),
    }


def build_context(manifest: dict) -> dict:
    project = manifest.get("project", {})
    stack = manifest.get("stack", {})
    modules = manifest.get("modules", [])
    provider = manifest.get("provider", {})
    models = manifest.get("models", {})
    mcp = manifest.get("mcp", {})
    lsp = manifest.get("lsp", {})
    ui = manifest.get("ui", {})
    code_quality = manifest.get("code_quality", {})

    provider_name = provider.get("name", "routerai")
    provider_id = provider_name.lower().replace(" ", "_").replace("-", "_")

    context7_cfg = mcp.get("context7", {})
    knowledge_cfg = mcp.get("knowledge", {})
    serena_cfg = mcp.get("serena", {})

    ui_framework = ui.get("framework") or ""
    colors = ui.get("colors", [])
    platforms = ui.get("platforms", [])

    default_model = models.get("default", "moonshotai/kimi-k2.6")
    coder_model = models.get("coder", "qwen/qwen3-coder-next")
    reviewer_model = models.get("reviewer", "deepseek/deepseek-v4-pro")
    designer_model = models.get("designer") or coder_model

    return {
        "PROJECT_NAME": project.get("name", "My Project"),
        "PROJECT_DESCRIPTION": project.get("description", ""),
        "BUILD_COMMAND": stack.get("build_command", "./gradlew"),
        "COMPILE_COMMAND": stack.get("compile_command", "./gradlew compileKotlin"),
        "LINT_COMMAND": stack.get("lint_command", "./gradlew detekt ktlintCheck"),
        "TEST_COMMAND_TEMPLATE": stack.get("test_command", "./gradlew :[module]:test"),
        "STACK_DESCRIPTION": f"{project.get('name', 'Project')} \u2014 {stack.get('language', 'Kotlin')} stack",
        "MODULE_TABLE": _build_module_table(modules),
        "MODULE_SOURCE_TABLE": _build_source_table(modules),
        "MODULE_TEST_TABLE": _build_test_table(modules),
        "MODULE_BUILD_COMMANDS": _build_module_build_commands(modules, stack),
        "MODULE_NAMES_LIST": _build_module_names_list(modules),
        "MODULE_DOCS_LIST": _build_module_docs_list(modules),
        "PROVIDER_ID": provider_id,
        "PROVIDER_NAME": provider_name,
        "PROVIDER_BASE_URL": provider.get("base_url", "https://routerai.ru/api/v1"),
        "PROVIDER_API_KEY_ENV": provider.get("api_key_env", "PROVIDER_API_KEY"),
        "DEFAULT_MODEL": default_model,
        "CODER_MODEL": coder_model,
        "REVIEWER_MODEL": reviewer_model,
        "DESIGNER_MODEL": designer_model,
        "SMALL_MODEL": models.get("small", coder_model),
        "ISO_TIMESTAMP_PLACEHOLDER": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "CONTEXT7_ENABLED": str(context7_cfg.get("enabled", True)).lower(),
        "CONTEXT7_API_KEY_ENV": context7_cfg.get("api_key_env", "CONTEXT7_API_KEY"),
        "KNOWLEDGE_ENABLED": str(knowledge_cfg.get("enabled", True)).lower(),
        "KNOWLEDGE_URL": knowledge_cfg.get("url", "http://localhost:8085/mcp"),
        "SERENA_ENABLED": str(serena_cfg.get("enabled", True)).lower(),
        "LSP_BLOCK": _build_lsp_block(lsp),
        "UI_FRAMEWORK": ui_framework,
        "PLATFORMS": ", ".join(platforms),
        "COLOR_TABLE": _build_color_table(colors),
        "FORBIDDEN_PATTERNS_LIST": _build_forbidden_list(
            code_quality.get("forbidden_patterns", [])
        ),
        "FORMATTER_BLOCK": _build_formatter_block(stack, manifest.get("formatter", {})),
        "FORMATTER_HOOK_COMMAND": _build_formatter_hook(manifest.get("formatter", {})),
        "CURSOR_GLOB_EXTENSIONS": _build_cursor_globs(lsp, stack),
        "DEPENDENCY_FILES_LIST": _build_deps_files(stack),
        "EVAL_GLOB_EXTENSIONS": _build_eval_globs(lsp),
    }
