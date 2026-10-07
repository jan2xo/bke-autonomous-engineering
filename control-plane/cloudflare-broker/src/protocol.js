const TRUSTED_ASSOCIATIONS = new Set(["OWNER", "MEMBER", "COLLABORATOR"]);
const ALLOWED_PULL_REQUEST_ACTIONS = new Set([
  "opened",
  "synchronize",
  "reopened",
  "ready_for_review",
]);
const SOURCE_REPOSITORY = "jan2xo/bke-autonomous-engineering";
const SHA_RE = /^[0-9a-f]{40}$/u;

function safeRelativePath(value) {
  if (typeof value !== "string" || !value || value.startsWith("/")) return false;
  const parts = value.split("/");
  return !parts.some((part) => part === "" || part === "." || part === "..");
}

async function verifyGitHubSignature(bodyBytes, signatureHeader, secret) {
  if (typeof secret !== "string" || !secret) return false;
  const match = /^sha256=([0-9a-f]{64})$/iu.exec(signatureHeader || "");
  if (!match) return false;
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["verify"],
  );
  const expected = Uint8Array.from(match[1].match(/../gu), (hex) =>
    Number.parseInt(hex, 16)
  );
  return crypto.subtle.verify("HMAC", key, expected, bodyBytes);
}

function routePullRequest(payload, deliveryId) {
  if (!payload || typeof payload !== "object") {
    return { kind: "error", status: 400, error: "GITHUB_PAYLOAD_INVALID" };
  }
  if (!ALLOWED_PULL_REQUEST_ACTIONS.has(String(payload.action || ""))) {
    return { kind: "ignore", reason: "IGNORED_ACTION" };
  }

  const repository = String(payload.repository?.full_name || "");
  const owner = String(payload.repository?.owner?.login || "");
  const pr = payload.pull_request;
  const number = Number(pr?.number);
  const head = String(pr?.head?.sha || "");
  const headRepository = String(pr?.head?.repo?.full_name || "");
  const baseRepository = String(pr?.base?.repo?.full_name || "");
  const association = String(pr?.user?.type === "Bot"
    ? payload.sender?.type || ""
    : payload.pull_request?.author_association || payload.sender?.author_association || "");

  if (owner.toLowerCase() !== "jan2xo" || !repository.startsWith("jan2xo/")) {
    return { kind: "ignore", reason: "UNENROLLED_OWNER" };
  }
  if (
    !Number.isInteger(number) ||
    number < 1 ||
    !SHA_RE.test(head) ||
    headRepository !== repository ||
    baseRepository !== repository
  ) {
    return {
      kind: "error",
      status: 403,
      error: "UNTRUSTED_PULL_REQUEST_BOUNDARY",
    };
  }

  const trustedAssociation = String(
    payload.pull_request?.author_association ||
    payload.sender?.author_association ||
    "",
  );
  if (!TRUSTED_ASSOCIATIONS.has(trustedAssociation)) {
    return {
      kind: "error",
      status: 403,
      error: "UNTRUSTED_PULL_REQUEST_AUTHOR",
    };
  }

  return {
    kind: "certify",
    request: {
      version: 1,
      repository,
      head,
      pull_request: number,
      manifest_path: ".bke/autonomous.json",
      delivery_id: String(deliveryId || ""),
    },
  };
}

function validateConsumerManifest(manifest) {
  if (!manifest || typeof manifest !== "object") {
    throw new Error("CONSUMER_MANIFEST_INVALID");
  }
  if (manifest.version !== 1) {
    throw new Error("CONSUMER_MANIFEST_VERSION_INVALID");
  }
  const source = manifest.instruction_source;
  if (
    !source ||
    source.repo !== SOURCE_REPOSITORY ||
    !SHA_RE.test(String(source.ref || ""))
  ) {
    throw new Error("CONSUMER_SOURCE_PIN_INVALID");
  }
  for (const key of [
    "intent_path",
    "instruction_catalog_path",
    "check_registry_path",
  ]) {
    if (!safeRelativePath(manifest[key])) {
      throw new Error(`CONSUMER_MANIFEST_PATH_INVALID:${key}`);
    }
  }
  return manifest;
}

export {
  ALLOWED_PULL_REQUEST_ACTIONS,
  SOURCE_REPOSITORY,
  TRUSTED_ASSOCIATIONS,
  routePullRequest,
  safeRelativePath,
  validateConsumerManifest,
  verifyGitHubSignature,
};
