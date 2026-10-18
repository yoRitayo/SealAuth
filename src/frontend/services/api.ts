// Cliente HTTP para a API do SealAuth.
//
// O access token vive só em memória (nunca em localStorage/sessionStorage), para reduzir
// o risco de roubo via XSS. O refresh token fica em cookie HttpOnly, enviado automaticamente
// pelo navegador com `credentials: 'include'`; por isso toda chamada passa por aqui.

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8001';

let accessToken: string | null = null;
let refrescandoPromise: Promise<boolean> | null = null;

export function definirAccessToken(token: string | null) {
  accessToken = token;
}

export function obterAccessToken(): string | null {
  return accessToken;
}

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown, message: string) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

function extrairMensagem(detail: unknown, fallback: string): string {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    // Erro de validação do FastAPI/Pydantic: lista de { loc, msg, ... }
    const mensagens = detail
      .map((item) => (typeof item === 'object' && item && 'msg' in item ? String((item as { msg: unknown }).msg) : null))
      .filter(Boolean);
    if (mensagens.length) return mensagens.join('; ');
  }
  return fallback;
}

async function tentarRenovarSessao(): Promise<boolean> {
  // Evita renovações simultâneas: só a primeira chamada tenta de fato, as demais aguardam.
  if (!refrescandoPromise) {
    refrescandoPromise = (async () => {
      try {
        const resposta = await fetch(`${BASE_URL}/auth/refresh`, {
          method: 'POST',
          credentials: 'include',
        });
        if (!resposta.ok) {
          definirAccessToken(null);
          return false;
        }
        const dados = await resposta.json();
        definirAccessToken(dados.access_token as string);
        return true;
      } catch {
        definirAccessToken(null);
        return false;
      } finally {
        refrescandoPromise = null;
      }
    })();
  }
  return refrescandoPromise;
}

interface OpcoesRequisicao extends RequestInit {
  semRenovacaoAutomatica?: boolean;
}

async function requisicao<T>(caminho: string, opcoes: OpcoesRequisicao = {}): Promise<T> {
  const { semRenovacaoAutomatica, ...resto } = opcoes;

  const montarCabecalhos = () => {
    const cabecalhos = new Headers(resto.headers);
    if (!(resto.body instanceof URLSearchParams) && resto.body && !cabecalhos.has('Content-Type')) {
      cabecalhos.set('Content-Type', 'application/json');
    }
    if (accessToken) {
      cabecalhos.set('Authorization', `Bearer ${accessToken}`);
    }
    return cabecalhos;
  };

  let resposta = await fetch(`${BASE_URL}${caminho}`, {
    ...resto,
    credentials: 'include',
    headers: montarCabecalhos(),
  });

  // 401 fora das rotas de autenticação: tenta renovar o access token uma vez e repete a chamada
  if (resposta.status === 401 && !semRenovacaoAutomatica && !caminho.startsWith('/auth/')) {
    const renovou = await tentarRenovarSessao();
    if (renovou) {
      resposta = await fetch(`${BASE_URL}${caminho}`, {
        ...resto,
        credentials: 'include',
        headers: montarCabecalhos(),
      });
    }
  }

  if (resposta.status === 204) {
    return undefined as T;
  }

  const corpoBruto = await resposta.text();
  const dados = corpoBruto ? JSON.parse(corpoBruto) : undefined;

  if (!resposta.ok) {
    const mensagem = extrairMensagem(dados?.detail, `Erro ${resposta.status}`);
    throw new ApiError(resposta.status, dados?.detail, mensagem);
  }

  return dados as T;
}

function comQuery(caminho: string, query?: Record<string, string | number | undefined>): string {
  if (!query) return caminho;
  const parametros = new URLSearchParams();
  for (const [chave, valor] of Object.entries(query)) {
    if (valor !== undefined) parametros.set(chave, String(valor));
  }
  const texto = parametros.toString();
  return texto ? `${caminho}?${texto}` : caminho;
}

export const api = {
  get: <T>(caminho: string, query?: Record<string, string | number | undefined>) =>
    requisicao<T>(comQuery(caminho, query), { method: 'GET' }),

  post: <T>(caminho: string, corpo?: unknown, opcoes: OpcoesRequisicao = {}) =>
    requisicao<T>(caminho, {
      method: 'POST',
      body: corpo instanceof URLSearchParams ? corpo : corpo !== undefined ? JSON.stringify(corpo) : undefined,
      ...opcoes,
    }),

  patch: <T>(caminho: string, corpo?: unknown) =>
    requisicao<T>(caminho, { method: 'PATCH', body: corpo !== undefined ? JSON.stringify(corpo) : undefined }),

  delete: <T>(caminho: string) => requisicao<T>(caminho, { method: 'DELETE' }),
};

// Form-urlencoded: é o que o OAuth2PasswordRequestForm do backend espera em /auth/login
export function loginForm(usuario: string, senha: string) {
  const corpo = new URLSearchParams({ username: usuario, password: senha });
  return requisicao<{ access_token: string; token_type: string }>('/auth/login', {
    method: 'POST',
    body: corpo,
    semRenovacaoAutomatica: true,
  });
}

export { tentarRenovarSessao };
