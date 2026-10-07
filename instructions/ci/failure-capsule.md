# CI Result Capsule

Intent CI maintains one compact current-status capsule per pull request. Full per-check raw evidence remains available in GitHub Actions logs/artifacts for the repository's configured platform retention window.

Preferred failure form:

`❌ FAIL | failing-check | shortest actionable error | run #N`

Preferred success form:

`✅ PASS | required-checks summary | run #N`

The capsule may include exact-head and instruction/plan digests on a second compact metadata line. Do not paste stack traces or large log excerpts into the PR status comment.

The replaceable current-status capsule and a temporary Actions run URL are not, by themselves, the long-term acceptance record. Before accepted work is integrated, preserve a durable consequential checkpoint in the PR, review, commit, release, or equivalent repository-linked ledger that identifies the evidence subject, applicable certification scope/meaning, relevant outcomes and limitations, and independent decision.

Retain selected raw evidence beyond the default platform window when the product's audit, release, recovery, regulatory, security, or operational risk requires it. Do not retain every raw log permanently merely for ceremony.
