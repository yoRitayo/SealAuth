import { api } from '../api';
import type { Papel, Usuario } from '../types/user-types';

export interface UsuarioCriar {
  nome_usuario: string;
  email: string;
  senha: string;
}

export interface UsuarioAtualizarSenha {
  senha_atual: string;
  nova_senha: string;
}

export const usuariosService = {
  listar: (pulo = 0, limite = 100) => api.get<Usuario[]>('/usuarios', { pulo, limite }),
  obter: (id: string) => api.get<Usuario>(`/usuarios/${id}`),
  obterAtual: () => api.get<Usuario>('/usuarios/me'),
  criar: (dados: UsuarioCriar) => api.post<Usuario>('/usuarios', dados),
  atualizarNome: (id: string, nomeUsuario: string) =>
    api.patch<Usuario>(`/usuarios/${id}/nome_usuario`, { nome_usuario: nomeUsuario }),
  atualizarSenha: (id: string, dados: UsuarioAtualizarSenha) =>
    api.patch<Usuario>(`/usuarios/${id}/senha`, dados),
  atualizarPapel: (id: string, papel: Papel) => api.patch<Usuario>(`/usuarios/${id}/papel`, { papel }),
  bloquear: (id: string) => api.post<Usuario>(`/usuarios/${id}/bloquear`),
  desbloquear: (id: string) => api.post<Usuario>(`/usuarios/${id}/desbloquear`),
  deletar: (id: string) => api.delete<void>(`/usuarios/${id}`),
};
