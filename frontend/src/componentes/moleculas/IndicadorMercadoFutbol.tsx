/**
 * IndicadorMercadoFutbol.tsx — Indicador visual de mercado Over/Under
 *
 * Muestra probabilidades de mercado con diseño futurista y colores neón.
 */

import { clsx } from 'clsx';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { TipoMercadoFutbol, ETIQUETAS_MERCADOS } from '../../tipos/futbol';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsIndicadorMercadoFutbol {
  /** Tipo de mercado */
  mercado: TipoMercadoFutbol;
  /** Línea del mercado (ej: 10.5) */
  linea: number;
  /** Probabilidad de OVER (0-1) */
  probabilidadOver: number;
  /** Probabilidad de UNDER (0-1) */
  probabilidadUnder: number;
  /** Lado recomendado (opcional) */
  lado?: 'OVER' | 'UNDER';
  /** Mostrar barra de probabilidad */
  mostrarBarra?: boolean;
  /** Compacto */
  compacto?: boolean;
  /** Clase CSS adicional */
  className?: string;
}

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

/**
 * Obtiene el color basado en la probabilidad
 */
function getColorProbabilidad(probabilidad: number, esOver: boolean): string {
  const baseColor = esOver ? 'neon-verde' : 'neon-rojo';

  if (probabilidad >= 0.7) {
    return `text-${baseColor}`;
  } else if (probabilidad >= 0.5) {
    return `text-${baseColor}/80`;
  } else if (probabilidad >= 0.3) {
    return 'text-texto-secundario';
  } else {
    return 'text-texto-terciario';
  }
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Indicador visual de probabilidades Over/Under para mercados de fútbol
 */
export function IndicadorMercadoFutbol({
  mercado,
  linea,
  probabilidadOver,
  probabilidadUnder,
  lado,
  mostrarBarra = true,
  compacto = false,
  className,
}: PropsIndicadorMercadoFutbol) {
  const porcentajeOver = (probabilidadOver * 100).toFixed(1);
  const porcentajeUnder = (probabilidadUnder * 100).toFixed(1);
  const etiquetaMercado = ETIQUETAS_MERCADOS[mercado];

  // Determinar cual lado está destacado
  const overDestacado = lado === 'OVER' || (!lado && probabilidadOver > probabilidadUnder);
  const underDestacado = lado === 'UNDER' || (!lado && probabilidadUnder > probabilidadOver);

  if (compacto) {
    return (
      <div
        className={clsx(
          'flex items-center gap-2 px-3 py-1.5 rounded-lg',
          'bg-futurista-negro/50 border border-neon-cyan/10',
          className
        )}
      >
        <span className="text-xs text-texto-terciario">{linea}</span>
        <div className="flex items-center gap-1">
          <span
            className={clsx(
              'text-xs font-mono font-semibold',
              getColorProbabilidad(probabilidadOver, true)
            )}
          >
            O {porcentajeOver}%
          </span>
          <span className="text-texto-terciario">/</span>
          <span
            className={clsx(
              'text-xs font-mono font-semibold',
              getColorProbabilidad(probabilidadUnder, false)
            )}
          >
            U {porcentajeUnder}%
          </span>
        </div>
      </div>
    );
  }

  return (
    <div
      className={clsx(
        'p-4 rounded-lg',
        'bg-futurista-oscuro/50 backdrop-blur-sm',
        'border border-neon-cyan/10',
        className
      )}
    >
      {/* Header: Mercado y Línea */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm text-texto-secundario">{etiquetaMercado}</span>
        <span className="text-lg font-mono font-bold text-neon-cyan">{linea}</span>
      </div>

      {/* Probabilidades */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        {/* OVER */}
        <div
          className={clsx(
            'flex flex-col items-center p-3 rounded-lg border transition-all duration-300',
            overDestacado
              ? 'bg-neon-verde/15 border-neon-verde/40 shadow-glow-verde/10'
              : 'bg-futurista-medio/20 border-futurista-medio/30'
          )}
        >
          <div className="flex items-center gap-1 mb-1">
            <TrendingUp
              size={14}
              className={clsx(overDestacado ? 'text-neon-verde' : 'text-texto-terciario')}
            />
            <span
              className={clsx(
                'text-xs font-semibold uppercase',
                overDestacado ? 'text-neon-verde' : 'text-texto-terciario'
              )}
            >
              Over
            </span>
          </div>
          <span
            className={clsx(
              'text-xl font-mono font-bold',
              overDestacado ? 'text-neon-verde' : 'text-texto-secundario'
            )}
          >
            {porcentajeOver}%
          </span>
          {lado === 'OVER' && (
            <span className="text-xs text-neon-verde mt-1">Recomendado</span>
          )}
        </div>

        {/* UNDER */}
        <div
          className={clsx(
            'flex flex-col items-center p-3 rounded-lg border transition-all duration-300',
            underDestacado
              ? 'bg-neon-rojo/15 border-neon-rojo/40 shadow-glow-rojo/10'
              : 'bg-futurista-medio/20 border-futurista-medio/30'
          )}
        >
          <div className="flex items-center gap-1 mb-1">
            <TrendingDown
              size={14}
              className={clsx(underDestacado ? 'text-neon-rojo' : 'text-texto-terciario')}
            />
            <span
              className={clsx(
                'text-xs font-semibold uppercase',
                underDestacado ? 'text-neon-rojo' : 'text-texto-terciario'
              )}
            >
              Under
            </span>
          </div>
          <span
            className={clsx(
              'text-xl font-mono font-bold',
              underDestacado ? 'text-neon-rojo' : 'text-texto-secundario'
            )}
          >
            {porcentajeUnder}%
          </span>
          {lado === 'UNDER' && (
            <span className="text-xs text-neon-rojo mt-1">Recomendado</span>
          )}
        </div>
      </div>

      {/* Barra de probabilidad */}
      {mostrarBarra && (
        <div className="relative h-2 rounded-full bg-neon-rojo/30 overflow-hidden">
          <div
            className="absolute inset-y-0 left-0 bg-gradient-to-r from-neon-verde to-neon-verde/80 rounded-full transition-all duration-500"
            style={{ width: `${probabilidadOver * 100}%` }}
            role="progressbar"
            aria-valuenow={probabilidadOver * 100}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${porcentajeOver}% OVER`}
          />
          {/* Marcador central */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-0.5 h-3 bg-futurista-claro/50" />
        </div>
      )}
    </div>
  );
}
