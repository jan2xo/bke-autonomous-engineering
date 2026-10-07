# BKE Consumer Certification Trust Model

The universal BKE consumer path must work for public and private product repositories without exposing the private Autonomous Engineering source or its credentials to pull-request code.

## Phase 1 — trusted resolve

A trusted control-plane job or service:

1. receives a GitHub App-authenticated certification request;
2. verifies repository enrollment, PR identity, exact consumer head, and the `.bke/autonomous.json` immutable source pin;
3. loads the pinned private Autonomous Engineering revision;
4. reads the consumer intent, repo instruction modules, and repo check registry as **data only**;
5. resolves the shared instruction bundle and repo certification graph;
6. emits only a sanitized `resolved-intent.json` containing digests, module metadata, and the executable repo plan;
7. never executes a command supplied by the consumer repository.

Private instruction text and GitHub App credentials do not leave this phase.

## Phase 2 — unprivileged execute

A fresh execution environment:

1. has no GitHub App credential;
2. has no Actions OIDC permission capable of minting the private-source credential;
3. has no checkout of the private Autonomous Engineering repository;
4. checks out only the consumer repository at the exact certified head;
5. receives the sanitized resolved plan and a minimal generic runner;
6. verifies the plan digest and exact consumer head;
7. executes only `repo.*` checks.

Consumer v1 therefore forbids executable shared/library checks and cross-namespace check dependencies. Shared policy is delivered through instructions and resolver semantics, while executable product certification remains repo-owned.

## Phase 3 — trusted report

A fresh trusted reporter or GitHub App:

1. receives only the resolved identity/digests plus per-check results;
2. does not execute consumer code;
3. publishes the compact PASS/FAIL capsule and commit/check status;
4. preserves required failure as red;
5. keeps full logs outside the actor-facing capsule.

## Why the split exists

A public repository cannot directly consume a private GitHub Action repository. More importantly, allowing PR-controlled code to mint a token for the private instruction repository would violate the trust boundary even if access were technically possible.

The GitHub App/control plane is therefore the bridge:

```text
Product PR / exact head
        ↓
GitHub App request
        ↓
TRUSTED RESOLVE
private pinned instructions + repo declarations as data
        ↓
sanitized plan
        ↓
UNPRIVILEGED EXECUTE
repo.* checks only
        ↓
results
        ↓
TRUSTED REPORT
GitHub App capsule / status
```

No visibility change to the private Autonomous Engineering repository is required.
