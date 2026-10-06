#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "instructions" / "catalog.json"
CHECK_REGISTRY_PATH = ROOT / "checks" / "registry.json"
INTENT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
MODULE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9.-]*$")
CHECK_ID_RE = re.compile(r"^[a-z0-9][a-z0-9.-]*$")


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical_json(value)).hexdigest()


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_string_list(value, name, *, allow_empty=True, pattern=None):
    if not isinstance(value, list):
        raise ValueError(f"{name} must be an array")
    if not allow_empty and not value:
        raise ValueError(f"{name} must be non-empty")
    if any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{name} must contain non-empty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{name} must contain unique values")
    if pattern:
        invalid = [item for item in value if not pattern.fullmatch(item)]
        if invalid:
            raise ValueError(f"{name} contains invalid id(s): {', '.join(invalid)}")


def validate_catalog(catalog):
    if not isinstance(catalog, dict) or set(catalog) != {"version", "modules"}:
        raise ValueError("instruction catalog must contain exactly version and modules")
    if catalog["version"] != 1 or not isinstance(catalog["modules"], list):
        raise ValueError("unsupported instruction catalog")
    seen_ids = set()
    seen_paths = set()
    for entry in catalog["modules"]:
        if not isinstance(entry, dict) or set(entry) != {"id", "path"}:
            raise ValueError("instruction catalog entries require id and path")
        module_id = entry["id"]
        path = entry["path"]
        if not isinstance(module_id, str) or not MODULE_ID_RE.fullmatch(module_id):
            raise ValueError(f"invalid instruction module id: {module_id!r}")
        if not isinstance(path, str) or not path:
            raise ValueError(f"invalid instruction module path for {module_id}")
        if module_id in seen_ids:
            raise ValueError("instruction catalog contains duplicate module ids")
        if path in seen_paths:
            raise ValueError("instruction catalog contains duplicate module paths")
        seen_ids.add(module_id)
        seen_paths.add(path)
    return {entry["id"]: entry for entry in catalog["modules"]}


def validate_intent(intent, catalog_by_id):
    required_keys = {"version", "id", "instructions", "certification", "failure_policy"}
    if not isinstance(intent, dict) or set(intent) != required_keys:
        raise ValueError(f"intent keys must be exactly {sorted(required_keys)}")
    if intent["version"] != 1:
        raise ValueError("unsupported intent version")
    if not isinstance(intent["id"], str) or not INTENT_ID_RE.fullmatch(intent["id"]):
        raise ValueError("intent id must match ^[a-z0-9][a-z0-9-]*$")

    validate_string_list(intent["instructions"], "instructions", allow_empty=False, pattern=MODULE_ID_RE)
    unknown_modules = [module_id for module_id in intent["instructions"] if module_id not in catalog_by_id]
    if unknown_modules:
        raise ValueError(f"unknown instruction module(s): {', '.join(unknown_modules)}")

    certification = intent["certification"]
    if not isinstance(certification, dict) or set(certification) != {"required", "optional"}:
        raise ValueError("certification requires required and optional arrays")
    validate_string_list(certification["required"], "certification.required", allow_empty=False, pattern=CHECK_ID_RE)
    validate_string_list(certification["optional"], "certification.optional", pattern=CHECK_ID_RE)
    overlap = set(certification["required"]) & set(certification["optional"])
    if overlap:
        raise ValueError(f"checks cannot be both required and optional: {', '.join(sorted(overlap))}")

    policy = intent["failure_policy"]
    policy_keys = {"independent_checks_continue", "dependent_checks_stop", "always_publish_capsule"}
    if not isinstance(policy, dict) or set(policy) != policy_keys:
        raise ValueError("invalid failure_policy keys")
    if not all(isinstance(policy[key], bool) for key in policy_keys):
        raise ValueError("failure_policy values must be boolean")


def validate_check_registry(registry):
    if not isinstance(registry, dict) or set(registry) != {"version", "checks"}:
        raise ValueError("check registry must contain exactly version and checks")
    if registry["version"] != 1:
        raise ValueError("unsupported check registry version")
    if not isinstance(registry["checks"], list):
        raise ValueError("check registry checks must be an array")

    allowed = {"id", "depends_on", "executor", "stage", "capsule_label"}
    checks_by_id = {}
    for entry in registry["checks"]:
        if not isinstance(entry, dict) or set(entry) != allowed:
            raise ValueError(f"check registry entries require exactly {sorted(allowed)}")
        check_id = entry["id"]
        if not isinstance(check_id, str) or not CHECK_ID_RE.fullmatch(check_id):
            raise ValueError(f"invalid check id: {check_id!r}")
        if check_id in checks_by_id:
            raise ValueError(f"duplicate check id: {check_id}")
        validate_string_list(entry["depends_on"], f"{check_id}.depends_on", pattern=CHECK_ID_RE)
        if check_id in entry["depends_on"]:
            raise ValueError(f"check cannot depend on itself: {check_id}")
        if entry["stage"] not in {"worker-loop", "convergence", "certification"}:
            raise ValueError(f"invalid stage for {check_id}")
        if not isinstance(entry["capsule_label"], str) or not entry["capsule_label"].strip():
            raise ValueError(f"invalid capsule_label for {check_id}")
        executor = entry["executor"]
        if not isinstance(executor, dict) or set(executor) != {"kind", "argv"}:
            raise ValueError(f"invalid executor for {check_id}")
        if executor["kind"] != "command":
            raise ValueError(f"unsupported executor kind for {check_id}: {executor['kind']!r}")
        validate_string_list(executor["argv"], f"{check_id}.executor.argv", allow_empty=False)
        checks_by_id[check_id] = entry

    for check_id, entry in checks_by_id.items():
        unknown = [dep for dep in entry["depends_on"] if dep not in checks_by_id]
        if unknown:
            raise ValueError(f"{check_id} has unknown dependency/dependencies: {', '.join(unknown)}")
    return checks_by_id


def resolve_check_plan(certification, registry):
    checks_by_id = validate_check_registry(registry)
    roots = list(certification["required"]) + list(certification["optional"])
    unknown = [check_id for check_id in roots if check_id not in checks_by_id]
    if unknown:
        raise ValueError(f"unknown certification check(s): {', '.join(unknown)}")

    state = {}
    order = []

    def visit(check_id, trail):
        current = state.get(check_id, 0)
        if current == 2:
            return
        if current == 1:
            cycle = " -> ".join(trail + [check_id])
            raise ValueError(f"check dependency cycle: {cycle}")
        state[check_id] = 1
        for dep in checks_by_id[check_id]["depends_on"]:
            visit(dep, trail + [check_id])
        state[check_id] = 2
        order.append(check_id)

    for root in roots:
        visit(root, [])

    required_closure = set()

    def mark_required(check_id):
        if check_id in required_closure:
            return
        required_closure.add(check_id)
        for dep in checks_by_id[check_id]["depends_on"]:
            mark_required(dep)

    for root in certification["required"]:
        mark_required(root)

    resolved_checks = []
    for check_id in order:
        entry = checks_by_id[check_id]
        resolved_checks.append({
            "id": check_id,
            "required": check_id in required_closure,
            "depends_on": list(entry["depends_on"]),
            "stage": entry["stage"],
            "capsule_label": entry["capsule_label"],
            "executor": entry["executor"],
        })

    return {
        "registry_version": registry["version"],
        "declared": {
            "required": list(certification["required"]),
            "optional": list(certification["optional"]),
        },
        "checks": resolved_checks,
    }


def resolve(intent_id, head=None):
    catalog = load_json(CATALOG_PATH)
    catalog_by_id = validate_catalog(catalog)

    intent_path = ROOT / "intents" / f"{intent_id}.json"
    if not intent_path.is_file():
        raise ValueError(f"unknown intent: {intent_id}")
    intent = load_json(intent_path)
    if intent.get("id") != intent_id:
        raise ValueError("intent id does not match filename")
    validate_intent(intent, catalog_by_id)

    registry = load_json(CHECK_REGISTRY_PATH)
    execution_plan = resolve_check_plan(intent["certification"], registry)

    resolved_modules = []
    bundle_parts = [f"# BKE Resolved Instruction Bundle\n\nIntent: `{intent_id}`\n"]
    digest_material = []
    for module_id in intent["instructions"]:
        entry = catalog_by_id[module_id]
        module_path = ROOT / entry["path"]
        if not module_path.is_file():
            raise ValueError(f"instruction module missing: {entry['path']}")
        module_content = module_path.read_text(encoding="utf-8").strip() + "\n"
        content_sha = hashlib.sha256(module_content.encode("utf-8")).hexdigest()
        resolved_modules.append({"id": module_id, "path": entry["path"], "sha256": content_sha})
        digest_material.append({"id": module_id, "sha256": content_sha})
        bundle_parts.append(f"\n---\n\n## {module_id}\n\n{module_content}")

    instruction_digest = digest(digest_material)
    plan_digest = digest(execution_plan)
    result = {
        "version": 1,
        "intent": intent_id,
        "head": head,
        "instruction_digest": instruction_digest,
        "plan_digest": plan_digest,
        "execution_key": digest({
            "head": head or "",
            "intent": intent_id,
            "instruction_digest": instruction_digest,
            "plan_digest": plan_digest,
        }),
        "modules": resolved_modules,
        "certification": intent["certification"],
        "execution_plan": execution_plan,
        "failure_policy": intent["failure_policy"],
        "bundle": "".join(bundle_parts).rstrip() + "\n",
    }
    return result


def main():
    parser = argparse.ArgumentParser(description="Resolve a BKE autonomous intent into instructions and an executable certification graph.")
    parser.add_argument("--intent", required=True)
    parser.add_argument("--head")
    parser.add_argument("--json-out")
    parser.add_argument("--bundle-out")
    args = parser.parse_args()

    result = resolve(args.intent, args.head)
    if args.json_out:
        serializable = dict(result)
        serializable.pop("bundle")
        Path(args.json_out).write_text(json.dumps(serializable, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.bundle_out:
        Path(args.bundle_out).write_text(result["bundle"], encoding="utf-8")
    if not args.json_out and not args.bundle_out:
        serializable = dict(result)
        serializable.pop("bundle")
        print(json.dumps(serializable, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
