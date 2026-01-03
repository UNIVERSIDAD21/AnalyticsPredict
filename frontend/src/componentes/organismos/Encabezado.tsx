/**
 * Encabezado.tsx — Header futurista de la aplicación
 */

import { useEffect, useState } from 'react';
import { Activity, Zap } from 'lucide-react';

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Encabezado principal con estética futurista
 */
export function Encabezado() {
  const [rutaActual, setRutaActual] = useState(window.location.pathname);

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

  return (
    <header className="relative overflow-hidden border-b border-neon-cyan/20">
      {/* Fondo con efecto */}
      <div className="absolute inset-0 bg-gradient-to-r from-futurista-negro via-futurista-oscuro to-futurista-negro" />

      {/* Línea decorativa superior */}
      <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-neon-cyan to-transparent" />

      {/* Grid pattern sutil */}
      <div className="absolute inset-0 grid-pattern opacity-30" />

      {/* Contenido */}
      <div className="relative contenedor py-5">
        <div className="flex items-center justify-between gap-4">
          {/* Logo y Título */}
          <div className="flex items-center gap-4">
            {/* Logo con glow */}
            <div className="relative">
              <div className="absolute inset-0 bg-neon-cyan/20 blur-xl rounded-full" />
              <div className="relative w-14 h-14 rounded-xl flex items-center justify-center border border-neon-cyan/30 bg-futurista-oscuro/80">
                <Activity className="w-7 h-7 text-neon-cyan" />
              </div>
            </div>

            {/* Título */}
            <div>
              <h1 className="text-2xl md:text-3xl font-futurista font-bold tracking-wider text-texto-principal texto-glow-cyan">
                NBA ANALYZER
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
            <div className="hidden md:flex items-center gap-2">
              <button
                type="button"
                className={`px-3 py-2 rounded-lg text-xs font-semibold uppercase tracking-widest border ${
                  rutaActual === '/'
                    ? 'border-neon-cyan text-neon-cyan'
                    : 'border-neon-cyan/20 text-texto-secundario'
                }`}
                onClick={() => navegar('/')}
              >
                Análisis
              </button>
              <button
                type="button"
                className={`px-3 py-2 rounded-lg text-xs font-semibold uppercase tracking-widest border ${
                  rutaActual === '/bitacora'
                    ? 'border-neon-magenta text-neon-magenta'
                    : 'border-neon-cyan/20 text-texto-secundario'
                }`}
                onClick={() => navegar('/bitacora')}
              >
                Bitácora
              </button>
            </div>

            {/* Indicador de estado */}
            <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-futurista-oscuro/50 border border-neon-verde/30">
              <div className="w-2 h-2 rounded-full bg-neon-verde animate-pulse" />
              <span className="text-xs text-neon-verde uppercase tracking-wider font-mono">
                Sistema Activo
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Línea decorativa inferior */}
      <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-neon-cyan/50 to-transparent" />
    </header>
  );
}
