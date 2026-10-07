#!/usr/bin/env python3
import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN_RE = re.compile(r"^[0-9a-f]{40}$")
CANONICAL_REPO = "jan2xo/bke-autonomous-engineering"


def load_core():
    path = ROOT / "scripts" / "resolve_intent.py"
    spec = importlib.util.spec_from_file_location("bke_resolve_intent_core", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def safe_child(root, relative, label):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError(f"{label} must be a non-empty relative path")
    root = Path(root).resolve()
    candidate = (root / relative).resolve()
    if candidate == root or root not in candidate.parents:
        raise ValueError(f"{label} escapes the consumer repository")
    return candidate


def git_head(root):
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError(f"cannot verify Git HEAD for {root}") from exc


def validate_manifest(manifest):
    required = {
        "version",
        "instruction_source",
        "intent_path",
        "instruction_catalog_path",
        "check_registry_path",
    }
    if not isinstance(manifest, dict) or set(manifest) != required:
        raise ValueError(f"consumer manifest keys must be exactly {sorted(required)}")
    if manifest["version"] != 1:
        raise ValueError("unsupported consumer manifest version")

    source = manifest["instruction_source"]
    if not isinstance(source, dict) or set(source) != {"repo", "ref"}:
        raise ValueError("instruction_source requires repo and ref")
    if source["repo"] != CANONICAL_REPO:
        raise ValueError(f"instruction_source.repo must be {CANONICAL_REPO}")
    if not isinstance(source["ref"], str) or not PIN_RE.fullmatch(source["ref"]):
        raise ValueError("instruction_source.ref must be a full immutable 40-character commit SHA")

    for key in ("intent_path", "instruction_catalog_path", "check_registry_path"):
        value = manifest[key]
        if not isinstance(value, str) or not value or Path(value).is_absolute():
            raise ValueError(f"{key} must be a non-empty relative path")


def validate_consumer_catalog(catalog, core):
    catalog_by_id = core.validate_catalog(catalog)
    invalid = [module_id for module_id in catalog_by_id if not module_id.startswith("repo.")]
    if invalid:
        raise ValueError(f"consumer instruction ids must use repo.* namespace: {', '.join(sorted(invalid))}")
    return catalog_by_id


def validate_consumer_registry_shape(registry):
    if not isinstance(registry, dict) or set(registry) != {"version", "checks"}:
        raise ValueError("consumer check registry must contain exactly version and checks")
    if registry["version"] != 1 or not isinstance(registry["checks"], list):
        raise ValueError("unsupported consumer check registry")
    ids = []
    for entry in registry["checks"]:
        if not isinstance(entry, dict):
            raise ValueError("consumer check registry entries must be objects")
        check_id = entry.get("id")
        if not isinstance(check_id, str) or not check_id.startswith("repo."):
            raise ValueError("consumer check ids must use repo.* namespace")
        ids.append(check_id)
    if len(ids) != len(set(ids)):
        raise ValueError("consumer check registry contains duplicate ids")


def resolve_consumer(
    consumer_root,
    manifest_path,
    head,
    *,
    library_head,
    consumer_head_actual,
):
    core = load_core()
    consumer_root = Path(consumer_root).resolve()

    if not isinstance(head, str) or not PIN_RE.fullmatch(head):
        raise ValueError("consumer head must be a full 40-character commit SHA")
    if consumer_head_actual != head:
        raise ValueError(f"consumer checkout head mismatch: expected {head}, got {consumer_head_actual}")

    manifest_file = safe_child(consumer_root, manifest_path, "manifest path")
    if not manifest_file.is_file():
        raise ValueError(f"consumer manifest not found: {manifest_path}")
    manifest = load_json(manifest_file)
    validate_manifest(manifest)

    source_ref = manifest["instruction_source"]["ref"]
    if library_head != source_ref:
        raise ValueError(f"instruction source mismatch: manifest pins {source_ref}, executing {library_head}")

    intent_file = safe_child(consumer_root, manifest["intent_path"], "intent_path")
    catalog_file = safe_child(consumer_root, manifest["instruction_catalog_path"], "instruction_catalog_path")
    registry_file = safe_child(consumer_root, manifest["check_registry_path"], "check_registry_path")
    for path, label in (
        (intent_file, "intent"),
        (catalog_file, "instruction catalog"),
        (registry_file, "check registry"),
    ):
        if not path.is_file():
            raise ValueError(f"consumer {label} not found: {path.relative_to(consumer_root)}")

    shared_catalog = core.load_json(ROOT / "instructions" / "catalog.json")
    shared_catalog_by_id = core.validate_catalog(shared_catalog)
    consumer_catalog = load_json(catalog_file)
    consumer_catalog_by_id = validate_consumer_catalog(consumer_catalog, core)
    overlap = set(shared_catalog_by_id) & set(consumer_catalog_by_id)
    if overlap:
        raise ValueError(f"consumer instruction ids collide with shared ids: {', '.join(sorted(overlap))}")
    combined_catalog_by_id = {**shared_catalog_by_id, **consumer_catalog_by_id}

    intent = load_json(intent_file)
    core.validate_intent(intent, combined_catalog_by_id)

    shared_registry = core.load_json(ROOT / "checks" / "registry.json")
    consumer_registry = load_json(registry_file)
    validate_consumer_registry_shape(consumer_registry)
    shared_ids = {entry["id"] for entry in shared_registry["checks"]}
    consumer_ids = {entry["id"] for entry in consumer_registry["checks"]}
    overlap = shared_ids & consumer_ids
    if overlap:
        raise ValueError(f"consumer check ids collide with shared ids: {', '.join(sorted(overlap))}")

    combined_registry = {
        "version": 1,
        "checks": list(shared_registry["checks"]) + list(consumer_registry["checks"]),
    }
    execution_plan = core.resolve_check_plan(
        intent["certification"],
        combined_registry,
        intent["failure_policy"],
    )
    for check in execution_plan["checks"]:
        check["execution_root"] = "consumer" if check["id"] in consumer_ids else "library"

    resolved_modules = []
    digest_material = []
    bundle_parts = [
        "# BKE Resolved Consumer Instruction Bundle\n\n"
        f"Intent: `{intent['id']}`\n\n"
        f"Consumer head: `{head}`\n\n"
        f"Autonomous Engineering: `{source_ref}`\n"
    ]

    for module_id in intent["instructions"]:
        if module_id in consumer_catalog_by_id:
            entry = consumer_catalog_by_id[module_id]
            source = "consumer"
            module_path = safe_child(consumer_root, entry["path"], f"instruction module {module_id}")
        else:
            entry = shared_catalog_by_id[module_id]
            source = "library"
            module_path = (ROOT / entry["path"]).resolve()
            if ROOT.resolve() not in module_path.parents:
                raise ValueError(f"shared instruction module escapes library root: {entry['path']}")

        if not module_path.is_file():
            raise ValueError(f"instruction module missing: {entry['path']}")
        module_content = module_path.read_text(encoding="utf-8").strip() + "\n"
        content_sha = hashlib.sha256(module_content.encode("utf-8")).hexdigest()
        resolved_modules.append({
            "id": module_id,
            "path": entry["path"],
            "source": source,
            "sha256": content_sha,
        })
        digest_material.append({"id": module_id, "source": source, "sha256": content_sha})
        bundle_parts.append(f"\n---\n\n## {module_id}\n\n{module_content}")

    manifest_digest = core.digest(manifest)
    instruction_digest = core.digest(digest_material)
    plan_digest = core.digest(execution_plan)
    result = {
        "version": 1,
        "intent": intent["id"],
        "head": head,
        "source": {"repo": CANONICAL_REPO, "ref": source_ref},
        "manifest_digest": manifest_digest,
        "instruction_digest": instruction_digest,
        "plan_digest": plan_digest,
        "execution_key": core.digest({
            "head": head,
            "intent": intent["id"],
            "source_ref": source_ref,
            "manifest_digest": manifest_digest,
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
    parser = argparse.ArgumentParser(description="Resolve a consumer repository against a pinned BKE Autonomous Engineering revision.")
    parser.add_argument("--consumer-root", required=True)
    parser.add_argument("--manifest", default=".bke/autonomous.json")
    parser.add_argument("--head", required=True)
    parser.add_argument("--library-head")
    parser.add_argument("--json-out")
    parser.add_argument("--bundle-out")
    args = parser.parse_args()

    consumer_root = Path(args.consumer_root).resolve()
    library_head = args.library_head or git_head(ROOT)
    consumer_head_actual = git_head(consumer_root)
    result = resolve_consumer(
        consumer_root,
        args.manifest,
        args.head,
        library_head=library_head,
        consumer_head_actual=consumer_head_actual,
    )

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
