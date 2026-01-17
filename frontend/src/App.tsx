/**
 * App.tsx — Componente raíz de la aplicación
 */

import { useEffect, useState } from 'react';
import {
  PaginaBitacora,
  PaginaPrincipal,
  PaginaConfiguracion,
} from './componentes/paginas';

/**
 * Componente principal de la aplicación
 */
function App() {
  const [ruta, setRuta] = useState(window.location.pathname);

  useEffect(() => {
    const manejarRuta = () => setRuta(window.location.pathname);
    window.addEventListener('popstate', manejarRuta);
    return () => window.removeEventListener('popstate', manejarRuta);
  }, []);

  if (ruta === '/bitacora') {
    return <PaginaBitacora />;
  }
  if (ruta === '/configuracion') {
    return <PaginaConfiguracion />;
  }
  return <PaginaPrincipal />;
}

export default App;
