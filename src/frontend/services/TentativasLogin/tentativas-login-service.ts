import { api } from '../api';
import type { TentativaLogin } from '../types/tentativas-login-types';

export const tentativasLoginService = {
  listarPorUsuario: (idUsuario: string) => api.get<TentativaLogin[]>(`/usuarios/${idUsuario}/tentativas_login`),
};
