/**
 * App.tsx — Componente raíz de la aplicación
 */

import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import {
  PaginaBitacora,
  PaginaPrincipal,
  PaginaConfiguracion,
  PaginaFutbol,
  AnalisisPartidoFutbol,
  DashboardFutbol,
} from './componentes/paginas';

/**
 * Componente principal de la aplicación
 */
function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Rutas principales */}
        <Route path="/" element={<PaginaPrincipal />} />
        <Route path="/bitacora" element={<PaginaBitacora />} />
        <Route path="/configuracion" element={<PaginaConfiguracion />} />

        {/* Rutas del módulo de fútbol */}
        <Route path="/futbol" element={<PaginaFutbol />} />
        <Route path="/futbol/partidos/:id" element={<AnalisisPartidoFutbol />} />
        <Route path="/futbol/bitacora" element={<PaginaBitacora />} />
        <Route path="/futbol/dashboard" element={<DashboardFutbol />} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
