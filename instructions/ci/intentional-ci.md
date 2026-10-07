# Intentional CI

CI executes the minimum complete verification graph required by the declared engineering intent. Intent check IDs resolve through the versioned check registry; the workflow must execute that resolved graph rather than a separately hard-coded interpretation.

Check continuation and dependency behavior follow the resolved, execution-bound failure policy that is part of the effective certification plan.

- When independent continuation is enabled, a failing check must not prevent otherwise independent checks from running.
- When independent continuation is disabled, later checks may stop or skip according to the bound policy.
- When dependent-stop behavior is enabled, work whose prerequisite failed must stop or skip rather than manufacture meaningless evidence.
- When dependent-stop behavior is disabled, the executor may continue that dependent work only according to the same bound policy.

The workflow must still reach final reporting for the resolved execution result. A required non-PASS result must never be translated into overall PASS.

Expensive CI is a convergence/certification gate, not the default editing feedback loop.
