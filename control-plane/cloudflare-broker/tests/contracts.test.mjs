import assert from "node:assert/strict";
import test from "node:test";

import {
  ACTIONS_OIDC_ISSUER,
  BROKER_AUDIENCE,
  CERTIFICATION_WORKFLOW_NAME,
  CERTIFICATION_WORKFLOW_REF,
  CONTROL_REPOSITORY,
  CONTROL_REPOSITORY_ID,
  permissionsForPurpose,
  validateActionsClaims,
  validateTargetRepository,
} from "../src/github-app.js";
import {
  routePullRequest,
  validateConsumerManifest,
} from "../src/protocol.js";

function validClaims(now = 2_000_000_000) {
  return {
    iss: ACTIONS_OIDC_ISSUER,
    aud: BROKER_AUDIENCE,
    repository: CONTROL_REPOSITORY,
    repository_id: CONTROL_REPOSITORY_ID,
    workflow_ref: CERTIFICATION_WORKFLOW_REF,
    workflow: CERTIFICATION_WORKFLOW_NAME,
    ref: "refs/heads/main",
    event_name: "workflow_dispatch",
    iat: now - 30,
    nbf: now - 30,
    exp: now + 300,
  };
}

test("OIDC claims accept only the trusted central main workflow", () => {
  const now = 2_000_000_000;
  assert.equal(validateActionsClaims(validClaims(now), now), true);

  const wrongRef = { ...validClaims(now), ref: "refs/pull/99/merge" };
  assert.throws(
    () => validateActionsClaims(wrongRef, now),
    /OIDC_REF_INVALID/,
  );

  const wrongWorkflow = {
    ...validClaims(now),
    workflow_ref:
      "jan2xo/bke-worker/.github/workflows/pr-guard.yml@refs/heads/main",
  };
  assert.throws(
    () => validateActionsClaims(wrongWorkflow, now),
    /OIDC_WORKFLOW_REF_INVALID/,
  );
});

test("token purposes are least privilege and dispatch is central-only", () => {
  assert.deepEqual(
    permissionsForPurpose("resolve", "jan2xo/bke-worker"),
    { contents: "read" },
  );
  assert.deepEqual(
    permissionsForPurpose("report", "jan2xo/bke-worker"),
    {
      checks: "write",
      issues: "write",
      pull_requests: "write",
    },
  );
  assert.deepEqual(
    permissionsForPurpose("dispatch", CONTROL_REPOSITORY),
    { actions: "write" },
  );
  assert.throws(
    () => permissionsForPurpose("dispatch", "jan2xo/bke-worker"),
    /DISPATCH_TARGET_INVALID/,
  );
});

test("target repositories are constrained to the BKE owner boundary", () => {
  assert.deepEqual(
    validateTargetRepository("jan2xo/bke-worker"),
    { fullName: "jan2xo/bke-worker", name: "bke-worker" },
  );
  assert.throws(
    () => validateTargetRepository("someone-else/bke-worker"),
    /TARGET_REPOSITORY_INVALID/,
  );
});

test("pull request routing accepts trusted same-repository heads", () => {
  const routed = routePullRequest(
    {
      action: "synchronize",
      repository: {
        full_name: "jan2xo/bke-worker",
        owner: { login: "jan2xo" },
      },
      pull_request: {
        number: 66,
        head: {
          sha: "a".repeat(40),
          repo: { full_name: "jan2xo/bke-worker" },
        },
        base: {
          repo: { full_name: "jan2xo/bke-worker" },
        },
        author_association: "OWNER",
      },
      sender: { login: "jan2xo" },
    },
    "delivery-1",
  );
  assert.equal(routed.kind, "certify");
  assert.equal(routed.request.repository, "jan2xo/bke-worker");
  assert.equal(routed.request.head, "a".repeat(40));
  assert.equal(routed.request.pull_request, 66);
});

test("pull request routing rejects forks and untrusted authors", () => {
  const basePayload = {
    action: "opened",
    repository: {
      full_name: "jan2xo/bke-worker",
      owner: { login: "jan2xo" },
    },
    pull_request: {
      number: 66,
      head: {
        sha: "a".repeat(40),
        repo: { full_name: "jan2xo/bke-worker" },
      },
      base: {
        repo: { full_name: "jan2xo/bke-worker" },
      },
      author_association: "OWNER",
    },
    sender: { login: "jan2xo" },
  };

  const fork = structuredClone(basePayload);
  fork.pull_request.head.repo.full_name = "contributor/fork";
  assert.equal(routePullRequest(fork, "d").kind, "error");

  const outsider = structuredClone(basePayload);
  outsider.pull_request.author_association = "NONE";
  const routed = routePullRequest(outsider, "d");
  assert.equal(routed.kind, "error");
  assert.equal(routed.error, "UNTRUSTED_PULL_REQUEST_AUTHOR");
});

test("consumer manifest requires immutable private source and safe relative paths", () => {
  const manifest = {
    version: 1,
    instruction_source: {
      repo: "jan2xo/bke-autonomous-engineering",
      ref: "b".repeat(40),
    },
    intent_path: ".bke/intent.json",
    instruction_catalog_path: ".bke/instructions/catalog.json",
    check_registry_path: ".bke/checks/registry.json",
  };
  assert.equal(validateConsumerManifest(manifest), manifest);

  const moving = structuredClone(manifest);
  moving.instruction_source.ref = "main";
  assert.throws(
    () => validateConsumerManifest(moving),
    /CONSUMER_SOURCE_PIN_INVALID/,
  );

  const escape = structuredClone(manifest);
  escape.intent_path = "../private.json";
  assert.throws(
    () => validateConsumerManifest(escape),
    /CONSUMER_MANIFEST_PATH_INVALID/,
  );
});
