export interface TentativaLogin {
  id: number;
  id_usuario: string;
  nome_usuario_informado: string;
  ip: string;
  com_sucesso: boolean;
  motivo: string;
  atualizado_em: string | null;
}
