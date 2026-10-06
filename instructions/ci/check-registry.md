# Certification Check Registry

Intents declare stable certification check IDs, not workflow-specific implementation details. Resolve those IDs through the versioned check registry into an effective dependency graph before execution.

Unknown required checks fail closed. CI executors must execute the resolved graph rather than hard-code domain check names. The plan digest must bind the effective check definitions and dependencies so a change in execution meaning invalidates stale proof.

Keep the executor generic: new unit, build, security, platform, packaging, recovery, or release checks should be addable through registry definitions without redesigning the intent contract.
