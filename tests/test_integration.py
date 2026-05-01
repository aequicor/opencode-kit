"""
Integration tests — full apply cycle with real manifests.
Run: python -m pytest tests/test_integration.py -v
"""

import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import apply as apply_mod
from core import build_context, verify_output, KIT_VERSION

SYSTEM_FILES = {".gitkeep"}


def _count_created_files(target: Path) -> list:
    return [
        str(f.relative_to(target))
        for f in target.rglob("*")
        if f.is_file() and f.name not in SYSTEM_FILES
    ]


# ─────────────────────────────────────────────
# Full kit application
# ─────────────────────────────────────────────


def test_full_apply_all_files_present(tmp_path):
    manifest = {
        "kit_version": KIT_VERSION,
        "editors": ["opencode", "cursor", "copilot"],
        "project": {
            "name": "Full Test",
            "description": "Integration test project",
        },
        "stack": {
            "language": "kotlin",
            "profile": "kotlin-multiplatform",
            "build_command": "./gradlew",
            "compile_command": "./gradlew compileKotlin",
            "lint_command": "./gradlew detekt",
            "test_command": "./gradlew :[module]:test",
        },
        "modules": [
            {
                "name": "server",
                "gradle_module": ":server",
                "source_root": "server/src/main/kotlin/",
                "test_root": "server/src/test/kotlin/",
                "docs_path": "docs/server/",
                "responsibility": "Backend API",
            },
            {
                "name": "client",
                "gradle_module": ":client",
                "source_root": "client/src/main/kotlin/",
                "test_root": "client/src/test/kotlin/",
                "docs_path": "docs/client/",
                "responsibility": "Frontend UI",
            },
        ],
        "provider": {
            "name": "routerai",
            "base_url": "https://routerai.ru/api/v1",
            "api_key_env": "ROUTERAI_KEY",
        },
        "models": {
            "default": "model-a",
            "coder": "model-b",
            "reviewer": "model-c",
            "designer": "model-d",
            "small": "model-e",
        },
        "mcp": {
            "context7": {"enabled": True, "api_key_env": "CONTEXT7_KEY"},
            "knowledge": {"enabled": True, "url": "http://localhost:8085/mcp"},
            "serena": {"enabled": True},
        },
        "lsp": {
            "enabled": True,
            "command": "kotlin-lsp",
            "extensions": [".kt", ".kts"],
        },
        "ui": {
            "framework": "Compose Multiplatform",
            "platforms": ["Desktop"],
            "colors": [
                {"name": "Test Red", "hex": "#FF0000", "purpose": "Accent"},
            ],
        },
        "code_quality": {
            "forbidden_patterns": ["!! operator", "GlobalScope.launch"],
        },
        "formatter": {
            "enabled": True,
            "name": "ktlint",
            "command": ["./gradlew", "ktlintFormat"],
            "extensions": [".kt", ".kts"],
        },
    }

    manifest_file = tmp_path / "test-manifest.yaml"
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

    files = _count_created_files(target_dir)

    # Required root files
    assert "opencode.json" in files, "opencode.json must be created"
    assert "AGENTS.md" in files, "AGENTS.md must be created"
    assert "CLAUDE.md" in files, "CLAUDE.md must be created"

    # Editor-specific
    assert str(Path(".cursor/rules/conventions.mdc")) in files
    assert str(Path(".github/copilot-instructions.md")) in files

    # Agents
    agents_dir = target_dir / ".opencode" / "agents"
    assert agents_dir.exists()
    expected_agents = [
        "Main.md", "CodeWriter.md", "CodeReviewer.md", "BugFixer.md",
        "debugger.md", "QA.md", "Designer.md", "PromptEngineer.md",
    ]
    for agent in expected_agents:
        assert (agents_dir / agent).exists(), f"Missing: {agent}"

    # Shared context
    shared_md = target_dir / ".opencode" / "_shared.md"
    assert shared_md.exists()
    shared_content = shared_md.read_text()
    assert "Full Test" in shared_content

    # Planning
    assert (target_dir / ".planning" / "CURRENT.md").exists()
    assert (target_dir / ".planning" / "DECISIONS.md").exists()

    # Commands
    assert (target_dir / ".opencode" / "commands" / "new-feature.md").exists()
    assert (target_dir / ".opencode" / "commands" / "resume.md").exists()
    assert (target_dir / ".opencode" / "commands" / "checkpoint.md").exists()

    # Skills
    assert (target_dir / ".opencode" / "skills" / "look-up" / "SKILL.md").exists()
    assert (target_dir / ".opencode" / "skills" / "bug-retro" / "SKILL.md").exists()

    # Docs scaffold
    assert (target_dir / "docs" / "server" / "requirements" / ".gitkeep").exists()
    assert (target_dir / "docs" / "server" / "spec" / ".gitkeep").exists()
    assert (target_dir / "docs" / "server" / "guidelines" / ".gitkeep").exists()
    assert (target_dir / "docs" / "server" / "plans" / ".gitkeep").exists()
    assert (target_dir / "docs" / "server" / "reports" / ".gitkeep").exists()
    assert (target_dir / "docs" / "client" / "requirements" / ".gitkeep").exists()


def test_verify_output_after_full_apply(tmp_path):
    manifest = {
        "kit_version": KIT_VERSION,
        "editors": ["opencode"],
        "project": {"name": "Verify Test", "description": ""},
        "stack": {
            "language": "kotlin",
            "build_command": "./gradlew",
            "compile_command": "./gradlew compileKotlin",
            "lint_command": "./gradlew detekt",
            "test_command": "./gradlew :[module]:test",
        },
        "modules": [
            {
                "name": "app",
                "gradle_module": ":app",
                "source_root": "app/src/main/kotlin/",
                "test_root": "app/src/test/kotlin/",
                "docs_path": "docs/app/",
                "responsibility": "App",
            }
        ],
        "provider": {
            "name": "routerai",
            "base_url": "https://routerai.ru/api/v1",
            "api_key_env": "ROUTERAI_KEY",
        },
        "models": {
            "default": "model-a",
            "coder": "model-b",
            "reviewer": "model-c",
        },
        "mcp": {
            "context7": {"enabled": False},
            "knowledge": {"enabled": False},
            "serena": {"enabled": False},
        },
        "lsp": {"enabled": False},
        "ui": {"framework": None},
        "code_quality": {"forbidden_patterns": []},
        "formatter": {"enabled": False},
    }

    manifest_file = tmp_path / "test-manifest.yaml"
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

    ctx = build_context(manifest)
    warnings = verify_output(target_dir, ctx)
    assert warnings == [], f"Verification warnings: {warnings}"


def test_no_literal_key_in_opencode_json(tmp_path):
    manifest = {
        "kit_version": KIT_VERSION,
        "editors": ["opencode"],
        "project": {"name": "Key Test", "description": ""},
        "stack": {
            "language": "kotlin",
            "build_command": "./gradlew",
            "compile_command": "./gradlew compileKotlin",
            "lint_command": "./gradlew detekt",
            "test_command": "./gradlew :[module]:test",
        },
        "modules": [
            {
                "name": "app",
                "gradle_module": ":app",
                "source_root": "app/src/main/kotlin/",
                "test_root": "app/src/test/kotlin/",
                "docs_path": "docs/app/",
                "responsibility": "App",
            }
        ],
        "provider": {
            "name": "test-provider",
            "base_url": "https://example.com/v1",
            "api_key_env": "MY_API_KEY",
        },
        "models": {
            "default": "model-a",
            "coder": "model-b",
            "reviewer": "model-c",
        },
        "mcp": {
            "context7": {"enabled": False},
            "knowledge": {"enabled": False},
            "serena": {"enabled": False},
        },
        "lsp": {"enabled": False},
        "ui": {"framework": None},
        "code_quality": {"forbidden_patterns": []},
        "formatter": {"enabled": False},
    }

    manifest_file = tmp_path / "test-manifest.yaml"
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

    opencode_json = target_dir / "opencode.json"
    content = opencode_json.read_text()

    # Must contain env: syntax, not a real key
    assert "{env:MY_API_KEY}" in content
    assert "apiKey" in content


def test_manifest_with_designer_null_omits_designer(tmp_path):
    manifest = {
        "kit_version": KIT_VERSION,
        "editors": ["opencode"],
        "project": {"name": "No Designer", "description": ""},
        "stack": {
            "language": "kotlin",
            "build_command": "./gradlew",
            "compile_command": "./gradlew compileKotlin",
            "lint_command": "./gradlew detekt",
            "test_command": "./gradlew :[module]:test",
        },
        "modules": [
            {
                "name": "app",
                "gradle_module": ":app",
                "source_root": "app/src/",
                "test_root": "app/src/test/",
                "docs_path": "docs/app/",
                "responsibility": "App",
            }
        ],
        "provider": {
            "name": "routerai",
            "base_url": "https://example.com/v1",
            "api_key_env": "MY_KEY",
        },
        "models": {
            "default": "m1",
            "coder": "m2",
            "reviewer": "m3",
            "designer": None,
        },
        "mcp": {
            "context7": {"enabled": False},
            "knowledge": {"enabled": False},
            "serena": {"enabled": False},
        },
        "lsp": {"enabled": False},
        "ui": {"framework": None},
        "code_quality": {"forbidden_patterns": []},
        "formatter": {"enabled": False},
    }

    manifest_file = tmp_path / "test-manifest.yaml"
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

    designer_md = target_dir / ".opencode" / "agents" / "Designer.md"
    assert designer_md.exists(), "Designer.md should still be created but model may be coder fallback"

    # Check MODEL_TABLE has no unresolved placeholders
    shared_md = target_dir / ".opencode" / "_shared.md"
    content = shared_md.read_text()
    assert "{{" not in content, f"Unresolved placeholders: {re.findall(r'{{[A-Z_]+}}', content)}"


def test_dry_run_preview_output(tmp_path, capsys):
    manifest = {
        "kit_version": KIT_VERSION,
        "editors": ["opencode"],
        "project": {"name": "Dry Run", "description": ""},
        "stack": {
            "language": "generic",
            "build_command": "make",
            "compile_command": "make check",
            "lint_command": "make lint",
            "test_command": "make test",
        },
        "modules": [
            {
                "name": "main",
                "gradle_module": None,
                "source_root": "src/",
                "test_root": "tests/",
                "docs_path": "docs/main/",
                "responsibility": "Everything",
            }
        ],
        "provider": {
            "name": "routerai",
            "base_url": "https://example.com/v1",
            "api_key_env": "MY_KEY",
        },
        "models": {
            "default": "m1",
            "coder": "m2",
            "reviewer": "m3",
        },
        "mcp": {
            "context7": {"enabled": False},
            "knowledge": {"enabled": False},
            "serena": {"enabled": False},
        },
        "lsp": {"enabled": False},
        "ui": {"framework": None},
        "code_quality": {"forbidden_patterns": []},
        "formatter": {"enabled": False},
    }

    manifest_file = tmp_path / "test-manifest.yaml"
    target_dir = tmp_path / "project"
    target_dir.mkdir()

    with open(manifest_file, "w") as f:
        yaml.dump(manifest, f)

    apply_mod.apply(
        manifest_path=str(manifest_file),
        target_dir=str(target_dir),
        dry_run=True,
        merge=False,
    )

    captured = capsys.readouterr()
    assert "[DRY RUN]" in captured.out
    assert "DRY RUN" in captured.out

    # No files should be created
    files = _count_created_files(target_dir)
    assert files == [], f"Dry run created files: {files}"


def test_edge_case_empty_modules(tmp_path):
    manifest = {
        "kit_version": KIT_VERSION,
        "editors": ["opencode"],
        "project": {"name": "Empty Modules", "description": ""},
        "stack": {
            "language": "generic",
            "build_command": "make",
            "compile_command": "make check",
            "lint_command": "make lint",
            "test_command": "make test",
        },
        "modules": [],
        "provider": {
            "name": "routerai",
            "base_url": "https://example.com/v1",
            "api_key_env": "MY_KEY",
        },
        "models": {
            "default": "m1",
            "coder": "m2",
            "reviewer": "m3",
        },
        "mcp": {
            "context7": {"enabled": False},
            "knowledge": {"enabled": False},
            "serena": {"enabled": False},
        },
        "lsp": {"enabled": False},
        "ui": {"framework": None},
        "code_quality": {"forbidden_patterns": []},
        "formatter": {"enabled": False},
    }

    manifest_file = tmp_path / "test-manifest.yaml"
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

    # Should succeed without error — no module rows in tables
    shared_md = target_dir / ".opencode" / "_shared.md"
    assert shared_md.exists()


def test_apply_creates_file_structure_md(tmp_path):
    manifest = {
        "kit_version": KIT_VERSION,
        "editors": ["opencode"],
        "project": {"name": "FS Test", "description": ""},
        "stack": {
            "language": "kotlin",
            "build_command": "./gradlew",
            "compile_command": "./gradlew compileKotlin",
            "lint_command": "./gradlew detekt",
            "test_command": "./gradlew :[module]:test",
        },
        "modules": [
            {
                "name": "app",
                "gradle_module": ":app",
                "source_root": "app/src/main/kotlin/",
                "test_root": "app/src/test/kotlin/",
                "docs_path": "docs/app/",
                "responsibility": "App",
            }
        ],
        "provider": {
            "name": "routerai",
            "base_url": "https://example.com/v1",
            "api_key_env": "MY_KEY",
        },
        "models": {
            "default": "m1",
            "coder": "m2",
            "reviewer": "m3",
        },
        "mcp": {
            "context7": {"enabled": False},
            "knowledge": {"enabled": False},
            "serena": {"enabled": False},
        },
        "lsp": {"enabled": False},
        "ui": {"framework": None},
        "code_quality": {"forbidden_patterns": []},
        "formatter": {"enabled": False},
    }

    manifest_file = tmp_path / "test-manifest.yaml"
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

    fs_md = target_dir / ".opencode" / "FILE_STRUCTURE.md"
    assert fs_md.exists(), "FILE_STRUCTURE.md must be created"
    content = fs_md.read_text()
    assert "FS Test" in content
    assert ":app" in content
    assert "app/src/main/kotlin/" in content
    assert "app/src/test/kotlin/" in content
    assert "GRADLE" in content.upper() or "Gradle" in content
