import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi, type Mock } from 'vitest';
import { Login } from '../../src/frontend/pages/Login/Login';
import { AuthProvider } from '../../src/frontend/services/Login/auth-context';

// ============================================================
// Tela de login (src/frontend/pages/Login/Login.tsx)
//
// A API é simulada trocando o fetch global: nenhuma chamada
// chega ao backend. Os textos de erro esperados são os que o
// Login.tsx mostra para cada status HTTP.
// ============================================================

type Rota = (init: RequestInit) => Response | Promise<Response>;

function respostaJson(status: number, corpo: unknown) {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

const USUARIO_ATIVO = {
  id: '3f2a9c1e-8b7d-4e6f-9a1b-2c3d4e5f6a7b',
  nome_usuario: 'ana',
  papel: 'usuario',
  status: 'ativo',
  falhas_consecutivas: 0,
  bloqueado_ate: null,
  criado_em: '2026-10-18T12:00:00Z',
};

// Rotas no formato "MÉTODO /caminho". Chamada fora da lista faz o teste falhar.
function simularApi(rotas: Record<string, Rota>) {
  const todasAsRotas: Record<string, Rota> = {
    // O AuthProvider tenta restaurar a sessão ao abrir a tela; sem cookie, o backend devolve 401
    'POST /auth/refresh': () => respostaJson(401, { detail: 'Sessão inválida ou expirada' }),
    ...rotas,
  };

  const fetchFalso = vi.fn(async (entrada: RequestInfo | URL, init: RequestInit = {}) => {
    const chave = `${init.method ?? 'GET'} ${new URL(String(entrada)).pathname}`;
    const rota = todasAsRotas[chave];
    if (!rota) throw new Error(`Chamada não simulada: ${chave}`);
    return rota(init);
  });

  vi.stubGlobal('fetch', fetchFalso);
  return fetchFalso;
}

function chamadas(fetchFalso: Mock, metodo: string, caminho: string) {
  return fetchFalso.mock.calls.filter(
    ([entrada, init]) =>
      (init?.method ?? 'GET') === metodo && new URL(String(entrada)).pathname === caminho,
  );
}

async function abrirLogin(fetchFalso: Mock) {
  const emSucessoLogin = vi.fn();

  render(
    <MemoryRouter>
      <AuthProvider>
        <Login emSucessoLogin={emSucessoLogin} />
      </AuthProvider>
    </MemoryRouter>,
  );

  await waitFor(() => expect(chamadas(fetchFalso, 'POST', '/auth/refresh')).toHaveLength(1));

  return { emSucessoLogin, usuario: userEvent.setup() };
}

async function enviarLogin(usuario: ReturnType<typeof userEvent.setup>, nome: string, senha: string) {
  await usuario.type(screen.getByLabelText('Nome de usuário'), nome);
  await usuario.type(screen.getByLabelText('Senha'), senha);
  await usuario.click(screen.getByRole('button', { name: 'Entrar' }));
}

describe('Tela de login', () => {
  it('mostra os campos, o botão e os links da tela', async () => {
    const fetchFalso = simularApi({});
    await abrirLogin(fetchFalso);

    expect(screen.getByRole('heading', { level: 1, name: 'Login' })).toBeTruthy();

    const campoUsuario = screen.getByLabelText('Nome de usuário') as HTMLInputElement;
    const campoSenha = screen.getByLabelText('Senha') as HTMLInputElement;
    expect(campoUsuario.type).toBe('text');
    // A senha não pode aparecer na tela
    expect(campoSenha.type).toBe('password');

    const botao = screen.getByRole('button', { name: 'Entrar' }) as HTMLButtonElement;
    expect(botao.disabled).toBe(false);

    expect(screen.getByRole('link', { name: 'Esqueceu a senha?' }).getAttribute('href')).toBe('/reset-senha');
    expect(screen.getByRole('link', { name: 'Criar conta' }).getAttribute('href')).toBe('/registrar');

    // Nenhuma mensagem de erro e nenhum login antes de enviar
    expect(screen.queryByRole('alert')).toBeNull();
    expect(chamadas(fetchFalso, 'POST', '/auth/login')).toHaveLength(0);
  });

  it('não envia o login com campos obrigatórios vazios', async () => {
    const fetchFalso = simularApi({});
    const { emSucessoLogin, usuario } = await abrirLogin(fetchFalso);

    const campoUsuario = screen.getByLabelText('Nome de usuário') as HTMLInputElement;
    const campoSenha = screen.getByLabelText('Senha') as HTMLInputElement;
    expect(campoUsuario.required).toBe(true);
    expect(campoSenha.required).toBe(true);

    // Tudo vazio
    await usuario.click(screen.getByRole('button', { name: 'Entrar' }));
    expect(campoUsuario.validity.valueMissing).toBe(true);

    // Só o usuário preenchido
    await usuario.type(campoUsuario, 'ana');
    await usuario.click(screen.getByRole('button', { name: 'Entrar' }));
    expect(campoSenha.validity.valueMissing).toBe(true);

    expect(chamadas(fetchFalso, 'POST', '/auth/login')).toHaveLength(0);
    expect(emSucessoLogin).not.toHaveBeenCalled();
  });

  it('envia as credenciais e conclui o login', async () => {
    // A resposta do login fica pendente para conferir o estado de carregamento
    let responderLogin!: (resposta: Response) => void;
    const fetchFalso = simularApi({
      'POST /auth/login': () => new Promise<Response>((resolver) => (responderLogin = resolver)),
      'GET /usuarios/me': () => respostaJson(200, USUARIO_ATIVO),
    });
    const { emSucessoLogin, usuario } = await abrirLogin(fetchFalso);

    await enviarLogin(usuario, 'ana', 'MinhaSenha#Forte2026!');

    // Enquanto espera a API, o botão trava para evitar envio duplicado
    const botao = await screen.findByRole('button', { name: 'Entrando...' });
    expect((botao as HTMLButtonElement).disabled).toBe(true);

    responderLogin(respostaJson(200, { access_token: 'jwt-ficticio', token_type: 'bearer' }));
    await waitFor(() => expect(emSucessoLogin).toHaveBeenCalledTimes(1));

    // O backend espera form-urlencoded (OAuth2PasswordRequestForm) e o cookie do refresh token
    const [[, initLogin]] = chamadas(fetchFalso, 'POST', '/auth/login');
    expect(initLogin.body).toBeInstanceOf(URLSearchParams);
    expect((initLogin.body as URLSearchParams).get('username')).toBe('ana');
    expect((initLogin.body as URLSearchParams).get('password')).toBe('MinhaSenha#Forte2026!');
    expect(initLogin.credentials).toBe('include');

    // Depois do login, o perfil é buscado com o access token recebido
    const [[, initPerfil]] = chamadas(fetchFalso, 'GET', '/usuarios/me');
    expect(new Headers(initPerfil.headers).get('Authorization')).toBe('Bearer jwt-ficticio');

    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('mostra erro genérico com usuário ou senha incorretos', async () => {
    const fetchFalso = simularApi({
      'POST /auth/login': () => respostaJson(401, { detail: 'Usuário ou senha inválidos' }),
    });
    const { emSucessoLogin, usuario } = await abrirLogin(fetchFalso);

    await enviarLogin(usuario, 'ana', 'SenhaErrada#1');

    expect((await screen.findByRole('alert')).textContent).toBe('Usuário ou senha inválidos.');
    expect(emSucessoLogin).not.toHaveBeenCalled();
    expect(chamadas(fetchFalso, 'GET', '/usuarios/me')).toHaveLength(0);

    // O botão volta a ficar disponível para tentar de novo
    const botao = screen.getByRole('button', { name: 'Entrar' }) as HTMLButtonElement;
    expect(botao.disabled).toBe(false);
  });

  it('avisa quando a conta está bloqueada (HTTP 423)', async () => {
    const fetchFalso = simularApi({
      'POST /auth/login': () => respostaJson(423, { detail: 'Conta bloqueada' }),
    });
    const { emSucessoLogin, usuario } = await abrirLogin(fetchFalso);

    await enviarLogin(usuario, 'ana', 'MinhaSenha#Forte2026!');

    expect((await screen.findByRole('alert')).textContent).toBe(
      'Conta bloqueada por excesso de tentativas. Tente novamente mais tarde.',
    );
    expect(emSucessoLogin).not.toHaveBeenCalled();
  });

  it('avisa quando há tentativas demais (HTTP 429)', async () => {
    const fetchFalso = simularApi({
      'POST /auth/login': () =>
        new Response(JSON.stringify({ detail: 'Muitas tentativas. Aguarde um minuto.' }), {
          status: 429,
          headers: { 'Content-Type': 'application/json', 'Retry-After': '60' },
        }),
    });
    const { emSucessoLogin, usuario } = await abrirLogin(fetchFalso);

    await enviarLogin(usuario, 'ana', 'SenhaErrada#1');

    expect((await screen.findByRole('alert')).textContent).toBe(
      'Muitas tentativas. Aguarde um minuto antes de tentar novamente.',
    );
    expect(emSucessoLogin).not.toHaveBeenCalled();
  });
});
