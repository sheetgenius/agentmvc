"""Create a fresh, isolated Codex home for one measured agent session.

The home copies your local Codex login and sets the isolation every measured run relies on: no approvals,
memories and extra features off, filesystem access limited to the workspace plus read-only toolchains,
and network access for package installs.
"""
import secrets
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def write_home(target):
    target = Path(target)
    if target.exists():
        raise SystemExit(f"Codex home exists: {target}")
    target.mkdir(parents=True, mode=0o700)
    auth = Path.home() / ".codex/auth.json"
    if not auth.is_file():
        raise SystemExit("Missing local Codex authentication; run `codex login` first")
    shutil.copy2(auth, target / "auth.json")
    (target / "auth.json").chmod(0o600)
    (target / "config.toml").write_text(f'''approval_policy = "never"
default_permissions = "workspace-only"
allow_login_shell = false
[features]
memories = false
multi_agent = false
apps = false
hooks = false
plugins = false
browser_use = false
computer_use = false
[permissions.workspace-only]
extends = ":workspace"
[permissions.workspace-only.filesystem]
":root" = "deny"
":minimal" = "read"
"/opt/homebrew" = "read"
"{Path.home()}/.rbenv" = "read"
"{Path.home()}/.cargo/bin" = "read"
"{Path.home()}/.rustup" = "read"
"/etc/resolv.conf" = "read"
"/Library/Developer" = "read"
":tmpdir" = "deny"
":slash_tmp" = "deny"
[permissions.workspace-only.network]
enabled = true
[projects."{ROOT}"]
trust_level = "trusted"
''')
    (target / "config.toml").chmod(0o600)


def write_token(path):
    """A private broker token for one run, unless one exists already."""
    path = Path(path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        path.write_text(secrets.token_hex(32) + "\n")
        path.chmod(0o600)
    return path.read_text().strip()
