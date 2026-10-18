import { useLocation, useNavigate, Navigate } from 'react-router-dom';
import { useState } from 'react';
import { useAuth } from '../services/Login/auth-context';
import { Inicio } from '../pages/Inicio';
import { Login } from '../pages/Login/Login';
import { Registrar } from '../pages/Login/Registrar';
import { ResetSenha } from '../pages/Login/ResetSenha';
import { RedefinirSenha } from '../pages/Login/RedefinirSenha';
import { VerificacaoEmail } from '../pages/Login/VerificacaoEmail';
import { NotFound } from '../pages/Login/NaoEncontrado';
import { ModalCadastroSucesso } from '../style/auth/ModalCadastroSucesso';

export function Root() {
  const endereco = useLocation();
  const navegar = useNavigate();
  const { usuario, carregando } = useAuth();
  const [mostrarSucessoRegistro, setmostrarSucessoRegistro] = useState(false);

  const pagina = endereco.pathname;

  const renderPage = () => {
    if (pagina === '/registrar') {
      return <Registrar comRegistroBemSucedido={() => setmostrarSucessoRegistro(true)} />;
    } else if (pagina === '/reset-senha') {
      return <ResetSenha />;
    } else if (pagina === '/redefinir-senha') {
      return <RedefinirSenha />;
    } else if (pagina === '/ativar-conta') {
      return <VerificacaoEmail />;
    } else if (pagina === '/inicio') {
      // Enquanto a sessão ainda está sendo restaurada (F5), evita piscar a tela de login
      if (carregando) return null;
      if (!usuario) return <Navigate to="/" replace />;
      return <Inicio />;
    } else if (pagina === '/' || pagina === '/entrar') {
      if (!carregando && usuario) return <Navigate to="/inicio" replace />;
      return <Login emSucessoLogin={() => navegar('/inicio')} />;
    } else {
      return <NotFound />;
    }
  };

  return (
    <>
      {renderPage()}

      <ModalCadastroSucesso
        open={mostrarSucessoRegistro}
        onClose={() => setmostrarSucessoRegistro(false)}
      />
    </>
  );
}
