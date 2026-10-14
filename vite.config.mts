import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(( { mode } ) => {
  const env = loadEnv(mode, process.cwd());

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(import.meta.dirname, '/src'),
        '@components': path.resolve(import.meta.dirname, 'src/style/componentes')
      },
    },
    server: {
      port: env.PORTA_APLICACAO ? Number(env.PORTA_APLICACAO): 3006,
      open: true, 
    },
    }
});
