#!/usr/bin/env python3
"""Build banner.json (the hook's output) from banner.txt, coloring the logo.

Run after editing banner.txt: python3 assets/build_banner.py
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
BLUE = "\x1b[38;2;26;107;237m"  # #1A6BED, the logo's blue
RESET = "\x1b[0m"

art = (HERE / "banner.txt").read_text().rstrip("\n").splitlines()
# Claude Code prefixes the first line with its own label, so start with an
# empty line to keep every row of the logo aligned.
message = "\n" + "\n".join(BLUE + line + RESET for line in art)
out = {
    "systemMessage": message,
    "hookSpecificOutput": {
        "hookEventName": "UserPromptExpansion",
        "additionalContext": "The ARK logo has already been shown to the user. Do not print it again.",
    },
}
(HERE / "banner.json").write_text(json.dumps(out, ensure_ascii=False) + "\n")
