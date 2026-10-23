import { useEffect, useState } from 'react';
import { alertasService } from '../../services/Alertas/alertas-service';
import { bloqueiosIpService } from '../../services/BloqueiosIP/bloqueios-ip-service';
import { ApiError } from '../../services/api';
import type { Alerta } from '../../services/types/alertas-types';
import type { BloqueioIP } from '../../services/types/bloqueios-ip-types';
import { Button } from '../../style/componentes/button';
import {
  Dialog,
  DialogClose,
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

const EVENTOS_POSSIVEIS = [
  { valor: 'login_suspeito', label: 'Login suspeito' },
  { valor: 'tentativa_forca_bruta', label: 'Tentativa força bruta' },
  { valor: 'acesso_nao_autorizado', label: 'Acesso não-autorizado' },
  { valor: 'atividade_suspeita', label: 'Atividade suspeita' },
  { valor: 'multiplas_falhas_login', label: 'Múltiplas falhas de login' },
];

const TEMPLATE_DADOS = JSON.stringify({
  motivo: 'Comportamento suspeito detectado',
  usuario: 'nome_usuario',
  tipo_alerta: 'seguranca'
}, null, 2);

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
            <Button className="rounded-xl bg-blue-600 hover:bg-blue-700 text-white">+ Novo alerta</Button>
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
              {alertas.map((alerta) => {
                const eventoLabel = EVENTOS_POSSIVEIS.find(e => e.valor === alerta.evento)?.label || alerta.evento;
                return (
                  <TableRow key={alerta.id}>
                    <TableCell>{alerta.id}</TableCell>
                    <TableCell>{eventoLabel}</TableCell>
                    <TableCell>{alerta.ip}</TableCell>
                    <TableCell className="font-mono text-xs">{alerta.id_usuario}</TableCell>
                    <TableCell>{new Date(alerta.criado_em).toLocaleString('pt-BR')}</TableCell>
                    <TableCell className="text-right">
                      <Button size="sm" variant="outline" className="rounded-lg" onClick={() => setAlertaSelecionado(alerta)}>
                        Ver / gerenciar
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })}
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

function ModalAjuda({ titulo, descricao }: { titulo: string; descricao: React.ReactNode }) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <button type="button" className="text-blue-600 hover:text-blue-800 text-sm font-semibold ml-1">?</button>
      </DialogTrigger>
      <DialogContent hideClose={true}>
        <DialogHeader>
          <DialogTitle>{titulo}</DialogTitle>
        </DialogHeader>
        <div className="text-sm text-gray-700 space-y-2">
          {descricao}
        </div>
        <DialogFooter>
          <DialogClose asChild>
            <Button type="button" className="rounded-xl">Entendi</Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function FormularioCriarAlerta({ onCriado }: { onCriado: (alerta: Alerta) => void }) {
  const [idUsuario, setIdUsuario] = useState('');
  const [evento, setEvento] = useState(EVENTOS_POSSIVEIS[0].valor);
  const [ip, setIp] = useState('203.0.113.7');
  const [jsonbTexto, setJsonbTexto] = useState(TEMPLATE_DADOS);
  const [hashAnterior, setHashAnterior] = useState('');
  const [hashAtual, setHashAtual] = useState('');
  const [assinatura, setAssinatura] = useState('');
  const [erro, setErro] = useState('');
  const [carregando, setCarregando] = useState(false);
  const [gerando, setGerando] = useState(false);

  const gerarAssinatura = async () => {
    setErro('');

    let jsonb: Record<string, unknown>;
    try {
      jsonb = JSON.parse(jsonbTexto || '{}');
    } catch {
      setErro('O campo "dados (JSON)" não é um JSON válido.');
      return;
    }

    if (!hashAnterior) {
      setErro('Preencha o hash anterior antes de gerar a assinatura.');
      return;
    }

    setGerando(true);
    try {
      const resultado = await alertasService.gerarAssinatura({
        id_usuario: idUsuario,
        evento,
        ip,
        jsonb,
        hash_anterior: hashAnterior,
      });
      setHashAtual(resultado.hash_atual);
      setAssinatura(resultado.assinatura);
    } catch (erroCapturado) {
      setErro(erroCapturado instanceof ApiError ? erroCapturado.message : 'Não foi possível gerar a assinatura.');
    } finally {
      setGerando(false);
    }
  };

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
        <DialogTitle>Criar alerta de segurança</DialogTitle>
      </DialogHeader>
      <form onSubmit={criar} className="space-y-3">
        <div className="space-y-1">
          <Label htmlFor="id_usuario">
            ID do usuário (UUID)
          </Label>
          <Input
            id="id_usuario"
            value={idUsuario}
            onChange={(e) => setIdUsuario(e.target.value)}
            placeholder="Copie do campo UUID nos logs de auditoria"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <div className="flex items-center">
              <Label htmlFor="evento">Evento</Label>
            </div>
            <select
              id="evento"
              value={evento}
              onChange={(e) => setEvento(e.target.value)}
              className="w-full px-3 py-2 border rounded-md"
              required
            >
              {EVENTOS_POSSIVEIS.map(e => (
                <option key={e.valor} value={e.valor}>{e.label}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <Label htmlFor="ip">IP</Label>
            <Input id="ip" value={ip} onChange={(e) => setIp(e.target.value)} required />
          </div>
        </div>

        <div className="space-y-1">
          <div className="flex items-center">
            <Label htmlFor="jsonb">Dados (JSON)</Label>
            <ModalAjuda
              titulo="Rótulos de Alerta"
              descricao={
                <div>
                  <p className="mb-2">Tipos de rótulo recomendados:</p>
                  <ul className="list-disc list-inside space-y-1 text-sm mb-3">
                    <li><strong>usuario:</strong> nome do usuário afetado</li>
                    <li><strong>motivo:</strong> descrição do comportamento detectado</li>
                    <li><strong>tipo_alerta:</strong> categoria (seguranca, acesso, etc)</li>
                  </ul>
                  <p className="text-sm font-semibold mb-2">Estrutura recomendada:</p>
                  <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto">
{JSON.stringify({
  motivo: 'Comportamento suspeito detectado',
  usuario: 'nome_usuario',
  tipo_alerta: 'seguranca'
}, null, 2)}
                  </pre>
                </div>
              }
            />
          </div>
          <Textarea id="jsonb" value={jsonbTexto} onChange={(e) => setJsonbTexto(e.target.value)} rows={3} />
        </div>

        <div className="space-y-1">
          <div className="flex items-center">
            <Label htmlFor="hash_anterior">Hash anterior</Label>
            <ModalAjuda
              titulo="Hash Anterior"
              descricao={
                <div>
                  <p>SHA256 criptográfico do último evento na sequência de auditoria.</p>
                  <p className="mt-2">Forma uma cadeia: cada novo evento referencia o anterior, garantindo que nenhum evento foi deletado ou alterado.</p>
                  <p className="mt-2 text-gray-600">Você pode copiá-lo do último evento nos logs de auditoria.</p>
                </div>
              }
            />
          </div>
          <Input id="hash_anterior" value={hashAnterior} onChange={(e) => setHashAnterior(e.target.value)} placeholder="Cole o hash do evento anterior" required />
        </div>

        <div className="space-y-1">
          <div className="flex items-center">
            <Label htmlFor="hash_atual">Hash atual e assinatura</Label>
            <ModalAjuda
              titulo="Geração Automática"
              descricao={
                <div>
                  <p className="mb-2">O sistema gera automaticamente:</p>
                  <ul className="list-disc list-inside space-y-1 text-sm mb-3">
                    <li><strong>Hash atual:</strong> SHA256 do evento (protege contra alterações)</li>
                    <li><strong>Assinatura:</strong> Prova criptográfica da integridade</li>
                  </ul>
                  <p className="text-sm text-gray-600">Clique no botão abaixo para gerar.</p>
                </div>
              }
            />
          </div>
          <Button
            type="button"
            onClick={gerarAssinatura}
            disabled={gerando || carregando || !idUsuario || !hashAnterior}
            className="w-full rounded-xl bg-purple-600 hover:bg-purple-700 text-white mb-3"
          >
            {gerando ? 'Gerando...' : 'Gerar hash atual e assinatura'}
          </Button>
          {hashAtual && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 space-y-2">
              <div className="text-sm">
                <p className="text-gray-600 mb-1">Hash atual:</p>
                <p className="font-mono text-xs bg-white p-2 rounded border break-all">{hashAtual}</p>
              </div>
              <div className="text-sm">
                <p className="text-gray-600 mb-1">Assinatura:</p>
                <p className="font-mono text-xs bg-white p-2 rounded border break-all">{assinatura}</p>
              </div>
            </div>
          )}
        </div>

        {erro && <p className="text-sm text-red-600">{erro}</p>}
        <DialogFooter>
          <Button type="submit" disabled={carregando} className="rounded-xl bg-green-600 hover:bg-green-700 text-white">
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
