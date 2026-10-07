# BKE Engineering GitHub App Control Plane

This Cloudflare Worker is the trust bridge between enrolled BKE product repositories and the private Autonomous Engineering source.

## Responsibilities

- receive GitHub App `pull_request` webhooks;
- accept only trusted same-repository PR heads owned under `jan2xo`;
- verify the exact head contains a valid `.bke/autonomous.json` pinned to the private Autonomous Engineering repository by full SHA;
- dispatch the trusted `consumer-certify.yml` workflow on Autonomous Engineering `main`;
- accept GitHub Actions OIDC only from that exact trusted workflow/ref;
- mint short-lived repository-scoped installation tokens by purpose:
  - `resolve`: contents read on the consumer repository;
  - `report`: checks/issues/pull-request write on the consumer repository;
  - `dispatch`: actions write only on the central Autonomous Engineering repository.

The App private key never enters product repositories or GitHub Actions secrets.

## Required GitHub App permissions

Repository permissions:

- Contents: read
- Issues: read/write
- Pull requests: read/write
- Checks: read/write
- Actions: read/write

Subscribe to `pull_request` events.

Install the App only on repositories authorized for BKE engineering automation, including the private central Autonomous Engineering repository.

## Cloudflare secrets

Preproduction/production bindings are human-authorized operations:

- `BKE_ENGINEERING_GITHUB_APP_ID`
- `BKE_ENGINEERING_GITHUB_APP_PRIVATE_KEY_PEM`
- `BKE_ENGINEERING_GITHUB_WEBHOOK_SECRET`

No secret value belongs in source, CI logs, PR comments, or prompts.

## Trust boundary

Product PR code can never call the token broker successfully: OIDC is accepted only from:

`jan2xo/bke-autonomous-engineering/.github/workflows/consumer-certify.yml@refs/heads/main`

The webhook path itself never returns an installation token. It validates enrollment and dispatches certification only.
