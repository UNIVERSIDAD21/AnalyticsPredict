/**
 * InputLinea.tsx — Input para la línea de puntos
 */

import { Input } from '../atomos';
import { Target } from 'lucide-react';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsInputLinea {
  /** Valor actual */
  valor: string;
  /** Callback cuando cambia el valor */
  onChange: (valor: string) => void;
  /** Mensaje de error */
  error?: string;
  /** Deshabilitado */
  deshabilitado?: boolean;
  /** Es para juego completo (cambia el placeholder) */
  esJuegoCompleto?: boolean;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Input especializado para ingresar la línea de puntos
 */
export function InputLinea({
  valor,
  onChange,
  error,
  deshabilitado = false,
  esJuegoCompleto = false,
}: PropsInputLinea) {
  const placeholder = esJuegoCompleto ? 'Ej: 225.5' : 'Ej: 55.5';
  const textoAyuda = esJuegoCompleto
    ? 'Total de puntos esperado en el juego completo'
    : 'Total de puntos esperado en el cuarto';

  return (
    <Input
      etiqueta="Línea"
      type="number"
      step="0.5"
      min="0"
      max="400"
      value={valor}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      textoAyuda={textoAyuda}
      error={error}
      disabled={deshabilitado}
      iconoInicio={<Target size={18} />}
    />
  );
}
