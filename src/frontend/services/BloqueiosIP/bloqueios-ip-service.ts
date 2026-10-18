import { api } from '../api';
import type { BloqueioIP, BloqueioIPAtualizar, BloqueioIPCriar } from '../types/bloqueios-ip-types';

export const bloqueiosIpService = {
  listar: (pulo = 0, limite = 100) => api.get<BloqueioIP[]>('/bloqueios_ip', { pulo, limite }),
  listarPorAlerta: (idAlerta: number) => api.get<BloqueioIP[]>(`/alertas/${idAlerta}/bloqueios_ip`),
  criar: (dados: BloqueioIPCriar) => api.post<BloqueioIP>('/bloqueios_ip', dados),
  atualizar: (id: number, dados: BloqueioIPAtualizar) => api.patch<BloqueioIP>(`/bloqueios_ip/${id}`, dados),
};
