/**
 * App.tsx — Componente raíz de la aplicación
 */

import { useEffect, useState } from 'react';
import {
  PaginaBitacora,
  PaginaPrincipal,
  PaginaConfiguracion,
  PaginaFutbol,
  AnalisisPartidoFutbol,
  BitacoraFutbol,
  DashboardFutbol,
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

  // Rutas existentes
  if (ruta === '/bitacora') {
    return <PaginaBitacora />;
  }
  if (ruta === '/configuracion') {
    return <PaginaConfiguracion />;
  }

  // Rutas del módulo de fútbol
  if (ruta === '/futbol') {
    return <PaginaFutbol />;
  }
  if (ruta.startsWith('/futbol/partidos/')) {
    return <AnalisisPartidoFutbol />;
  }
  if (ruta === '/futbol/bitacora') {
    return <BitacoraFutbol />;
  }
  if (ruta === '/futbol/dashboard') {
    return <DashboardFutbol />;
  }

  return <PaginaPrincipal />;
}

export default App;
