import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from core.profiles import deep_merge, merge_profiles, load_profile, apply_profiles_to_manifest

PROFILES_DIR = Path(__file__).parent.parent / "profiles"


@pytest.fixture
def profiles_dir():
    return PROFILES_DIR


class TestDeepMerge:
    def test_flat_dicts(self):
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_dicts(self):
        base = {"stack": {"language": "kotlin", "build_command": "./gradlew"}}
        override = {"stack": {"language": "java"}}
        result = deep_merge(base, override)
        assert result == {"stack": {"language": "java", "build_command": "./gradlew"}}

    def test_lists_merge_unique(self):
        base = {"code_quality": {"forbidden_patterns": ["A", "B"]}}
        override = {"code_quality": {"forbidden_patterns": ["B", "C"]}}
        result = deep_merge(base, override)
        patterns = result["code_quality"]["forbidden_patterns"]
        assert "A" in patterns
        assert "B" in patterns
        assert "C" in patterns
        assert len(patterns) == 3

    def test_null_override(self):
        base = {"ui": {"framework": "React"}}
        override = {"ui": {"framework": None}}
        result = deep_merge(base, override)
        assert result["ui"]["framework"] is None

    def test_does_not_mutate_base(self):
        base = {"stack": {"language": "kotlin"}}
        override = {"stack": {"language": "java"}}
        result = deep_merge(base, override)
        assert base["stack"]["language"] == "kotlin"
        assert result["stack"]["language"] == "java"

    def test_empty_override(self):
        base = {"a": 1, "b": {"c": 2}}
        result = deep_merge(base, {})
        assert result == {"a": 1, "b": {"c": 2}}

    def test_empty_base(self):
        override = {"a": 1}
        result = deep_merge({}, override)
        assert result == {"a": 1}

    def test_deeply_nested(self):
        base = {"mcp": {"context7": {"enabled": True}}}
        override = {"mcp": {"context7": {"api_key_env": "MY_KEY"}}}
        result = deep_merge(base, override)
        assert result == {"mcp": {"context7": {"enabled": True, "api_key_env": "MY_KEY"}}}


class TestLoadProfile:
    def test_load_kotlin_jvm_ktor(self, profiles_dir):
        data = load_profile("kotlin-jvm-ktor", profiles_dir)
        assert data["stack"]["language"] == "kotlin"
        assert "_profile_name" not in data
        assert "_profile_category" not in data

    def test_load_nonexistent_raises(self, profiles_dir):
        with pytest.raises(FileNotFoundError):
            load_profile("nonexistent-profile", profiles_dir)

    def test_strips_underscore_prefixed_keys(self, profiles_dir):
        data = load_profile("java-spring", profiles_dir)
        assert "_profile_name" not in data
        assert "_profile_description" not in data
        assert "_profile_category" not in data
        assert "stack" in data


class TestMergeProfiles:
    def test_merge_two_profiles(self, profiles_dir):
        result = merge_profiles(["kotlin-jvm-ktor", "requirements-pipeline"], profiles_dir)
        assert result["stack"]["language"] == "kotlin"
        assert result["lsp"]["enabled"] is True

    def test_merge_single(self, profiles_dir):
        result = merge_profiles(["python-fastapi"], profiles_dir)
        assert result["stack"]["language"] == "python"

    def test_merge_empty_list(self, profiles_dir):
        result = merge_profiles([], profiles_dir)
        assert result == {}


class TestApplyProfilesToManifest:
    def test_profiles_list(self, profiles_dir):
        manifest = {
            "kit_version": "1.5.0",
            "project": {"name": "Test"},
            "stack": {
                "profiles": ["kotlin-jvm-ktor"],
                "language": "override",
            },
            "modules": [{"name": "app", "source_root": "src/", "test_root": "tests/", "docs_path": "docs/"}],
            "provider": {"name": "test", "base_url": "https://api.test.com", "api_key_env": "TEST_KEY"},
            "models": {"default": "m1", "coder": "m2", "reviewer": "m3"},
        }
        result = apply_profiles_to_manifest(manifest, profiles_dir)
        assert result["stack"]["language"] == "override"
        assert "profiles" not in result["stack"]

    def test_legacy_profile_string(self, profiles_dir):
        manifest = {
            "kit_version": "1.5.0",
            "project": {"name": "Test"},
            "stack": {
                "profile": "python-fastapi",
            },
            "modules": [{"name": "app", "source_root": "src/", "test_root": "tests/", "docs_path": "docs/"}],
            "provider": {"name": "test", "base_url": "https://api.test.com", "api_key_env": "TEST_KEY"},
            "models": {"default": "m1", "coder": "m2", "reviewer": "m3"},
        }
        result = apply_profiles_to_manifest(manifest, profiles_dir)
        assert result["stack"]["language"] == "python"
        assert result["stack"]["profile"] == "python-fastapi"

    def test_manifest_values_override_profiles(self, profiles_dir):
        manifest = {
            "kit_version": "1.5.0",
            "project": {"name": "Test"},
            "stack": {
                "profiles": ["generic"],
                "lint_command": "my-custom-lint",
            },
            "modules": [{"name": "app", "source_root": "src/", "test_root": "tests/", "docs_path": "docs/"}],
            "provider": {"name": "test", "base_url": "https://api.test.com", "api_key_env": "TEST_KEY"},
            "models": {"default": "m1", "coder": "m2", "reviewer": "m3"},
        }
        result = apply_profiles_to_manifest(manifest, profiles_dir)
        assert result["stack"]["lint_command"] == "my-custom-lint"

    def test_no_profiles_returns_manifest_unchanged(self, profiles_dir):
        manifest = {"kit_version": "1.5.0", "stack": {}}
        result = apply_profiles_to_manifest(manifest, profiles_dir)
        assert result == manifest

    def test_strips_profiles_key_from_result(self, profiles_dir):
        manifest = {
            "kit_version": "1.5.0",
            "project": {"name": "Test"},
            "stack": {"profiles": ["generic"]},
            "modules": [],
            "provider": {"name": "t", "base_url": "https://t.com", "api_key_env": "K"},
            "models": {"default": "m1", "coder": "m2", "reviewer": "m3"},
        }
        result = apply_profiles_to_manifest(manifest, profiles_dir)
        assert "profiles" not in result.get("stack", {})