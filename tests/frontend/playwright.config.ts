import { defineConfig, devices } from '@playwright/test';

const PORTA = 5199;

// Com --headed, cada ação fica mais lenta para dar para acompanhar no navegador.
// A variável de ambiente leva essa escolha para os workers do Playwright.
if (process.argv.includes('--headed')) process.env.SEALAUTH_ASSISTIR = '1';
const assistir = process.env.SEALAUTH_ASSISTIR === '1';

export default defineConfig({
  testDir: './e2e',
  testMatch: '**/*.spec.ts',
  outputDir: './test-results',
  fullyParallel: false,
  reporter: [['list'], ['html', { outputFolder: 'playwright-report', open: 'never' }]],
  use: {
    baseURL: `http://localhost:${PORTA}`,
    // Print do fim de cada teste no relatório; trace e vídeo só quando falha
    screenshot: 'on',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    launchOptions: { slowMo: assistir ? 400 : 0 },
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  // Sobe o frontend atual de src/frontend e derruba ao terminar
  webServer: {
    command: 'npx vite --config vite.e2e.config.mts',
    url: `http://localhost:${PORTA}`,
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
