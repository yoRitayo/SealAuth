import { useEffect, useState } from 'react';
import { alertasService } from '../../services/Alertas/alertas-service';
import type { Alerta } from '../../services/types/alertas-types';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../style/componentes/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../style/componentes/tabs';
import { AbaLogs } from './AbaLogs';
import { PainelCabecalho } from './PainelCabecalho';

export function PainelAnalista() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <PainelCabecalho titulo="Painel do analista" />
      <main className="max-w-6xl mx-auto px-4 py-8">
        <Tabs defaultValue="alertas">
          <TabsList>
            <TabsTrigger value="alertas">Alertas</TabsTrigger>
            <TabsTrigger value="logs">Logs de auditoria</TabsTrigger>
          </TabsList>
          <TabsContent value="alertas" className="pt-4">
            <AbaAlertasSomenteLeitura />
          </TabsContent>
          <TabsContent value="logs" className="pt-4">
            <AbaLogs />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

// O analista só lê: sem botão de criar, bloquear ou excluir (permissão "ler_alertas" apenas)
function AbaAlertasSomenteLeitura() {
  const [alertas, setAlertas] = useState<Alerta[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState('');

  useEffect(() => {
    alertasService
      .listar()
      .then(setAlertas)
      .catch(() => setErro('Não foi possível carregar os alertas.'))
      .finally(() => setCarregando(false));
  }, []);

  if (carregando) return <p className="text-gray-500">Carregando…</p>;
  if (erro) return <p className="text-red-600">{erro}</p>;
  if (!alertas.length) return <p className="text-gray-500">Nenhum alerta registrado.</p>;

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
          {alertas.map((alerta) => (
            <TableRow key={alerta.id}>
              <TableCell>{alerta.id}</TableCell>
              <TableCell>{alerta.evento}</TableCell>
              <TableCell>{alerta.ip}</TableCell>
              <TableCell className="font-mono text-xs">{alerta.id_usuario}</TableCell>
              <TableCell>{new Date(alerta.criado_em).toLocaleString('pt-BR')}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
