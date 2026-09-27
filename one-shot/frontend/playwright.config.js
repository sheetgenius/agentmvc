import {defineConfig} from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  testMatch: '*.spec.js',
  workers: 1,
  timeout: 90000,
  use: {baseURL: `http://127.0.0.1:${process.env.FRONTEND_PORT || 5173}`, browserName: 'chromium'},
});
