/**
 * TarjetaProbabilidad.tsx — Visualización de probabilidades Over/Under futurista
 */

import { TrendingUp, TrendingDown } from 'lucide-react';
import { Tarjeta } from '../atomos';
import { LadoApuesta } from '../../tipos';

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
  /** Lado seleccionado por el usuario */
  seleccionUsuario?: LadoApuesta;
}

// ══════════════════════════════════════════════════════════════
// UTILIDADES
// ══════════════════════════════════════════════════════════════

function formatearPorcentaje(valor: number): string {
  return `${(valor * 100).toFixed(1)}%`;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Muestra las probabilidades Over/Under con barra visual futurista
 */
export function TarjetaProbabilidad({
  linea,
  probabilidadOver,
  probabilidadUnder,
  mediaTotal,
  desviacion,
  seleccionUsuario,
}: PropsTarjetaProbabilidad) {
  const esOverFavorito = probabilidadOver > probabilidadUnder;
  const porcentajeOver = probabilidadOver * 100;

  return (
    <Tarjeta className="animate-deslizar-arriba">
      {/* Encabezado */}
      <div className="text-center mb-6">
        <span className="text-xs text-texto-secundario uppercase tracking-widest">
          Línea Analizada
        </span>
        <div className="text-5xl font-futurista font-bold text-neon-cyan mt-2 texto-glow-cyan">
          {linea.toFixed(1)}
        </div>
        <span className="text-sm text-texto-terciario">puntos</span>
      </div>

      {/* Barra de probabilidad futurista */}
      <div className="relative h-14 rounded-xl overflow-hidden bg-futurista-oscuro border border-neon-cyan/20 mb-6">
        {/* Lado Over */}
        <div
          className="absolute left-0 top-0 h-full transition-all duration-1000 ease-out"
          style={{
            width: `${porcentajeOver}%`,
            background: 'linear-gradient(90deg, rgba(0, 255, 136, 0.3) 0%, rgba(0, 255, 136, 0.6) 100%)',
          }}
        />

        {/* Lado Under */}
        <div
          className="absolute right-0 top-0 h-full transition-all duration-1000 ease-out"
          style={{
            width: `${100 - porcentajeOver}%`,
            background: 'linear-gradient(90deg, rgba(255, 0, 85, 0.6) 0%, rgba(255, 0, 85, 0.3) 100%)',
          }}
        />

        {/* Indicador central */}
        <div
          className="absolute top-0 w-1 h-full bg-texto-principal shadow-lg z-10"
          style={{ left: `${porcentajeOver}%`, transform: 'translateX(-50%)' }}
        />

        {/* Labels en la barra */}
        <div className="absolute inset-0 flex items-center justify-between px-4 z-20">
          <div className={`flex items-center gap-2 ${esOverFavorito ? 'text-neon-verde font-bold texto-glow-verde' : 'text-texto-secundario'}`}>
            <TrendingUp size={20} />
            <span className="font-futurista tracking-wider">OVER</span>
          </div>
          <div className={`flex items-center gap-2 ${!esOverFavorito ? 'text-neon-rojo font-bold texto-glow-rojo' : 'text-texto-secundario'}`}>
            <span className="font-futurista tracking-wider">UNDER</span>
            <TrendingDown size={20} />
          </div>
        </div>
      </div>

      {/* Probabilidades numéricas */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* Over */}
        <div className={`text-center p-4 rounded-xl border transition-all duration-300 ${
          esOverFavorito
            ? 'bg-gradiente-over border-neon-verde/30'
            : 'bg-futurista-oscuro/50 border-neon-cyan/10'
        } ${seleccionUsuario === 'OVER' ? 'ring-2 ring-neon-verde/50' : ''}`}>
          <div className={`text-3xl font-mono font-bold ${esOverFavorito ? 'text-neon-verde texto-glow-verde' : 'text-texto-secundario'}`}>
            {formatearPorcentaje(probabilidadOver)}
          </div>
          <div className="flex items-center justify-center gap-1 mt-2 text-sm text-texto-secundario">
            <TrendingUp size={14} />
            <span>Over {linea.toFixed(1)}</span>
          </div>
          {seleccionUsuario === 'OVER' && (
            <div className="mt-2 text-xs text-neon-verde">Tu predicción</div>
          )}
        </div>

        {/* Under */}
        <div className={`text-center p-4 rounded-xl border transition-all duration-300 ${
          !esOverFavorito
            ? 'bg-gradiente-under border-neon-rojo/30'
            : 'bg-futurista-oscuro/50 border-neon-cyan/10'
        } ${seleccionUsuario === 'UNDER' ? 'ring-2 ring-neon-rojo/50' : ''}`}>
          <div className={`text-3xl font-mono font-bold ${!esOverFavorito ? 'text-neon-rojo texto-glow-rojo' : 'text-texto-secundario'}`}>
            {formatearPorcentaje(probabilidadUnder)}
          </div>
          <div className="flex items-center justify-center gap-1 mt-2 text-sm text-texto-secundario">
            <TrendingDown size={14} />
            <span>Under {linea.toFixed(1)}</span>
          </div>
          {seleccionUsuario === 'UNDER' && (
            <div className="mt-2 text-xs text-neon-rojo">Tu predicción</div>
          )}
        </div>
      </div>

      {/* Estadísticas adicionales */}
      <div className="border-t border-neon-cyan/10 pt-4">
        <div className="grid grid-cols-2 gap-4 text-center">
          <div className="p-3 rounded-lg bg-futurista-oscuro/30">
            <div className="text-xs text-texto-terciario uppercase tracking-wider mb-1">
              Media Predicha
            </div>
            <div className="text-xl font-mono font-semibold text-neon-cyan">
              {mediaTotal.toFixed(1)} <span className="text-xs text-texto-secundario">pts</span>
            </div>
          </div>
          <div className="p-3 rounded-lg bg-futurista-oscuro/30">
            <div className="text-xs text-texto-terciario uppercase tracking-wider mb-1">
              Desviación
            </div>
            <div className="text-xl font-mono font-semibold text-neon-magenta">
              ±{desviacion.toFixed(1)} <span className="text-xs text-texto-secundario">pts</span>
            </div>
          </div>
        </div>
      </div>
    </Tarjeta>
  );
}
