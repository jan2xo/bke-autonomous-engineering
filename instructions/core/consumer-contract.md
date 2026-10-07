# Consumer Contract

BKE repositories declare Autonomous Engineering through an immutable commit SHA. Never bind engineering behavior to a moving branch.

A consumer owns only its repository-specific intent, `repo.*` instruction modules, and `repo.*` executable check adapters. Shared instruction IDs remain owned by BKE Autonomous Engineering and cannot be overridden by a consumer.

The effective instruction digest binds both shared and repository-specific instruction content. The effective plan digest binds repository-specific executable check definitions, dependencies, and execution semantics. The execution key additionally binds the exact consumer head, immutable private source revision, and manifest digest.

The private Autonomous Engineering source is resolved by the trusted GitHub App/control-plane side. Consumer commands execute only from a sanitized plan in a separate unprivileged environment with no private-source credential or checkout.

Consumer certification is exact-head evidence for the product repository and exact-source evidence for the pinned Autonomous Engineering revision.
