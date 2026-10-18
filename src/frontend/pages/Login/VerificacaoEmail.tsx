import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ApiError } from '../../services/api';
import { authService } from '../../services/Login/auth-service';
import { AuthCard } from '../../style/auth/AuthCard';
import { AuthLogo } from '../../style/auth/AuthLogo';
import { Button } from '../../style/componentes/button';

type Estado = 'verificando' | 'sucesso' | 'erro' | 'sem_token';

export function VerificacaoEmail() {
  const [parametros] = useSearchParams();
  const token = parametros.get('token') ?? '';
  const [estado, setEstado] = useState<Estado>(token ? 'verificando' : 'sem_token');
  const jaTentou = useRef(false);

  useEffect(() => {
    if (!token || jaTentou.current) return;
    jaTentou.current = true; // evita ativar duas vezes (token de uso único)

    authService
      .ativarConta(token)
      .then(() => setEstado('sucesso'))
      .catch((erro) => {
        setEstado('erro');
        if (!(erro instanceof ApiError)) {
          console.error(erro);
        }
      });
  }, [token]);

  const conteudo = {
    verificando: {
      titulo: 'Ativando sua conta…',
      subtitulo: 'Aguarde um instante',
      corpo: null,
    },
    sucesso: {
      titulo: 'Conta ativada!',
      subtitulo: 'Agora você já pode entrar com suas credenciais',
      corpo: (
        <Link to="/">
          <Button className="w-full h-12 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700">
            Ir para o login
          </Button>
        </Link>
      ),
    },
    erro: {
      titulo: 'Não foi possível ativar',
      subtitulo: 'Esse link é inválido ou já expirou',
      corpo: (
        <Link
          to="/"
          className="flex items-center justify-center text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
        >
          Voltar para o login
        </Link>
      ),
    },
    sem_token: {
      titulo: 'Link inválido',
      subtitulo: 'Nenhum token de ativação foi encontrado',
      corpo: (
        <Link
          to="/"
          className="flex items-center justify-center text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
        >
          Voltar para o login
        </Link>
      ),
    },
  }[estado];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-md">
        <div className="lg:hidden mb-8">
          <AuthLogo />
        </div>
        <AuthCard title={conteudo.titulo} subtitle={conteudo.subtitulo}>
          <div className="space-y-6">
            {estado === 'verificando' && (
              <div className="flex justify-center py-4">
                <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
              </div>
            )}
            {conteudo.corpo}
          </div>
        </AuthCard>
      </div>
    </div>
  );
}
