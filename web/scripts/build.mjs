import {
  copyFile,
  cp,
  mkdir,
  readFile,
  rm,
  stat,
  writeFile,
} from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const webDirectory = path.resolve(scriptDirectory, '..');
const repositoryRoot = path.resolve(webDirectory, '..');
const distDirectory = path.resolve(webDirectory, 'dist');

const sourceHtmlPath = path.join(repositoryRoot, 'static', 'index.html');
const sourceSoundLibraryPath = path.join(
  repositoryRoot,
  'sounds',
  'sound_library.json',
);
const sourceBuildInfoPath = path.join(repositoryRoot, 'nocturne_build.json');

const hostedTitle = 'Nocturne — Onsen, Sky, Radio';
const hostedDescription = 'A quiet browser-based night soundscape with an eight-channel ambient mixer, local weather sky, personal Radio, and sleep timer.';
const canonicalUrl = 'https://nocturne.cmish.dev/';

function assertSafeDistPath() {
  if (
    path.dirname(distDirectory) !== webDirectory
    || path.basename(distDirectory) !== 'dist'
    || distDirectory === repositoryRoot
    || distDirectory === webDirectory
    || distDirectory === path.parse(distDirectory).root
  ) {
    throw new Error(`Refusing to clear unsafe dist path: ${distDirectory}`);
  }
}

async function requireFile(filePath) {
  const fileStat = await stat(filePath).catch(() => null);
  if (!fileStat?.isFile()) {
    throw new Error(`Required build input is missing: ${filePath}`);
  }
}

async function copyRequiredFile(source, destination) {
  await requireFile(source);
  await mkdir(path.dirname(destination), { recursive: true });
  await copyFile(source, destination);
}

async function copyRequiredDirectory(source, destination) {
  const sourceStat = await stat(source).catch(() => null);
  if (!sourceStat?.isDirectory()) {
    throw new Error(`Required build input directory is missing: ${source}`);
  }
  await cp(source, destination, { recursive: true, force: true });
}

function externalizeInlineScripts(sourceHtml) {
  const inlineScripts = [];
  const scriptPattern = /<script\s*>([\s\S]*?)<\/script>/gi;
  const html = sourceHtml.replace(scriptPattern, (_match, source) => {
    const outputName = inlineScripts.length === 0 ? 'preload.js' : 'app.js';
    inlineScripts.push({ outputName, source });
    return outputName === 'app.js'
      ? '<script src="/web-build.js"></script>\n<script src="/app.js"></script>'
      : '<script src="/preload.js"></script>';
  });

  if (inlineScripts.length !== 2) {
    throw new Error(
      `Expected exactly two inline scripts in static/index.html; found ${inlineScripts.length}.`,
    );
  }

  if (
    inlineScripts[0].outputName !== 'preload.js'
    || inlineScripts[1].outputName !== 'app.js'
  ) {
    throw new Error('Inline script output ordering changed unexpectedly.');
  }

  return { html, inlineScripts };
}

function setHostedHeadMetadata(sourceHtml) {
  let html = sourceHtml;
  html = html.replace(
    /<title>[\s\S]*?<\/title>/i,
    `<title>${hostedTitle}</title>`,
  );
  html = html.replace(
    /<meta\s+name=["']description["'][^>]*>/i,
    `<meta name="description" content="${hostedDescription}">`,
  );

  const managedTags = [
    /\s*<link\s+rel=["']canonical["'][^>]*>\s*/gi,
    /\s*<meta\s+property=["']og:(?:title|description|type|url)["'][^>]*>\s*/gi,
  ];
  for (const pattern of managedTags) {
    html = html.replace(pattern, '\n');
  }

  const hostedTags = [
    `<link rel="canonical" href="${canonicalUrl}">`,
    `<meta property="og:title" content="${hostedTitle}">`,
    `<meta property="og:description" content="${hostedDescription}">`,
    '<meta property="og:type" content="website">',
    `<meta property="og:url" content="${canonicalUrl}">`,
  ].join('\n');
  if (!/<\/head>/i.test(html)) {
    throw new Error('Could not find </head> while adding hosted metadata.');
  }
  return html.replace(/<\/head>/i, `${hostedTags}\n</head>`);
}

function markWebDeployment(sourceHtml) {
  const htmlTagPattern = /<html\b([^>]*)>/i;
  const match = sourceHtml.match(htmlTagPattern);
  if (!match) {
    throw new Error('Could not find the root <html> element.');
  }
  if (/\bdata-deployment\s*=/.test(match[0])) {
    return sourceHtml.replace(
      htmlTagPattern,
      (_tag, attributes) => `<html${attributes.replace(
        /\sdata-deployment\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)/i,
        '',
      )} data-deployment="web">`,
    );
  }
  return sourceHtml.replace(
    htmlTagPattern,
    (_tag, attributes) => `<html${attributes} data-deployment="web">`,
  );
}

function normalizePublicSoundPath(sourcePath) {
  const publicPath = String(sourcePath ?? '').trim().replace(/^\/+/, '');
  if (
    !publicPath.startsWith('sounds/library/')
    || publicPath.includes('..')
    || path.extname(publicPath).toLowerCase() !== '.mp3'
  ) {
    throw new Error(`Unsafe or unsupported bundled sound path: ${sourcePath}`);
  }
  return publicPath;
}

async function stageSoundLibrary() {
  await requireFile(sourceSoundLibraryPath);
  const sourceLibrary = JSON.parse(
    await readFile(sourceSoundLibraryPath, 'utf8'),
  );
  if (!Array.isArray(sourceLibrary.sounds)) {
    throw new Error('sounds/sound_library.json does not contain a sounds array.');
  }

  const sounds = sourceLibrary.sounds.filter(
    (sound) => sound?.availability === 'bundled'
      && sound?.source_type === 'recorded_cc0',
  );
  const soundIds = new Set(sounds.map((sound) => sound.id));
  if (soundIds.size !== sounds.length) {
    throw new Error('The bundled recorded catalog contains duplicate sound IDs.');
  }

  const defaultSlots = (sourceLibrary.default_slots ?? []).filter((id) => soundIds.has(id));
  if (defaultSlots.length !== 8) {
    throw new Error(
      `Expected eight bundled recorded Tonight defaults; found ${defaultSlots.length}.`,
    );
  }

  const publicLibrary = {
    version: sourceLibrary.version,
    notes: 'Hosted Nocturne web catalog. Bundled recorded CC0 entries only; generated, personal Radio, and quarantined audio are not deployed.',
    default_slots: defaultSlots,
    sounds,
    excluded_sounds: [],
  };

  const outputLibraryPath = path.join(
    distDirectory,
    'sounds',
    'sound_library.json',
  );
  await mkdir(path.dirname(outputLibraryPath), { recursive: true });
  await writeFile(
    outputLibraryPath,
    `${JSON.stringify(publicLibrary, null, 2)}\n`,
    'utf8',
  );

  for (const sound of sounds) {
    const publicPath = normalizePublicSoundPath(sound.src);
    await copyRequiredFile(
      path.join(repositoryRoot, publicPath),
      path.join(distDirectory, publicPath),
    );
  }
}

async function stageSharedAssets() {
  const staticDirectory = path.join(repositoryRoot, 'static');
  await Promise.all([
    copyRequiredFile(
      path.join(staticDirectory, 'nocturne-polish.css'),
      path.join(distDirectory, 'nocturne-polish.css'),
    ),
    copyRequiredFile(
      path.join(staticDirectory, 'manifest.webmanifest'),
      path.join(distDirectory, 'manifest.webmanifest'),
    ),
    copyRequiredFile(
      path.join(staticDirectory, 'rain.mp4'),
      path.join(distDirectory, 'rain.mp4'),
    ),
    copyRequiredFile(
      path.join(staticDirectory, 'rain-still.webp'),
      path.join(distDirectory, 'rain-still.webp'),
    ),
    copyRequiredDirectory(
      path.join(staticDirectory, 'fonts'),
      path.join(distDirectory, 'fonts'),
    ),
    copyRequiredDirectory(
      path.join(staticDirectory, 'icons'),
      path.join(distDirectory, 'icons'),
    ),
  ]);
}

async function stageNoticesAndMetadata() {
  const rootFiles = [
    'LICENSE',
    'AUDIO_CREDITS.md',
    'AUDIO_PROVENANCE.md',
    'MEDIA_LICENSES.md',
  ];
  const publicFiles = [
    'NOTICE.txt',
    '404.html',
    '_headers',
    'robots.txt',
    'sitemap.xml',
  ];

  await Promise.all([
    ...rootFiles.map((name) => copyRequiredFile(
      path.join(repositoryRoot, name),
      path.join(distDirectory, name),
    )),
    ...publicFiles.map((name) => copyRequiredFile(
      path.join(webDirectory, 'public', name),
      path.join(distDirectory, name),
    )),
  ]);
}

function normalizedGitRevision(value) {
  const revision = String(value ?? '').trim().toLowerCase();
  return /^[0-9a-f]{7,64}$/.test(revision) ? revision : '';
}

function normalizedBranch(value) {
  const branch = String(value ?? '').trim();
  return branch && branch.length <= 200 ? branch : '';
}

async function stageBuildInfo() {
  await requireFile(sourceBuildInfoPath);
  const buildInfo = JSON.parse(await readFile(sourceBuildInfoPath, 'utf8'));
  const webSourceRevision = normalizedGitRevision(
    process.env.WORKERS_CI_COMMIT_SHA
      || process.env.GITHUB_SHA
      || process.env.NOCTURNE_WEB_COMMIT_SHA,
  );
  const webSourceBranch = normalizedBranch(
    process.env.WORKERS_CI_BRANCH
      || process.env.GITHUB_REF_NAME
      || process.env.NOCTURNE_WEB_BRANCH,
  );
  const webBuildInfo = {
    ...buildInfo,
    deployment: 'web',
    profile: 'nocturne-web',
    channel: 'web',
    ...(webSourceRevision ? { web_source_revision: webSourceRevision } : {}),
    ...(webSourceBranch ? { web_source_branch: webSourceBranch } : {}),
  };
  await Promise.all([
    writeFile(
      path.join(distDirectory, 'nocturne_build.json'),
      `${JSON.stringify(webBuildInfo, null, 2)}\n`,
      'utf8',
    ),
    writeFile(
      path.join(distDirectory, 'web-build.js'),
      `/* Nocturne web edition build metadata; generated from nocturne_build.json. */\nwindow.NOCTURNE_WEB_BUILD = ${JSON.stringify(webBuildInfo)};\n`,
      'utf8',
    ),
  ]);
}

async function build() {
  assertSafeDistPath();
  await requireFile(sourceHtmlPath);
  await rm(distDirectory, { recursive: true, force: true });
  await mkdir(distDirectory, { recursive: true });

  const sourceHtml = await readFile(sourceHtmlPath, 'utf8');
  const { html: externalizedHtml, inlineScripts } = externalizeInlineScripts(sourceHtml);
  const hostedHtml = setHostedHeadMetadata(externalizedHtml);
  const webHtml = markWebDeployment(hostedHtml).replace(
    /<!doctype html>/i,
    '<!DOCTYPE html>\n<!-- Nocturne web edition: generated from static/index.html for hosted deployment. -->',
  );

  await Promise.all([
    writeFile(path.join(distDirectory, 'index.html'), webHtml, 'utf8'),
    ...inlineScripts.map(({ outputName, source }) => writeFile(
      path.join(distDirectory, outputName),
      `/* Nocturne web edition: externalized from static/index.html for hosted deployment. */\n${source.trim()}\n`,
      'utf8',
    )),
    stageSharedAssets(),
    stageSoundLibrary(),
    stageNoticesAndMetadata(),
    stageBuildInfo(),
  ]);

  console.log(`Built hosted Nocturne assets in ${path.relative(repositoryRoot, distDirectory)}/`);
}

await build();
