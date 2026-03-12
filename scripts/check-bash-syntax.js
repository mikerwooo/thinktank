#!/usr/bin/env node
/**
 * Cross-platform bash syntax checker.
 * Replaces the `bash -n script1 && bash -n script2 && ...` chain in npm test,
 * enabling Windows support via Git for Windows (Git Bash).
 */

'use strict';

const { execSync } = require('child_process');
const { existsSync } = require('fs');
const path = require('path');

function findBash() {
  if (process.platform !== 'win32') return 'bash';
  const candidates = [
    process.env.PROGRAMFILES && path.join(process.env.PROGRAMFILES, 'Git', 'bin', 'bash.exe'),
    'C:\\Program Files\\Git\\bin\\bash.exe',
    'C:\\Program Files (x86)\\Git\\bin\\bash.exe',
  ].filter(Boolean);
  for (const c of candidates) {
    if (existsSync(c)) return c;
  }
  return 'bash'; // fallback: hope it's in PATH
}

const bash = findBash();
const root = path.join(__dirname, '..');

const scripts = [
  'autonomy/run.sh',
  'autonomy/loki',
  'autonomy/completion-council.sh',
  'autonomy/app-runner.sh',
  'autonomy/prd-checklist.sh',
  'autonomy/playwright-verify.sh',
];

let failed = false;
for (const s of scripts) {
  const full = path.join(root, s);
  if (!existsSync(full)) {
    console.error(`SKIP (not found): ${s}`);
    continue;
  }
  try {
    execSync(`"${bash}" -n "${full}"`, { stdio: 'inherit' });
  } catch {
    console.error(`FAIL: bash syntax error in ${s}`);
    failed = true;
  }
}

if (failed) {
  process.exit(1);
}
console.log('Bash syntax OK');
