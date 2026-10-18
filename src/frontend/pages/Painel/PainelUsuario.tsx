import { useState } from 'react';
import { ApiError } from '../../services/api';
import { useAuth } from '../../services/Login/auth-context';
import { usuariosService } from '../../services/Usuarios/usuarios-service';
import { Badge } from '../../style/componentes/badge';
import { Button } from '../../style/componentes/button';
import { Input } from '../../style/componentes/input';
import { Label } from '../../style/componentes/label';
import { ValidadorDeSenha } from '../utils';
import { PainelCabecalho } from './PainelCabecalho';

export function PainelUsuario() {
  const { usuario, recarregarUsuario } = useAuth();

  if (!usuario) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <PainelCabecalho titulo="Meu perfil" />
      <main className="max-w-2xl mx-auto px-4 py-8 space-y-6">
        <CartaoPerfil />
        <CartaoAlterarNome nomeAtual={usuario.nome_usuario} onAtualizado={recarregarUsuario} />
        <CartaoAlterarSenha />
      </main>
    </div>
  );
}

function CartaoPerfil() {
  const { usuario } = useAuth();
  if (!usuario) return null;
  return (
    <section className="bg-white rounded-2xl shadow p-6 space-y-3">
      <h2 className="text-lg font-semibold text-gray-900">Dados da conta</h2>
      <dl className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <dt className="text-gray-500">Nome de usuário</dt>
          <dd className="font-medium">{usuario.nome_usuario}</dd>
        </div>
        <div>
          <dt className="text-gray-500">Status</dt>
          <dd>
            <Badge variant={usuario.status === 'ativo' ? 'default' : 'destructive'}>{usuario.status}</Badge>
          </dd>
        </div>
        <div>
          <dt className="text-gray-500">Conta criada em</dt>
          <dd className="font-medium">{new Date(usuario.criado_em).toLocaleString('pt-BR')}</dd>
        </div>
        <div>
          <dt className="text-gray-500">Falhas de login consecutivas</dt>
          <dd className="font-medium">{usuario.falhas_consecutivas}</dd>
        </div>
      </dl>
    </section>
  );
}

function CartaoAlterarNome({ nomeAtual, onAtualizado }: { nomeAtual: string; onAtualizado: () => Promise<void> }) {
  const { usuario } = useAuth();
  const [nome, setNome] = useState(nomeAtual);
  const [carregando, setCarregando] = useState(false);
  const [mensagem, setMensagem] = useState<{ tipo: 'erro' | 'sucesso'; texto: string } | null>(null);

  const salvar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!usuario) return;
    setCarregando(true);
    setMensagem(null);
    try {
      await usuariosService.atualizarNome(usuario.id, nome);
      await onAtualizado();
      setMensagem({ tipo: 'sucesso', texto: 'Nome de usuário atualizado.' });
    } catch (erro) {
      const texto = erro instanceof ApiError && erro.status === 409
        ? 'Esse nome de usuário já está em uso.'
        : 'Não foi possível atualizar o nome.';
      setMensagem({ tipo: 'erro', texto });
    } finally {
      setCarregando(false);
    }
  };

  return (
    <section className="bg-white rounded-2xl shadow p-6 space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Nome de usuário</h2>
      <form onSubmit={salvar} className="flex gap-3 items-end">
        <div className="flex-1 space-y-2">
          <Label htmlFor="nome-usuario">Nome de usuário</Label>
          <Input id="nome-usuario" value={nome} onChange={(e) => setNome(e.target.value)} required />
        </div>
        <Button type="submit" disabled={carregando || nome === nomeAtual} className="rounded-xl">
          Salvar
        </Button>
      </form>
      {mensagem && (
        <p className={mensagem.tipo === 'erro' ? 'text-sm text-red-600' : 'text-sm text-green-600'}>
          {mensagem.texto}
        </p>
      )}
    </section>
  );
}

function CartaoAlterarSenha() {
  const { usuario } = useAuth();
  const [senhaAtual, setSenhaAtual] = useState('');
  const [novaSenha, setNovaSenha] = useState('');
  const [confirmarSenha, setConfirmarSenha] = useState('');
  const [carregando, setCarregando] = useState(false);
  const [mensagem, setMensagem] = useState<{ tipo: 'erro' | 'sucesso'; texto: string } | null>(null);

  const salvar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!usuario) return;
    setMensagem(null);

    const validacao = ValidadorDeSenha.validar(novaSenha);
    if (!validacao.eValida) {
      setMensagem({ tipo: 'erro', texto: validacao.erro || 'Senha inválida.' });
      return;
    }
    if (novaSenha !== confirmarSenha) {
      setMensagem({ tipo: 'erro', texto: 'As senhas não coincidem.' });
      return;
    }

    setCarregando(true);
    try {
      await usuariosService.atualizarSenha(usuario.id, { senha_atual: senhaAtual, nova_senha: novaSenha });
      setSenhaAtual('');
      setNovaSenha('');
      setConfirmarSenha('');
      setMensagem({ tipo: 'sucesso', texto: 'Senha atualizada. Suas outras sessões foram desconectadas.' });
    } catch (erro) {
      const texto = erro instanceof ApiError && erro.status === 403
        ? 'Senha atual incorreta.'
        : 'Não foi possível atualizar a senha.';
      setMensagem({ tipo: 'erro', texto });
    } finally {
      setCarregando(false);
    }
  };

  return (
    <section className="bg-white rounded-2xl shadow p-6 space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Alterar senha</h2>
      <form onSubmit={salvar} className="space-y-3">
        <div className="space-y-2">
          <Label htmlFor="senha-atual">Senha atual</Label>
          <Input id="senha-atual" type="password" value={senhaAtual} onChange={(e) => setSenhaAtual(e.target.value)} required />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label htmlFor="nova-senha">Nova senha</Label>
            <Input id="nova-senha" type="password" value={novaSenha} onChange={(e) => setNovaSenha(e.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirmar-nova-senha">Confirmar nova senha</Label>
            <Input id="confirmar-nova-senha" type="password" value={confirmarSenha} onChange={(e) => setConfirmarSenha(e.target.value)} required />
          </div>
        </div>
        {mensagem && (
          <p className={mensagem.tipo === 'erro' ? 'text-sm text-red-600' : 'text-sm text-green-600'}>
            {mensagem.texto}
          </p>
        )}
        <Button type="submit" disabled={carregando} className="rounded-xl">
          {carregando ? 'Salvando...' : 'Alterar senha'}
        </Button>
      </form>
    </section>
  );
}
