import { ArrowLeft } from 'lucide-react';
import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ApiError } from '../../services/api';
import { authService } from '../../services/Login/auth-service';
import { AuthCard } from '../../style/auth/AuthCard';
import { AuthLogo } from '../../style/auth/AuthLogo';
import { Button } from '../../style/componentes/button';
import { Input } from '../../style/componentes/input';
import { Label } from '../../style/componentes/label';
import { ValidadorDeSenha } from '../utils';

export function RedefinirSenha() {
  const [parametros] = useSearchParams();
  const token = parametros.get('token') ?? '';

  const [novaSenha, setNovaSenha] = useState('');
  const [confirmarSenha, setConfirmarSenha] = useState('');
  const [estaCarregando, setEstaCarregando] = useState(false);
  const [erro, setErro] = useState('');
  const [sucesso, setSucesso] = useState(false);

  const handleSubmissao = async (e: React.FormEvent) => {
    e.preventDefault();

    const validacao = ValidadorDeSenha.validar(novaSenha);
    if (!validacao.eValida) {
      setErro(validacao.erro || 'Senha inválida.');
      return;
    }
    if (novaSenha !== confirmarSenha) {
      setErro('As senhas não coincidem.');
      return;
    }

    setErro('');
    setEstaCarregando(true);
    try {
      await authService.redefinirSenha(token, novaSenha);
      setSucesso(true);
    } catch (erroCapturado) {
      if (erroCapturado instanceof ApiError && erroCapturado.status === 400) {
        setErro('Esse link de redefinição é inválido ou já expirou. Solicite um novo.');
      } else {
        setErro('Não foi possível redefinir a senha. Tente novamente.');
      }
    } finally {
      setEstaCarregando(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-cyan-50 to-blue-50 flex items-center justify-center px-4 py-8">
        <div className="w-full max-w-md">
          <div className="lg:hidden mb-8">
            <AuthLogo />
          </div>
          <AuthCard title="Link inválido" subtitle="Nenhum token de redefinição foi encontrado">
            <Link
              to="/reset-senha"
              className="flex items-center justify-center gap-2 text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Solicitar um novo link
            </Link>
          </AuthCard>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-cyan-50 to-blue-50 flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-md">
        <div className="lg:hidden mb-8">
          <AuthLogo />
        </div>
        <AuthCard
          title={sucesso ? 'Senha redefinida' : 'Defina uma nova senha'}
          subtitle={sucesso ? 'Você já pode entrar com a nova senha' : 'Escolha uma senha forte para sua conta'}
        >
          {sucesso ? (
            <div className="space-y-6">
              <div className="flex justify-center">
                <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
                  <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              </div>
              <Link to="/">
                <Button className="w-full h-12 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700">
                  Ir para o login
                </Button>
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmissao} className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="novaSenha">Nova senha</Label>
                <Input
                  id="novaSenha"
                  type="password"
                  value={novaSenha}
                  onChange={(e) => setNovaSenha(e.target.value)}
                  required
                  className="h-12 rounded-xl"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirmarSenha">Confirmar nova senha</Label>
                <Input
                  id="confirmarSenha"
                  type="password"
                  value={confirmarSenha}
                  onChange={(e) => setConfirmarSenha(e.target.value)}
                  required
                  className="h-12 rounded-xl"
                />
                {erro && <p className="text-sm text-red-600">{erro}</p>}
              </div>
              <Button
                type="submit"
                className="w-full h-12 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700"
                disabled={estaCarregando}
              >
                {estaCarregando ? 'Redefinindo...' : 'Redefinir senha'}
              </Button>
            </form>
          )}
        </AuthCard>
      </div>
    </div>
  );
}
