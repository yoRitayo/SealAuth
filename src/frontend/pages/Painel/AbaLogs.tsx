import { useEffect, useState } from 'react';
import { logsAuditoriaService } from '../../services/LogsAuditoria/logs-auditoria-service';
import type { LogAuditoria } from '../../services/types/logs-auditoria-types';
import { Badge } from '../../style/componentes/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../style/componentes/table';

// Somente leitura em todos os papéis: o banco torna LOGS_AUDITORIA imutável (trigger),
// então não existe endpoint de edição ou exclusão para expor aqui.
export function AbaLogs() {
  const [logs, setLogs] = useState<LogAuditoria[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState('');

  useEffect(() => {
    logsAuditoriaService
      .listar()
      .then(setLogs)
      .catch(() => setErro('Não foi possível carregar os logs.'))
      .finally(() => setCarregando(false));
  }, []);

  if (carregando) return <p className="text-gray-500">Carregando…</p>;
  if (erro) return <p className="text-red-600">{erro}</p>;
  if (!logs.length) return <p className="text-gray-500">Nenhum log registrado.</p>;

  return (
    <div className="bg-white rounded-2xl shadow overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>ID</TableHead>
            <TableHead>Evento</TableHead>
            <TableHead>IP</TableHead>
            <TableHead>Usuário</TableHead>
            <TableHead>Criado em</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {logs.map((log) => (
            <TableRow key={log.id}>
              <TableCell>{log.id}</TableCell>
              <TableCell>{log.evento}</TableCell>
              <TableCell>{log.ip}</TableCell>
              <TableCell className="font-mono text-xs">
                {log.id_usuario ?? <Badge variant="outline">excluído</Badge>}
              </TableCell>
              <TableCell>{new Date(log.criado_em).toLocaleString('pt-BR')}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
