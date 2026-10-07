# BKE Autonomous Engineering Consumer Contract v1

Every BKE engineering repository consumes the same private Autonomous Engineering instruction/certification semantics without copying the central instruction library and without requiring the product repository to read the private source directly.

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

Shared instruction IDs remain centrally owned. Repository-specific instruction/check IDs use the `repo.*` namespace.

## Immutable source pin

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

v1 requires a full lowercase 40-character commit SHA. Moving branches and floating tags are rejected as execution authority.

## Universal control-plane path

The canonical path is **not** a direct cross-repository `uses:` dependency on the private source.

```text
product PR + exact head
        ↓
BKE GitHub App
        ↓
trusted resolve
  - validates exact head
  - loads pinned private instructions
  - reads .bke declarations as data
  - executes no product commands
        ↓
sanitized resolved plan
        ↓
unprivileged execute
  - fresh environment
  - no App credential
  - no OIDC private-source minting
  - no private instruction checkout
  - repo.* checks only
        ↓
per-check results
        ↓
trusted report
  - no product code execution
  - App-owned status + compact capsule
```

See `consumer/TRUST-MODEL.md`.

## Consumer certification scope

For v1, executable consumer checks and their dependencies must use `repo.*`. This is deliberate trust separation: product-supplied commands execute only in the unprivileged phase.

Shared BKE behavior remains centrally resolved through instruction modules and resolver/executor semantics. Future executor kinds may add separately isolated platform/release certification without weakening this boundary.

## Evidence identity

The effective evidence binds:

```text
consumer exact HEAD
+ pinned Autonomous Engineering SHA
+ manifest digest
+ shared instruction content hashes
+ repo.* instruction content hashes
+ repo.* executable check definitions
+ dependency graph
= execution key + compact PASS/FAIL capsule
```

The resolved JSON transferred into execution contains metadata/digests and the repo plan, not the private instruction bundle.

## Repository-agnostic design

BKE Worker is only the first proving adopter. Launcher, Licensing Agent, Digital Solutions, Air Stack, Render Dock, and future BKE repositories use the same manifest and trust protocol while retaining their own `repo.*` toolchain adapters.

The GitHub App/control plane owns enrollment, request authentication, least-privilege repository access, and result publication. Product repositories own implementation and repo-specific certification adapters. Autonomous Engineering owns shared instruction semantics and plan resolution.
