# Intentional CI

CI executes the minimum complete verification graph required by the declared engineering intent. Intent check IDs resolve through the versioned check registry; the workflow must execute that resolved graph rather than a separately hard-coded interpretation.

A failing check must not prevent independent checks or final reporting from running. Dependent work whose prerequisites failed should stop or skip rather than manufacture meaningless evidence. The final workflow result must remain failed when a required check fails.

Expensive CI is a convergence/certification gate, not the default editing feedback loop.
