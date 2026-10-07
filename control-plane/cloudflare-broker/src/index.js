import {
  CONTROL_REPOSITORY,
  mintRepositoryToken,
  verifyActionsOidcToken,
} from "./github-app.js";
import {
  routePullRequest,
  validateConsumerManifest,
  verifyGitHubSignature,
} from "./protocol.js";

const GITHUB_API_VERSION = "2026-03-10";
const MAX_WEBHOOK_BYTES = 1024 * 1024;

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

function githubHeaders(token) {
  return {
    accept: "application/vnd.github+json",
    authorization: `Bearer ${token}`,
    "user-agent": "bke-engineering-control-plane",
    "x-github-api-version": GITHUB_API_VERSION,
  };
}

function decodeBase64Utf8(value) {
  const normalized = String(value || "").replace(/\s+/gu, "");
  const binary = atob(normalized);
  const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

async function fetchConsumerManifest(env, request, fetchImpl = fetch) {
  const access = await mintRepositoryToken(
    env,
    request.repository,
    "resolve",
    fetchImpl,
  );
  const encodedPath = request.manifest_path
    .split("/")
    .map(encodeURIComponent)
    .join("/");
  const response = await fetchImpl(
    `https://api.github.com/repos/${request.repository}/contents/${encodedPath}?ref=${request.head}`,
    { headers: githubHeaders(access.token) },
  );
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(`CONSUMER_MANIFEST_FETCH_FAILED:${response.status}`);
  }
  if (
    !payload ||
    payload.type !== "file" ||
    payload.encoding !== "base64" ||
    typeof payload.content !== "string"
  ) {
    throw new Error("CONSUMER_MANIFEST_RESPONSE_INVALID");
  }
  let manifest;
  try {
    manifest = JSON.parse(decodeBase64Utf8(payload.content));
  } catch {
    throw new Error("CONSUMER_MANIFEST_JSON_INVALID");
  }
  return validateConsumerManifest(manifest);
}

async function dispatchCertification(env, request, fetchImpl = fetch) {
  const access = await mintRepositoryToken(
    env,
    CONTROL_REPOSITORY,
    "dispatch",
    fetchImpl,
  );
  const response = await fetchImpl(
    `https://api.github.com/repos/${CONTROL_REPOSITORY}/actions/workflows/consumer-certify.yml/dispatches`,
    {
      method: "POST",
      headers: {
        ...githubHeaders(access.token),
        "content-type": "application/json",
      },
      body: JSON.stringify({
        ref: "main",
        inputs: {
          repository: request.repository,
          head: request.head,
          pull_request: String(request.pull_request),
          manifest_path: request.manifest_path,
        },
      }),
    },
  );
  if (response.status !== 204) {
    throw new Error(`CERTIFICATION_DISPATCH_FAILED:${response.status}`);
  }
}

async function handleGitHubWebhook(request, env, fetchImpl = fetch) {
  const secret = String(env.BKE_ENGINEERING_GITHUB_WEBHOOK_SECRET || "");
  if (!secret) return json({ error: "WEBHOOK_SECRET_UNCONFIGURED" }, 503);

  const contentLength = Number(request.headers.get("Content-Length") || "0");
  if (Number.isFinite(contentLength) && contentLength > MAX_WEBHOOK_BYTES) {
    return json({ error: "GITHUB_PAYLOAD_TOO_LARGE" }, 413);
  }
  const body = new Uint8Array(await request.arrayBuffer());
  if (body.byteLength > MAX_WEBHOOK_BYTES) {
    return json({ error: "GITHUB_PAYLOAD_TOO_LARGE" }, 413);
  }
  const signature = request.headers.get("X-Hub-Signature-256") || "";
  if (!(await verifyGitHubSignature(body, signature, secret))) {
    return json({ error: "GITHUB_SIGNATURE_INVALID" }, 401);
  }

  const eventName = request.headers.get("X-GitHub-Event") || "";
  if (eventName === "ping") {
    return json({ accepted: true, reason: "PING" });
  }
  if (eventName !== "pull_request") {
    return json({ accepted: false, reason: "IGNORED_EVENT" }, 202);
  }

  let payload;
  try {
    payload = JSON.parse(new TextDecoder().decode(body));
  } catch {
    return json({ error: "GITHUB_PAYLOAD_INVALID" }, 400);
  }

  const routing = routePullRequest(
    payload,
    request.headers.get("X-GitHub-Delivery") || "",
  );
  if (routing.kind === "ignore") {
    return json({ accepted: false, reason: routing.reason }, 202);
  }
  if (routing.kind === "error") {
    return json({ error: routing.error }, routing.status);
  }

  try {
    const manifest = await fetchConsumerManifest(
      env,
      routing.request,
      fetchImpl,
    );
    await dispatchCertification(env, routing.request, fetchImpl);
    return json(
      {
        accepted: true,
        repository: routing.request.repository,
        pull_request: routing.request.pull_request,
        head: routing.request.head,
        instruction_source: manifest.instruction_source.ref,
      },
      202,
    );
  } catch (error) {
    const code = error instanceof Error
      ? error.message
      : "CERTIFICATION_REQUEST_FAILED";
    const status =
      code.endsWith("_UNCONFIGURED") ? 503 :
      code.startsWith("CONSUMER_") ? 422 :
      502;
    return json({ error: code }, status);
  }
}

async function handleRepositoryToken(request, env, fetchImpl = fetch) {
  const authorization = request.headers.get("Authorization") || "";
  const match = /^Bearer\s+(.+)$/iu.exec(authorization);
  if (!match) return json({ error: "ACTIONS_OIDC_REQUIRED" }, 401);

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "TOKEN_REQUEST_INVALID" }, 400);
  }

  try {
    await verifyActionsOidcToken(match[1], fetchImpl);
    const minted = await mintRepositoryToken(
      env,
      body?.repository,
      body?.purpose,
      fetchImpl,
    );
    return json(minted, 200);
  } catch (error) {
    const code = error instanceof Error
      ? error.message
      : "GITHUB_APP_BROKER_FAILED";
    const status =
      code.startsWith("OIDC_") ? 401 :
      code.endsWith("_INVALID") ? 400 :
      code.endsWith("_UNCONFIGURED") ? 503 :
      502;
    return json({ error: code }, status);
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/webhooks/github") {
      if (request.method !== "POST") {
        return json({ error: "METHOD_NOT_ALLOWED" }, 405);
      }
      return handleGitHubWebhook(request, env);
    }
    if (url.pathname === "/github/app/repository-token") {
      if (request.method !== "POST") {
        return json({ error: "METHOD_NOT_ALLOWED" }, 405);
      }
      return handleRepositoryToken(request, env);
    }
    return json({ error: "NOT_FOUND" }, 404);
  },
};

export {
  dispatchCertification,
  fetchConsumerManifest,
  handleGitHubWebhook,
  handleRepositoryToken,
};
