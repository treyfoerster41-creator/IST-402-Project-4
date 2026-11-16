import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './e2e', fullyParallel: false, workers: 1, retries: process.env.CI ? 1 : 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: { baseURL: 'http://127.0.0.1:5175', trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  webServer: [
    { command: '../.venv/bin/python ../backend/tests/e2e_server.py', url: 'http://127.0.0.1:8005/api/trading/runs', reuseExistingServer: false, timeout: 30000 },
    { command: 'npm run dev -- --port 5175 --strictPort', url: 'http://127.0.0.1:5175', env: { MARKET_BACKEND_URL: 'http://127.0.0.1:8005' }, reuseExistingServer: false },
  ],
});
