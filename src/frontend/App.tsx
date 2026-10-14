import { RouterProvider } from 'react-router-dom';
import { Router } from './routes';

import './style/index.css';

export default function App() {
  return <RouterProvider router={Router} />
}