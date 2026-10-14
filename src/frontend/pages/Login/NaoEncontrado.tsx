import { Home } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '../../style/componentes/button';

export function NotFound() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-gray-50 to-slate-50 flex items-center justify-center px-4">
      <div className="text-center space-y-6">
        <div className="space-y-2">
          <h1 className="text-9xl font-bold text-gray-300">404</h1>
          <h2 className="text-3xl font-semibold text-gray-800">Página não encontrada</h2>
          <p className="text-gray-600 max-w-md mx-auto">
            A página que você está procurando não existe ou foi movida.
          </p>
        </div>

        <Link to="/">
          <Button className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 rounded-xl">
            <Home className="w-4 h-4 mr-2" />
            Voltar para o login
          </Button>
        </Link>
      </div>
    </div>
  );
}
