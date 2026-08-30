#!/usr/bin/env node

import { createHash } from "node:crypto";
import {
  existsSync,
  lstatSync,
  readFileSync,
  readdirSync,
  statSync,
} from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const WEB_ROOT = path.resolve(SCRIPT_DIR, "..");
const DIST_ROOT = path.resolve(
  process.argv[2] ? process.cwd() : WEB_ROOT,
  process.argv[2] ?? "dist",
);

// Cloudflare Workers Static Assets reject an individual file above 25 MiB.
const MAX_FILE_BYTES = 25 * 1024 * 1024;

const CANONICAL_DEFAULT_SLOTS = Object.freeze([
  "rain-heavy-open-window",
  "rain-balcony-peaceful",
  "rain-tent-heavy",
  "fire-crackling-loop",
  "crickets-at-night-clean",
  "rain-city-pooling",
  "campfire-loop-stereo",
  "flowing-water",
]);

const REQUIRED_FILES = Object.freeze([
  "index.html",
  "404.html",
  "app.js",
  "preload.js",
  "web-build.js",
  "nocturne-polish.css",
  "_headers",
  "robots.txt",
  "sitemap.xml",
  "manifest.webmanifest",
  "nocturne_build.json",
  "LICENSE",
  "NOTICE.txt",
  "AUDIO_CREDITS.md",
  "AUDIO_PROVENANCE.md",
  "MEDIA_LICENSES.md",
  "rain.mp4",
  "rain-still.webp",
  "fonts/fraunces-italic-latin.woff2",
  "fonts/fraunces-latin.woff2",
  "fonts/jetbrains-mono-latin.woff2",
  "fonts/manrope-latin.woff2",
  "fonts/licenses/Fraunces-OFL.txt",
  "fonts/licenses/JetBrains-Mono-OFL.txt",
  "fonts/licenses/Manrope-OFL.txt",
  "icons/apple-touch-icon.png",
  "icons/favicon.png",
  "icons/nocturne-192.png",
  "icons/nocturne-512.png",
  "icons/nocturne-maskable-512.png",
  "sounds/sound_library.json",
]);

const failures = [];
let assertions = 0;

function check(condition, message) {
  assertions += 1;
  if (!condition) failures.push(message);
  return Boolean(condition);
}

function relative(filePath) {
  return path.relative(DIST_ROOT, filePath).split(path.sep).join("/");
}

function requiredFile(relativePath, { allowEmpty = false } = {}) {
  const absolutePath = path.join(DIST_ROOT, relativePath);
  if (!check(existsSync(absolutePath), `missing required file: ${relativePath}`)) {
    return null;
  }
  const details = lstatSync(absolutePath);
  if (!check(details.isFile(), `required path is not a regular file: ${relativePath}`)) {
    return null;
  }
  check(allowEmpty || details.size > 0, `required file is empty: ${relativePath}`);
  return absolutePath;
}

function readText(relativePath) {
  const filePath = requiredFile(relativePath);
  return filePath ? readFileSync(filePath, "utf8") : "";
}

function readJson(relativePath) {
  const source = readText(relativePath);
  if (!source) return null;
  try {
    return JSON.parse(source);
  } catch (error) {
    failures.push(`invalid JSON in ${relativePath}: ${error.message}`);
    return null;
  }
}

function walk(directory) {
  const files = [];
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const absolutePath = path.join(directory, entry.name);
    if (entry.isSymbolicLink()) {
      failures.push(`symbolic links are not permitted in dist: ${relative(absolutePath)}`);
    } else if (entry.isDirectory()) {
      files.push(...walk(absolutePath));
    } else if (entry.isFile()) {
      files.push(absolutePath);
    } else {
      failures.push(`unsupported filesystem entry in dist: ${relative(absolutePath)}`);
    }
  }
  return files;
}

function extractAttribute(attributes, name) {
  const match = attributes.match(
    new RegExp(`\\b${name}\\s*=\\s*(?:"([^"]*)"|'([^']*)'|([^\\s>]+))`, "i"),
  );
  return match ? (match[1] ?? match[2] ?? match[3] ?? "") : null;
}

function localAssetPath(reference, htmlRelativePath) {
  const withoutQuery = reference.split(/[?#]/, 1)[0];
  let decoded;
  try {
    decoded = decodeURIComponent(withoutQuery);
  } catch {
    return null;
  }
  if (!decoded || /^(?:[a-z][a-z\d+.-]*:|\/\/)/i.test(decoded)) return null;

  const base = decoded.startsWith("/")
    ? DIST_ROOT
    : path.join(DIST_ROOT, path.dirname(htmlRelativePath));
  const resolved = path.resolve(base, decoded.replace(/^\/+/, ""));
  const insideDist = resolved === DIST_ROOT || resolved.startsWith(`${DIST_ROOT}${path.sep}`);
  return insideDist ? resolved : null;
}

function verifyExternalScripts(html, htmlRelativePath, { requireScript = false } = {}) {
  check(
    !/\son[a-z][a-z\d_-]*\s*=/i.test(html),
    `${htmlRelativePath} contains an inline event-handler attribute`,
  );
  check(
    !/javascript\s*:/i.test(html),
    `${htmlRelativePath} contains a javascript: URL`,
  );

  const scriptPattern = /<script\b([^>]*)>([\s\S]*?)<\/script\s*>/gi;
  const scripts = [...html.matchAll(scriptPattern)];
  if (requireScript) {
    check(scripts.length > 0, `${htmlRelativePath} has no external application script`);
  }

  for (const [index, script] of scripts.entries()) {
    const attributes = script[1] ?? "";
    const body = script[2] ?? "";
    const src = extractAttribute(attributes, "src");
    check(src !== null && src !== "", `${htmlRelativePath} script ${index + 1} is inline`);
    check(body.trim() === "", `${htmlRelativePath} script ${index + 1} has inline JavaScript`);
    if (!src) continue;

    const assetPath = localAssetPath(src, htmlRelativePath);
    if (!check(assetPath !== null, `${htmlRelativePath} script ${index + 1} is not a local asset: ${src}`)) {
      continue;
    }
    check(
      existsSync(assetPath) && statSync(assetPath).isFile(),
      `${htmlRelativePath} references missing script asset: ${src}`,
    );
  }
}

function sha256(filePath) {
  return createHash("sha256").update(readFileSync(filePath)).digest("hex");
}

function verifyCatalog(catalog) {
  if (!catalog) return;
  const sounds = catalog.sounds;
  if (!check(Array.isArray(sounds), "sound_library.json sounds must be an array")) return;

  check(sounds.length === 11, `web catalog must contain exactly 11 sounds, found ${sounds.length}`);
  check(
    Array.isArray(catalog.default_slots),
    "sound_library.json default_slots must be an array",
  );
  if (Array.isArray(catalog.default_slots)) {
    check(
      JSON.stringify(catalog.default_slots) === JSON.stringify(CANONICAL_DEFAULT_SLOTS),
      `web catalog default_slots must be the canonical ordered eight: ${CANONICAL_DEFAULT_SLOTS.join(", ")}`,
    );
  }
  check(
    Array.isArray(catalog.excluded_sounds) && catalog.excluded_sounds.length === 0,
    "web catalog excluded_sounds must be an empty array",
  );

  const ids = new Set();
  const referencedAssets = new Set();
  for (const [index, sound] of sounds.entries()) {
    const label = sound && typeof sound.id === "string" ? sound.id : `entry ${index + 1}`;
    check(sound && typeof sound === "object", `catalog ${label} is not an object`);
    if (!sound || typeof sound !== "object") continue;

    check(typeof sound.id === "string" && sound.id.length > 0, `catalog ${label} has no id`);
    check(!ids.has(sound.id), `catalog contains duplicate id: ${sound.id}`);
    ids.add(sound.id);
    check(sound.source_type === "recorded_cc0", `${label} is not recorded_cc0`);
    check(sound.availability === "bundled", `${label} is not marked bundled`);
    check(sound.license === "CC0 1.0", `${label} is not labeled CC0 1.0`);
    for (const field of ["name", "creator", "source_url", "license_url", "sha256"]) {
      check(
        typeof sound[field] === "string" && sound[field].trim().length > 0,
        `${label} is missing provenance field ${field}`,
      );
    }

    const source = typeof sound.src === "string" ? sound.src : "";
    check(
      /^\/sounds\/library\/[a-z0-9][a-z0-9-]*\.mp3$/.test(source),
      `${label} has an invalid web asset path: ${source || "(missing)"}`,
    );
    if (!source) continue;
    const assetRelative = source.replace(/^\//, "");
    check(!referencedAssets.has(assetRelative), `catalog reuses asset path: ${source}`);
    referencedAssets.add(assetRelative);
    const assetPath = path.join(DIST_ROOT, assetRelative);
    if (!check(existsSync(assetPath), `${label} references a missing asset: ${source}`)) continue;
    if (!check(lstatSync(assetPath).isFile(), `${label} asset is not a regular file: ${source}`)) continue;

    if (typeof sound.file_size_bytes === "number") {
      check(
        statSync(assetPath).size === sound.file_size_bytes,
        `${label} file_size_bytes does not match ${source}`,
      );
    }
    if (typeof sound.sha256 === "string" && /^[a-f\d]{64}$/i.test(sound.sha256)) {
      check(
        sha256(assetPath) === sound.sha256.toLowerCase(),
        `${label} sha256 does not match ${source}`,
      );
    }
  }

  for (const id of CANONICAL_DEFAULT_SLOTS) {
    check(ids.has(id), `canonical default sound is absent from web catalog: ${id}`);
  }

  const libraryRoot = path.join(DIST_ROOT, "sounds", "library");
  if (!check(existsSync(libraryRoot), "missing sounds/library directory")) return;
  const libraryFiles = walk(libraryRoot).map(relative).sort();
  check(
    libraryFiles.length === 11,
    `sounds/library must contain exactly 11 files, found ${libraryFiles.length}`,
  );
  check(
    libraryFiles.every((file) => file.endsWith(".mp3")),
    "sounds/library contains a non-MP3 or generated audio artifact",
  );
  check(
    JSON.stringify(libraryFiles) === JSON.stringify([...referencedAssets].sort()),
    "sounds/library contents do not exactly match the web catalog",
  );
}

function verifyHeaders(headers) {
  check(/^\/\*\s*$/m.test(headers), "_headers has no catch-all /* rule");
  for (const header of [
    "Content-Security-Policy",
    "Permissions-Policy",
    "Referrer-Policy",
    "X-Content-Type-Options",
    "X-Frame-Options",
  ]) {
    check(new RegExp(`^\\s+${header}:`, "mi").test(headers), `_headers is missing ${header}`);
  }
  for (const route of ["/sounds/*", "/rain.mp4", "/rain-still.webp", "/fonts/*", "/icons/*", "/index.html"]) {
    check(headers.includes(route), `_headers is missing cache scope ${route}`);
  }

  const csp = headers.match(/^\s+Content-Security-Policy:\s*(.+)$/mi)?.[1] ?? "";
  check(csp.length > 0, "_headers has no parseable Content-Security-Policy value");
  const directives = csp.split(";").map((part) => part.trim());
  const scriptSrc = directives.find((directive) => /^script-src\b/i.test(directive)) ?? "";
  const mediaSrc = directives.find((directive) => /^media-src\b/i.test(directive)) ?? "";
  const connectSrc = directives.find((directive) => /^connect-src\b/i.test(directive)) ?? "";
  check(
    scriptSrc.toLowerCase() === "script-src 'self'",
    "CSP script-src must be exactly script-src 'self'",
  );
  check(/\bmedia-src\b/i.test(mediaSrc) && /'self'/i.test(mediaSrc) && /blob:/i.test(mediaSrc), "CSP media-src must allow self and local Radio blob URLs");
  check(connectSrc.includes("https://api.open-meteo.com"), "CSP connect-src must allow Open-Meteo weather");
  check(connectSrc.includes("https://geocoding-api.open-meteo.com"), "CSP connect-src must allow Open-Meteo place search");
}

function verifyHostedPage(indexHtml) {
  check(/<html\b[^>]*\bdata-deployment=["']web["']/i.test(indexHtml), "hosted HTML is not marked as the web deployment");
  check(/<body\b[^>]*\bdata-mode=["']onsen["']/i.test(indexHtml), "hosted HTML must paint Onsen as the initial room");
  check(indexHtml.includes('<link rel="canonical" href="https://nocturne.cmish.dev/">'), "hosted HTML is missing the canonical URL");
  check(indexHtml.includes('id="radio-file-privacy"'), "hosted HTML is missing persistent local-Radio privacy copy");
  check(indexHtml.includes('files stay in this tab and are never uploaded'), "hosted HTML does not state the local-Radio boundary");
  check(indexHtml.includes('class="mode-btn local-only" data-mode="utility"'), "Utility mode lacks a no-JavaScript web boundary");
  check(indexHtml.includes('class="mode-btn local-only" data-mode="dashboard"'), "Dashboard mode lacks a no-JavaScript web boundary");

  const scriptSources = [...indexHtml.matchAll(/<script\b([^>]*)>/gi)]
    .map((match) => extractAttribute(match[1] ?? "", "src"));
  check(
    JSON.stringify(scriptSources) === JSON.stringify(["/preload.js", "/web-build.js", "/app.js"]),
    `hosted script order changed: ${scriptSources.join(", ")}`,
  );

  const css = readText("nocturne-polish.css");
  check(/\.video-stage\.profile-static[\s\S]{0,300}rain-still\.webp/.test(css), "reduced-motion/static Onsen has no visible rain still");
  check(/@media\s*\(pointer:\s*coarse\)[\s\S]*min-block-size:\s*44px\s*!important/.test(css), "coarse pointers lack a final 44px target safeguard");

  const app = readText("app.js");
  for (const token of ["scenes:v1", "MediaSession", "radio:shuffle", "WEB_SETTINGS_KEY", "credentials: 'omit'", "referrerPolicy: 'no-referrer'"]) {
    check(app.includes(token), `hosted app is missing web-profile contract token: ${token}`);
  }
}

function verifyRadioBuild(allFiles) {
  const scripts = allFiles.filter((file) => /\.(?:m?js)$/i.test(file));
  if (!check(scripts.length > 0, "dist contains no JavaScript application asset")) return;
  const source = scripts.map((file) => readFileSync(file, "utf8")).join("\n");

  for (const token of [
    "defaultPlaybackRate",
    "playbackRate",
    "loadedmetadata",
    "preservesPitch",
    "mozPreservesPitch",
    "webkitPreservesPitch",
  ]) {
    check(source.includes(token), `built Radio code is missing ${token}`);
  }
  check(
    /return\s+1\s*-\s*(?:radioState\.)?drift\s*\*\s*0?\.25/.test(source) ||
      /return\s+1\s*-\s*0?\.25\s*\*\s*(?:radioState\.)?drift/.test(source) ||
      /return\s+1\s*-\s*(?:radioState\.)?drift\s*\*\s*0?\.0025/.test(source),
    "built Radio Drift must map its state to the 1.00x-0.75x range",
  );
  check(
    /loadedmetadata[\s\S]{0,500}(?:applyRadioPlaybackRate|defaultPlaybackRate|playbackRate)/.test(source) ||
      /(?:applyRadioPlaybackRate|defaultPlaybackRate|playbackRate)[\s\S]{0,500}loadedmetadata/.test(source),
    "built Radio code does not show playback-rate reapplication at loadedmetadata",
  );
}

function main() {
  if (!existsSync(DIST_ROOT) || !lstatSync(DIST_ROOT).isDirectory()) {
    console.error(`verify-build: dist directory not found: ${DIST_ROOT}`);
    process.exitCode = 1;
    return;
  }

  for (const file of REQUIRED_FILES) requiredFile(file);

  const allFiles = walk(DIST_ROOT);
  for (const file of allFiles) {
    const size = statSync(file).size;
    check(
      size <= MAX_FILE_BYTES,
      `${relative(file)} is ${(size / 1024 / 1024).toFixed(2)} MiB; Workers Static Assets permit at most 25 MiB per file`,
    );
  }
  check(
    !allFiles.some((file) => /\.wav$/i.test(file)),
    "dist contains a generated WAV; the web profile may bundle recorded MP3s only",
  );

  const indexHtml = readText("index.html");
  const notFoundHtml = readText("404.html");
  verifyExternalScripts(indexHtml, "index.html", { requireScript: true });
  verifyExternalScripts(notFoundHtml, "404.html");
  verifyHostedPage(indexHtml);

  const build = readJson("nocturne_build.json");
  if (build) {
    check(build.deployment === "web", 'nocturne_build.json must contain deployment: "web"');
  }

  verifyCatalog(readJson("sounds/sound_library.json"));
  verifyHeaders(readText("_headers"));
  verifyRadioBuild(allFiles);

  if (failures.length > 0) {
    console.error(`verify-build: FAIL (${failures.length} finding${failures.length === 1 ? "" : "s"})`);
    for (const failure of failures) console.error(`  - ${failure}`);
    process.exitCode = 1;
    return;
  }

  console.log(`verify-build: PASS (${assertions} build-contract assertions)`);
}

main();
