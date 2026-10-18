export interface LogAuditoria {
  id: number;
  id_usuario: string | null;
  evento: string;
  ip: string;
  jsonb: Record<string, unknown>;
  hash_anterior: string;
  hash_atual: string;
  assinatura: string; // base64
  criado_em: string;
}
