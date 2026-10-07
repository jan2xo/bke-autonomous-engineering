# GitHub App Trust Bridge

Use the BKE GitHub App/control plane as the authority bridge between product repositories and private Autonomous Engineering instructions.

Do not require public product repositories to directly download a private action or instruction repository. Do not grant pull-request-controlled code an installation token that can read the private instruction source.

Keep privileged resolution, unprivileged repo-check execution, and privileged reporting in separate trust domains. The resolver may read consumer files as data but must never execute consumer-supplied commands. The executor receives no private source credential and may execute only the sanitized `repo.*` plan for the exact consumer head. The reporter executes no consumer code.

GitHub App tokens must be short-lived, least-privilege, and repository-scoped. Human authentication, production authorization, signing material, and other locked actions remain human-controlled unless separately and explicitly authorized.
