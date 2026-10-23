import { useAuth } from '../../services/Login/auth-context';
import { MeuPerfil } from './MeuPerfil';
import { PainelCabecalho } from './PainelCabecalho';

export function PainelUsuario() {
  const { usuario } = useAuth();

  if (!usuario) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <header className="border-b bg-white">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
          <h2 className="text-xl font-semibold text-gray-900">Meu perfil</h2>
        </div>
      </header>
      <main className="max-w-2xl mx-auto px-4 py-8">
        <MeuPerfil />
      </main>
    </div>
  );
}
