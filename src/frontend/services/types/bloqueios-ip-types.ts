export interface BloqueioIP {
  id: number;
  id_alerta: number | null;
  faixa: string;
  criado_em: string;
  expira_em: string;
}

export interface BloqueioIPCriar {
  id_alerta?: number | null;
  faixa: string;
  expira_em: string;
}

export interface BloqueioIPAtualizar {
  id_alerta?: number | null;
  faixa?: string;
  expira_em?: string;
}
