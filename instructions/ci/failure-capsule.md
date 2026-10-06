# CI Result Capsule

Intent CI maintains one compact current-status capsule per pull request and preserves full raw evidence in GitHub Actions/logs/artifacts.

Preferred failure form:

`❌ FAIL | failing-check | shortest actionable error | run #N`

Preferred success form:

`✅ PASS | required-checks summary | run #N`

The capsule may include exact-head and instruction/plan digests on a second compact metadata line. Do not paste stack traces or large log excerpts into the PR status comment.
