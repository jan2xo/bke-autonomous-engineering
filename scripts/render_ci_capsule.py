#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

MARKER = "<!-- bke-intent-ci-status -->"
ANSI = re.compile(r"\x1b\[[0-9;]*m")
EXCEPTION_CAUSE = re.compile(r"(?:\b[A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception):\s*.+|\berror:\s*.+)")
TEST_LABEL = re.compile(r"^(?:FAIL|ERROR):\s*.+")
SIGNALS = re.compile(r"(FAILED|ERROR|Exception|Traceback)", re.IGNORECASE)
GENERIC_SUMMARY = re.compile(r"^(?:FAILED|ERRORS?)\s*\([^)]*\)$", re.IGNORECASE)


def compact(text, limit=180):
    text = ANSI.sub("", text)
    text = " ".join(text.strip().split())
    if len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def shortest_actionable_error(log_path):
    if not log_path or not Path(log_path).is_file():
        return "required verification failed; inspect the failing step"
    lines = Path(log_path).read_text(encoding="utf-8", errors="replace").splitlines()[-250:]
    causal = []
    labels = []
    fallback = []
    for line in lines:
        value = compact(line)
        if not value or GENERIC_SUMMARY.fullmatch(value) or value.startswith("Traceback ("):
            continue
        if EXCEPTION_CAUSE.search(value):
            causal.append(value)
        elif TEST_LABEL.search(value):
            labels.append(value)
        elif SIGNALS.search(value):
            fallback.append(value)
    if causal:
        return causal[-1]
    if labels:
        return labels[-1]
    if fallback:
        return fallback[-1]
    for line in reversed(lines[-80:]):
        value = compact(line)
        if value:
            return value
    return "required verification failed; inspect the failing step"


def render(args):
    icon = "✅" if args.status == "PASS" else "❌"
    if args.status == "PASS":
        detail = compact(args.summary or "required verification passed")
    else:
        detail = shortest_actionable_error(args.log)
    run = f"run #{args.run_id}" if args.run_id else "run unavailable"
    line = f"{icon} {args.status} | {args.check} | {detail} | {run}"
    fields = [
        f"HEAD {(args.head or 'unknown')[:12]}",
        f"INTENT {args.intent}",
    ]
    if args.source_ref:
        fields.append(f"SRC {args.source_ref[:12]}")
    fields.extend([
        f"INSTR {(args.instruction_digest or 'unknown')[:12]}",
        f"PLAN {(args.plan_digest or 'unknown')[:12]}",
    ])
    meta = "`" + " | ".join(fields) + "`"
    return f"{MARKER}\n{line}\n{meta}\n"


def main():
    parser = argparse.ArgumentParser(description="Render the compact canonical BKE Intent CI PR capsule.")
    parser.add_argument("--status", choices=["PASS", "FAIL"], required=True)
    parser.add_argument("--check", required=True)
    parser.add_argument("--intent", required=True)
    parser.add_argument("--head")
    parser.add_argument("--source-ref")
    parser.add_argument("--instruction-digest")
    parser.add_argument("--plan-digest")
    parser.add_argument("--run-id")
    parser.add_argument("--summary")
    parser.add_argument("--log")
    args = parser.parse_args()
    print(render(args), end="")


if __name__ == "__main__":
    main()
