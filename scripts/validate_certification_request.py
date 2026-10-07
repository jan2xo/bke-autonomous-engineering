#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

REPOSITORY_RE = re.compile(r"^jan2xo/[A-Za-z0-9_.-]+$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def safe_relative_path(value):
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        return False
    return all(part not in {"", ".", ".."} for part in Path(value).parts)


def validate_request(repository, head, pull_request, manifest_path):
    if not isinstance(repository, str) or not REPOSITORY_RE.fullmatch(repository):
        raise ValueError("repository must be an enrolled jan2xo repository")
    if not isinstance(head, str) or not SHA_RE.fullmatch(head):
        raise ValueError("head must be a full lowercase 40-character commit SHA")
    try:
        pr_number = int(pull_request)
    except (TypeError, ValueError) as exc:
        raise ValueError("pull_request must be a positive integer") from exc
    if pr_number < 1:
        raise ValueError("pull_request must be a positive integer")
    if not safe_relative_path(manifest_path):
        raise ValueError("manifest_path must be a safe relative path")
    return {
        "version": 1,
        "repository": repository,
        "head": head,
        "pull_request": pr_number,
        "manifest_path": manifest_path,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate a BKE consumer-certification request.")
    parser.add_argument("--repository", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--pull-request", required=True)
    parser.add_argument("--manifest-path", default=".bke/autonomous.json")
    parser.add_argument("--json-out")
    args = parser.parse_args()

    request = validate_request(
        args.repository,
        args.head,
        args.pull_request,
        args.manifest_path,
    )
    payload = json.dumps(request, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        Path(args.json_out).write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
