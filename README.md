# BKE Autonomous Engineering

Reusable autonomous-development governance for BKE software repositories.

## Files

- `AGENTS.md` — intentionally small recovery compass / agent entry point.
- `AUTONOMOUS-CORE-INSTRUCTION.md` — full worker/orchestrator autonomous operating contract.
- `CI-VERIFICATION-ECONOMY.md` — autonomous rules for tiered verification and deliberate use of metered remote CI.

## Relationship to BKE Engineering Standard

This repository complements, and does not replace, the BKE Engineering Standard.

Engineering doctrine remains authoritative in:

`jan2xo/bke-engineering-standard`

Development repositories should keep their local `AGENTS.md` small and use it to redirect agents to the Autonomous Core when context is lost, rejection loops occur, or autonomous responsibilities are unclear.

Autonomous workers and orchestrators must also follow `CI-VERIFICATION-ECONOMY.md` when repository work can trigger metered or expensive CI. Cost control changes where and when verification executes; it never weakens a required acceptance or certification gate.

## Intended hierarchy

```text
BKE Engineering Standard
        ↓
BKE Autonomous Engineering
        ↓
Development Repository AGENTS.md
        ↓
Task + Roadmap + Source + Tests + Git Evidence
```

Evidence over claims. Repository over conversational memory.
