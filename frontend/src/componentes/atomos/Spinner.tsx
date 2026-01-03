/**
 * Spinner.tsx — Indicador de carga futurista
 */

import { clsx } from 'clsx';

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

const tamanos: Record<TamanoSpinner, { size: number; border: number }> = {
  sm: { size: 20, border: 2 },
  md: { size: 32, border: 3 },
  lg: { size: 48, border: 4 },
  xl: { size: 64, border: 5 },
};

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Indicador de carga animado con estilo neón
 */
export function Spinner({
  tamano = 'md',
  texto,
  centrado = false,
  className,
}: PropsSpinner) {
  const config = tamanos[tamano];

  return (
    <div
      className={clsx(
        'flex items-center gap-3',
        centrado && 'justify-center flex-col',
        className
      )}
      role="status"
      aria-label={texto || 'Cargando...'}
    >
      {/* Spinner con efecto neón */}
      <div
        className="relative"
        style={{ width: config.size, height: config.size }}
      >
        {/* Anillo exterior */}
        <div
          className="absolute inset-0 rounded-full animate-spin"
          style={{
            border: `${config.border}px solid transparent`,
            borderTopColor: '#00f5ff',
            borderRightColor: '#00f5ff',
            boxShadow: '0 0 15px rgba(0, 245, 255, 0.3)',
          }}
        />
        {/* Anillo interior */}
        <div
          className="absolute inset-1 rounded-full animate-spin"
          style={{
            border: `${config.border - 1}px solid transparent`,
            borderBottomColor: '#ff00ff',
            borderLeftColor: '#ff00ff',
            animationDirection: 'reverse',
            animationDuration: '0.8s',
          }}
        />
        {/* Punto central */}
        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-neon-cyan animate-pulse"
          style={{
            width: config.size / 4,
            height: config.size / 4,
            boxShadow: '0 0 10px rgba(0, 245, 255, 0.5)',
          }}
        />
      </div>

      {texto && (
        <span className="text-texto-secundario text-sm">{texto}</span>
      )}
    </div>
  );
}
