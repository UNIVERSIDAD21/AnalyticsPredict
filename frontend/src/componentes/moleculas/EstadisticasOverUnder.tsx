/**
 * EstadisticasOverUnder.tsx — Panel de estadísticas agregadas OVER/UNDER
 *
 * Muestra record O/U, promedio, racha actual y tendencia.
 */

import { clsx } from 'clsx';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { EstadisticasOverUnder as TipoEstadisticas } from '../../tipos';
import type { Mercado } from '../../tipos/analisis';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsEstadisticasOverUnder {
  /** Estadísticas calculadas */
  estadisticas: TipoEstadisticas;
  /** Mercado seleccionado */
  mercado: Mercado;
  /** Línea de referencia */
  linea: number;
  /** Clase CSS adicional */
  className?: string;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Panel de estadísticas agregadas OVER/UNDER con barra de progreso visual
 */
export function EstadisticasOverUnder({
  estadisticas,
  mercado,
  linea,
  className,
}: PropsEstadisticasOverUnder) {
  const {
    totalPartidos,
    partidosOver,
    partidosUnder,
    porcentajeOver,
    promedioTotal,
    promedioVsLinea,
    rachaActual,
    tendencia,
  } = estadisticas;

  // Nombre del mercado para mostrar
  const nombreMercado = mercado === 'COMPLETO' ? 'Total' : mercado;

  return (
    <div
      className={clsx(
        'grid grid-cols-2 lg:grid-cols-4 gap-3 p-4 rounded-lg',
        'bg-futurista-negro/50 border border-neon-cyan/10',
        className
      )}
    >
      {/* Record Over/Under */}
      <div className="space-y-2">
        <span className="text-xs text-texto-terciario uppercase tracking-wider">
          Record O/U
        </span>
        <div className="flex items-baseline gap-2">
          <span className="text-xl font-mono font-bold text-over-medio">{partidosOver}</span>
          <span className="text-texto-terciario">/</span>
          <span className="text-xl font-mono font-bold text-under-medio">{partidosUnder}</span>
        </div>
        {/* Barra de progreso */}
        <div className="h-1.5 rounded-full bg-under-claro overflow-hidden">
          <div
            className="h-full bg-over-medio transition-all duration-500"
            style={{ width: `${porcentajeOver}%` }}
            role="progressbar"
            aria-valuenow={porcentajeOver}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${porcentajeOver.toFixed(0)}% OVER`}
          />
        </div>
        <span className="text-xs text-neon-cyan font-medium">
          {porcentajeOver.toFixed(0)}% OVER
        </span>
      </div>

      {/* Promedio */}
      <div className="space-y-2">
        <span className="text-xs text-texto-terciario uppercase tracking-wider">
          Promedio {nombreMercado}
        </span>
        <div className="text-xl font-mono font-bold text-texto-principal">
          {promedioTotal.toFixed(1)}
        </div>
        <div
          className={clsx(
            'text-xs font-medium',
            promedioVsLinea > 0 ? 'text-over-medio' : 'text-under-medio'
          )}
        >
          {promedioVsLinea > 0 ? '+' : ''}
          {promedioVsLinea.toFixed(1)} vs línea
        </div>
      </div>

      {/* Racha */}
      <div className="space-y-2">
        <span className="text-xs text-texto-terciario uppercase tracking-wider">
          Racha Actual
        </span>
        <div
          className={clsx(
            'text-xl font-mono font-bold',
            rachaActual.tipo === 'OVER'
              ? 'text-over-medio'
              : rachaActual.tipo === 'UNDER'
              ? 'text-under-medio'
              : 'text-texto-secundario'
          )}
        >
          {rachaActual.cantidad} {rachaActual.tipo}
        </div>
        <span className="text-xs text-texto-terciario">consecutivos</span>
      </div>

      {/* Tendencia */}
      <div className="space-y-2">
        <span className="text-xs text-texto-terciario uppercase tracking-wider">
          Tendencia
        </span>
        <div
          className={clsx(
            'text-xl font-bold flex items-center gap-1',
            tendencia === 'SUBIENDO'
              ? 'text-over-medio'
              : tendencia === 'BAJANDO'
              ? 'text-under-medio'
              : 'text-texto-secundario'
          )}
        >
          {tendencia === 'SUBIENDO' && <TrendingUp className="w-5 h-5" />}
          {tendencia === 'BAJANDO' && <TrendingDown className="w-5 h-5" />}
          {tendencia === 'ESTABLE' && <Minus className="w-5 h-5" />}
          <span className="text-sm font-normal">
            {tendencia === 'SUBIENDO'
              ? 'Subiendo'
              : tendencia === 'BAJANDO'
              ? 'Bajando'
              : 'Estable'}
          </span>
        </div>
        <span className="text-xs text-texto-terciario">Últimos 5 vs anteriores</span>
      </div>
    </div>
  );
}
