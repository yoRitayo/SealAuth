import { useEffect, useState } from 'react';
import { alertasService } from '../../services/Alertas/alertas-service';
import { bloqueiosIpService } from '../../services/BloqueiosIP/bloqueios-ip-service';
import { ApiError } from '../../services/api';
import type { Alerta } from '../../services/types/alertas-types';
import type { BloqueioIP } from '../../services/types/bloqueios-ip-types';
import { Button } from '../../style/componentes/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../../style/componentes/dialog';
import { Input } from '../../style/componentes/input';
import { Label } from '../../style/componentes/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../style/componentes/table';
import { Textarea } from '../../style/componentes/textarea';

export function AbaAlertasAdmin() {
  const [alertas, setAlertas] = useState<Alerta[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState('');
  const [abrirCriacao, setAbrirCriacao] = useState(false);
  const [alertaSelecionado, setAlertaSelecionado] = useState<Alerta | null>(null);

  useEffect(() => {
    alertasService
      .listar()
      .then(setAlertas)
      .catch(() => setErro('Não foi possível carregar os alertas.'))
      .finally(() => setCarregando(false));
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Dialog open={abrirCriacao} onOpenChange={setAbrirCriacao}>
          <DialogTrigger asChild>
            <Button className="rounded-xl">Criar alerta</Button>
          </DialogTrigger>
          <FormularioCriarAlerta
            onCriado={(alerta) => {
              setAlertas((lista) => [alerta, ...lista]);
              setAbrirCriacao(false);
            }}
          />
        </Dialog>
      </div>

      {carregando && <p className="text-gray-500">Carregando…</p>}
      {erro && <p className="text-red-600">{erro}</p>}

      {!carregando && !erro && (
        <div className="bg-white rounded-2xl shadow overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Evento</TableHead>
                <TableHead>IP</TableHead>
                <TableHead>Usuário</TableHead>
                <TableHead>Criado em</TableHead>
                <TableHead className="text-right">Bloqueios de IP</TableHead>
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
                  <TableCell className="text-right">
                    <Button size="sm" variant="outline" className="rounded-lg" onClick={() => setAlertaSelecionado(alerta)}>
                      Ver / gerenciar
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {!alertas.length && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-gray-500">
                    Nenhum alerta registrado.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      )}

      <Dialog open={!!alertaSelecionado} onOpenChange={(aberto) => !aberto && setAlertaSelecionado(null)}>
        {alertaSelecionado && <DialogBloqueiosDoAlerta alerta={alertaSelecionado} />}
      </Dialog>
    </div>
  );
}

function FormularioCriarAlerta({ onCriado }: { onCriado: (alerta: Alerta) => void }) {
  const [idUsuario, setIdUsuario] = useState('');
  const [evento, setEvento] = useState('login_suspeito');
  const [ip, setIp] = useState('203.0.113.7');
  const [jsonbTexto, setJsonbTexto] = useState('{}');
  const [hashAnterior, setHashAnterior] = useState('0'.repeat(16));
  const [hashAtual, setHashAtual] = useState('0'.repeat(16));
  const [assinatura, setAssinatura] = useState(btoa('assinatura-de-teste'));
  const [erro, setErro] = useState('');
  const [carregando, setCarregando] = useState(false);

  const criar = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro('');

    let jsonb: Record<string, unknown>;
    try {
      jsonb = JSON.parse(jsonbTexto || '{}');
    } catch {
      setErro('O campo "dados (JSON)" não é um JSON válido.');
      return;
    }

    setCarregando(true);
    try {
      const alerta = await alertasService.criar({
        id_usuario: idUsuario,
        evento,
        ip,
        jsonb,
        hash_anterior: hashAnterior,
        hash_atual: hashAtual,
        assinatura,
      });
      onCriado(alerta);
    } catch (erroCapturado) {
      setErro(erroCapturado instanceof ApiError ? erroCapturado.message : 'Não foi possível criar o alerta.');
    } finally {
      setCarregando(false);
    }
  };

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Criar alerta</DialogTitle>
        <DialogDescription>Útil para testar o endpoint POST /alertas manualmente.</DialogDescription>
      </DialogHeader>
      <form onSubmit={criar} className="space-y-3">
        <div className="space-y-1">
          <Label htmlFor="id_usuario">ID do usuário (UUID)</Label>
          <Input id="id_usuario" value={idUsuario} onChange={(e) => setIdUsuario(e.target.value)} required />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <Label htmlFor="evento">Evento</Label>
            <Input id="evento" value={evento} onChange={(e) => setEvento(e.target.value)} required />
          </div>
          <div className="space-y-1">
            <Label htmlFor="ip">IP</Label>
            <Input id="ip" value={ip} onChange={(e) => setIp(e.target.value)} required />
          </div>
        </div>
        <div className="space-y-1">
          <Label htmlFor="jsonb">Dados (JSON)</Label>
          <Textarea id="jsonb" value={jsonbTexto} onChange={(e) => setJsonbTexto(e.target.value)} rows={2} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <Label htmlFor="hash_anterior">Hash anterior</Label>
            <Input id="hash_anterior" value={hashAnterior} onChange={(e) => setHashAnterior(e.target.value)} required />
          </div>
          <div className="space-y-1">
            <Label htmlFor="hash_atual">Hash atual</Label>
            <Input id="hash_atual" value={hashAtual} onChange={(e) => setHashAtual(e.target.value)} required />
          </div>
        </div>
        <div className="space-y-1">
          <Label htmlFor="assinatura">Assinatura (base64)</Label>
          <Input id="assinatura" value={assinatura} onChange={(e) => setAssinatura(e.target.value)} required />
        </div>
        {erro && <p className="text-sm text-red-600">{erro}</p>}
        <DialogFooter>
          <Button type="submit" disabled={carregando} className="rounded-xl">
            {carregando ? 'Criando...' : 'Criar alerta'}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  );
}

function DialogBloqueiosDoAlerta({ alerta }: { alerta: Alerta }) {
  const [bloqueios, setBloqueios] = useState<BloqueioIP[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [faixa, setFaixa] = useState('203.0.113.0/24');
  const [expiraEm, setExpiraEm] = useState('');
  const [erro, setErro] = useState('');

  useEffect(() => {
    bloqueiosIpService
      .listarPorAlerta(alerta.id)
      .then(setBloqueios)
      .catch(() => setBloqueios([])) // 404 == nenhum bloqueio ainda, não é um erro para o usuário
      .finally(() => setCarregando(false));
  }, [alerta.id]);

  const criarBloqueio = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro('');
    try {
      const bloqueio = await bloqueiosIpService.criar({
        id_alerta: alerta.id,
        faixa,
        expira_em: new Date(expiraEm).toISOString(),
      });
      setBloqueios((lista) => [bloqueio, ...lista]);
    } catch (erroCapturado) {
      setErro(erroCapturado instanceof ApiError ? erroCapturado.message : 'Não foi possível criar o bloqueio.');
    }
  };

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Bloqueios de IP do alerta #{alerta.id}</DialogTitle>
        <DialogDescription>{alerta.evento} · {alerta.ip}</DialogDescription>
      </DialogHeader>

      {carregando ? (
        <p className="text-gray-500 text-sm">Carregando…</p>
      ) : bloqueios.length ? (
        <ul className="space-y-2 text-sm max-h-48 overflow-y-auto">
          {bloqueios.map((b) => (
            <li key={b.id} className="border rounded-lg p-2">
              <span className="font-mono">{b.faixa}</span> — expira em{' '}
              {new Date(b.expira_em).toLocaleString('pt-BR')}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-gray-500">Nenhum bloqueio de IP para este alerta ainda.</p>
      )}

      <form onSubmit={criarBloqueio} className="space-y-3 pt-2 border-t">
        <div className="space-y-1">
          <Label htmlFor="faixa">Faixa de IP (CIDR)</Label>
          <Input id="faixa" value={faixa} onChange={(e) => setFaixa(e.target.value)} required />
        </div>
        <div className="space-y-1">
          <Label htmlFor="expira_em">Expira em</Label>
          <Input id="expira_em" type="datetime-local" value={expiraEm} onChange={(e) => setExpiraEm(e.target.value)} required />
        </div>
        {erro && <p className="text-sm text-red-600">{erro}</p>}
        <DialogFooter>
          <Button type="submit" className="rounded-xl">Bloquear este IP</Button>
        </DialogFooter>
      </form>
    </DialogContent>
  );
}
