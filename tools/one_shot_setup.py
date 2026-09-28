"""Create the fresh Codex homes and broker tokens for a Rails, Phoenix or Loco one-shot run.

Usage: ONE_SHOT_RUN=NAME python3 tools/one_shot_setup.py [rails|phoenix|loco ...]

Run it after `tools/one_shot.py prepare`. It writes .work/NAME-homes/STACK/ for each stack and adds a token
per stack to .work/NAME-control/tokens.json, which the broker and the agent launcher read.
"""
import json
import secrets
import sys

import codex_home
import one_shot


def main():
    stacks = sys.argv[1:] or list(one_shot.STACKS)
    if any(stack not in one_shot.STACKS for stack in stacks):
        raise SystemExit(__doc__)
    tokens_file = one_shot.CONTROL / "tokens.json"
    tokens = json.loads(tokens_file.read_text()) if tokens_file.exists() else {}
    for stack in stacks:
        codex_home.write_home(one_shot.HOMES / stack)
        tokens.setdefault(stack, secrets.token_hex(32))
    one_shot.CONTROL.mkdir(parents=True, exist_ok=True, mode=0o700)
    tokens_file.write_text(json.dumps(tokens, indent=2) + "\n")
    tokens_file.chmod(0o600)
    print(f"homes in {one_shot.HOMES}; broker tokens in {tokens_file}")


if __name__ == "__main__":
    main()
