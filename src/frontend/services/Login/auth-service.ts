import { api } from '../api';

export const authService = {
  registrar: (nomeUsuario: string, email: string, senha: string) =>
    api.post<{ id: string }>('/usuarios', { nome_usuario: nomeUsuario, email, senha }),
  ativarConta: (token: string) => api.post<{ detail: string }>('/auth/ativar-conta', { token }),
  reenviarAtivacao: (email: string) => api.post<{ detail: string }>('/auth/reenviar-ativacao', { email }),
  esqueciSenha: (email: string) => api.post<{ detail: string }>('/auth/esqueci-senha', { email }),
  redefinirSenha: (token: string, novaSenha: string) =>
    api.post<{ detail: string }>('/auth/redefinir-senha', { token, nova_senha: novaSenha }),
};
