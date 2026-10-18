import { api } from '../api';
import type { Alerta, AlertaCriar } from '../types/alertas-types';

export const alertasService = {
  listar: (pulo = 0, limite = 100) => api.get<Alerta[]>('/alertas', { pulo, limite }),
  listarPorUsuario: (idUsuario: string) => api.get<Alerta[]>(`/usuarios/${idUsuario}/alertas`),
  criar: (dados: AlertaCriar) => api.post<Alerta>('/alertas', dados),
};
