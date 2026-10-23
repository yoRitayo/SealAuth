import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';
import { definirAccessToken } from '../../src/frontend/services/api';

// O jsdom não tem ResizeObserver, que o Checkbox do Radix usa para medir o tamanho
if (!('ResizeObserver' in globalThis)) {
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  // O access token fica em memória no módulo da API; não pode vazar entre testes
  definirAccessToken(null);
});
