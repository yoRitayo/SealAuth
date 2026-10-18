import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { api, definirAccessToken, loginForm, tentarRenovarSessao } from '../api';
import type { Usuario } from '../types/user-types';
import { temPermissao } from './rbac';

interface AuthContextValue {
  usuario: Usuario | null;
  carregando: boolean;
  entrar: (nomeUsuario: string, senha: string) => Promise<void>;
  sair: () => Promise<void>;
  recarregarUsuario: () => Promise<void>;
  temPermissao: (permissao: Parameters<typeof temPermissao>[1]) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [carregando, setCarregando] = useState(true);

  const buscarUsuarioAtual = async () => {
    const dados = await api.get<Usuario>('/usuarios/me');
    setUsuario(dados);
    return dados;
  };

  useEffect(() => {
    // Ao carregar a página: tenta renovar a sessão a partir do cookie do refresh token,
    // para que um F5 não derrube o usuário logado.
    (async () => {
      const renovou = await tentarRenovarSessao();
      if (renovou) {
        try {
          await buscarUsuarioAtual();
        } catch {
          definirAccessToken(null);
          setUsuario(null);
        }
      }
      setCarregando(false);
    })();
  }, []);

  const entrar = async (nomeUsuario: string, senha: string) => {
    const resultado = await loginForm(nomeUsuario, senha);
    definirAccessToken(resultado.access_token);
    await buscarUsuarioAtual();
  };

  const sair = async () => {
    try {
      await api.post('/auth/logout');
    } finally {
      definirAccessToken(null);
      setUsuario(null);
    }
  };

  const valor: AuthContextValue = {
    usuario,
    carregando,
    entrar,
    sair,
    recarregarUsuario: async () => {
      await buscarUsuarioAtual();
    },
    temPermissao: (permissao) => (usuario ? temPermissao(usuario.papel, permissao) : false),
  };

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const contexto = useContext(AuthContext);
  if (!contexto) {
    throw new Error('useAuth precisa ser usado dentro de um AuthProvider');
  }
  return contexto;
}
