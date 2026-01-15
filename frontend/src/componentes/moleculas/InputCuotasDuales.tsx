/**
 * InputCuotasDuales.tsx — Input dual para cuotas Over/Under con estilo futurista
 *
 * Permite ingresar ambas cuotas para de-vig exacto, o solo una para de-vig estimado.
 * El lado seleccionado se resalta visualmente para guiar al usuario.
 */

import { DollarSign, TrendingUp, TrendingDown, Info } from 'lucide-react';
import { LadoApuesta } from '../../tipos';
import { esCuotaValida } from '../../utilidades/validadores';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsInputCuotasDuales {
  /** Valor actual de la cuota Over */
  cuotaOver: string;
  /** Valor actual de la cuota Under */
  cuotaUnder: string;
  /** Callback cuando cambia la cuota Over */
  onCuotaOverChange: (valor: string) => void;
  /** Callback cuando cambia la cuota Under */
  onCuotaUnderChange: (valor: string) => void;
  /** Lado de apuesta seleccionado (para resaltar el input correspondiente) */
  ladoSeleccionado: LadoApuesta;
  /** Deshabilitado */
  deshabilitado?: boolean;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Input dual para cuotas Over/Under con indicadores de de-vig
 */
export function InputCuotasDuales({
  cuotaOver,
  cuotaUnder,
  onCuotaOverChange,
  onCuotaUnderChange,
  ladoSeleccionado,
  deshabilitado = false,
}: PropsInputCuotasDuales) {
  // Determinar estado de cada cuota
  const tieneOver = cuotaOver.trim() !== '';
  const tieneUnder = cuotaUnder.trim() !== '';
  const overValida = !tieneOver || esCuotaValida(cuotaOver);
  const underValida = !tieneUnder || esCuotaValida(cuotaUnder);
  const ambasCuotas = tieneOver && tieneUnder && overValida && underValida;
  const unaCuota = (tieneOver && overValida) !== (tieneUnder && underValida);

  // Determinar si el usuario llenó solo la cuota del lado opuesto (error UX)
  const soloLadoOpuesto =
    (ladoSeleccionado === 'OVER' && tieneUnder && !tieneOver) ||
    (ladoSeleccionado === 'UNDER' && tieneOver && !tieneUnder);

  return (
    <div className="w-full space-y-3">
      {/* Etiqueta principal */}
      <label className="etiqueta flex items-center gap-2">
        <DollarSign size={14} className="text-neon-cyan" />
        Cuotas del mercado (opcional)
      </label>

      {/* Contenedor de inputs duales */}
      <div className="grid grid-cols-2 gap-3">
        {/* Input Cuota Over */}
        <div className="space-y-1">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp
              size={14}
              className={ladoSeleccionado === 'OVER' ? 'text-neon-verde' : 'text-texto-terciario'}
            />
            <span
              className={`text-xs font-semibold uppercase tracking-wider ${
                ladoSeleccionado === 'OVER' ? 'text-neon-verde' : 'text-texto-terciario'
              }`}
            >
              Cuota Over
            </span>
          </div>
          <div className="relative">
            <input
              type="number"
              step="0.01"
              min="1.01"
              max="100"
              value={cuotaOver}
              onChange={(e) => onCuotaOverChange(e.target.value)}
              placeholder="Ej: 1.85"
              disabled={deshabilitado}
              className={`input-base font-mono text-center ${
                !overValida ? 'input-error' : ''
              } ${
                ladoSeleccionado === 'OVER' && tieneOver && overValida
                  ? 'border-neon-verde/50 shadow-[0_0_10px_rgba(0,255,136,0.15)]'
                  : ''
              }`}
            />
            {ladoSeleccionado === 'OVER' && (
              <div className="absolute right-2 top-1/2 -translate-y-1/2">
                <div className="w-2 h-2 rounded-full bg-neon-verde animate-pulse" />
              </div>
            )}
          </div>
          {!overValida && tieneOver && (
            <p className="texto-error text-xs">Cuota inválida (&gt;1)</p>
          )}
        </div>

        {/* Input Cuota Under */}
        <div className="space-y-1">
          <div className="flex items-center gap-2 mb-1">
            <TrendingDown
              size={14}
              className={ladoSeleccionado === 'UNDER' ? 'text-neon-rojo' : 'text-texto-terciario'}
            />
            <span
              className={`text-xs font-semibold uppercase tracking-wider ${
                ladoSeleccionado === 'UNDER' ? 'text-neon-rojo' : 'text-texto-terciario'
              }`}
            >
              Cuota Under
            </span>
          </div>
          <div className="relative">
            <input
              type="number"
              step="0.01"
              min="1.01"
              max="100"
              value={cuotaUnder}
              onChange={(e) => onCuotaUnderChange(e.target.value)}
              placeholder="Ej: 1.95"
              disabled={deshabilitado}
              className={`input-base font-mono text-center ${
                !underValida ? 'input-error' : ''
              } ${
                ladoSeleccionado === 'UNDER' && tieneUnder && underValida
                  ? 'border-neon-rojo/50 shadow-[0_0_10px_rgba(255,0,85,0.15)]'
                  : ''
              }`}
            />
            {ladoSeleccionado === 'UNDER' && (
              <div className="absolute right-2 top-1/2 -translate-y-1/2">
                <div className="w-2 h-2 rounded-full bg-neon-rojo animate-pulse" />
              </div>
            )}
          </div>
          {!underValida && tieneUnder && (
            <p className="texto-error text-xs">Cuota inválida (&gt;1)</p>
          )}
        </div>
      </div>

      {/* Indicador de modo de-vig */}
      <div className="flex items-start gap-2 p-3 rounded-lg bg-futurista-oscuro/50 border border-neon-cyan/10">
        <Info size={14} className="text-neon-cyan flex-shrink-0 mt-0.5" />
        <div className="text-xs">
          {ambasCuotas ? (
            <p className="text-neon-verde font-semibold">
              De-vig exacto — Con ambas cuotas se calcula el overround real
            </p>
          ) : unaCuota ? (
            <p className="text-neon-amarillo font-semibold">
              De-vig estimado — Agrega la cuota del lado opuesto para precisión exacta
            </p>
          ) : (
            <p className="text-texto-secundario">
              Sin cuotas — Solo probabilidades, sin cálculo de EV
            </p>
          )}
        </div>
      </div>

      {/* Error: solo cuota del lado opuesto */}
      {soloLadoOpuesto && (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-neon-rojo/10 border border-neon-rojo/30">
          <TrendingDown size={14} className="text-neon-rojo flex-shrink-0 mt-0.5" />
          <p className="text-xs text-neon-rojo">
            Ingresaste cuota del lado contrario. Completa la cuota{' '}
            <span className="font-bold">{ladoSeleccionado}</span> o cambia el lado de apuesta.
          </p>
        </div>
      )}
    </div>
  );
}
