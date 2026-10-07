# BKE Engineering Control Plane

The control plane joins GitHub App authority, private Autonomous Engineering instructions, and exact-head CI evidence across all enrolled BKE engineering repositories.

## Runtime flow

```text
GitHub pull_request webhook
        ↓
Cloudflare GitHub App broker
        ├─ verifies webhook signature
        ├─ rejects forks/untrusted authors
        ├─ checks exact consumer manifest/source pin
        └─ dispatches central trusted workflow
                    ↓
           Trusted resolve job
                    ↓
            sanitized handoff
                    ↓
        Unprivileged execute job
                    ↓
              result artifact
                    ↓
           Trusted report job
                    ↓
       GitHub App PR capsule + Check Run
```

The execute job has no `id-token: write`, no broker URL, no App token, and no private Autonomous Engineering checkout.

## Deployment status

Source and contract tests may be developed/certified before deployment. Enabling the live bridge requires human authorization because it changes GitHub App installation/permissions and stores the App private key + webhook secret in Cloudflare.

Do not weaken those gates for convenience.
