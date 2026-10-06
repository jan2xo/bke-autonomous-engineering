# BKE Autonomous Engineering

Reusable autonomous-development governance for BKE software repositories.

## Authority

This repository complements, and does not replace, the BKE Engineering Standard.

Engineering doctrine remains authoritative in:

`jan2xo/bke-engineering-standard`

This repository owns reusable autonomous execution behavior: bounded worker/orchestrator rules, instruction composition, intent-driven CI behavior, compact CI evidence, and context-loss recovery.

## Bootstrap files

- `AGENTS.md` — intentionally small recovery compass / agent entry point.
- `AUTONOMOUS-CORE-INSTRUCTION.md` — full worker/orchestrator autonomous operating contract.
- `CI-VERIFICATION-ECONOMY.md` — tiered verification and deliberate use of metered remote CI.

## Versioned instruction library

`instructions/catalog.json` maps stable instruction IDs to small Markdown modules. An intent names only the modules and certification graph it needs.

Current foundation modules cover:

- GitHub as durable engineering truth;
- PR-as-ledger boundaries;
- exact-head evidence;
- worker ownership;
- human authorization/security boundaries;
- intentional CI;
- versioned certification check resolution;
- compact PASS/FAIL capsules;
- progressive evidence escalation.

Intent declarations live under `intents/`. They are data, not giant copied prompts.

Resolve an intent with:

```bash
python3 scripts/resolve_intent.py \
  --intent library-maintenance \
  --head "$(git rev-parse HEAD)" \
  --json-out resolved-intent.json \
  --bundle-out resolved-instructions.md
```

The resolver produces a deterministic instruction digest, an effective executable certification graph, a plan digest over that resolved graph, and an execution key bound to the supplied head.

## Upgradeable certification graph

`checks/registry.json` maps stable check IDs to versioned executable definitions and dependencies. Intents continue to declare only required/optional check IDs.

The effective plan is resolved as:

```text
intent check IDs
    ↓
versioned check registry
    ↓
resolved dependency graph + executable definitions
    ↓
plan digest
    ↓
generic graph executor
```

Unknown declared checks fail closed. A change to the executable meaning of a resolved check changes the plan digest, so old proof cannot silently acquire a new meaning.

The registry begins with one dogfood check, but the contract is intended to grow from one check to multi-platform certification graphs without redesigning the intent format or hard-coding check IDs into workflow logic.

Execute a previously resolved graph with:

```bash
python3 scripts/run_intent_ci.py \
  --resolved resolved-intent.json \
  --result-out intent-ci-result.json \
  --log-dir .intent-ci
```

Independent checks may continue after a failure; dependent checks stop when their prerequisites fail according to the declared failure policy. Any non-PASS required check keeps the final result failed.

## Intent CI contract

The repository dogfoods the library through `.github/workflows/intent-ci.yml`.

The workflow checks out the exact PR head, resolves the declared intent and effective plan, executes that plan through the generic executor, and always reaches compact reporting. Workflow YAML does not separately hard-code which certification check constitutes the plan.

The PR receives one replaceable current-status capsule:

```text
❌ FAIL | failing-check | shortest actionable error | run #1842
HEAD ... | INTENT ... | INSTR ... | PLAN ...
```

or:

```text
✅ PASS | required-plan | 3/3 required checks passed | run #1843
HEAD ... | INTENT ... | INSTR ... | PLAN ...
```

Full per-check logs remain in GitHub Actions. Autonomous actors should use the capsule first and open progressively deeper evidence only when the capsule is insufficient.

## Intended hierarchy

```text
BKE Engineering Standard
        ↓
BKE Autonomous Engineering
        ↓
Development Repository bootstrap / pinned intent source
        ↓
Declared intent + resolved instructions + effective certification graph
        ↓
Task + source + tests + exact-head Git evidence
```

Development repositories should keep local bootstrap instructions small. Adoption must pin an immutable revision or version of this library so instruction or execution changes cannot silently rewrite old certification meaning.

Evidence over claims. Repository over conversational memory.
