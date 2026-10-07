# Consumer Contract

BKE repositories consume Autonomous Engineering through an immutable full commit SHA. Never bind engineering behavior to a moving branch.

A consumer owns its repository-specific intent, `repo.*` instruction modules, and `repo.*` check adapters. Shared instruction/check IDs remain owned by BKE Autonomous Engineering and cannot be overridden by a consumer.

The effective instruction digest binds shared plus repository-specific instruction content. The effective plan digest binds shared plus repository-specific executable definitions, dependencies, execution roots, and semantics.

Consumer certification is exact-head evidence for the product repository and exact-source evidence for the pinned Autonomous Engineering revision.
