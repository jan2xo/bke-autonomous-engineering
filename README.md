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

The resolver produces deterministic instruction and certification-plan digests plus an execution key bound to the supplied head.

## Intent CI contract

The repository dogfoods the library through `.github/workflows/intent-ci.yml`.

The workflow checks out the exact PR head, resolves the declared intent, executes the required contract, and always reaches compact reporting. A failed required check still makes the workflow fail; reporting survival does not convert failure into success.

The PR receives one replaceable current-status capsule:

```text
❌ FAIL | instruction-library-contract | shortest actionable error | run #1842
HEAD ... | INTENT ... | INSTR ... | PLAN ...
```

or:

```text
✅ PASS | instruction-library-contract | resolver + contract tests | run #1843
HEAD ... | INTENT ... | INSTR ... | PLAN ...
```

Full logs remain in GitHub Actions. Autonomous actors should use the capsule first and open progressively deeper evidence only when the capsule is insufficient.

## Intended hierarchy

```text
BKE Engineering Standard
        ↓
BKE Autonomous Engineering
        ↓
Development Repository bootstrap / pinned intent source
        ↓
Declared intent + resolved instruction bundle
        ↓
Task + source + tests + exact-head Git evidence
```

Development repositories should keep local bootstrap instructions small. Adoption must pin an immutable revision or version of this library so instruction changes cannot silently rewrite old certification meaning.

Evidence over claims. Repository over conversational memory.
