import { RouterProvider } from 'react-router-dom';
import { Router } from './routes/routes';
import { AuthProvider } from './services/Login/auth-context';
import './style/index.css';

export default function App() {
  return (
    <AuthProvider>
      <RouterProvider router={Router} />
    </AuthProvider>
  );
}
