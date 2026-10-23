import { useEffect, useState } from 'react';
import { ApiError } from '../../services/api';
import { useAuth } from '../../services/Login/auth-context';
import { usuariosService } from '../../services/Usuarios/usuarios-service';
import type { Papel, Usuario } from '../../services/types/user-types';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '../../style/componentes/alert-dialog';
import { Badge } from '../../style/componentes/badge';
import { Button } from '../../style/componentes/button';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../../style/componentes/dialog';
import { Input } from '../../style/componentes/input';
import { Label } from '../../style/componentes/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../style/componentes/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../style/componentes/table';
import { ValidadorDeSenha } from '../utils';

const CORES_STATUS: Record<string, 'default' | 'secondary' | 'destructive'> = {
  ativo: 'default',
  pendente: 'secondary',
  bloqueado: 'destructive',
};

export function AbaUsuarios() {
  const { usuario: usuarioLogado } = useAuth();
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState('');
  const [abrirCriacao, setAbrirCriacao] = useState(false);

  useEffect(() => {
    usuariosService
      .listar()
      .then(setUsuarios)
      .catch(() => setErro('Não foi possível carregar os usuários.'))
      .finally(() => setCarregando(false));
  }, []);

  const atualizarNaLista = (atualizado: Usuario) =>
    setUsuarios((lista) => lista.map((u) => (u.id === atualizado.id ? atualizado : u)));

  const removerDaLista = (id: string) => setUsuarios((lista) => lista.filter((u) => u.id !== id));

  if (carregando) return <p className="text-gray-500">Carregando…</p>;
  if (erro) return <p className="text-red-600">{erro}</p>;

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Dialog open={abrirCriacao} onOpenChange={setAbrirCriacao}>
          <DialogTrigger asChild>
            <Button className="rounded-xl bg-blue-600 hover:bg-blue-700 text-white">+ Novo usuário</Button>
          </DialogTrigger>
          <FormularioCriarUsuario
            onCriado={(usuario) => {
              setUsuarios((lista) => [usuario, ...lista]);
              setAbrirCriacao(false);
            }}
          />
        </Dialog>
      </div>

      <div className="bg-white rounded-2xl shadow overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nome de usuário</TableHead>
              <TableHead>Papel</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Falhas</TableHead>
              <TableHead>Criado em</TableHead>
              <TableHead className="text-right">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {usuarios.map((usuario) => (
              <LinhaUsuario
                key={usuario.id}
                usuario={usuario}
                ehVoceMesmo={usuario.id === usuarioLogado?.id}
                onAtualizado={atualizarNaLista}
                onDeletado={() => removerDaLista(usuario.id)}
              />
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

function FormularioCriarUsuario({ onCriado }: { onCriado: (usuario: Usuario) => void }) {
  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [tipo, setTipo] = useState<Papel>('usuario');
  const [erro, setErro] = useState('');
  const [carregando, setCarregando] = useState(false);

  const criar = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro('');

    const validacao = ValidadorDeSenha.validar(senha);
    if (!validacao.eValida) {
      setErro(validacao.erro || 'Senha inválida.');
      return;
    }

    setCarregando(true);
    try {
      const usuario = await usuariosService.criar({
        nome_usuario: nome,
        email,
        senha,
      });
      onCriado(usuario);
    } catch (erroCapturado) {
      const texto = erroCapturado instanceof ApiError && erroCapturado.status === 409
        ? 'Esse nome de usuário ou email já está em uso.'
        : 'Não foi possível criar o usuário.';
      setErro(texto);
    } finally {
      setCarregando(false);
    }
  };

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Criar novo usuário</DialogTitle>
      </DialogHeader>
      <form onSubmit={criar} className="space-y-3">
        <div className="space-y-1">
          <Label htmlFor="novo-nome">Nome de usuário</Label>
          <Input
            id="novo-nome"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            placeholder="ana.silva"
            required
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="novo-email">Email</Label>
          <Input
            id="novo-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="ana@exemplo.com"
            required
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="nova-senha">Senha</Label>
          <Input
            id="nova-senha"
            type="password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            placeholder="Senha forte"
            required
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="tipo">Tipo de usuário</Label>
          <Select value={tipo} onValueChange={(valor) => setTipo(valor as Papel)}>
            <SelectTrigger id="tipo">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="usuario">Usuário</SelectItem>
              <SelectItem value="analista">Analista</SelectItem>
              <SelectItem value="admin">Admin</SelectItem>
            </SelectContent>
          </Select>
        </div>
        {erro && <p className="text-sm text-red-600">{erro}</p>}
        <DialogFooter>
          <Button type="submit" disabled={carregando} className="rounded-xl bg-blue-600 hover:bg-blue-700 text-white">
            {carregando ? 'Criando...' : 'Criar usuário'}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  );
}

function LinhaUsuario({
  usuario,
  ehVoceMesmo,
  onAtualizado,
  onDeletado,
}: {
  usuario: Usuario;
  ehVoceMesmo: boolean;
  onAtualizado: (u: Usuario) => void;
  onDeletado: () => void;
}) {
  const [processando, setProcessando] = useState(false);

  const alternarBloqueio = async () => {
    setProcessando(true);
    try {
      const atualizado = usuario.status === 'bloqueado'
        ? await usuariosService.desbloquear(usuario.id)
        : await usuariosService.bloquear(usuario.id);
      onAtualizado(atualizado);
    } finally {
      setProcessando(false);
    }
  };

  const alterarPapel = async (papel: Papel) => {
    setProcessando(true);
    try {
      const atualizado = await usuariosService.atualizarPapel(usuario.id, papel);
      onAtualizado(atualizado);
    } finally {
      setProcessando(false);
    }
  };

  const deletar = async () => {
    setProcessando(true);
    try {
      await usuariosService.deletar(usuario.id);
      onDeletado();
    } finally {
      setProcessando(false);
    }
  };

  return (
    <TableRow>
      <TableCell className="font-medium">
        {usuario.nome_usuario} {ehVoceMesmo && <span className="text-xs text-gray-400">(você)</span>}
      </TableCell>
      <TableCell>
        <Select
          value={usuario.papel}
          onValueChange={(valor) => alterarPapel(valor as Papel)}
          disabled={ehVoceMesmo || processando}
        >
          <SelectTrigger className="w-32 h-8">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="usuario">Usuário</SelectItem>
            <SelectItem value="analista">Analista</SelectItem>
            <SelectItem value="admin">Admin</SelectItem>
          </SelectContent>
        </Select>
      </TableCell>
      <TableCell>
        <Badge variant={CORES_STATUS[usuario.status] ?? 'secondary'}>{usuario.status}</Badge>
      </TableCell>
      <TableCell>{usuario.falhas_consecutivas}</TableCell>
      <TableCell>{new Date(usuario.criado_em).toLocaleDateString('pt-BR')}</TableCell>
      <TableCell className="text-right space-x-2">
        <Button
          size="sm"
          variant="outline"
          disabled={ehVoceMesmo || processando}
          onClick={alternarBloqueio}
          className="rounded-lg"
        >
          {usuario.status === 'bloqueado' ? 'Desbloquear' : 'Bloquear'}
        </Button>
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button size="sm" variant="destructive" disabled={ehVoceMesmo || processando} className="rounded-lg">
              Excluir
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Excluir "{usuario.nome_usuario}"?</AlertDialogTitle>
              <AlertDialogDescription>
                Essa ação não pode ser desfeita. Os alertas do usuário também serão excluídos.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancelar</AlertDialogCancel>
              <AlertDialogAction onClick={deletar}>Excluir</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </TableCell>
    </TableRow>
  );
}
