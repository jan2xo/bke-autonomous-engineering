# Consumer Contract

BKE repositories consume Autonomous Engineering through an immutable commit SHA. Never bind engineering behavior to a moving branch.

A consumer owns only its repository-specific intent, `repo.*` instruction modules, and `repo.*` check adapters. Shared instruction IDs and shared check IDs remain owned by BKE Autonomous Engineering and cannot be overridden by a consumer.

The effective instruction digest binds both shared and repository-specific instruction content. The effective plan digest binds shared and repository-specific executable check definitions, dependency relationships, execution roots, and semantics.

Consumer certification is exact-head evidence for the consumer repository and exact-source evidence for the pinned Autonomous Engineering revision.
