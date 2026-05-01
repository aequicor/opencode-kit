import re
import sys

_LOOKS_LIKE_KEY = re.compile(r"[A-Za-z0-9_\-]{32,}")


def check_credentials(manifest: dict) -> None:
    provider = manifest.get("provider", {})
    api_key_env = provider.get("api_key_env", "")

    if api_key_env and _LOOKS_LIKE_KEY.match(api_key_env) and len(api_key_env) > 30:
        print(f"ERROR: provider.api_key_env looks like an actual API key: {api_key_env!r}")
        print("  Put the ENVIRONMENT VARIABLE NAME here, not the actual key.")
        print("  Example: api_key_env: ROUTERAI_OPENCODE")
        sys.exit(1)

    for mcp_name, mcp_cfg in manifest.get("mcp", {}).items():
        for field in ("api_key", "token", "secret", "password"):
            val = mcp_cfg.get(field, "")
            if val and _LOOKS_LIKE_KEY.match(str(val)) and len(str(val)) > 20:
                print(f"ERROR: mcp.{mcp_name}.{field} looks like a real secret: {str(val)[:8]}...")
                print("  Use api_key_env to reference an environment variable name instead.")
                sys.exit(1)


def looks_like_key(text: str) -> bool:
    return bool(_LOOKS_LIKE_KEY.search(text))
