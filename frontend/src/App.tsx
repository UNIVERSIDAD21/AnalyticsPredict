/** Rutas de la plataforma personal AnalyticsPredict. */
import { lazy, Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom';

import type { LigaBaloncesto } from './utilidades/ligasBaloncesto';
const PaginaBaloncesto = lazy(async () => ({ default: (await import('./componentes/paginas/PaginaBaloncesto')).PaginaBaloncesto }));
const PaginaOperacion = lazy(async () => ({ default: (await import('./componentes/paginas/PaginaOperacion')).PaginaOperacion }));
const PaginaDashboardUsuario = lazy(async () => ({ default: (await import('./componentes/paginas/PaginaDashboardUsuario')).PaginaDashboardUsuario }));
const PaginaBitacora = lazy(async () => ({ default: (await import('./componentes/paginas/PaginaBitacora')).PaginaBitacora }));
const PaginaConfiguracion = lazy(async () => ({ default: (await import('./componentes/paginas/PaginaConfiguracion')).PaginaConfiguracion }));
const PaginaFutbol = lazy(async () => ({ default: (await import('./componentes/paginas/PaginaFutbol')).PaginaFutbol }));
const AnalisisPartidoFutbol = lazy(async () => ({ default: (await import('./componentes/paginas/AnalisisPartidoFutbol')).AnalisisPartidoFutbol }));
const PaginaAnalisisNbaAdmin = lazy(async () => ({ default: (await import('./componentes/paginas/PaginaAnalisisNbaAdmin')).PaginaAnalisisNbaAdmin }));

/** Compatibilidad de marcadores anteriores sin mantener páginas paralelas. */
function RedireccionBaloncesto({ liga }: { liga: LigaBaloncesto }) {
  const { search, hash } = useLocation();
  const params = new URLSearchParams(search);
  params.set('liga', liga);
  return <Navigate to={`/baloncesto?${params}${hash}`} replace />;
}

export function RutasAplicacion() {
  return (
      <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-texto-secundario">Cargando módulo...</div>}>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/centro-analitico" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<PaginaDashboardUsuario />} />
          <Route path="/operacion" element={<PaginaOperacion />} />
          <Route path="/baloncesto" element={<PaginaBaloncesto />} />
          <Route path="/app" element={<RedireccionBaloncesto liga="nba" />} />
          <Route path="/euroliga" element={<RedireccionBaloncesto liga="euroliga" />} />
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
  );
}

export default function App() {
  return <BrowserRouter><RutasAplicacion /></BrowserRouter>;
}
