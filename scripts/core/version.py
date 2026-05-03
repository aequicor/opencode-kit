import sys

KIT_VERSION = "1.5.0"


def check_kit_version(manifest: dict) -> None:
    manifest_version = manifest.get("kit_version")
    if not manifest_version:
        return
    if manifest_version != KIT_VERSION:
        print(
            f"ERROR: manifest kit_version={manifest_version!r} does not match this script version {KIT_VERSION!r}."
        )
        print("  Update kit_version in your manifest, or remove it to skip the version check.")
        sys.exit(1)
