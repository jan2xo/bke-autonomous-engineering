# Pull Request Ledger

Use one fresh pull request for one independent engineering intent unless repository policy explicitly defines a different safe boundary.

The PR states human-readable intent and acceptance scope. Durable comments and review records preserve consequential implementation, certification, blocked, remediation, reassignment, acceptance, and merge checkpoints. Do not turn the PR description into a chronological transcript.

Before integration of accepted work, the durable ledger must make the acceptance reconstructable even after replaceable status comments change or hosted CI raw evidence expires. Record, directly or by durable reference:

- the immutable evidence subject reviewed or certified;
- the applicable certification scope or execution meaning;
- relevant verification outcomes and material limitations;
- the independent ACCEPT / REMEDIATE / REJECT decision;
- the accepted integration identity when integration occurs.

Raw logs and artifacts may remain in hosted CI only for their configured retention window unless project risk requires selected evidence to be preserved longer.
