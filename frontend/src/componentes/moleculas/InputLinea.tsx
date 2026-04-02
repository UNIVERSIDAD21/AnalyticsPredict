/**
 * InputLinea.tsx — Input para la línea de puntos con selector Over/Under
 */

import { TrendingUp, TrendingDown, Target } from 'lucide-react';
import { LadoApuesta } from '../../tipos';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsInputLinea {
  valor: string;
  onChange: (valor: string) => void;
  ladoApuesta?: LadoApuesta;
  onLadoChange?: (lado: LadoApuesta) => void;
  error?: string;
  deshabilitado?: boolean;
  esJuegoCompleto?: boolean;
  unidadLabel?: string;
  periodoLabel?: string;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Input especializado para ingresar la línea de puntos con selector Over/Under
 */
export function InputLinea({
  valor,
  onChange,
  ladoApuesta = 'OVER',
  onLadoChange,
  error,
  deshabilitado = false,
  esJuegoCompleto = false,
  unidadLabel = 'puntos',
  periodoLabel,
}: PropsInputLinea) {
  const placeholder = esJuegoCompleto ? 'Ej: 225.5' : 'Ej: 55.5';

  return (
    <div className="w-full space-y-3">
      {/* Etiqueta */}
      <label className="etiqueta flex items-center gap-2">
        <Target size={14} className="text-neon-cyan" />
        Línea y Predicción
      </label>

      {/* Selector Over/Under */}
      <div className="toggle-over-under">
        <button
          type="button"
          onClick={() => onLadoChange?.('OVER')}
          disabled={deshabilitado}
          className={`flex items-center justify-center gap-2 ${
            ladoApuesta === 'OVER' ? 'activo-over' : ''
          }`}
        >
          <TrendingUp size={18} />
          <span>Over</span>
        </button>
        <button
          type="button"
          onClick={() => onLadoChange?.('UNDER')}
          disabled={deshabilitado}
          className={`flex items-center justify-center gap-2 ${
            ladoApuesta === 'UNDER' ? 'activo-under' : ''
          }`}
        >
          <TrendingDown size={18} />
          <span>Under</span>
        </button>
      </div>

      {/* Input de valor */}
      <div className="relative">
        <input
          type="number"
          step="0.5"
          min="0"
          max="400"
          value={valor}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={deshabilitado}
          className={`input-base text-center text-lg font-mono ${error ? 'input-error' : ''}`}
        />

        {/* Indicador visual del lado */}
        {valor && (
          <div className={`absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 text-xs font-semibold ${
            ladoApuesta === 'OVER' ? 'text-neon-verde' : 'text-neon-rojo'
          }`}>
            {ladoApuesta === 'OVER' ? (
              <>
                <TrendingUp size={14} />
                <span>+</span>
              </>
            ) : (
              <>
                <TrendingDown size={14} />
                <span>-</span>
              </>
            )}
          </div>
        )}
      </div>

      {/* Texto de ayuda */}
      <p className="texto-ayuda text-center">
        {ladoApuesta === 'OVER' ? 'Más de' : 'Menos de'} {valor || '...'} {unidadLabel}
        {periodoLabel ? ` en ${periodoLabel}` : (esJuegoCompleto ? ' en el juego completo' : ' en el periodo')}
      </p>

      {/* Error */}
      {error && (
        <p className="texto-error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
