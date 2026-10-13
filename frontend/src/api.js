// One small wrapper around fetch: adds the JWT, parses JSON, turns errors into readable messages.
const BASE = import.meta.env.VITE_API_URL || "";

export function getToken() {
  return localStorage.getItem("token");
}
export function setToken(token) {
  token ? localStorage.setItem("token", token) : localStorage.removeItem("token");
}

export async function api(path, { method = "GET", body, form } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body) headers["Content-Type"] = "application/json";

  const res = await fetch(BASE + path, {
    method,
    headers,
    body: form ? form : body ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401 && token) {
    setToken(null);
    window.location.href = "/login"; // token expired -> back to login
    return;
  }
  if (res.status === 204) return null;

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    let msg = data?.detail ?? `Request failed (${res.status})`;
    if (Array.isArray(msg)) msg = msg.map((d) => d.msg).join(", "); // FastAPI validation errors
    throw new Error(msg);
  }
  return data;
}

export const STATUSES = [
  { key: "saved", label: "Saved" },
  { key: "applied", label: "Applied" },
  { key: "interview", label: "Interview" },
  { key: "offer", label: "Offer" },
  { key: "rejected", label: "Rejected" },
];
