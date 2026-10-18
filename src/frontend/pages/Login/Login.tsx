import type { CheckedState } from '@radix-ui/react-checkbox';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ApiError } from '../../services/api';
import { useAuth } from '../../services/Login/auth-context';
import { AuthCard } from '../../style/auth/AuthCard';
import { AuthLogo } from '../../style/auth/AuthLogo';
import { Button } from '../../style/componentes/button';
import { Checkbox } from '../../style/componentes/checkbox';
import { Input } from '../../style/componentes/input';
import { Label } from '../../style/componentes/label';

interface LoginPageProps {
  emSucessoLogin: () => void;
}

export function Login({ emSucessoLogin }: LoginPageProps) {
  const { entrar } = useAuth();
  const [nomeUsuario, setNomeUsuario] = useState('');
  const [senha, setSenha] = useState('');
  const [lembreDeMim, setLembreDeMim] = useState(false);
  const [estaCarregando, setEstaCarregando] = useState(false);
  const [erro, setErro] = useState('');

  const handleSubmissao = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro('');
    setEstaCarregando(true);

    try {
      await entrar(nomeUsuario, senha);
      emSucessoLogin();
    } catch (erroCapturado) {
      if (erroCapturado instanceof ApiError) {
        if (erroCapturado.status === 429) {
          setErro('Muitas tentativas. Aguarde um minuto antes de tentar novamente.');
        } else if (erroCapturado.status === 423) {
          setErro('Conta bloqueada por excesso de tentativas. Tente novamente mais tarde.');
        } else if (erroCapturado.status === 403) {
          setErro(erroCapturado.message);
        } else {
          setErro('Usuário ou senha inválidos.');
        }
      } else {
        setErro('Não foi possível conectar ao servidor. Tente novamente.');
      }
    } finally {
      setEstaCarregando(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-6xl grid lg:grid-cols-2 gap-8 lg:gap-12 items-center">
        {/* Lado esquerdo - Ilustração */}
        <div className="hidden lg:flex flex-col justify-center items-center space-y-6">
          <div className="text-center space-y-2">
              <AuthLogo />
            <h2 className="text-2xl font-semibold text-gray-800">Bem-vindo ao seu novo espaço seguro</h2>
            <p className="text-gray-600 max-w-md">
              Acesse sua conta para começar a explorar para se beneficiar de um acesso seguro.
            </p>
          </div>
        </div>

        {/* Lado direito - Formulário de login */}
        <div className="flex justify-center w-full">
          <div className="w-full max-w-[480px]">
            <div className="lg:hidden mb-8">
              <AuthLogo />
            </div>
            <AuthCard
              title="Login"
              subtitle="Informe suas credenciais para acessar sua conta"
            >
              <form onSubmit={handleSubmissao} className="space-y-5">
                {/* Campo de nome de usuário */}
                <div className="space-y-2">
                  <Label htmlFor="nomeUsuario">Nome de usuário</Label>
                  <Input
                    id="nomeUsuario"
                    type="text"
                    placeholder="seu-usuario"
                    value={nomeUsuario}
                    onChange={(e) => setNomeUsuario(e.target.value)}
                    required
                    className="h-12 rounded-xl"
                  />
                </div>

                {/* Campo de senha */}
                <div className="space-y-2">
                  <Label htmlFor="senha">Senha</Label>
                  <Input
                    id="senha"
                    type="password"
                    placeholder="••••••••"
                    value={senha}
                    onChange={(e) => setSenha(e.target.value)}
                    required
                    className="h-12 rounded-xl"
                  />
                </div>

                {erro && (
                  <p className="text-sm text-red-600" role="alert">
                    {erro}
                  </p>
                )}

                {/* Lembrar-me e Esqueci a senha */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="remember"
                      checked={lembreDeMim}
                      onCheckedChange={(checked: CheckedState) => setLembreDeMim(checked === true)}
                    />
                    <Label
                      htmlFor="remember"
                      className="text-sm font-normal cursor-pointer"
                    >
                      Lembrar-me
                    </Label>
                  </div>
                  <Link
                    to="/reset-senha"
                    className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
                  >
                    Esqueceu a senha?
                  </Link>
                </div>

                {/* Botão de login */}
                <Button
                  type="submit"
                  className="w-full h-12 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 transition-all duration-200"
                  disabled={estaCarregando}
                >
                  {estaCarregando ? 'Entrando...' : 'Entrar'}
                </Button>

                {/* Link para registro */}
                <div className="text-center pt-4">
                  <p className="text-sm text-gray-600">
                    Não tem uma conta?{' '}
                    <Link
                      to="/registrar"
                      className="text-blue-600 hover:text-blue-700 font-medium transition-colors"
                    >
                      Criar conta
                    </Link>
                  </p>
                </div>
              </form>
            </AuthCard>
          </div>
        </div>
      </div>
    </div>
  );
}
