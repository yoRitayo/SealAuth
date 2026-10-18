import { useEffect, useState } from 'react';
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../style/componentes/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../style/componentes/table';

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
