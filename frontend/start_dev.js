const { spawn } = require('child_process');

console.log('Starting PrepIQ Frontend Server on http://localhost:3000');
console.log('Documentation default port: 3000');

// Spawn next dev with explicit port 3000
const nextProcess = spawn('npx', ['next', 'dev', '-p', '3000'], {
  stdio: 'inherit',
  shell: true
});

nextProcess.on('close', (code) => {
  console.log(`Frontend server exited with code ${code}`);
});

nextProcess.on('error', (error) => {
  console.error('Failed to start frontend server:', error);
});