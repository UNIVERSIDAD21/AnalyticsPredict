/**
 * TarjetaProbabilidad.tsx — Visualización de probabilidades Over/Under
 */

import { TrendingUp, TrendingDown } from 'lucide-react';
import { Tarjeta } from '../atomos';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsTarjetaProbabilidad {
  /** Línea analizada */
  linea: number;
  /** Probabilidad de Over (0-1) */
  probabilidadOver: number;
  /** Probabilidad de Under (0-1) */
  probabilidadUnder: number;
  /** Media total predicha */
  mediaTotal: number;
  /** Desviación estándar */
  desviacion: number;
}

// ══════════════════════════════════════════════════════════════
// UTILIDADES
// ══════════════════════════════════════════════════════════════

function formatearPorcentaje(valor: number): string {
  return `${(valor * 100).toFixed(1)}%`;
}

function obtenerColorBarra(probabilidad: number): string {
  if (probabilidad >= 0.6) return 'bg-over-medio';
  if (probabilidad >= 0.55) return 'bg-over-medio/70';
  if (probabilidad >= 0.5) return 'bg-nba-gris-400';
  if (probabilidad >= 0.45) return 'bg-under-medio/70';
  return 'bg-under-medio';
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Muestra las probabilidades Over/Under con barra visual
 */
export function TarjetaProbabilidad({
  linea,
  probabilidadOver,
  probabilidadUnder,
  mediaTotal,
  desviacion,
}: PropsTarjetaProbabilidad) {
  const esOverFavorito = probabilidadOver > probabilidadUnder;
  const porcentajeOver = probabilidadOver * 100;
  const colorBarra = obtenerColorBarra(probabilidadOver);

  return (
    <Tarjeta className="animate-deslizar-arriba">
      {/* Encabezado */}
      <div className="text-center mb-6">
        <span className="text-sm text-nba-gris-500 uppercase tracking-wide">
          Línea Analizada
        </span>
        <div className="text-4xl font-bold text-nba-gris-900 mt-1">
          {linea.toFixed(1)}
        </div>
      </div>

      {/* Barra de probabilidad */}
      <div className="relative h-12 rounded-full overflow-hidden bg-under-claro mb-4">
        {/* Lado Over */}
        <div
          className={`absolute left-0 top-0 h-full transition-all duration-500 ${colorBarra}`}
          style={{ width: `${porcentajeOver}%` }}
        />

        {/* Indicador central */}
        <div
          className="absolute top-0 w-1 h-full bg-white shadow-md"
          style={{ left: `${porcentajeOver}%`, transform: 'translateX(-50%)' }}
        />

        {/* Labels en la barra */}
        <div className="absolute inset-0 flex items-center justify-between px-4">
          <div className={`flex items-center gap-1 ${esOverFavorito ? 'text-white font-bold' : 'text-over-oscuro'}`}>
            <TrendingUp size={18} />
            <span>OVER</span>
          </div>
          <div className={`flex items-center gap-1 ${!esOverFavorito ? 'text-white font-bold' : 'text-under-oscuro'}`}>
            <span>UNDER</span>
            <TrendingDown size={18} />
          </div>
        </div>
      </div>

      {/* Probabilidades numéricas */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className={`text-center p-4 rounded-lg ${esOverFavorito ? 'bg-over-claro' : 'bg-nba-gris-100'}`}>
          <div className={`text-3xl font-bold ${esOverFavorito ? 'text-over-oscuro' : 'text-nba-gris-600'}`}>
            {formatearPorcentaje(probabilidadOver)}
          </div>
          <div className="text-sm text-nba-gris-600 mt-1">Over {linea.toFixed(1)}</div>
        </div>

        <div className={`text-center p-4 rounded-lg ${!esOverFavorito ? 'bg-under-claro' : 'bg-nba-gris-100'}`}>
          <div className={`text-3xl font-bold ${!esOverFavorito ? 'text-under-oscuro' : 'text-nba-gris-600'}`}>
            {formatearPorcentaje(probabilidadUnder)}
          </div>
          <div className="text-sm text-nba-gris-600 mt-1">Under {linea.toFixed(1)}</div>
        </div>
      </div>

      {/* Estadísticas adicionales */}
      <div className="border-t border-nba-gris-200 pt-4">
        <div className="grid grid-cols-2 gap-4 text-center">
          <div>
            <div className="text-sm text-nba-gris-500">Media Predicha</div>
            <div className="text-xl font-semibold text-nba-gris-900">
              {mediaTotal.toFixed(1)} pts
            </div>
          </div>
          <div>
            <div className="text-sm text-nba-gris-500">Desviación</div>
            <div className="text-xl font-semibold text-nba-gris-900">
              ±{desviacion.toFixed(1)} pts
            </div>
          </div>
        </div>
      </div>
    </Tarjeta>
  );
}
