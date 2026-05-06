/**
 * App.tsx — Componente raíz de la aplicación
 */

import { lazy, Suspense, type ReactElement } from 'react';
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { PaginaLogin } from './componentes/paginas/PaginaLogin';
import { PaginaLegal } from './componentes/paginas/PaginaLegal';
import { PaginaOnboarding } from './componentes/paginas/PaginaOnboarding';
import { useAuth } from './contextos/AuthContext';
import { useAccessPolicy } from './contextos/AccessPolicyContext';
import type { Capability } from './servicios/accessPolicy';
import { obtenerEstadoOnboarding } from './servicios/onboarding';

const PaginaPrincipal = lazy(async () => ({ default: (await import('./componentes/paginas/PaginaPrincipal')).PaginaPrincipal }));
const PaginaDashboardUsuario = lazy(async () => ({ default: (await import('./componentes/paginas/PaginaDashboardUsuario')).PaginaDashboardUsuario }));
const PaginaBitacora = lazy(async () => ({ default: (await import('./componentes/paginas/PaginaBitacora')).PaginaBitacora }));
const PaginaConfiguracion = lazy(async () => ({ default: (await import('./componentes/paginas/PaginaConfiguracion')).PaginaConfiguracion }));
const PaginaFutbol = lazy(async () => ({ default: (await import('./componentes/paginas/PaginaFutbol')).PaginaFutbol }));
const AnalisisPartidoFutbol = lazy(async () => ({ default: (await import('./componentes/paginas/AnalisisPartidoFutbol')).AnalisisPartidoFutbol }));
const PaginaAnalisisNbaAdmin = lazy(async () => ({ default: (await import('./componentes/paginas/PaginaAnalisisNbaAdmin')).PaginaAnalisisNbaAdmin }));

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

function RutaConOnboarding({ children }: { children: ReactElement }) {
  const { usuario } = useAuth();
  const location = useLocation();

  if (!usuario) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (location.pathname === '/onboarding') {
    return children;
  }

  const estadoOnboarding = obtenerEstadoOnboarding(String(usuario.id));
  if (!estadoOnboarding.completado) {
    return <Navigate to="/onboarding" replace state={{ from: location }} />;
  }

  return children;
}

function RutaConCapacidad({
  capability,
  children,
  fallback = '/dashboard',
}: {
  capability: Capability;
  children: ReactElement;
  fallback?: string;
}) {
  const { can, cargandoTier } = useAccessPolicy();

  if (cargandoTier) {
    return <CargandoRuta />;
  }

  if (!can(capability)) {
    return <Navigate to={fallback} replace />;
  }

  return children;
}

function CargandoRuta() {
  return (
    <div className="min-h-screen flex items-center justify-center text-texto-secundario">
      Cargando módulo...
    </div>
  );
}

/**
 * Componente principal de la aplicación
 */
function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<CargandoRuta />}>
        <Routes>
        <Route path="/login" element={<PaginaLogin />} />
        <Route path="/legal/terminos" element={<PaginaLegal tipo="terminos" />} />
        <Route path="/legal/privacidad" element={<PaginaLegal tipo="privacidad" />} />
        <Route path="/legal/disclaimer" element={<PaginaLegal tipo="disclaimer" />} />

        <Route path="/onboarding" element={<RutaProtegida><PaginaOnboarding /></RutaProtegida>} />

        {/* Entry points */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/centro-analitico" element={<Navigate to="/dashboard" replace />} />

        {/* Rutas principales protegidas */}
        <Route path="/app" element={<RutaProtegida><RutaConOnboarding><RutaConCapacidad capability="analisis.nba.base"><PaginaPrincipal /></RutaConCapacidad></RutaConOnboarding></RutaProtegida>} />
        <Route path="/dashboard" element={<RutaProtegida><RutaConOnboarding><RutaConCapacidad capability="dashboard.personal"><PaginaDashboardUsuario /></RutaConCapacidad></RutaConOnboarding></RutaProtegida>} />
        <Route path="/bitacora" element={<RutaProtegida><RutaConOnboarding><RutaConCapacidad capability="bitacora.personal"><PaginaBitacora /></RutaConCapacidad></RutaConOnboarding></RutaProtegida>} />
        <Route path="/configuracion" element={<RutaProtegida><RutaConOnboarding><RutaConCapacidad capability="configuracion.base"><PaginaConfiguracion /></RutaConCapacidad></RutaConOnboarding></RutaProtegida>} />
        <Route path="/chat" element={<Navigate to="/" replace />} />

        {/* Herramientas internas/admin protegidas */}
        <Route path="/admin/nba-analysis" element={<RutaProtegida><RutaConOnboarding><RutaConCapacidad capability="analisis.nba.base"><PaginaAnalisisNbaAdmin /></RutaConCapacidad></RutaConOnboarding></RutaProtegida>} />

        {/* Rutas del módulo de fútbol protegidas */}
        <Route path="/futbol" element={<RutaProtegida><RutaConOnboarding><RutaConCapacidad capability="futbol.base"><PaginaFutbol /></RutaConCapacidad></RutaConOnboarding></RutaProtegida>} />
        <Route path="/futbol/partidos/:id" element={<RutaProtegida><RutaConOnboarding><RutaConCapacidad capability="futbol.base"><AnalisisPartidoFutbol /></RutaConCapacidad></RutaConOnboarding></RutaProtegida>} />
        <Route path="/futbol/bitacora" element={<Navigate to="/bitacora" replace />} />
        <Route path="/futbol/dashboard" element={<Navigate to="/dashboard" replace />} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
