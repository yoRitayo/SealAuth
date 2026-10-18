import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../style/componentes/tabs';
import { AbaAlertasAdmin } from './AbaAlertasAdmin';
import { AbaLogs } from './AbaLogs';
import { AbaUsuarios } from './AbaUsuarios';
import { PainelCabecalho } from './PainelCabecalho';

export function PainelAdmin() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <PainelCabecalho titulo="Painel do administrador" />
      <main className="max-w-6xl mx-auto px-4 py-8">
        <Tabs defaultValue="usuarios">
          <TabsList>
            <TabsTrigger value="usuarios">Usuários</TabsTrigger>
            <TabsTrigger value="alertas">Alertas</TabsTrigger>
            <TabsTrigger value="logs">Logs de auditoria</TabsTrigger>
          </TabsList>
          <TabsContent value="usuarios" className="pt-4">
            <AbaUsuarios />
          </TabsContent>
          <TabsContent value="alertas" className="pt-4">
            <AbaAlertasAdmin />
          </TabsContent>
          <TabsContent value="logs" className="pt-4">
            <AbaLogs />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
