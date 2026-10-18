import { api } from '../api';
import type { LogAuditoria } from '../types/logs-auditoria-types';

export const logsAuditoriaService = {
  listar: (pulo = 0, limite = 100) => api.get<LogAuditoria[]>('/logs-auditoria', { pulo, limite }),
};
