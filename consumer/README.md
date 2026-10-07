# BKE Autonomous Engineering Consumer Contract v1

Every BKE engineering repository may consume the same Autonomous Engineering runtime without copying the shared instruction library or CI implementation.

## Repository-owned files

A consumer keeps only small repository-specific declarations under `.bke/`:

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

Shared instruction/check IDs are owned centrally. Repository-specific IDs use the `repo.*` namespace and cannot override shared IDs.

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

v1 deliberately requires a full 40-character commit SHA. Moving branches and floating tags are rejected.

## Tiny consumer workflow

The consumer workflow pins the composite action to the same SHA:

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

The action verifies that its own pinned action ref equals the SHA declared by the consumer manifest. The consumer checkout HEAD is also verified against the supplied exact head.

## Composition

The effective evidence binds:

```text
consumer HEAD
+ pinned Autonomous Engineering SHA
+ shared instruction content
+ repo.* instruction content
+ shared check definitions
+ repo.* check definitions
+ dependency graph
+ execution roots
= exact execution key + compact PASS/FAIL capsule
```

Shared checks execute from the Autonomous Engineering action root. `repo.*` checks execute from the consumer repository root.

This contract is repository-agnostic. BKE Worker, Launcher, Licensing Agent, Digital Solutions, Air Stack, Render Dock, and future repositories can all consume the same protocol while retaining their own toolchains and certification adapters.
