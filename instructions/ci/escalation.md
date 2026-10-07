# Evidence Escalation

Treat the latest exact-head Intent CI capsule as the first failure interface.

If the capsule is sufficient, act without opening full logs. If it is insufficient, inspect the failing job or smallest useful log slice. Expand to broader logs/artifacts only when the narrower evidence cannot support the next engineering decision.

Do not consume stale historical failures by default. Historical runs are evidence for forensics, not the active working set after a new head exists.
