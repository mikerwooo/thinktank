#!/usr/bin/env node
/**
 * Loki Mode CLI wrapper for npm distribution
 * Delegates to the bash CLI
 */

const { spawn } = require('child_process');
const { existsSync } = require('fs');
const path = require('path');

const lokiScript = path.join(__dirname, '..', 'autonomy', 'loki');
const args = process.argv.slice(2);

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
  return 'bash'; // fallback: hope it's in PATH via Git for Windows
}

const bash = findBash();
const child = process.platform === 'win32'
  ? spawn(bash, [lokiScript, ...args], { stdio: 'inherit' })
  : spawn(lokiScript, args, { stdio: 'inherit', shell: true });

child.on('close', (code) => {
  process.exit(code || 0);
});

child.on('error', (err) => {
  console.error('Error running loki:', err.message);
  if (process.platform === 'win32') {
    console.error('Make sure Git for Windows is installed and bash is available in your PATH.');
    console.error('Download from: https://git-scm.com/download/win');
  } else {
    console.error('Make sure bash is available on your system');
  }
  process.exit(1);
});
