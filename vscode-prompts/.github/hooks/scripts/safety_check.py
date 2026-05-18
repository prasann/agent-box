"""
safety_check.py — Pre-tool-use hook that blocks dangerous terminal commands.

Reads JSON from stdin containing the tool input. Inspects the command
for dangerous patterns and exits with the appropriate code:
  0 = allow (command is safe)
  2 = block (dangerous command detected)
"""

import json
import re
import sys

DANGEROUS_PATTERNS = [
    re.compile(r"\brm\b", re.IGNORECASE),  # block all rm calls (plain, -rf, etc.)
    re.compile(r"rm\s+-rf", re.IGNORECASE),
    re.compile(r"rm\s+-fr", re.IGNORECASE),
    re.compile(r"rmdir\s+/s", re.IGNORECASE),
    re.compile(r"del\s+/s\s+/q", re.IGNORECASE),
    re.compile(r"Remove-Item", re.IGNORECASE),
    re.compile(r"DROP\s+TABLE", re.IGNORECASE),
    re.compile(r"DROP\s+DATABASE", re.IGNORECASE),
    re.compile(r"DELETE\s+FROM", re.IGNORECASE),
    re.compile(r"TRUNCATE\s+TABLE", re.IGNORECASE),
    re.compile(r":\(\)\s*\{\s*:\|:&\s*\};:"),
    re.compile(r"mkfs\.", re.IGNORECASE),
    re.compile(r"dd\s+if=", re.IGNORECASE),
    re.compile(r"format\s+[a-z]:", re.IGNORECASE),
    re.compile(r">\s*/dev/sda", re.IGNORECASE),
]


def main():
    raw_input = sys.stdin.read()

    try:
        data = json.loads(raw_input)
        tool_name = data.get("tool_name", "")

        # Only inspect terminal commands
        if tool_name != "run_in_terminal":
            sys.exit(0)

        tool_input = data.get("tool_input", {})
        command = tool_input.get("command", "") or tool_input.get("input", "")

        for pattern in DANGEROUS_PATTERNS:
            if pattern.search(command):
                reason = f"Dangerous pattern '{pattern.pattern}' detected in command"
                output = {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "ask",
                        "permissionDecisionReason": reason,
                    }
                }
                sys.stdout.write(json.dumps(output))
                sys.stdout.flush()
                sys.exit(0)

        sys.exit(0)
    except (json.JSONDecodeError, KeyError):
        sys.exit(0)


if __name__ == "__main__":
    main()
 