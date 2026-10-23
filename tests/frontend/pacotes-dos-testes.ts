import path from 'node:path';
import { fileURLToPath } from 'node:url';
import type { Plugin } from 'vite';

export const PASTA_TESTES = path.dirname(fileURLToPath(import.meta.url));
export const RAIZ = path.resolve(PASTA_TESTES, '../..');
export const FRONTEND = path.join(RAIZ, 'src', 'frontend');

// src/frontend não tem node_modules instalado: os imports de pacotes feitos
// pelo código do frontend são resolvidos a partir desta pasta de testes
export function pacotesDosTestes(): Plugin {
  return {
    name: 'pacotes-dos-testes',
    enforce: 'pre',
    async resolveId(fonte, importador, opcoes) {
      const ehPacote = !fonte.startsWith('.') && !fonte.startsWith('/') && !fonte.startsWith('\0') && !path.isAbsolute(fonte);
      const vemDoFrontend = importador?.replace(/\\/g, '/').includes('/src/frontend/');
      if (!ehPacote || !vemDoFrontend) return null;
      return this.resolve(fonte, path.join(PASTA_TESTES, 'setup.ts'), { ...opcoes, skipSelf: true });
    },
  };
}

// O Tailwind usa um resolvedor próprio para o @import do CSS, que não passa pelo
// plugin acima. Aponta o import para o pacote desta pasta (só em memória, o arquivo não muda).
export function tailwindDosTestes(): Plugin {
  const cssTailwind = path.join(PASTA_TESTES, 'node_modules', 'tailwindcss', 'index.css').replace(/\\/g, '/');

  return {
    name: 'tailwind-dos-testes',
    enforce: 'pre',
    transform(codigo, id) {
      const ehCssDoFrontend = id.replace(/\\/g, '/').includes('/src/frontend/') && id.split('?')[0].endsWith('.css');
      if (!ehCssDoFrontend) return null;
      return codigo.replace(/@import\s+['"]tailwindcss['"]/g, `@import "${cssTailwind}"`);
    },
  };
}
