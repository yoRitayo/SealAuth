import { LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../services/Login/auth-context';
import { Badge } from '../../style/componentes/badge';
import { Button } from '../../style/componentes/button';

const ROTULO_PAPEL: Record<string, string> = {
  admin: 'Administrador',
  analista: 'Analista',
  usuario: 'Usuário',
};

export function PainelCabecalho({ titulo }: { titulo: string }) {
  const { usuario, sair } = useAuth();
  const navegar = useNavigate();

  const handleSair = async () => {
    await sair();
    navegar('/');
  };

  return (
    <header className="border-b bg-white">
      <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">{titulo}</h1>
          {usuario && (
            <p className="text-sm text-gray-500">
              {usuario.nome_usuario} ·{' '}
              <Badge variant="secondary">{ROTULO_PAPEL[usuario.papel] ?? usuario.papel}</Badge>
            </p>
          )}
        </div>
        <Button variant="outline" onClick={handleSair} className="rounded-xl">
          <LogOut className="w-4 h-4 mr-2" />
          Sair
        </Button>
      </div>
    </header>
  );
}
