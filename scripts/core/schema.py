"""
JSON Schema validation for opencode-kit manifests.
"""

import json
import sys
from pathlib import Path
from typing import Optional

_SCHEMA_PATH = Path(__file__).parent.parent / "kit" / "manifest.schema.json"


def _load_schema():
    try:
        import jsonschema
        return jsonschema
    except ImportError:
        return None


def validate_manifest(manifest: dict, manifest_path: str = "") -> list[str]:
    errors = []

    jsonschema_mod = _load_schema()
    if jsonschema_mod is None:
        return errors

    schema_file = _SCHEMA_PATH
    if not schema_file.exists():
        return []

    try:
        with open(schema_file) as f:
            schema = json.load(f)

        validator_cls = jsonschema_mod.validators.validator_for(schema)
        validator = validator_cls(schema)
        for error in validator.iter_errors(manifest):
            errors.append(f"{error.json_path}: {error.message}")
    except Exception as e:
        errors.append(f"Schema validation error: {e}")

    return errors


def print_schema_errors(errors: list[str], manifest_path: str) -> None:
    if not errors:
        return
    print(f"\n\u26a0\ufe0f  Schema validation warnings for {manifest_path}:")
    for e in errors[:20]:
        print(f"  - {e}")
    if len(errors) > 20:
        print(f"  ... and {len(errors) - 20} more")
    print()
