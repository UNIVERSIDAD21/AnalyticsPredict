/**
 * InputCuota.tsx — Input para la cuota decimal
 */

import { Input } from '../atomos';
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
    <Input
      etiqueta="Cuota (opcional)"
      type="number"
      step="0.01"
      min="1.01"
      max="100"
      value={valor}
      onChange={(e) => onChange(e.target.value)}
      placeholder="Ej: 1.85"
      textoAyuda="Cuota decimal para calcular valor esperado (EV)"
      error={error}
      disabled={deshabilitado}
      iconoInicio={<DollarSign size={18} />}
    />
  );
}
