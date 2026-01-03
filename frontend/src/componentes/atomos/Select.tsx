/**
 * Select.tsx — Componente de selector reutilizable
 */

import { SelectHTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

export interface OpcionSelect {
  valor: string;
  etiqueta: string;
  deshabilitada?: boolean;
}

interface PropsSelect extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'children'> {
  /** Etiqueta del campo */
  etiqueta?: string;
  /** Opciones del selector */
  opciones: OpcionSelect[];
  /** Texto del placeholder (primera opción vacía) */
  placeholder?: string;
  /** Texto de ayuda debajo del select */
  textoAyuda?: string;
  /** Mensaje de error */
  error?: string;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Selector desplegable con etiqueta, ayuda y errores
 */
export const Select = forwardRef<HTMLSelectElement, PropsSelect>(
  (
    {
      etiqueta,
      opciones,
      placeholder = 'Selecciona una opción',
      textoAyuda,
      error,
      className,
      id,
      ...props
    },
    ref
  ) => {
    const selectId = id || `select-${etiqueta?.toLowerCase().replace(/\s+/g, '-')}`;
    const tieneError = Boolean(error);

    return (
      <div className="w-full">
        {/* Etiqueta */}
        {etiqueta && (
          <label htmlFor={selectId} className="etiqueta">
            {etiqueta}
          </label>
        )}

        {/* Select */}
        <select
          ref={ref}
          id={selectId}
          className={clsx(
            'select-base',
            tieneError && 'input-error',
            className
          )}
          aria-invalid={tieneError}
          aria-describedby={
            tieneError ? `${selectId}-error` : textoAyuda ? `${selectId}-ayuda` : undefined
          }
          {...props}
        >
          {/* Placeholder */}
          <option value="" disabled>
            {placeholder}
          </option>

          {/* Opciones */}
          {opciones.map((opcion) => (
            <option
              key={opcion.valor}
              value={opcion.valor}
              disabled={opcion.deshabilitada}
            >
              {opcion.etiqueta}
            </option>
          ))}
        </select>

        {/* Texto de ayuda */}
        {textoAyuda && !tieneError && (
          <p id={`${selectId}-ayuda`} className="texto-ayuda">
            {textoAyuda}
          </p>
        )}

        {/* Mensaje de error */}
        {tieneError && (
          <p id={`${selectId}-error`} className="texto-error" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';
