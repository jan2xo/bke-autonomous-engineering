# BKE Autonomous Engineering

Private reusable autonomous-development governance and intent-driven certification semantics for BKE engineering repositories.

## Authority

This repository complements, and does not replace, the BKE Engineering Standard.

Engineering doctrine remains authoritative in:

`jan2xo/bke-engineering-standard`

This repository owns reusable autonomous execution behavior: bounded worker/orchestrator rules, instruction composition, intent-driven CI semantics, compact evidence, consumer contracts, and context-loss recovery.

## Versioned instruction and certification runtime

`instructions/catalog.json` maps stable shared instruction IDs to small Markdown modules. `checks/registry.json` maps checks used by this central repository. Product repositories define their executable adapters under the reserved `repo.*` namespace.

The resolver produces exact-head/source-bound instruction and plan digests plus an execution key. Unknown required checks fail closed. A change in execution meaning changes the plan digest, so stale proof cannot silently acquire a new meaning.

## Universal consumer architecture

All BKE engineering repositories may consume the same private instruction source through an immutable SHA, regardless of whether the product repository itself is public or private.

The product repo does **not** need direct read access to this private repository.

```text
Product PR / exact head
        ↓
BKE GitHub App
        ↓
TRUSTED RESOLVE
private pinned instructions + .bke declarations as data
        ↓
sanitized resolved plan
        ↓
UNPRIVILEGED EXECUTE
repo.* checks; no App token / no private source
        ↓
results
        ↓
TRUSTED REPORT
App-owned PASS/FAIL status + compact capsule
```

This split prevents PR-controlled code from receiving a credential capable of reading private engineering instructions.

Consumer repositories keep only:

```text
.bke/autonomous.json
.bke/intent.json
.bke/instructions/catalog.json + repo.* modules
.bke/checks/registry.json + repo.* checks
```

See `consumer/README.md` and `consumer/TRUST-MODEL.md`.

## Certification flow

```text
exact consumer HEAD
      ↓
declared intent
      ↓
shared + repo.* instruction resolution
      ↓
repo.* certification graph resolution
      ↓
effective PLAN digest
      ↓
isolated execution
      ↓
required result aggregation
   ┌───────┴───────┐
 PASS             FAIL
   ↓                ↓
PASS capsule     FAIL capsule
   ↓                ↓
green evidence    red evidence
```

Independent repo checks may continue after another graph branch fails. Dependent checks stop/skip when prerequisites fail. Full per-check output stays in CI evidence; actor-facing capsules remain compact.

## Intended hierarchy

```text
BKE Engineering Standard
        ↓
BKE Autonomous Engineering @ immutable SHA
        ↓
BKE GitHub App / control plane
        ↓
Any enrolled BKE engineering repository
        ↓
repo intent + repo.* adapters
        ↓
exact-head PASS/FAIL evidence
```

BKE Worker is the first proving adopter, not a special-case target. Evidence over claims. Repository over conversational memory.
