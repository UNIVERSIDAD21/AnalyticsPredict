/**
 * Tarjeta.tsx — Contenedor tipo card
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

const estilosVariante: Record<VarianteTarjeta, string> = {
  normal: 'bg-white shadow-tarjeta',
  elevada: 'bg-white shadow-elevada',
  borde: 'bg-white border border-nba-gris-200',
};

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
 * Tarjeta contenedora con diferentes variantes
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
          'rounded-xl',
          estilosVariante[variante],
          estilosPadding[padding],
          hover && 'transition-shadow duration-200 hover:shadow-tarjeta-hover cursor-pointer',
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
