# BKE Autonomous Engineering

Reusable autonomous-development governance for BKE software repositories.

## Files

- `AGENTS.md` — intentionally small recovery compass / agent entry point.
- `AUTONOMOUS-CORE-INSTRUCTION.md` — full worker/orchestrator autonomous operating contract.

## Relationship to BKE Engineering Standard

This repository complements, and does not replace, the BKE Engineering Standard.

Engineering doctrine remains authoritative in:

`jan2xo/bke-engineering-standard`

Development repositories should keep their local `AGENTS.md` small and use it to redirect agents to the Autonomous Core when context is lost, rejection loops occur, or autonomous responsibilities become unclear.

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
