#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical_json(value)).hexdigest()


def safe_name(check_id):
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", check_id).strip("-") or "check"


def write_log(log_path, text):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(text, encoding="utf-8", errors="replace")


def execution_cwd(check, consumer_root):
    execution_root = check.get("execution_root", "library")
    if execution_root == "library":
        return ROOT
    if execution_root == "consumer":
        if consumer_root is None:
            raise ValueError(f"consumer execution root required for {check['id']}")
        return Path(consumer_root).resolve()
    raise ValueError(f"unsupported execution_root for {check['id']}: {execution_root!r}")


def execute_plan(resolved, log_dir, consumer_root=None):
    execution_plan = resolved.get("execution_plan")
    if not isinstance(execution_plan, dict):
        raise ValueError("resolved intent has no execution_plan")
    if digest(execution_plan) != resolved.get("plan_digest"):
        raise ValueError("resolved plan digest mismatch")

    checks = execution_plan.get("checks")
    if not isinstance(checks, list):
        raise ValueError("execution_plan.checks must be an array")
    policy = resolved.get("failure_policy", {})
    dependent_checks_stop = policy.get("dependent_checks_stop") is True
    independent_checks_continue = policy.get("independent_checks_continue") is True

    log_dir = Path(log_dir)
    statuses = {}
    results = []
    required_failure_seen = False

    for check in checks:
        check_id = check["id"]
        required = check.get("required") is True
        log_path = log_dir / f"{safe_name(check_id)}.log"
        dependencies = check.get("depends_on", [])
        blocked_deps = [dep for dep in dependencies if statuses.get(dep) != "PASS"]

        if dependent_checks_stop and blocked_deps:
            status = "SKIP"
            reason = f"dependency not PASS: {', '.join(blocked_deps)}"
            write_log(log_path, reason + "\n")
            return_code = None
        elif required_failure_seen and not independent_checks_continue:
            status = "SKIP"
            reason = "stopped after earlier required failure"
            write_log(log_path, reason + "\n")
            return_code = None
        else:
            executor = check.get("executor", {})
            if executor.get("kind") != "command":
                status = "FAIL"
                reason = f"unsupported executor kind: {executor.get('kind')!r}"
                write_log(log_path, reason + "\n")
                return_code = None
            else:
                argv = executor.get("argv")
                if not isinstance(argv, list) or not argv or any(not isinstance(item, str) or not item for item in argv):
                    status = "FAIL"
                    reason = "invalid command executor argv"
                    write_log(log_path, reason + "\n")
                    return_code = None
                else:
                    try:
                        cwd = execution_cwd(check, consumer_root)
                    except ValueError as exc:
                        status = "FAIL"
                        reason = str(exc)
                        write_log(log_path, reason + "\n")
                        return_code = None
                    else:
                        completed = subprocess.run(
                            argv,
                            cwd=cwd,
                            text=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                        )
                        write_log(log_path, completed.stdout or "")
                        return_code = completed.returncode
                        status = "PASS" if return_code == 0 else "FAIL"
                        reason = None

        statuses[check_id] = status
        if required and status != "PASS":
            required_failure_seen = True
        results.append({
            "id": check_id,
            "required": required,
            "status": status,
            "return_code": return_code,
            "execution_root": check.get("execution_root", "library"),
            "log": str(log_path),
            "reason": reason,
        })

    required_results = [item for item in results if item["required"]]
    required_nonpass = [item for item in required_results if item["status"] != "PASS"]
    optional_nonpass = [item for item in results if not item["required"] and item["status"] != "PASS"]
    overall = "FAIL" if required_nonpass else "PASS"

    failing = next((item for item in required_nonpass if item["status"] == "FAIL"), None)
    if failing is None and required_nonpass:
        failing = required_nonpass[0]

    passed_required = sum(item["status"] == "PASS" for item in required_results)
    summary = f"{passed_required}/{len(required_results)} required checks passed"
    if optional_nonpass:
        summary += f"; {len(optional_nonpass)} optional checks non-PASS"

    return {
        "status": overall,
        "summary": summary,
        "failing_check": failing["id"] if failing else None,
        "failing_log": failing["log"] if failing else None,
        "checks": results,
    }


def print_check_logs(result):
    for item in result["checks"]:
        log_path = Path(item["log"])
        print(f"::group::BKE check {item['id']} [{item['status']}]")
        if log_path.is_file():
            content = log_path.read_text(encoding="utf-8", errors="replace")
            if content:
                print(content, end="" if content.endswith("\n") else "\n")
        if item.get("reason"):
            print(item["reason"])
        print("::endgroup::")


def main():
    parser = argparse.ArgumentParser(description="Execute a resolved BKE Intent CI certification graph.")
    parser.add_argument("--resolved", required=True)
    parser.add_argument("--result-out", required=True)
    parser.add_argument("--log-dir", required=True)
    parser.add_argument("--consumer-root")
    args = parser.parse_args()

    resolved = json.loads(Path(args.resolved).read_text(encoding="utf-8"))
    result = execute_plan(resolved, Path(args.log_dir), consumer_root=args.consumer_root)
    Path(args.result_out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for item in result["checks"]:
        print(f"{item['status']} {item['id']} ({'required' if item['required'] else 'optional'})")
    print(result["summary"])
    print_check_logs(result)
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
