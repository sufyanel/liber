#!/usr/bin/env python3
"""PreToolUse hook (Bash matcher): block `git add` until docs are synced.

Per the user's global CLAUDE.md rule: README.md and the module's
static/description/index.html must be updated for any module(s) whose files
are being staged, batched to just before staging rather than after every
prompt. This hook enforces that batching point instead of relying on a
self-reminder.
"""
import json
import re
import sys

# Match `git add` at the start of the command or right after a command
# separator (;, &, |, a backtick, or $( ), so it catches compound commands
# like `cd foo && git add .` but not an unrelated string that merely
# contains the words "git add" (e.g. inside an echoed message).
_GIT_ADD_RE = re.compile(r'(^|[;&|]|`|\$\()\s*git\s+add\b', re.IGNORECASE)


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return
    command = (payload.get("tool_input") or {}).get("command") or ""
    if not _GIT_ADD_RE.search(command):
        return

    reason = (
        "Run a documentation-sync pass first (per CLAUDE.md): update README.md "
        "and the module's static/description/index.html (create it if the "
        "module has none) for every module whose files are about to be "
        "staged. Delegate that rewrite to a lower-effort subagent, then "
        "retry git add."
    )
    # Claude Code reads the permission decision from this process's stdout
    # (the PreToolUse hook protocol) — this is not application logging, and
    # routing it through `logger` would prevent the harness from seeing it.
    print(json.dumps({  # pylint: disable=print-used
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


if __name__ == "__main__":
    main()
