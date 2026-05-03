import copy
from pathlib import Path
from typing import Optional

_PROFILES_DIR = None


def set_profiles_dir(path: Path) -> None:
    global _PROFILES_DIR
    _PROFILES_DIR = path


def get_profiles_dir() -> Path:
    if _PROFILES_DIR is not None:
        return _PROFILES_DIR
    return Path(__file__).parent.parent.parent / "profiles"


def load_profile(name: str, profiles_dir: Optional[Path] = None) -> dict:
    import yaml

    d = profiles_dir or get_profiles_dir()
    path = d / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {path}")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data or not isinstance(data, dict):
        raise ValueError(f"Profile {name!r} is empty or invalid")
    for key in list(data.keys()):
        if key.startswith("_"):
            data.pop(key)
    return data


def deep_merge(base: dict, override: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        elif (
            key in result
            and isinstance(result[key], list)
            and isinstance(value, list)
        ):
            merged = list(result[key])
            for item in value:
                if item not in merged:
                    merged.append(item)
            result[key] = merged
        else:
            result[key] = copy.deepcopy(value)
    return result


def merge_profiles(
    profile_names: list[str],
    profiles_dir: Optional[Path] = None,
) -> dict:
    if not profile_names:
        return {}
    result: dict = {}
    for name in profile_names:
        profile_data = load_profile(name, profiles_dir)
        result = deep_merge(result, profile_data)
    return result


def apply_profiles_to_manifest(
    manifest: dict,
    profiles_dir: Optional[Path] = None,
) -> dict:
    stack = manifest.get("stack", {})
    profile_names = stack.get("profiles", [])
    if not profile_names:
        legacy = stack.get("profile")
        if legacy:
            profile_names = [legacy]
    if not profile_names:
        return manifest
    merged_profiles = merge_profiles(profile_names, profiles_dir)
    result = deep_merge(merged_profiles, manifest)
    if "profiles" in result.get("stack", {}):
        result["stack"].pop("profiles", None)
    if "profile" in result.get("stack", {}):
        result["stack"]["profile"] = ",".join(profile_names)
    return result


def list_profiles(profiles_dir: Optional[Path] = None) -> list[dict]:
    import yaml

    d = profiles_dir or get_profiles_dir()
    profiles = []
    if not d.exists():
        return profiles
    for yaml_file in sorted(d.glob("*.yaml")):
        try:
            with open(yaml_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data or not isinstance(data, dict):
                continue
            profiles.append({
                "name": data.get("_profile_name", yaml_file.stem),
                "description": data.get("_profile_description", ""),
                "category": data.get("_profile_category", "stack"),
                "file": str(yaml_file),
            })
        except Exception:
            continue
    return profiles