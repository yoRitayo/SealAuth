import { useAuth } from '../services/Login/auth-context';
import { PainelAdmin } from './Painel/PainelAdmin';
import { PainelAnalista } from './Painel/PainelAnalista';
import { PainelUsuario } from './Painel/PainelUsuario';

// Página inicial é um despachante: cada papel vê um painel diferente,
// compatível com as ações que ele de fato pode executar na API.
export function Inicio() {
  const { usuario } = useAuth();

  if (!usuario) return null;

  switch (usuario.papel) {
    case 'admin':
      return <PainelAdmin />;
    case 'analista':
      return <PainelAnalista />;
    default:
      return <PainelUsuario />;
  }
}
