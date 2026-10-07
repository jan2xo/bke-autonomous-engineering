# BKE Autonomous Engineering

Reusable autonomous-development governance and intent-driven certification runtime for BKE engineering repositories.

## Authority

This repository complements, and does not replace, the BKE Engineering Standard.

Engineering doctrine remains authoritative in:

`jan2xo/bke-engineering-standard`

This repository owns reusable autonomous execution behavior: bounded worker/orchestrator rules, instruction composition, intent-driven CI behavior, compact CI evidence, consumer contracts, and context-loss recovery.

## Versioned instruction and certification runtime

`instructions/catalog.json` maps stable shared instruction IDs to small Markdown modules. `checks/registry.json` maps stable shared check IDs to executable definitions and dependencies. Intents name only the instruction/check IDs they need.

The resolver produces:

```text
exact head
+ resolved instructions
+ effective executable certification graph
+ instruction digest
+ plan digest
+ execution key
```

Unknown required checks fail closed. A change to executable meaning changes the plan digest, so stale proof cannot silently acquire a new meaning.

## Repository-agnostic consumer contract

All BKE engineering repositories can consume the same runtime through an immutable full commit SHA.

A consumer owns only:

```text
.bke/autonomous.json
.bke/intent.json
.bke/instructions/catalog.json + repo.* modules
.bke/checks/registry.json + repo.* checks
tiny workflow calling the pinned composite action
```

Shared IDs cannot be overridden locally. Repository-specific IDs use `repo.*`.

The pinned composite action lives at:

```text
.github/actions/intent-ci/action.yml
```

A product repository calls it at the same immutable SHA declared in `.bke/autonomous.json`. The runtime verifies the consumer exact head and the Autonomous Engineering source pin before executing certification.

See `consumer/README.md` for the generic integration contract. It is deliberately not Worker-specific; BKE Worker is only intended as the first proving adopter.

## Certification flow

```text
GitHub exact head
      ↓
declared intent
      ↓
shared + repo.* instruction resolution
      ↓
shared + repo.* certification graph resolution
      ↓
effective PLAN digest
      ↓
generic graph execution
      ↓
required result aggregation
   ┌───────┴───────┐
 PASS             FAIL
   ↓                ↓
PASS capsule     FAIL capsule
   ↓                ↓
CI green          CI red
```

Independent checks may continue after another graph branch fails. Dependent checks stop/skip when prerequisites fail. Full per-check output remains in GitHub Actions; PR comments remain compact.

## Intended hierarchy

```text
BKE Engineering Standard
        ↓
BKE Autonomous Engineering @ immutable SHA
        ↓
Any BKE engineering repository
        ↓
repo intent + repo.* adapters
        ↓
effective certification graph
        ↓
exact-head PASS/FAIL evidence
```

Development repositories should keep local bootstrap instructions small. Evidence over claims. Repository over conversational memory.
