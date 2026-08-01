import { isAbsolute, relative, resolve, sep, win32 } from "node:path";

function text(value, label) {
  if (typeof value !== "string" || !value || value.includes("\0")) {
    throw new Error(`${label} must be a non-empty path string`);
  }
  return value;
}

export function resolveWithin(root, value, label = "path") {
  const raw = text(value, label);
  if (raw.includes("\\")) throw new Error(`${label} must use forward slashes: ${JSON.stringify(raw)}`);
  if (isAbsolute(raw) || win32.isAbsolute(raw)) throw new Error(`${label} must be relative: ${JSON.stringify(raw)}`);
  if (raw.split("/").some((part) => !part || part === "." || part === "..")) {
    throw new Error(`${label} contains an unsafe path segment: ${JSON.stringify(raw)}`);
  }
  const base = resolve(root);
  const candidate = resolve(base, raw);
  const rel = relative(base, candidate);
  if (rel === ".." || rel.startsWith(`..${sep}`) || isAbsolute(rel)) {
    throw new Error(`${label} escapes ${base}: ${JSON.stringify(raw)}`);
  }
  return candidate;
}

export function resolveCatalogPath(repository, value, declaredRoot, label = "catalog path") {
  const candidate = resolveWithin(repository, value, label);
  const base = resolve(declaredRoot);
  const rel = relative(base, candidate);
  if (rel === ".." || rel.startsWith(`..${sep}`) || isAbsolute(rel)) {
    throw new Error(`${label} escapes ${base}: ${JSON.stringify(value)}`);
  }
  return candidate;
}
