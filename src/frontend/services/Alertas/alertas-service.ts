import { api } from '../api';
import type { Alerta, AlertaCriar } from '../types/alertas-types';

interface DadosAlertaParaAssinar {
  id_usuario: string;
  evento: string;
  ip: string;
  jsonb: Record<string, unknown>;
  hash_anterior: string;
}

interface ResultadoAssinatura {
  hash_atual: string;
  assinatura: string;
}

export const alertasService = {
  listar: (pulo = 0, limite = 100) => api.get<Alerta[]>('/alertas', { pulo, limite }),
  listarPorUsuario: (idUsuario: string) => api.get<Alerta[]>(`/usuarios/${idUsuario}/alertas`),
  criar: (dados: AlertaCriar) => api.post<Alerta>('/alertas', dados),
  gerarAssinatura: (dados: DadosAlertaParaAssinar) =>
    api.post<ResultadoAssinatura>('/alertas/gerar-assinatura', dados),
};
