"""
Unit tests for opencode-kit core and apply scripts.
Run: python -m pytest tests/ -v
"""

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import apply as apply_mod
from core import (
    build_context,
    check_unresolved,
    create_docs_scaffold,
    get_target_path,
    kit_path_to_target,
    render,
    verify_output,
)
from core import (
    check_credentials as _check_credentials,
)
from core import (
    check_kit_version as _check_kit_version,
)
from core.context import _build_formatter_hook, _build_nested_context
from core.version import KIT_VERSION

# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

MINIMAL_MANIFEST = {
    "kit_version": "1.4.0",
    "editors": ["opencode"],
    "project": {"name": "Test Project", "description": "A test project"},
    "stack": {
        "language": "kotlin",
        "build_command": "./gradlew",
        "compile_command": "./gradlew compileKotlin",
        "lint_command": "./gradlew detekt",
        "test_command": "./gradlew :app:test",
    },
    "modules": [
        {
            "name": "app",
            "gradle_module": ":app",
            "source_root": "app/src/main/kotlin/",
            "test_root": "app/src/test/kotlin/",
            "responsibility": "Main application",
        }
    ],
    "provider": {
        "name": "routerai",
        "base_url": "https://routerai.ru/api/v1",
        "api_key_env": "ROUTERAI_KEY",
    },
    "models": {
        "default": "moonshotai/kimi-k2.6",
        "coder": "qwen/qwen3-coder",
        "reviewer": "deepseek/deepseek-v4-pro",
    },
    "mcp": {
        "context7": {"enabled": True, "api_key_env": "CONTEXT7_KEY"},
        "knowledge": {"enabled": False},
        "serena": {"enabled": True},
    },
    "lsp": {"enabled": True, "command": "kotlin-lsp", "extensions": [".kt", ".kts"]},
    "ui": {"framework": None},
    "code_quality": {"forbidden_patterns": ["!! operator", "GlobalScope.launch"]},
    "formatter": {
        "enabled": True,
        "name": "ktlint",
        "command": ["./gradlew", "ktlintFormat"],
        "extensions": [".kt", ".kts"],
    },
}


# ─────────────────────────────────────────────
# build_context tests
# ─────────────────────────────────────────────


def test_build_context_project_fields():
    ctx = build_context(MINIMAL_MANIFEST)
    assert ctx["PROJECT_NAME"] == "Test Project"
    assert ctx["PROJECT_DESCRIPTION"] == "A test project"


def test_build_context_stack_commands():
    ctx = build_context(MINIMAL_MANIFEST)
    assert ctx["BUILD_COMMAND"] == "./gradlew"
    assert ctx["COMPILE_COMMAND"] == "./gradlew compileKotlin"
    assert ctx["LINT_COMMAND"] == "./gradlew detekt"
    assert ctx["TEST_COMMAND_TEMPLATE"] == "./gradlew :app:test"


def test_build_context_models():
    ctx = build_context(MINIMAL_MANIFEST)
    assert ctx["DEFAULT_MODEL"] == "moonshotai/kimi-k2.6"
    assert ctx["CODER_MODEL"] == "qwen/qwen3-coder"
    assert ctx["REVIEWER_MODEL"] == "deepseek/deepseek-v4-pro"
    assert ctx["DESIGNER_MODEL"] == "qwen/qwen3-coder"


def test_build_context_module_table():
    ctx = build_context(MINIMAL_MANIFEST)
    assert "app" in ctx["MODULE_TABLE"]
    assert ":app" in ctx["MODULE_TABLE"]
    assert ".vault/app/" in ctx["MODULE_TABLE"]


def test_build_context_forbidden_list():
    ctx = build_context(MINIMAL_MANIFEST)
    assert "- !! operator" in ctx["FORBIDDEN_PATTERNS_LIST"]
    assert "- GlobalScope.launch" in ctx["FORBIDDEN_PATTERNS_LIST"]


def test_build_context_cursor_globs_from_lsp():
    ctx = build_context(MINIMAL_MANIFEST)
    assert '"**/*.kt"' in ctx["CURSOR_GLOB_EXTENSIONS"]
    assert '"**/*.kts"' in ctx["CURSOR_GLOB_EXTENSIONS"]


def test_build_context_cursor_globs_fallback_by_language():
    manifest = dict(MINIMAL_MANIFEST)
    manifest["lsp"] = {"enabled": False}
    ctx = build_context(manifest)
    assert '"**/*.kt"' in ctx["CURSOR_GLOB_EXTENSIONS"]


def test_build_context_typescript_globs():
    manifest = dict(MINIMAL_MANIFEST)
    manifest["stack"] = dict(MINIMAL_MANIFEST["stack"])
    manifest["stack"]["language"] = "typescript"
    manifest["lsp"] = {"enabled": False}
    ctx = build_context(manifest)
    assert '"**/*.ts"' in ctx["CURSOR_GLOB_EXTENSIONS"]
    assert '"**/*.tsx"' in ctx["CURSOR_GLOB_EXTENSIONS"]


def test_build_context_lsp_block():
    ctx = build_context(MINIMAL_MANIFEST)
    assert '"kotlin"' in ctx["LSP_BLOCK"]
    assert '"kotlin-lsp"' in ctx["LSP_BLOCK"]


def test_build_context_lsp_disabled():
    manifest = dict(MINIMAL_MANIFEST)
    manifest["lsp"] = {"enabled": False}
    ctx = build_context(manifest)
    assert ctx["LSP_BLOCK"] == ""


def test_build_context_formatter_block():
    ctx = build_context(MINIMAL_MANIFEST)
    assert "ktlint" in ctx["FORMATTER_BLOCK"]
    assert "ktlintFormat" in ctx["FORMATTER_BLOCK"]


def test_build_context_formatter_disabled():
    manifest = dict(MINIMAL_MANIFEST)
    manifest["formatter"] = {"enabled": False}
    ctx = build_context(manifest)
    assert ctx["FORMATTER_BLOCK"] == ""


# ─────────────────────────────────────────────
# render tests
# ─────────────────────────────────────────────


def test_render_basic():
    result = render("Hello {{NAME}}!", {"NAME": "World"})
    assert result == "Hello World!"


def test_render_multiple_keys():
    result = render("{{A}} + {{B}} = {{C}}", {"A": "1", "B": "2", "C": "3"})
    assert result == "1 + 2 = 3"


def test_render_no_placeholders():
    result = render("plain text", {"KEY": "val"})
    assert result == "plain text"


def test_check_unresolved_detects():
    unresolved = check_unresolved("{{A}} and {{UNSET}}", "test.md")
    assert "{{A}}" in unresolved
    assert "{{UNSET}}" in unresolved


def test_check_unresolved_empty():
    unresolved = check_unresolved("all resolved", "test.md")
    assert unresolved == []


# ─────────────────────────────────────────────
# get_target_path tests
# ─────────────────────────────────────────────


def test_get_target_path_template_stripping():
    kit_root = Path("/kit")
    target_root = Path("/project")
    kit_file = Path("/kit/opencode.json.template")
    result = get_target_path(kit_file, kit_root, target_root)
    assert result == Path("/project/opencode.json")


def test_get_target_path_non_template():
    kit_root = Path("/kit")
    target_root = Path("/project")
    kit_file = Path("/kit/.opencode/commands/resume.md")
    result = get_target_path(kit_file, kit_root, target_root)
    assert result == Path("/project/.opencode/commands/resume.md")


def test_get_target_path_editor_prefix_stripped():
    kit_root = Path("/kit")
    target_root = Path("/project")
    kit_file = Path("/kit/editors/opencode/CLAUDE.md.template")
    result = get_target_path(kit_file, kit_root, target_root)
    assert result == Path("/project/CLAUDE.md")


def test_get_target_path_cursor_nested():
    kit_root = Path("/kit")
    target_root = Path("/project")
    kit_file = Path("/kit/editors/cursor/.cursor/rules/conventions.mdc.template")
    result = get_target_path(kit_file, kit_root, target_root)
    assert result == Path("/project/.cursor/rules/conventions.mdc")


def test_get_target_path_copilot():
    kit_root = Path("/kit")
    target_root = Path("/project")
    kit_file = Path("/kit/editors/copilot/.github/copilot-instructions.md.template")
    result = get_target_path(kit_file, kit_root, target_root)
    assert result == Path("/project/.github/copilot-instructions.md")


def test_kit_path_to_target_template():
    result = kit_path_to_target("kit/opencode.json.template")
    assert result == "opencode.json"


def test_kit_path_to_target_editor():
    result = kit_path_to_target("kit/editors/cursor/.cursor/rules/conventions.mdc.template")
    assert result == str(Path(".cursor/rules/conventions.mdc"))


# ─────────────────────────────────────────────
# _check_credentials tests
# ─────────────────────────────────────────────


def test_check_credentials_valid_env_name():
    manifest = {"provider": {"api_key_env": "MY_API_KEY"}, "mcp": {}}
    _check_credentials(manifest)


def test_check_credentials_rejects_long_key():
    manifest = {
        "provider": {"api_key_env": "sk-" + "a" * 50},
        "mcp": {},
    }
    with pytest.raises(SystemExit):
        _check_credentials(manifest)


def test_check_credentials_rejects_mcp_secret():
    manifest = {
        "provider": {"api_key_env": "MY_KEY"},
        "mcp": {"context7": {"api_key": "real_secret_key_value_1234567890abc"}},
    }
    with pytest.raises(SystemExit):
        _check_credentials(manifest)


# ─────────────────────────────────────────────
# _check_kit_version tests
# ─────────────────────────────────────────────


def test_check_kit_version_match(capsys):
    manifest = {"kit_version": KIT_VERSION}
    _check_kit_version(manifest)
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out


def test_check_kit_version_mismatch_exits(capsys):
    manifest = {"kit_version": "0.0.1"}
    with pytest.raises(SystemExit) as exc_info:
        _check_kit_version(manifest)
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "ERROR" in captured.out


def test_check_kit_version_missing_no_warning(capsys):
    manifest = {}
    _check_kit_version(manifest)
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out


# ─────────────────────────────────────────────
# Full apply integration test
# ─────────────────────────────────────────────


def test_apply_dry_run_does_not_write_files(tmp_path):
    manifest_file = tmp_path / "manifest.yaml"
    target_dir = tmp_path / "project"
    target_dir.mkdir()

    with open(manifest_file, "w") as f:
        yaml.dump(MINIMAL_MANIFEST, f)

    apply_mod.apply(
        manifest_path=str(manifest_file),
        target_dir=str(target_dir),
        dry_run=True,
        merge=False,
    )

    target_files = list(target_dir.rglob("*"))
    non_gitkeep = [f for f in target_files if f.is_file() and f.name != ".gitkeep"]
    assert len(non_gitkeep) == 0


def test_apply_creates_agents(tmp_path):
    manifest_file = tmp_path / "manifest.yaml"
    target_dir = tmp_path / "project"
    target_dir.mkdir()

    with open(manifest_file, "w") as f:
        yaml.dump(MINIMAL_MANIFEST, f)

    apply_mod.apply(
        manifest_path=str(manifest_file),
        target_dir=str(target_dir),
        dry_run=False,
        merge=False,
    )

    agents_dir = target_dir / ".opencode" / "agents"
    assert agents_dir.exists(), ".opencode/agents/ should be created"
    assert (agents_dir / "Main.md").exists()
    assert (agents_dir / "CodeWriter.md").exists()
    assert (agents_dir / "CodeReviewer.md").exists()


def test_apply_creates_agents_md(tmp_path):
    manifest_file = tmp_path / "manifest.yaml"
    target_dir = tmp_path / "project"
    target_dir.mkdir()

    with open(manifest_file, "w") as f:
        yaml.dump(MINIMAL_MANIFEST, f)

    apply_mod.apply(
        manifest_path=str(manifest_file),
        target_dir=str(target_dir),
        dry_run=False,
        merge=False,
    )

    agents_md = target_dir / "AGENTS.md"
    assert agents_md.exists(), "AGENTS.md should be created"
    content = agents_md.read_text()
    assert "Test Project" in content
    assert "## Build and Test Commands" in content


def test_apply_opencode_editor_creates_claude_md(tmp_path):
    manifest_file = tmp_path / "manifest.yaml"
    target_dir = tmp_path / "project"
    target_dir.mkdir()

    with open(manifest_file, "w") as f:
        yaml.dump(MINIMAL_MANIFEST, f)

    apply_mod.apply(
        manifest_path=str(manifest_file),
        target_dir=str(target_dir),
        dry_run=False,
        merge=False,
    )

    claude_md = target_dir / "CLAUDE.md"
    assert claude_md.exists(), "CLAUDE.md should be created for opencode editor"
    content = claude_md.read_text()
    assert "@AGENTS.md" in content


def test_apply_cursor_editor_creates_mdc(tmp_path):
    manifest = {**MINIMAL_MANIFEST, "editors": ["opencode", "cursor"]}
    manifest_file = tmp_path / "manifest.yaml"
    target_dir = tmp_path / "project"
    target_dir.mkdir()

    with open(manifest_file, "w") as f:
        yaml.dump(manifest, f)

    apply_mod.apply(
        manifest_path=str(manifest_file),
        target_dir=str(target_dir),
        dry_run=False,
        merge=False,
    )

    mdc = target_dir / ".cursor" / "rules" / "conventions.mdc"
    assert mdc.exists(), ".cursor/rules/conventions.mdc should be created"


def test_apply_copilot_editor_creates_instructions(tmp_path):
    manifest = {**MINIMAL_MANIFEST, "editors": ["opencode", "copilot"]}
    manifest_file = tmp_path / "manifest.yaml"
    target_dir = tmp_path / "project"
    target_dir.mkdir()

    with open(manifest_file, "w") as f:
        yaml.dump(manifest, f)

    apply_mod.apply(
        manifest_path=str(manifest_file),
        target_dir=str(target_dir),
        dry_run=False,
        merge=False,
    )

    instructions = target_dir / ".github" / "copilot-instructions.md"
    assert instructions.exists(), ".github/copilot-instructions.md should be created"


def test_apply_skip_existing_without_merge(tmp_path):
    manifest_file = tmp_path / "manifest.yaml"
    target_dir = tmp_path / "project"
    target_dir.mkdir()

    with open(manifest_file, "w") as f:
        yaml.dump(MINIMAL_MANIFEST, f)

    agents_md = target_dir / "AGENTS.md"
    agents_md.write_text("ORIGINAL CONTENT")

    apply_mod.apply(
        manifest_path=str(manifest_file),
        target_dir=str(target_dir),
        dry_run=False,
        merge=False,
    )

    assert agents_md.read_text() == "ORIGINAL CONTENT"


def test_apply_overwrites_with_merge(tmp_path):
    manifest_file = tmp_path / "manifest.yaml"
    target_dir = tmp_path / "project"
    target_dir.mkdir()

    with open(manifest_file, "w") as f:
        yaml.dump(MINIMAL_MANIFEST, f)

    agents_md = target_dir / "AGENTS.md"
    agents_md.write_text("ORIGINAL CONTENT")

    apply_mod.apply(
        manifest_path=str(manifest_file),
        target_dir=str(target_dir),
        dry_run=False,
        merge=True,
    )

    content = agents_md.read_text()
    assert content != "ORIGINAL CONTENT"
    assert "Test Project" in content


# ─────────────────────────────────────────────
# verify_output tests
# ─────────────────────────────────────────────


def test_verify_output_missing_agent(tmp_path):
    target = tmp_path / "project"
    agents_dir = target / ".opencode" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "Main.md").write_text("")

    warnings = verify_output(target, {"PROVIDER_API_KEY_ENV": "TEST_KEY"})
    assert any("CodeWriter.md" in w for w in warnings)


def test_verify_output_valid_json(tmp_path):
    target = tmp_path / "project"
    agents_dir = target / ".opencode" / "agents"
    agents_dir.mkdir(parents=True)
    for agent in [
        "Main.md",
        "CodeWriter.md",
        "CodeReviewer.md",
        "BugFixer.md",
        "debugger.md",
        "QA.md",
        "Designer.md",
        "AutoApprover.md",
        "PromptEngineer.md",
    ]:
        (agents_dir / agent).write_text("")

    opencode_json = target / "opencode.json"
    opencode_json.write_text('{"apiKey": "{env:MY_KEY}"}')

    warnings = verify_output(target, {"PROVIDER_API_KEY_ENV": "MY_KEY"})
    assert len(warnings) == 0


def test_verify_output_invalid_json(tmp_path):
    target = tmp_path / "project"
    agents_dir = target / ".opencode" / "agents"
    agents_dir.mkdir(parents=True)
    for agent in [
        "Main.md",
        "CodeWriter.md",
        "CodeReviewer.md",
        "BugFixer.md",
        "debugger.md",
        "QA.md",
        "Designer.md",
        "AutoApprover.md",
        "PromptEngineer.md",
    ]:
        (agents_dir / agent).write_text("")

    opencode_json = target / "opencode.json"
    opencode_json.write_text("{invalid json")

    warnings = verify_output(target, {"PROVIDER_API_KEY_ENV": "MY_KEY"})
    assert any("INVALID JSON" in w for w in warnings)


# ─────────────────────────────────────────────
# create_docs_scaffold tests
# ─────────────────────────────────────────────


def test_create_docs_scaffold_creates_dirs(tmp_path):
    modules = [{"name": "app", "source_root": "src/", "test_root": "tests/"}]
    created = create_docs_scaffold(modules, tmp_path, dry_run=False)
    assert len(created) > 0
    assert (tmp_path / ".vault/concepts/app/requirements/.gitkeep").exists()
    assert (tmp_path / ".vault/guidelines/libs/.gitkeep").exists()


def test_create_docs_scaffold_dry_run(tmp_path):
    modules = [{"name": "app", "source_root": "src/", "test_root": "tests/"}]
    created = create_docs_scaffold(modules, tmp_path, dry_run=True)
    assert len(created) > 0
    assert not (tmp_path / ".vault").exists()


# ─────────────────────────────────────────────
# apply_remote tests
# ─────────────────────────────────────────────


class TestApplyRemote:
    def test_apply_remote_import(self):
        import apply_remote

        assert hasattr(apply_remote, "apply")

    def test_apply_remote_kit_path_to_target(self):
        import apply_remote

        result = apply_remote.kit_path_to_target("kit/opencode.json.template")
        assert result == "opencode.json"

    def test_apply_remote_filter_by_editors(self):
        import apply_remote

        paths = [
            "kit/opencode.json.template",
            "kit/editors/opencode/CLAUDE.md.template",
            "kit/editors/cursor/.cursor/rules/conventions.mdc.template",
        ]
        filtered = apply_remote._filter_by_editors(paths, ["opencode"])
        assert "kit/opencode.json.template" in filtered
        assert "kit/editors/opencode/CLAUDE.md.template" in filtered
        assert "kit/editors/cursor/.cursor/rules/conventions.mdc.template" not in filtered

    def test_apply_remote_hardcoded_files(self):
        import apply_remote

        files = apply_remote._hardcoded_kit_files(["opencode"])
        assert any("kit/opencode.json.template" in f for f in files)
        assert any("CLAUDE.md" in f for f in files)

    def test_apply_remote_constant_values(self):
        import apply_remote

        assert apply_remote.KIT_REPO == "aequicor/opencode-kit"
        assert apply_remote.KIT_BRANCH == "main"


def test_apply_remote_cli_exists():
    import apply_remote

    assert hasattr(apply_remote, "main")


# ─────────────────────────────────────────────
# New features — nested AGENTS.md
# ─────────────────────────────────────────────


def test_nested_context_generation():
    module = {
        "name": "server",
        "gradle_module": ":server",
        "source_root": "server/src/main/kotlin/",
        "test_root": "server/src/test/kotlin/",
        "responsibility": "Backend API",
        "conventions": "Use Ktor for HTTP",
        "module_dependencies": "depends on :shared",
    }
    stack = {
        "build_command": "./gradlew",
        "compile_command": "./gradlew compileKotlin",
        "test_command": "./gradlew :[module]:test",
    }
    ctx = _build_nested_context(module, stack, "Test Project")
    assert ctx["MODULE_NAME"] == "server"
    assert ctx["MODULE_SOURCE_ROOT"] == "server/src/main/kotlin/"
    assert ctx["MODULE_RESPONSIBILITY"] == "Backend API"
    assert ":server:build" in ctx["MODULE_BUILD_TABLE"]
    assert "Conventions" in ctx["MODULE_CONVENTIONS"] or "Ktor" in ctx["MODULE_CONVENTIONS"]
    assert "depends on" in ctx["MODULE_DEPENDENCIES"]


def test_nested_context_no_gradle():
    module = {
        "name": "frontend",
        "gradle_module": None,
        "source_root": "frontend/src/",
        "test_root": "frontend/tests/",
        "responsibility": "Frontend UI",
    }
    stack = {"build_command": "make", "compile_command": "make check", "test_command": "make test"}
    ctx = _build_nested_context(module, stack, "Test")
    assert "not a Gradle project" in ctx["MODULE_GRADLE_LINE"]


def test_formatter_hook_generation():
    assert (
        _build_formatter_hook(
            {"enabled": True, "command": ["./gradlew", "detekt", "--auto-correct"]}
        )
        == "./gradlew detekt --auto-correct"
    )
    assert _build_formatter_hook({"enabled": False}) == "echo"


# ─────────────────────────────────────────────
# New features — costs
# ─────────────────────────────────────────────


def test_cost_tracker_basic():
    from core.costs import CostTracker

    tracker = CostTracker(budget=10.0)
    entry = tracker.record("CodeWriter", "qwen/qwen3-coder-next", 500, 200)
    assert entry.agent_name == "CodeWriter"
    assert entry.input_tokens == 500
    assert entry.output_tokens == 200
    assert entry.cost > 0


def test_cost_tracker_over_budget():
    from core.costs import CostTracker

    tracker = CostTracker(budget=0.001)
    tracker.record("Test", "qwen/qwen3-coder-next", 5000, 5000)
    assert tracker.is_over_budget()


def test_cost_tracker_summary():
    from core.costs import CostTracker

    tracker = CostTracker(budget=5.0)
    tracker.record("Main", "deepseek/deepseek-v4-pro", 1000, 500)
    s = tracker.summary()
    assert "total_cost" in s
    assert "by_agent" in s
    assert "by_model" in s
    assert "Main" in s["by_agent"]


def test_cost_tracker_remaining():
    from core.costs import CostTracker

    tracker = CostTracker(budget=5.0)
    assert tracker.remaining_budget() == 5.0


def test_default_pricing():
    from core.costs import DEFAULT_PRICING

    assert "moonshotai/kimi-k2.6" in DEFAULT_PRICING
    pricing = DEFAULT_PRICING["moonshotai/kimi-k2.6"]
    cost = pricing.estimate_cost(1000, 500)
    assert cost > 0


# ─────────────────────────────────────────────
# New features — metrics
# ─────────────────────────────────────────────


def test_metrics_collector_events(tmp_path):
    from core.metrics import MetricsCollector

    mc = MetricsCollector(store_dir=tmp_path)
    mc.log_anti_loop("Main", "Same task twice", "STOP")
    mc.log_hitl("Main", "DEPLOY", "Pushing to prod", "approved")
    mc.log_token_usage("CodeWriter", "model-x", 100, 50)
    mc.save()

    files = list(tmp_path.glob("events-*.json"))
    assert len(files) == 1


def test_metrics_generate_report(tmp_path):
    from core.metrics import MetricsCollector

    mc = MetricsCollector(store_dir=tmp_path)
    mc.log_anti_loop("Main", "Loop", "Stopped")
    mc.save()

    report = mc.generate_report(days=30)
    assert "Metrics Report" in report
    assert "Anti-Loop Events" in report


# ─────────────────────────────────────────────
# New features — AUTO_MEMORY.md template
# ─────────────────────────────────────────────


def test_auto_memory_template_renders(tmp_path):
    manifest = dict(MINIMAL_MANIFEST)
    manifest_file = tmp_path / "manifest.yaml"
    target_dir = tmp_path / "project"
    target_dir.mkdir()

    with open(manifest_file, "w") as f:
        yaml.dump(manifest, f)

    apply_mod.apply(
        manifest_path=str(manifest_file),
        target_dir=str(target_dir),
        dry_run=False,
        merge=False,
    )

    auto_memory = target_dir / "AUTO_MEMORY.md"
    assert auto_memory.exists(), "AUTO_MEMORY.md must be created"
    content = auto_memory.read_text()
    assert "Learned Build Commands" in content
    assert "Debugging Insights" in content
    assert "API Pitfalls" in content
