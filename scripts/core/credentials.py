import re
import sys

_ENV_VAR_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_KNOWN_KEY_PREFIXES = re.compile(r"^(sk-|ghp_|github_pat_|AKIA[0-9A-Z]|xox[baprs]-|ghs_|glpat-)")
_HIGH_ENTROPY = re.compile(r"^[A-Za-z0-9+/=_\-]{32,}$")


def _looks_like_secret(value: str) -> bool:
    if _KNOWN_KEY_PREFIXES.match(value):
        return True
    return bool(_HIGH_ENTROPY.match(value))


def check_credentials(manifest: dict) -> None:
    provider = manifest.get("provider", {})
    api_key_env = provider.get("api_key_env", "")

    if api_key_env:
        if _KNOWN_KEY_PREFIXES.match(api_key_env):
            print(f"ERROR: provider.api_key_env looks like an actual API key: {api_key_env!r}")
            print("  Put the ENVIRONMENT VARIABLE NAME here, not the actual key.")
            print("  Example: api_key_env: ROUTERAI_OPENCODE")
            sys.exit(1)
        if not _ENV_VAR_NAME.match(api_key_env):
            print(
                f"ERROR: provider.api_key_env {api_key_env!r} is not a valid environment variable name."
            )
            print("  Must match [A-Za-z_][A-Za-z0-9_]* — e.g. ROUTERAI_OPENCODE")
            sys.exit(1)

    for mcp_name, mcp_cfg in manifest.get("mcp", {}).items():
        if not isinstance(mcp_cfg, dict):
            print(
                f"  WARNING: mcp.{mcp_name} is not a mapping (got {type(mcp_cfg).__name__}) — skipping credential check for this entry"
            )
            continue
        for field in ("api_key", "token", "secret", "password"):
            val = mcp_cfg.get(field, "")
            if val and _looks_like_secret(str(val)):
                print(f"ERROR: mcp.{mcp_name}.{field} looks like a real secret: {str(val)[:8]}...")
                print("  Use api_key_env to reference an environment variable name instead.")
                sys.exit(1)


def looks_like_key(text: str) -> bool:
    return _looks_like_secret(text)
