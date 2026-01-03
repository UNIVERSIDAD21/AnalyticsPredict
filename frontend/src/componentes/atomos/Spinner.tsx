/**
 * Spinner.tsx — Indicador de carga
 */

import { clsx } from 'clsx';
import { Loader2 } from 'lucide-react';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

type TamanoSpinner = 'sm' | 'md' | 'lg' | 'xl';

interface PropsSpinner {
  /** Tamaño del spinner */
  tamano?: TamanoSpinner;
  /** Texto a mostrar junto al spinner */
  texto?: string;
  /** Centrar en el contenedor */
  centrado?: boolean;
  /** Clases adicionales */
  className?: string;
}

// ══════════════════════════════════════════════════════════════
// ESTILOS
// ══════════════════════════════════════════════════════════════

const tamanos: Record<TamanoSpinner, number> = {
  sm: 16,
  md: 24,
  lg: 32,
  xl: 48,
};

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Indicador de carga animado
 */
export function Spinner({
  tamano = 'md',
  texto,
  centrado = false,
  className,
}: PropsSpinner) {
  return (
    <div
      className={clsx(
        'flex items-center gap-3',
        centrado && 'justify-center',
        className
      )}
      role="status"
      aria-label={texto || 'Cargando...'}
    >
      <Loader2
        className="animate-spin text-nba-azul"
        size={tamanos[tamano]}
      />
      {texto && (
        <span className="text-nba-gris-600">{texto}</span>
      )}
    </div>
  );
}
