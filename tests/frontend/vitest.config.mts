import { defineConfig } from 'vitest/config';
import { PASTA_TESTES, RAIZ, pacotesDosTestes } from './pacotes-dos-testes.ts';

// Testes de componente (jsdom). Os testes do Playwright ficam em e2e/ e não entram aqui.
export default defineConfig({
  root: PASTA_TESTES,
  plugins: [pacotesDosTestes()],
  oxc: {
    jsx: { runtime: 'automatic' },
  },
  server: {
    fs: { allow: [RAIZ] },
  },
  test: {
    environment: 'jsdom',
    include: ['**/*.test.tsx'],
    exclude: ['node_modules/**', 'e2e/**'],
    setupFiles: ['./setup.ts'],
  },
});
