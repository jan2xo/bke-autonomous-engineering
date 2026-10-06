#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "instructions" / "catalog.json"


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical_json(value)).hexdigest()


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_intent(intent, catalog_by_id):
    required = {"version", "id", "instructions", "certification", "failure_policy"}
    if set(intent) != required:
        raise ValueError(f"intent keys must be exactly {sorted(required)}")
    if intent["version"] != 1:
        raise ValueError("unsupported intent version")
    if not intent["instructions"] or len(intent["instructions"]) != len(set(intent["instructions"])):
        raise ValueError("instructions must be non-empty and unique")
    unknown = [module_id for module_id in intent["instructions"] if module_id not in catalog_by_id]
    if unknown:
        raise ValueError(f"unknown instruction module(s): {', '.join(unknown)}")
    certification = intent["certification"]
    if set(certification) != {"required", "optional"} or not certification["required"]:
        raise ValueError("certification requires non-empty required and optional arrays")
    policy = intent["failure_policy"]
    policy_keys = {"independent_checks_continue", "dependent_checks_stop", "always_publish_capsule"}
    if set(policy) != policy_keys or not all(isinstance(policy[k], bool) for k in policy_keys):
        raise ValueError("invalid failure_policy")


def resolve(intent_id, head=None):
    catalog = load_json(CATALOG_PATH)
    modules = catalog.get("modules", [])
    catalog_by_id = {entry["id"]: entry for entry in modules}
    if len(catalog_by_id) != len(modules):
        raise ValueError("instruction catalog contains duplicate module ids")

    intent_path = ROOT / "intents" / f"{intent_id}.json"
    if not intent_path.is_file():
        raise ValueError(f"unknown intent: {intent_id}")
    intent = load_json(intent_path)
    if intent.get("id") != intent_id:
        raise ValueError("intent id does not match filename")
    validate_intent(intent, catalog_by_id)

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
    plan_digest = digest(intent["certification"])
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
        "failure_policy": intent["failure_policy"],
        "bundle": "".join(bundle_parts).rstrip() + "\n",
    }
    return result


def main():
    parser = argparse.ArgumentParser(description="Resolve a BKE autonomous intent into an exact instruction bundle.")
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
