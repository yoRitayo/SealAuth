import { useEffect, useState } from 'react';
import { logsAuditoriaService } from '../../services/LogsAuditoria/logs-auditoria-service';
import type { LogAuditoria } from '../../services/types/logs-auditoria-types';
import { Badge } from '../../style/componentes/badge';
import { Button } from '../../style/componentes/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../style/componentes/table';

// Somente leitura em todos os papéis: o banco torna LOGS_AUDITORIA imutável (trigger),
// então não existe endpoint de edição ou exclusão para expor aqui.
export function AbaLogs() {
  const [logs, setLogs] = useState<LogAuditoria[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState('');
  const [copiado, setCopiado] = useState(false);

  useEffect(() => {
    logsAuditoriaService
      .listar()
      .then(setLogs)
      .catch(() => setErro('Não foi possível carregar os logs.'))
      .finally(() => setCarregando(false));
  }, []);

  const copiarHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiado(true);
    setTimeout(() => setCopiado(false), 2000);
  };

  if (carregando) return <p className="text-gray-500">Carregando…</p>;
  if (erro) return <p className="text-red-600">{erro}</p>;

  const ultimoLog = logs[0];

  return (
    <div className="space-y-4">
      {ultimoLog && (
        <div className="bg-blue-50 border border-blue-200 rounded-2xl p-4 space-y-3">
          <p className="text-sm font-semibold text-blue-900">Último hash (para criar alertas):</p>
          <code className="block bg-white p-3 rounded border border-blue-300 text-xs font-mono break-all text-blue-900">
            {ultimoLog.hash_atual}
          </code>
          <Button
            size="sm"
            onClick={() => copiarHash(ultimoLog.hash_atual)}
            className="rounded-lg"
            variant={copiado ? "default" : "outline"}
          >
            {copiado ? '✓ Copiado' : 'Copiar'}
          </Button>
        </div>
      )}

      <div className="bg-white rounded-2xl shadow overflow-x-auto">
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
            {logs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-gray-500">
                  Nenhum log registrado.
                </TableCell>
              </TableRow>
            ) : (
              logs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell>{log.id}</TableCell>
                  <TableCell>{log.evento}</TableCell>
                  <TableCell>{log.ip}</TableCell>
                  <TableCell className="font-mono text-xs">
                    {log.id_usuario ?? <Badge variant="outline">excluído</Badge>}
                  </TableCell>
                  <TableCell>{new Date(log.criado_em).toLocaleString('pt-BR')}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
