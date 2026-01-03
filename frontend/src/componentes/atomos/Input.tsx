/**
 * Input.tsx — Componente de input reutilizable
 */

import { InputHTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsInput extends InputHTMLAttributes<HTMLInputElement> {
  /** Etiqueta del campo */
  etiqueta?: string;
  /** Texto de ayuda debajo del input */
  textoAyuda?: string;
  /** Mensaje de error */
  error?: string;
  /** Icono a mostrar al inicio */
  iconoInicio?: React.ReactNode;
  /** Icono a mostrar al final */
  iconoFin?: React.ReactNode;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Input de texto/número con etiqueta, ayuda y errores
 */
export const Input = forwardRef<HTMLInputElement, PropsInput>(
  (
    {
      etiqueta,
      textoAyuda,
      error,
      iconoInicio,
      iconoFin,
      className,
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || `input-${etiqueta?.toLowerCase().replace(/\s+/g, '-')}`;
    const tieneError = Boolean(error);

    return (
      <div className="w-full">
        {/* Etiqueta */}
        {etiqueta && (
          <label htmlFor={inputId} className="etiqueta">
            {etiqueta}
          </label>
        )}

        {/* Contenedor del input */}
        <div className="relative">
          {/* Icono inicio */}
          {iconoInicio && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-nba-gris-400">
              {iconoInicio}
            </div>
          )}

          {/* Input */}
          <input
            ref={ref}
            id={inputId}
            className={clsx(
              'input-base',
              tieneError && 'input-error',
              iconoInicio && 'pl-10',
              iconoFin && 'pr-10',
              className
            )}
            aria-invalid={tieneError}
            aria-describedby={
              tieneError ? `${inputId}-error` : textoAyuda ? `${inputId}-ayuda` : undefined
            }
            {...props}
          />

          {/* Icono fin */}
          {iconoFin && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-nba-gris-400">
              {iconoFin}
            </div>
          )}
        </div>

        {/* Texto de ayuda */}
        {textoAyuda && !tieneError && (
          <p id={`${inputId}-ayuda`} className="texto-ayuda">
            {textoAyuda}
          </p>
        )}

        {/* Mensaje de error */}
        {tieneError && (
          <p id={`${inputId}-error`} className="texto-error" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
