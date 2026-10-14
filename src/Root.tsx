import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Inicio } from './pages/Inicio';
import { Login } from './pages/Login/Login';
import { Registrar } from './pages/Login/Registrar';
import { ResetSenha } from './pages/Login/ResetSenha';
import { ModalCadastroSucesso } from './style/auth/ModalCadastroSucesso';

export function Root() {
  const endereco = useLocation();
  const navegar = useNavigate();
  const [mostrarSucessoRegistro, setmostrarSucessoRegistro] = useState(false);

  const pagina = endereco.pathname;

  const renderPage = () => {
    if (pagina === '/registrar') {
      return <Registrar comRegistroBemSucedido={() => setmostrarSucessoRegistro(true)} />;
    } else if (pagina === '/reset-senha') {
      return <ResetSenha />;
    } else if (pagina === '/inicio') {
      return <Inicio />;
    } else if (pagina === '/') {
      return <Login emSucessoLogin={() => navegar('/inicio')} />;
    }
    
    return null;
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