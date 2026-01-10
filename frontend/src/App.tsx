/**
 * App.tsx — Componente raíz de la aplicación
 */

import { useEffect, useState } from 'react';
import {
  PaginaBitacora,
  PaginaHistorialEquipo,
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
  const coincidenciaHistorial = ruta.match(/^\/equipo\/([^/]+)\/historial$/);
  if (coincidenciaHistorial) {
    return <PaginaHistorialEquipo equipoId={coincidenciaHistorial[1]} />;
  }
  return <PaginaPrincipal />;
}

export default App;
