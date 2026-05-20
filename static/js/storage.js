/**
 * Browser-only script snapshots (localStorage), scoped per account.
 * Logged-in users: key includes user id. After logout: "guest" scope (separate list).
 * Server-side workspace scripts were already isolated by user_id.
 */

const LEGACY_V1 = "interactive-repl:scripts:v1";
const LEGACY_V2 = "interactive-repl:scripts:v2";

function scopeId() {
  if (typeof document === "undefined") return "guest";
  const raw = document.body?.dataset?.userId;
  const id = raw != null && String(raw).trim() !== "" ? String(raw).trim() : "";
  return id ? "u" + id : "guest";
}

function storageKey() {
  return "interactive-repl:scripts:v3:" + scopeId();
}

function readAll() {
  const key = storageKey();
  try {
    let raw = localStorage.getItem(key);
    if (!raw && key.endsWith(":guest")) {
      raw = localStorage.getItem(LEGACY_V2);
      if (raw) {
        localStorage.setItem(key, raw);
      }
    }
    if (!raw && key.endsWith(":guest")) {
      raw = localStorage.getItem(LEGACY_V1);
      if (raw) {
        localStorage.setItem(key, raw);
      }
    }
    if (!raw) return [];
    const data = JSON.parse(raw);
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

function writeAll(items) {
  const key = storageKey();
  try {
    localStorage.setItem(key, JSON.stringify(items));
  } catch (e) {
    const msg =
      e && (e.name === "QuotaExceededError" || e.code === 22)
        ? "Browser storage is full."
        : "Cannot write to localStorage: " + (e && e.message);
    throw new Error(msg);
  }
}

function newScriptId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return "s-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 11);
}

export function listLocalScripts() {
  return readAll();
}

export function saveLocalScript(title, code, language = "python") {
  const items = readAll();
  const id = newScriptId();
  const name = (title || "").trim() || "Untitled";
  items.unshift({
    id,
    title: name,
    code,
    language: language || "python",
    savedAt: new Date().toISOString(),
  });
  writeAll(items);
  return id;
}

export function getLocalScript(id) {
  return readAll().find((s) => s.id === id) || null;
}

export function deleteLocalScript(id) {
  writeAll(readAll().filter((s) => s.id !== id));
}
