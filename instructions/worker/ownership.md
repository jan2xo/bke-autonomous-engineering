# Worker Ownership

A worker executes only explicitly delegated work. It must fail closed on ambiguous, conflicting, or duplicate ownership.

Concurrent workers may progress independent pull requests when repository policy permits it. A worker must not silently race another worker on the same active assignment or invent unqueued work.
