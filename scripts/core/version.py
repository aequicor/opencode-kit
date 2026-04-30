KIT_VERSION = "1.3.0"


def check_kit_version(manifest: dict) -> None:
    manifest_version = manifest.get("kit_version")
    if not manifest_version:
        return
    if manifest_version != KIT_VERSION:
        print(
            f"WARNING: manifest kit_version={manifest_version!r} but this script is {KIT_VERSION!r}."
        )
        print(
            "  Some templates may have changed. Run with --merge to overwrite existing files."
        )
        print()
