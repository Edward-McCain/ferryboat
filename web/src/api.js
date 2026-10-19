const headers = { "Content-Type": "application/json" };

async function send(path, options) {
  const response = await fetch(path, options);
  if (response.status === 204) {
    return null;
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(body?.error?.message ?? "Лист не ответил.");
  }
  return body;
}

export function listCrossings() {
  return send("/api/crossings");
}

export function createCrossing(payload) {
  return send("/api/crossings", {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
}

export function updateCrossing(id, payload) {
  return send(`/api/crossings/${id}`, {
    method: "PATCH",
    headers,
    body: JSON.stringify(payload),
  });
}

export function setStatus(id, status) {
  return send(`/api/crossings/${id}/status`, {
    method: "POST",
    headers,
    body: JSON.stringify({ status }),
  });
}

export function removeCrossing(id) {
  return send(`/api/crossings/${id}`, { method: "DELETE" });
}
