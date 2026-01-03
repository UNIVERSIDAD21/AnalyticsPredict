/**
 * InputCuota.tsx — Input para la cuota decimal con estilo futurista
 */

import { DollarSign } from 'lucide-react';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsInputCuota {
  /** Valor actual */
  valor: string;
  /** Callback cuando cambia el valor */
  onChange: (valor: string) => void;
  /** Mensaje de error */
  error?: string;
  /** Deshabilitado */
  deshabilitado?: boolean;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Input especializado para ingresar la cuota decimal
 */
export function InputCuota({
  valor,
  onChange,
  error,
  deshabilitado = false,
}: PropsInputCuota) {
  return (
    <div className="w-full">
      <label className="etiqueta flex items-center gap-2">
        <DollarSign size={14} className="text-neon-cyan" />
        Cuota (opcional)
      </label>

      <div className="relative">
        <input
          type="number"
          step="0.01"
          min="1.01"
          max="100"
          value={valor}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Ej: 1.85"
          disabled={deshabilitado}
          className={`input-base font-mono ${error ? 'input-error' : ''}`}
        />
      </div>

      <p className="texto-ayuda">
        Cuota decimal para calcular valor esperado (EV)
      </p>

      {error && (
        <p className="texto-error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
