import { expect, test, type Page } from '@playwright/test';

// ============================================================
// Login no navegador (Chromium), com o frontend atual.
//
// Toda chamada para a API (localhost:8001) é interceptada pelo
// Playwright e respondida aqui: nada chega ao backend real.
// ============================================================

const API = 'http://localhost:8001';
const ORIGEM_FRONTEND = 'http://localhost:5199';

const USUARIO_ATIVO = {
  id: '3f2a9c1e-8b7d-4e6f-9a1b-2c3d4e5f6a7b',
  nome_usuario: 'ana',
  papel: 'usuario',
  status: 'ativo',
  falhas_consecutivas: 0,
  bloqueado_ate: null,
  criado_em: '2026-10-18T12:00:00Z',
};

type Resposta = { status: number; corpo: unknown };

// A API recebe fetch com cookie, então a resposta precisa liberar o CORS como o backend faz
const CABECALHOS_CORS = {
  'Access-Control-Allow-Origin': ORIGEM_FRONTEND,
  'Access-Control-Allow-Credentials': 'true',
  'Access-Control-Allow-Headers': 'Authorization, Content-Type',
  'Access-Control-Allow-Methods': 'GET, POST, PATCH, DELETE, OPTIONS',
};

async function simularApi(page: Page, respostaLogin: Resposta) {
  const respostas: Record<string, Resposta> = {
    // Ao abrir, o app tenta restaurar a sessão; sem cookie, o backend responde 401
    'POST /auth/refresh': { status: 401, corpo: { detail: 'Sessão inválida ou expirada' } },
    'POST /auth/login': respostaLogin,
    'GET /usuarios/me': { status: 200, corpo: USUARIO_ATIVO },
  };

  const registro = { chamadas: [] as string[], corpoLogin: '' };

  await page.route(`${API}/**`, async (rota) => {
    const requisicao = rota.request();

    if (requisicao.method() === 'OPTIONS') {
      return rota.fulfill({ status: 204, headers: CABECALHOS_CORS });
    }

    const chave = `${requisicao.method()} ${new URL(requisicao.url()).pathname}`;
    registro.chamadas.push(chave);
    if (chave === 'POST /auth/login') registro.corpoLogin = requisicao.postData() ?? '';

    const resposta = respostas[chave];
    // Rota não prevista é cortada aqui, sem sair para a rede
    if (!resposta) return rota.abort();

    return rota.fulfill({
      status: resposta.status,
      headers: CABECALHOS_CORS,
      contentType: 'application/json',
      body: JSON.stringify(resposta.corpo),
    });
  });

  return registro;
}

// Digita devagar para dar para ver os campos sendo preenchidos
async function preencherEEntrar(page: Page, nome: string, senha: string) {
  await page.getByLabel('Nome de usuário').pressSequentially(nome, { delay: 60 });
  await page.getByLabel('Senha').pressSequentially(senha, { delay: 60 });
  await page.getByRole('button', { name: 'Entrar' }).click();
}

test.describe('Login no navegador', () => {
  test('login com sucesso leva ao painel do usuário', async ({ page }) => {
    const api = await simularApi(page, {
      status: 200,
      corpo: { access_token: 'jwt-ficticio', token_type: 'bearer' },
    });

    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Login' })).toBeVisible();

    await preencherEEntrar(page, 'ana', 'MinhaSenha#Forte2026!');

    // O app troca de página e mostra os dados do usuário que entrou
    await expect(page).toHaveURL(/\/inicio$/);
    await expect(page.getByRole('heading', { name: 'Dados da conta' })).toBeVisible();
    await expect(page.getByText('ana').first()).toBeVisible();

    expect(new URLSearchParams(api.corpoLogin).get('username')).toBe('ana');
    expect(api.chamadas).toContain('GET /usuarios/me');
  });

  test('senha incorreta (HTTP 401) mostra erro e continua no login', async ({ page }) => {
    const api = await simularApi(page, {
      status: 401,
      corpo: { detail: 'Usuário ou senha inválidos' },
    });

    await page.goto('/');
    await preencherEEntrar(page, 'ana', 'SenhaErrada#1');

    await expect(page.getByRole('alert')).toHaveText('Usuário ou senha inválidos.');
    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByRole('button', { name: 'Entrar' })).toBeEnabled();

    expect(api.chamadas).not.toContain('GET /usuarios/me');
  });

  test('conta bloqueada (HTTP 423) mostra aviso de bloqueio', async ({ page }) => {
    const api = await simularApi(page, {
      status: 423,
      corpo: { detail: 'Conta bloqueada' },
    });

    await page.goto('/');
    await preencherEEntrar(page, 'ana', 'MinhaSenha#Forte2026!');

    await expect(page.getByRole('alert')).toHaveText(
      'Conta bloqueada por excesso de tentativas. Tente novamente mais tarde.',
    );
    await expect(page).toHaveURL(/\/$/);

    expect(api.chamadas).not.toContain('GET /usuarios/me');
  });
});
