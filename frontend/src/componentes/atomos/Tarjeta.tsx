/**
 * Tarjeta.tsx — Contenedor glassmorphism futurista
 */

import { HTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

type VarianteTarjeta = 'normal' | 'elevada' | 'borde';

interface PropsTarjeta extends HTMLAttributes<HTMLDivElement> {
  /** Variante visual */
  variante?: VarianteTarjeta;
  /** Padding interno */
  padding?: 'none' | 'sm' | 'md' | 'lg';
  /** Efecto hover */
  hover?: boolean;
}

// ══════════════════════════════════════════════════════════════
// ESTILOS
// ══════════════════════════════════════════════════════════════

const estilosPadding: Record<string, string> = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Tarjeta contenedora con efecto glassmorphism futurista
 */
export const Tarjeta = forwardRef<HTMLDivElement, PropsTarjeta>(
  (
    {
      variante = 'normal',
      padding = 'md',
      hover = false,
      className,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <div
        ref={ref}
        className={clsx(
          'tarjeta',
          estilosPadding[padding],
          hover && 'tarjeta-hover cursor-pointer',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Tarjeta.displayName = 'Tarjeta';
