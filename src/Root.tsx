import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Login } from './pages/Login/Login';
import { Registrar } from './pages/Login/Registrar';
import { ResetSenha } from './pages/Login/ResetSenha';
import { LoginErrorModal } from './style/auth/LoginErrorModal';
import { RegistrationSuccessModal } from './style/auth/RegistrationSucessModal';

export function Root() {
  const endereco = useLocation();
  const [mostrarErroLogin, setMostrarErroLogin] = useState(false);
  const [mostrarSucessoRegistro, setmostrarSucessoRegistro] = useState(false);

  const pagina = endereco.pathname;

  const renderPage = () => {
    if (pagina === '/registrar') {
      return <Registrar comRegistroBemSucedido={() => setmostrarSucessoRegistro(true)} />;
    } else if (pagina === '/reset-senha') {
      return <ResetSenha />;
    } else if (pagina === '/') {
      return <Login emErroLogin={() => setMostrarErroLogin(true)} />;
    }
    // Se nenhuma das páginas retornar então o router vai para a página 404
    return null;
  };

  return (
    <>
      {renderPage()}
      
      <LoginErrorModal 
        open={mostrarErroLogin} 
        onClose={() => setMostrarErroLogin(false)} 
      />
      
      <RegistrationSuccessModal 
        open={mostrarSucessoRegistro} 
        onClose={() => setmostrarSucessoRegistro(false)} 
      />
    </>
  );
}