# BKE Autonomous Engineering Consumer Contract v1

Every BKE engineering repository can consume the same Autonomous Engineering runtime without copying the shared instruction library or CI implementation.

## Repository-owned bootstrap

A consumer keeps only small repository-specific declarations:

```text
.bke/
├── autonomous.json
├── intent.json
├── instructions/
│   ├── catalog.json
│   └── ...
└── checks/
    └── registry.json
```

Shared IDs are centrally owned. Repository-specific IDs use `repo.*`.

## Immutable pin

`.bke/autonomous.json` pins the exact Autonomous Engineering commit:

```json
{
  "version": 1,
  "instruction_source": {
    "repo": "jan2xo/bke-autonomous-engineering",
    "ref": "0123456789abcdef0123456789abcdef01234567"
  },
  "intent_path": ".bke/intent.json",
  "instruction_catalog_path": ".bke/instructions/catalog.json",
  "check_registry_path": ".bke/checks/registry.json"
}
```

v1 deliberately requires a full lowercase 40-character commit SHA. Moving branches and floating tags are rejected as execution authority.

## Tiny consumer workflow

The repository pins the public composite action to the same exact SHA:

```yaml
name: BKE Intent CI

on:
  pull_request:
    branches: [main]

permissions:
  contents: read
  issues: write
  pull-requests: write

jobs:
  intent:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}

      - uses: jan2xo/bke-autonomous-engineering/.github/actions/intent-ci@0123456789abcdef0123456789abcdef01234567
        with:
          head-sha: ${{ github.event.pull_request.head.sha }}
          pr-number: ${{ github.event.pull_request.number }}
          run-id: ${{ github.run_id }}
          github-token: ${{ github.token }}
```

The action verifies that its own immutable action ref equals the SHA declared by the consumer manifest. It also verifies the consumer checkout HEAD before execution.

If a repository intentionally keeps PR permissions read-only, omit `github-token` and `pr-number`; the same compact capsule is still rendered into the Actions job summary.

## Composition

The effective evidence binds:

```text
consumer HEAD
+ pinned Autonomous Engineering SHA
+ manifest digest
+ shared instruction content
+ repo.* instruction content
+ shared check definitions
+ repo.* check definitions
+ dependency graph
+ execution roots
= exact execution key + compact PASS/FAIL capsule
```

Shared checks execute from the pinned Autonomous Engineering action root. `repo.*` checks execute from the consumer repository root.

BKE Worker, Launcher, Licensing Agent, Digital Solutions, Air Stack, Render Dock, and future repositories can all consume the same protocol while retaining their own toolchains and certification adapters.
