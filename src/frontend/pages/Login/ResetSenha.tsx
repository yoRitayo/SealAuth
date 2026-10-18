import { ArrowLeft, Mail } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { authService } from '../../services/Login/auth-service';
import { AuthCard } from '../../style/auth/AuthCard';
import { AuthLogo } from '../../style/auth/AuthLogo';
import { Button } from '../../style/componentes/button';
import { Input } from '../../style/componentes/input';
import { Label } from '../../style/componentes/label';

export function ResetSenha() {
  const [email, setEmail] = useState('');
  const [estaCarregando, setEstaCarregando] = useState(false);
  const [foiEnviado, setFoiEnviado] = useState(false);

  const handleSubmissao = async (e: React.FormEvent) => {
    e.preventDefault();
    setEstaCarregando(true);

    try {
      // Sempre responde 202, mesmo que o e-mail não exista: evita revelar quais contas existem
      await authService.esqueciSenha(email);
    } finally {
      setEstaCarregando(false);
      setFoiEnviado(true);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-cyan-50 to-blue-50 flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-md">
        <div className="lg:hidden mb-8">
          <AuthLogo />
        </div>
        <AuthCard
          title={foiEnviado ? "Verifique seu e-mail" : "Redefinir senha"}
          subtitle={foiEnviado
            ? "Se o e-mail existir em nossa base, enviamos as instruções de redefinição de senha"
            : "Informe seu endereço de e-mail e enviaremos um link de redefinição"
          }
        >
          {!foiEnviado ? (
            <form onSubmit={handleSubmissao} className="space-y-6">
              {/* Campo de e-mail */}
              <div className="space-y-2">
                <Label htmlFor="email">Endereço de e-mail</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="voce@exemplo.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="h-12 rounded-xl pl-11"
                  />
                </div>
              </div>

              {/* Botão de envio */}
              <Button
                type="submit"
                className="w-full h-12 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 transition-all duration-200"
                disabled={estaCarregando}
              >
                {estaCarregando ? 'Enviando...' : 'Enviar link de redefinição'}
              </Button>

              {/* Voltar para o login */}
              <Link
                to="/"
                className="flex items-center justify-center gap-2 text-sm text-gray-600 hover:text-gray-900 font-medium transition-colors pt-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Voltar para o login
              </Link>
            </form>
          ) : (
            <div className="space-y-6">
              {/* Ícone de sucesso */}
              <div className="flex justify-center">
                <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
                  <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              </div>

              {/* Mensagem */}
              <div className="text-center space-y-3">
                <p className="text-gray-600">
                  Se existir uma conta com o e-mail
                </p>
                <p className="font-medium text-gray-900">{email}</p>
                <p className="text-sm text-gray-500">
                  você receberá um link de redefinição. Não recebeu? Verifique sua caixa de spam ou tente novamente.
                </p>
              </div>

              {/* Ações */}
              <div className="space-y-3 pt-4">
                <Button
                  onClick={() => setFoiEnviado(false)}
                  variant="outline"
                  className="w-full h-12 rounded-xl"
                >
                  Tentar outro e-mail
                </Button>

                <Link
                  to="/"
                  className="flex items-center justify-center gap-2 text-sm text-gray-600 hover:text-gray-900 font-medium transition-colors pt-2"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Voltar para o login
                </Link>
              </div>
            </div>
          )}
        </AuthCard>
      </div>
    </div>
  );
}
