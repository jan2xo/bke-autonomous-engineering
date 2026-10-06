#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

MARKER = "<!-- bke-intent-ci-status -->"
ANSI = re.compile(r"\x1b\[[0-9;]*m")
SIGNALS = re.compile(r"(FAILED|ERROR|AssertionError|Error:|error:|Exception|Traceback)", re.IGNORECASE)


def compact(text, limit=180):
    text = ANSI.sub("", text)
    text = " ".join(text.strip().split())
    if len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def shortest_actionable_error(log_path):
    if not log_path or not Path(log_path).is_file():
        return "required verification failed; inspect the failing step"
    lines = Path(log_path).read_text(encoding="utf-8", errors="replace").splitlines()
    candidates = []
    for line in lines[-250:]:
        value = compact(line)
        if value and SIGNALS.search(value):
            candidates.append(value)
    if not candidates:
        for line in reversed(lines[-80:]):
            value = compact(line)
            if value:
                return value
        return "required verification failed; inspect the failing step"
    candidates.sort(key=lambda value: (len(value), value))
    return candidates[0]


def render(args):
    icon = "✅" if args.status == "PASS" else "❌"
    if args.status == "PASS":
        detail = compact(args.summary or "required verification passed")
    else:
        detail = shortest_actionable_error(args.log)
    run = f"run #{args.run_id}" if args.run_id else "run unavailable"
    line = f"{icon} {args.status} | {args.check} | {detail} | {run}"
    meta = (
        f"`HEAD {(args.head or 'unknown')[:12]} | INTENT {args.intent} | "
        f"INSTR {(args.instruction_digest or 'unknown')[:12]} | PLAN {(args.plan_digest or 'unknown')[:12]}`"
    )
    return f"{MARKER}\n{line}\n{meta}\n"


def main():
    parser = argparse.ArgumentParser(description="Render the compact canonical BKE Intent CI PR capsule.")
    parser.add_argument("--status", choices=["PASS", "FAIL"], required=True)
    parser.add_argument("--check", required=True)
    parser.add_argument("--intent", required=True)
    parser.add_argument("--head")
    parser.add_argument("--instruction-digest")
    parser.add_argument("--plan-digest")
    parser.add_argument("--run-id")
    parser.add_argument("--summary")
    parser.add_argument("--log")
    args = parser.parse_args()
    print(render(args), end="")


if __name__ == "__main__":
    main()
