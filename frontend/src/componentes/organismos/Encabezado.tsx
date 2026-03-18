/**
 * Encabezado.tsx — Header futurista de la aplicación
 */

import { useEffect, useState } from 'react';
import { Activity, Zap, Settings, BarChart3, LogOut } from 'lucide-react';
import { useConfiguracionUsuario } from '../../contextos/ConfiguracionUsuario';
import { useDeporte } from '../../contextos/DeporteContext';
import { SelectorDeporte } from '../atomos/SelectorDeporte';
import { useAuth } from '../../contextos/AuthContext';

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Encabezado principal con estética futurista
 */
export function Encabezado() {
  const [rutaActual, setRutaActual] = useState(window.location.pathname);
  const { configuracion } = useConfiguracionUsuario();
  const { esFutbol } = useDeporte();
  const { usuario, logout } = useAuth();

  useEffect(() => {
    const manejarRuta = () => setRutaActual(window.location.pathname);
    window.addEventListener('popstate', manejarRuta);
    return () => window.removeEventListener('popstate', manejarRuta);
  }, []);

  const navegar = (ruta: string) => {
    if (window.location.pathname === ruta) return;
    window.history.pushState({}, '', ruta);
    window.dispatchEvent(new PopStateEvent('popstate'));
  };

  const bankrollConfigurado = configuracion.bankroll !== null && configuracion.bankroll > 0;

  // Determinar rutas según el deporte activo
  const rutaAnalisis = esFutbol ? '/futbol' : '/';
  const rutaBitacora = esFutbol ? '/futbol/bitacora' : '/bitacora';
  const rutaDashboard = esFutbol ? '/futbol/dashboard' : null;

  // Determinar si estamos en la ruta de análisis
  const enAnalisis = esFutbol
    ? rutaActual === '/futbol' || rutaActual.startsWith('/futbol/partidos/')
    : rutaActual === '/';

  // Determinar si estamos en la ruta de bitácora
  const enBitacora = esFutbol
    ? rutaActual === '/futbol/bitacora'
    : rutaActual === '/bitacora';

  // Determinar si estamos en el dashboard
  const enDashboard = rutaActual === '/futbol/dashboard';

  // Título dinámico según el deporte
  const titulo = esFutbol ? 'FÚTBOL ANALYZER' : 'NBA ANALYZER';
  const colorPrimario = esFutbol ? 'neon-verde' : 'neon-cyan';

  return (
    <header className="relative overflow-hidden border-b border-neon-cyan/20">
      {/* Fondo con efecto */}
      <div className="absolute inset-0 bg-gradient-to-r from-futurista-negro via-futurista-oscuro to-futurista-negro" />

      {/* Línea decorativa superior */}
      <div className={`absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-${colorPrimario} to-transparent`} />

      {/* Grid pattern sutil */}
      <div className="absolute inset-0 grid-pattern opacity-30" />

      {/* Contenido */}
      <div className="relative contenedor py-5">
        <div className="flex items-center justify-between gap-4">
          {/* Logo y Título */}
          <div className="flex items-center gap-4">
            {/* Logo con glow */}
            <div className="relative">
              <div className={`absolute inset-0 bg-${colorPrimario}/20 blur-xl rounded-full`} />
              <div className={`relative w-14 h-14 rounded-xl flex items-center justify-center border border-${colorPrimario}/30 bg-futurista-oscuro/80`}>
                <Activity className={`w-7 h-7 text-${colorPrimario}`} />
              </div>
            </div>

            {/* Título */}
            <div>
              <h1 className={`text-2xl md:text-3xl font-futurista font-bold tracking-wider text-texto-principal ${esFutbol ? 'texto-glow-verde' : 'texto-glow-cyan'}`}>
                {titulo}
              </h1>
              <div className="flex items-center gap-2 mt-1">
                <Zap className="w-3 h-3 text-neon-magenta" />
                <p className="text-xs md:text-sm text-texto-secundario uppercase tracking-widest">
                  Sistema de Predicción Avanzada
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Selector de Deporte */}
            <SelectorDeporte tamaño="sm" className="hidden sm:flex" />

            {/* Navegación */}
            <div className="hidden md:flex items-center gap-2">
              <button
                type="button"
                className={`px-3 py-2 rounded-lg text-xs font-semibold uppercase tracking-widest border ${
                  enAnalisis
                    ? `border-${colorPrimario} text-${colorPrimario}`
                    : 'border-neon-cyan/20 text-texto-secundario'
                }`}
                onClick={() => navegar(rutaAnalisis)}
              >
                {esFutbol ? 'Partidos' : 'Análisis'}
              </button>
              <button
                type="button"
                className={`px-3 py-2 rounded-lg text-xs font-semibold uppercase tracking-widest border ${
                  enBitacora
                    ? 'border-neon-magenta text-neon-magenta'
                    : 'border-neon-cyan/20 text-texto-secundario'
                }`}
                onClick={() => navegar(rutaBitacora)}
              >
                Bitácora
              </button>
              {rutaDashboard && (
                <button
                  type="button"
                  className={`px-3 py-2 rounded-lg text-xs font-semibold uppercase tracking-widest border flex items-center gap-1.5 ${
                    enDashboard
                      ? 'border-neon-azul text-neon-azul'
                      : 'border-neon-cyan/20 text-texto-secundario'
                  }`}
                  onClick={() => navegar(rutaDashboard)}
                >
                  <BarChart3 className="w-3.5 h-3.5" />
                  Dashboard
                </button>
              )}
            </div>

            <div
              className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${
                bankrollConfigurado
                  ? 'border-neon-verde/40 text-neon-verde'
                  : 'border-advertencia-500/40 text-advertencia-500'
              }`}
              title={
                bankrollConfigurado
                  ? 'Bankroll configurado'
                  : 'Modo demo: configura tu bankroll'
              }
            >
              <div
                className={`w-2 h-2 rounded-full ${
                  bankrollConfigurado ? 'bg-neon-verde' : 'bg-advertencia-500'
                }`}
              />
              <span className="text-xs uppercase tracking-widest font-mono">
                {bankrollConfigurado ? 'Bankroll ✓' : 'Demo'}
              </span>
            </div>

            <button
              type="button"
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold uppercase tracking-widest border ${
                rutaActual === '/configuracion'
                  ? 'border-neon-cyan text-neon-cyan'
                  : 'border-neon-cyan/20 text-texto-secundario'
              }`}
              onClick={() => navegar('/configuracion')}
            >
              <Settings className="w-4 h-4" />
              <span className="hidden md:inline">Config</span>
            </button>

            <button
              type="button"
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold uppercase tracking-widest border border-neon-cyan/20 text-texto-secundario hover:border-neon-magenta hover:text-neon-magenta"
              onClick={() => {
                void logout();
                navegar('/login');
              }}
              title={usuario?.email || 'Cerrar sesión'}
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden md:inline">Salir</span>
            </button>

          </div>
        </div>
      </div>

      {/* Línea decorativa inferior */}
      <div className={`absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-${colorPrimario}/50 to-transparent`} />
    </header>
  );
}
