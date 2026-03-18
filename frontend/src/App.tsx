/**
 * App.tsx — Componente raíz de la aplicación
 */

import type { ReactElement } from 'react';
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import {
  PaginaBitacora,
  PaginaPrincipal,
  PaginaConfiguracion,
  PaginaFutbol,
  AnalisisPartidoFutbol,
  DashboardFutbol,
  PaginaLogin,
} from './componentes/paginas';
import { useAuth } from './contextos/AuthContext';

function RutaProtegida({ children }: { children: ReactElement }) {
  const { autenticado, cargando } = useAuth();
  const location = useLocation();

  if (cargando) {
    return <div className="min-h-screen flex items-center justify-center text-texto-secundario">Validando sesión…</div>;
  }

  if (!autenticado) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}

/**
 * Componente principal de la aplicación
 */
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<PaginaLogin />} />

        {/* Rutas principales protegidas */}
        <Route path="/" element={<RutaProtegida><PaginaPrincipal /></RutaProtegida>} />
        <Route path="/bitacora" element={<RutaProtegida><PaginaBitacora /></RutaProtegida>} />
        <Route path="/configuracion" element={<RutaProtegida><PaginaConfiguracion /></RutaProtegida>} />

        {/* Rutas del módulo de fútbol protegidas */}
        <Route path="/futbol" element={<RutaProtegida><PaginaFutbol /></RutaProtegida>} />
        <Route path="/futbol/partidos/:id" element={<RutaProtegida><AnalisisPartidoFutbol /></RutaProtegida>} />
        <Route path="/futbol/bitacora" element={<RutaProtegida><PaginaBitacora /></RutaProtegida>} />
        <Route path="/futbol/dashboard" element={<RutaProtegida><DashboardFutbol /></RutaProtegida>} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
