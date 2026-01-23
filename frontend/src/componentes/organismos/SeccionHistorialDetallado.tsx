/**
 * SeccionHistorialDetallado.tsx — Sección expandible con historial de ambos equipos
 *
 * Contenedor principal que muestra los paneles de historial del equipo local
 * y visitante lado a lado en desktop, apilados en móvil.
 */

import { useState } from 'react';
import { ChevronDown, ChevronUp, History } from 'lucide-react';
import { clsx } from 'clsx';
import { Tarjeta } from '../atomos';
import { PanelHistorialEquipo } from './PanelHistorialEquipo';
import type { Mercado } from '../../tipos/analisis';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsSeccionHistorialDetallado {
  /** ID del equipo local */
  equipoLocalId: string;
  /** Nombre completo del equipo local */
  equipoLocalNombre: string;
  /** Abreviatura del equipo local */
  equipoLocalAbr: string;
  /** ID del equipo visitante */
  equipoVisitanteId: string;
  /** Nombre completo del equipo visitante */
  equipoVisitanteNombre: string;
  /** Abreviatura del equipo visitante */
  equipoVisitanteAbr: string;
  /** Mercado seleccionado en el análisis */
  mercado: Mercado;
  /** Línea ingresada en el análisis */
  linea: number;
  /** Iniciar expandido o colapsado */
  inicialmenteExpandido?: boolean;
  /** Clase CSS adicional */
  className?: string;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Sección de historial detallado con paneles para ambos equipos
 */
export function SeccionHistorialDetallado({
  equipoLocalId,
  equipoLocalNombre,
  equipoLocalAbr,
  equipoVisitanteId,
  equipoVisitanteNombre,
  equipoVisitanteAbr,
  mercado,
  linea,
  inicialmenteExpandido = false,
  className,
}: PropsSeccionHistorialDetallado) {
  const [expandido, setExpandido] = useState(inicialmenteExpandido);

  // Nombre del mercado para mostrar
  const nombreMercado = mercado === 'COMPLETO' ? 'Total' : mercado;

  return (
    <Tarjeta className={clsx('space-y-4', className)} padding="md">
      {/* Header colapsable */}
      <button
        type="button"
        onClick={() => setExpandido(!expandido)}
        className="w-full flex items-center justify-between gap-2 group"
        aria-expanded={expandido}
        aria-controls="contenido-historial-detallado"
      >
        <div className="flex items-center gap-2 flex-wrap">
          <History className="w-5 h-5 text-neon-cyan" />
          <h3 className="text-lg font-futurista text-texto-principal tracking-wide">
            Historial Detallado
          </h3>
          <span
            className="px-2 py-0.5 text-xs font-mono rounded bg-neon-cyan/10
                        text-neon-cyan border border-neon-cyan/30"
          >
            {nombreMercado} • Línea {linea}
          </span>
        </div>

        {expandido ? (
          <ChevronUp className="w-5 h-5 text-texto-terciario group-hover:text-neon-cyan transition-colors flex-shrink-0" />
        ) : (
          <ChevronDown className="w-5 h-5 text-texto-terciario group-hover:text-neon-cyan transition-colors flex-shrink-0" />
        )}
      </button>

      {/* Contenido expandible */}
      {expandido && (
        <div
          id="contenido-historial-detallado"
          className="relative grid grid-cols-1 lg:grid-cols-2 gap-6 pt-4 border-t border-neon-cyan/10"
        >
          {/* Panel Equipo Local */}
          <PanelHistorialEquipo
            equipoId={equipoLocalId}
            equipoNombre={equipoLocalNombre}
            equipoAbr={equipoLocalAbr}
            mercado={mercado}
            linea={linea}
          />

          {/* Divisor vertical (solo desktop) */}
          <div
            className="hidden lg:block absolute left-1/2 top-4 bottom-0 w-px bg-neon-cyan/10 -translate-x-1/2"
            aria-hidden="true"
          />

          {/* Panel Equipo Visitante */}
          <PanelHistorialEquipo
            equipoId={equipoVisitanteId}
            equipoNombre={equipoVisitanteNombre}
            equipoAbr={equipoVisitanteAbr}
            mercado={mercado}
            linea={linea}
          />
        </div>
      )}
    </Tarjeta>
  );
}
