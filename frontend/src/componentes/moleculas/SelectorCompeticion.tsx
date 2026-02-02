/**
 * SelectorCompeticion.tsx — Selector de competiciones de fútbol
 *
 * Dropdown futurista para seleccionar competiciones con soporte para logos.
 */

import { useMemo } from 'react';
import { Trophy } from 'lucide-react';
import { clsx } from 'clsx';
import { Competicion } from '../../tipos/futbol';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsSelectorCompeticion {
  /** Lista de competiciones disponibles */
  competiciones: Competicion[];
  /** ID de la competición seleccionada */
  valor: string;
  /** Callback cuando cambia la selección */
  onChange: (competicionId: string) => void;
  /** Etiqueta del selector */
  etiqueta?: string;
  /** Placeholder */
  placeholder?: string;
  /** Mensaje de error */
  error?: string;
  /** Deshabilitado */
  deshabilitado?: boolean;
  /** Texto de ayuda */
  textoAyuda?: string;
  /** Clase CSS adicional */
  className?: string;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Selector especializado para competiciones de fútbol
 * con soporte para logos y diseño glassmorphism futurista.
 */
export function SelectorCompeticion({
  competiciones,
  valor,
  onChange,
  etiqueta = 'Competición',
  placeholder = 'Selecciona una competición',
  error,
  deshabilitado = false,
  textoAyuda,
  className,
}: PropsSelectorCompeticion) {
  // Encontrar la competición seleccionada
  const competicionSeleccionada = useMemo(() => {
    return competiciones.find((c) => c.id === valor);
  }, [competiciones, valor]);

  // Agrupar competiciones por país
  const competicionesAgrupadas = useMemo(() => {
    const grupos: Record<string, Competicion[]> = {};
    competiciones.forEach((comp) => {
      if (!grupos[comp.pais]) {
        grupos[comp.pais] = [];
      }
      grupos[comp.pais].push(comp);
    });
    // Ordenar por prioridad dentro de cada grupo
    Object.keys(grupos).forEach((pais) => {
      grupos[pais].sort((a, b) => a.prioridad - b.prioridad);
    });
    return grupos;
  }, [competiciones]);

  const selectId = `select-competicion-${etiqueta?.toLowerCase().replace(/\s+/g, '-')}`;
  const tieneError = Boolean(error);

  return (
    <div className={clsx('w-full', className)}>
      {/* Etiqueta */}
      {etiqueta && (
        <label htmlFor={selectId} className="etiqueta flex items-center gap-2">
          <Trophy size={14} className="text-neon-cyan" />
          {etiqueta}
        </label>
      )}

      {/* Contenedor con glassmorphism */}
      <div className="relative">
        {/* Logo de la competición seleccionada */}
        {competicionSeleccionada?.logoUrl && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 w-6 h-6 flex items-center justify-center z-10">
            <img
              src={competicionSeleccionada.logoUrl}
              alt={competicionSeleccionada.nombre}
              className="w-5 h-5 object-contain"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
          </div>
        )}

        {/* Select */}
        <select
          id={selectId}
          value={valor}
          onChange={(e) => onChange(e.target.value)}
          disabled={deshabilitado}
          className={clsx(
            'select-base',
            competicionSeleccionada?.logoUrl && 'pl-11',
            tieneError && 'input-error',
            'bg-futurista-oscuro/80 backdrop-blur-sm',
            'border border-neon-cyan/20',
            'hover:border-neon-cyan/40 hover:shadow-glow-cyan/10',
            'focus:border-neon-cyan focus:shadow-glow-cyan/20',
            'transition-all duration-300'
          )}
          aria-invalid={tieneError}
          aria-describedby={
            tieneError ? `${selectId}-error` : textoAyuda ? `${selectId}-ayuda` : undefined
          }
        >
          {/* Placeholder */}
          <option value="" disabled>
            {placeholder}
          </option>

          {/* Opciones agrupadas por país */}
          {Object.entries(competicionesAgrupadas).map(([pais, comps]) => (
            <optgroup key={pais} label={pais}>
              {comps.map((comp) => (
                <option
                  key={comp.id}
                  value={comp.id}
                  disabled={!comp.activa}
                >
                  {comp.nombre}
                </option>
              ))}
            </optgroup>
          ))}
        </select>

        {/* Indicador de tipo de competición */}
        {competicionSeleccionada && (
          <div className="absolute right-10 top-1/2 -translate-y-1/2 pointer-events-none">
            <span
              className={clsx(
                'text-xs px-2 py-0.5 rounded-full',
                competicionSeleccionada.tipo === 'liga' &&
                  'bg-neon-verde/10 text-neon-verde border border-neon-verde/30',
                competicionSeleccionada.tipo === 'copa_nacional' &&
                  'bg-neon-amarillo/10 text-neon-amarillo border border-neon-amarillo/30',
                competicionSeleccionada.tipo === 'continental' &&
                  'bg-neon-cyan/10 text-neon-cyan border border-neon-cyan/30'
              )}
            >
              {competicionSeleccionada.tipo === 'liga'
                ? 'Liga'
                : competicionSeleccionada.tipo === 'copa_nacional'
                ? 'Copa'
                : 'Continental'}
            </span>
          </div>
        )}
      </div>

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
