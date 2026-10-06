/** Rutas de la plataforma personal AnalyticsPredict. */
import { lazy, Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

const PaginaPrincipal = lazy(async () => ({ default: (await import('./componentes/paginas/PaginaPrincipal')).PaginaPrincipal }));
const PaginaDashboardUsuario = lazy(async () => ({ default: (await import('./componentes/paginas/PaginaDashboardUsuario')).PaginaDashboardUsuario }));
const PaginaBitacora = lazy(async () => ({ default: (await import('./componentes/paginas/PaginaBitacora')).PaginaBitacora }));
const PaginaConfiguracion = lazy(async () => ({ default: (await import('./componentes/paginas/PaginaConfiguracion')).PaginaConfiguracion }));
const PaginaFutbol = lazy(async () => ({ default: (await import('./componentes/paginas/PaginaFutbol')).PaginaFutbol }));
const AnalisisPartidoFutbol = lazy(async () => ({ default: (await import('./componentes/paginas/AnalisisPartidoFutbol')).AnalisisPartidoFutbol }));
const PaginaAnalisisNbaAdmin = lazy(async () => ({ default: (await import('./componentes/paginas/PaginaAnalisisNbaAdmin')).PaginaAnalisisNbaAdmin }));

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-texto-secundario">Cargando módulo...</div>}>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/centro-analitico" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<PaginaDashboardUsuario />} />
          <Route path="/app" element={<PaginaPrincipal />} />
          <Route path="/bitacora" element={<PaginaBitacora />} />
          <Route path="/configuracion" element={<PaginaConfiguracion />} />
          <Route path="/admin/nba-analysis" element={<PaginaAnalisisNbaAdmin />} />
          <Route path="/futbol" element={<PaginaFutbol />} />
          <Route path="/futbol/partidos/:id" element={<AnalisisPartidoFutbol />} />
          <Route path="/futbol/bitacora" element={<Navigate to="/bitacora" replace />} />
          <Route path="/futbol/dashboard" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
