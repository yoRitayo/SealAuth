import path from 'node:path';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';
import { FRONTEND, PASTA_TESTES, RAIZ, pacotesDosTestes, tailwindDosTestes } from './pacotes-dos-testes.ts';

// Sobe o frontend atual (src/frontend) só para os testes do Playwright,
// sem instalar nada nem gravar arquivos dentro de src/
export default defineConfig({
  root: FRONTEND,
  // Não lê o .env de src/frontend: a API fica no endereço padrão e é simulada nos testes
  envDir: PASTA_TESTES,
  cacheDir: path.join(PASTA_TESTES, 'node_modules', '.vite-e2e'),
  plugins: [pacotesDosTestes(), tailwindDosTestes(), tailwindcss()],
  oxc: {
    jsx: { runtime: 'automatic' },
  },
  server: {
    port: 5199,
    strictPort: true,
    open: false,
    fs: { allow: [RAIZ] },
  },
});
