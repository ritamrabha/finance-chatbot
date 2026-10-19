/**
 * FinSight AI - Concurrent Dev Server Runner
 * Runs both Python Backend (server.py:8000) and Vite Frontend (port:5173) simultaneously.
 * Gracefully terminates both processes on Ctrl+C.
 */
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, '..');

// 1. Determine Python executable
function getPythonExecutable() {
  const venvWin = path.join(ROOT_DIR, '.venv', 'Scripts', 'python.exe');
  const venvUnix = path.join(ROOT_DIR, '.venv', 'bin', 'python');

  if (fs.existsSync(venvWin)) return venvWin;
  if (fs.existsSync(venvUnix)) return venvUnix;
  return process.platform === 'win32' ? 'python' : 'python3';
}

const pythonBin = getPythonExecutable();

console.log('\x1b[36m%s\x1b[0m', '============================================================');
console.log('\x1b[1m\x1b[32m%s\x1b[0m', '⚡ FinSight AI - Fullstack Dev Environment');
console.log('   ➜ Backend Server:  \x1b[34mhttp://localhost:8000/\x1b[0m');
console.log('   ➜ Frontend Client:  \x1b[35mhttp://localhost:5173/\x1b[0m');
console.log('   ➜ Default Login:    \x1b[33madmin\x1b[0m / \x1b[33mdemo-o5FNMgTTn2gK\x1b[0m (Auto-filled)');
console.log('   ➜ Using Python:     ' + pythonBin);
console.log('\x1b[36m%s\x1b[0m', '============================================================\n');

// 2. Start Python Backend
const backend = spawn(pythonBin, ['server.py'], {
  cwd: ROOT_DIR,
  env: { ...process.env, PORT: '8000', PYTHONUNBUFFERED: '1' }
});

backend.stdout.on('data', (data) => {
  const lines = data.toString().trim().split('\n');
  lines.forEach(line => {
    if (line.trim()) console.log('\x1b[34m[BACKEND]\x1b[0m ' + line);
  });
});

backend.stderr.on('data', (data) => {
  const lines = data.toString().trim().split('\n');
  lines.forEach(line => {
    if (line.trim()) console.error('\x1b[31m[BACKEND-ERR]\x1b[0m ' + line);
  });
});

// 3. Start Vite Frontend
const npxCmd = process.platform === 'win32' ? 'npx.cmd' : 'npx';
const frontend = spawn(npxCmd, ['vite'], {
  cwd: ROOT_DIR,
  env: process.env,
  shell: true
});

frontend.stdout.on('data', (data) => {
  const lines = data.toString().trim().split('\n');
  lines.forEach(line => {
    if (line.trim()) console.log('\x1b[35m[FRONTEND]\x1b[0m ' + line);
  });
});

frontend.stderr.on('data', (data) => {
  const lines = data.toString().trim().split('\n');
  lines.forEach(line => {
    if (line.trim()) console.error('\x1b[33m[FRONTEND]\x1b[0m ' + line);
  });
});

// 4. Clean exit handling
function cleanup() {
  console.log('\n\x1b[33mShutting down FinSight AI dev servers...\x1b[0m');
  try {
    if (process.platform === 'win32') {
      if (backend.pid) spawn('taskkill', ['/pid', backend.pid.toString(), '/f', '/t']);
      if (frontend.pid) spawn('taskkill', ['/pid', frontend.pid.toString(), '/f', '/t']);
    } else {
      backend.kill('SIGINT');
      frontend.kill('SIGINT');
    }
  } catch (err) {
    // Ignore cleanup errors
  }
  setTimeout(() => process.exit(0), 500);
}

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
