/**
 * PanelHistorialEquipo.tsx — Panel completo de historial para un equipo
 *
 * Incluye filtros, estadísticas agregadas y tabla de partidos.
 * Calcula datos dinámicamente según el mercado y línea seleccionados.
 */

import { useState } from 'react';
import { clsx } from 'clsx';
import type { CantidadPartidos, FiltroUbicacion } from '../../tipos';
import type { Mercado } from '../../tipos/analisis';
import { useHistorialEquipoExtendido } from '../../hooks/useHistorialEquipoExtendido';
import { FiltrosHistorial, TablaPartidosHistorial, EstadisticasOverUnder } from '../moleculas';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsPanelHistorialEquipo {
  /** ID del equipo */
  equipoId: string;
  /** Nombre completo del equipo */
  equipoNombre: string;
  /** Abreviatura del equipo */
  equipoAbr: string;
  /** Mercado seleccionado en el análisis */
  mercado: Mercado;
  /** Línea ingresada en el análisis */
  linea: number;
  /** Clase CSS adicional */
  className?: string;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Panel de historial completo para un equipo individual
 */
export function PanelHistorialEquipo({
  equipoId,
  equipoNombre,
  equipoAbr,
  mercado,
  linea,
  className,
}: PropsPanelHistorialEquipo) {
  // Estado de filtros locales
  const [cantidad, setCantidad] = useState<CantidadPartidos>(10);
  const [ubicacion, setUbicacion] = useState<FiltroUbicacion>('TODOS');

  // Hook para obtener datos con filtros
  const { partidos, estadisticas, cargando, error } = useHistorialEquipoExtendido(equipoId, {
    cantidad,
    ubicacion,
    mercado,
    linea,
  });

  return (
    <div className={clsx('space-y-4', className)}>
      {/* Header del equipo */}
      <div className="flex items-center gap-3">
        <span className="text-2xl" aria-hidden="true">
          🏀
        </span>
        <div>
          <h4 className="font-futurista text-lg text-texto-principal tracking-wide">
            {equipoNombre}
          </h4>
          <span className="text-xs text-texto-terciario uppercase tracking-wider">
            Historial de partidos
          </span>
        </div>
      </div>

      {/* Filtros */}
      <FiltrosHistorial
        cantidad={cantidad}
        ubicacion={ubicacion}
        mercadoActivo={mercado}
        onCambiarCantidad={setCantidad}
        onCambiarUbicacion={setUbicacion}
      />

      {/* Estadísticas agregadas */}
      {!cargando && estadisticas && (
        <EstadisticasOverUnder estadisticas={estadisticas} mercado={mercado} linea={linea} />
      )}

      {/* Tabla de partidos */}
      <TablaPartidosHistorial
        partidos={partidos}
        equipoAbr={equipoAbr}
        linea={linea}
        mercado={mercado}
        cargando={cargando}
      />

      {/* Error */}
      {error && (
        <div className="p-3 rounded-lg bg-error-500/10 border border-error-500/30 text-error-500 text-sm">
          {error}
        </div>
      )}
    </div>
  );
}
