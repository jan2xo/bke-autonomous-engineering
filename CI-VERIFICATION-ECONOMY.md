# Autonomous CI Verification Economy

This document applies the BKE Engineering Standard's CI Verification Economy policy to autonomous worker/orchestrator execution.

The Engineering Standard remains authoritative. This document does not weaken any verification, audit, milestone, release, security, recovery, or production gate.

## Core Rule

**Expensive CI is a convergence/certification gate, not the autonomous worker's editing feedback loop.**

Autonomous development should normally follow:

```text
WORKER
  ↓
implement
  ↓
local/disposable worker-loop verification
  ↓
commit / bounded remediation
  ↓
worker-loop verification
  ↓
HANDOFF
  ↓
ORCHESTRATOR
  ↓
review evidence
  ↓
meaningful convergence boundary
  ↓
bounded remote CI
  ↓
independent review
  ↓
ACCEPT / REMEDIATE / REJECT
  ↓
certification boundary when applicable
  ↓
full required certification CI
```

## Worker Rules

Workers shall:

- prefer repository-controlled local or disposable-environment verification during implementation;
- run focused syntax, lint, type, unit, changed-area, and other appropriate fast checks before handoff;
- not push trivial commits merely to use remote CI as a test command;
- not repeatedly trigger full integration, end-to-end, recovery, deployment, security, or certification suites after every edit when equivalent inner-loop verification exists;
- preserve executed verification evidence in the handoff;
- identify which broader checks remain required at convergence or certification.

A worker may use remote CI during implementation when the required behavior genuinely cannot be reproduced in the worker environment or when repository policy explicitly requires that remote boundary. The reason must be material, not convenience.

## Orchestrator Rules

The orchestrator shall:

- distinguish worker-loop, convergence, and certification verification;
- prevent unnecessary remote CI churn across worker commits;
- request broader CI when a branch is genuinely review-ready or when a material remediation invalidates prior evidence;
- avoid rerunning unrelated expensive suites whose evidence remains valid for the reviewed revision and risk boundary;
- ensure all verification required by the Engineering Standard still executes before the applicable acceptance gate;
- treat CI minutes, runner time, external API quotas, and equivalent metered verification resources as finite engineering resources.

The orchestrator must never trade away required assurance merely to conserve CI resources.

## Review and Remediation

Independent review should evaluate the evidence already produced before requesting another run.

After REMEDIATE or REJECT, rerun the verification invalidated by the remediation. Full-suite reruns are required only when the change or governing gate makes the prior full-suite evidence stale.

Do not create the loop:

```text
edit → push → full CI → edit → push → full CI
```

when this is sufficient:

```text
edit → focused verification → remediate → focused verification
                                  ↓
                            review-ready
                                  ↓
                          convergence CI
```

## CI Trigger Design

Autonomous repositories should prefer risk-appropriate deliberate triggers for expensive jobs, including review-ready pull requests, protected-branch integration, merge queues, workflow dispatch, release events, or equivalent gates.

Unconditional `push` triggers for expensive suites should exist only when justified by repository risk or architecture.

Cheap required checks may remain frequent.

## Evidence Integrity

Cost optimization changes **where and when** verification executes. It does not change what PASS means.

`PASS` still means the required verification actually executed successfully.

`NOT RUN`, `PARTIAL`, and `BLOCKED` remain distinct states and must never be relabeled as PASS to save runner resources.

## Governing Principle

Use the cheapest environment that faithfully verifies the required behavior.

Escalate verification cost as the change approaches convergence, acceptance, release, and production.

**Spend CI where it buys assurance, not where it merely repeats feedback.**
