/**
 * SelectorEquipo.tsx — Selector de equipo NBA
 */

import { useMemo } from 'react';
import { Select, OpcionSelect } from '../atomos';
import { Equipo } from '../../tipos';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsSelectorEquipo {
  /** Etiqueta del selector */
  etiqueta: string;
  /** Lista de equipos disponibles */
  equipos: Equipo[];
  /** Valor seleccionado (nombre del equipo en minúsculas) */
  valor: string;
  /** Callback cuando cambia la selección */
  onChange: (valor: string) => void;
  /** Equipo a excluir (para no seleccionar el mismo dos veces) */
  equipoExcluido?: string;
  /** Mensaje de error */
  error?: string;
  /** Deshabilitado */
  deshabilitado?: boolean;
  /** Placeholder */
  placeholder?: string;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Selector especializado para equipos NBA
 */
export function SelectorEquipo({
  etiqueta,
  equipos,
  valor,
  onChange,
  equipoExcluido,
  error,
  deshabilitado = false,
  placeholder = 'Selecciona un equipo',
}: PropsSelectorEquipo) {
  // Convertir equipos a opciones del select
  const opciones = useMemo<OpcionSelect[]>(() => {
    return equipos.map((equipo) => ({
      valor: equipo.nombre.toLowerCase(),
      etiqueta: `${equipo.nombre} (${equipo.abreviatura})`,
      deshabilitada: equipo.nombre.toLowerCase() === equipoExcluido?.toLowerCase(),
    }));
  }, [equipos, equipoExcluido]);

  return (
    <Select
      etiqueta={etiqueta}
      opciones={opciones}
      value={valor}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      error={error}
      disabled={deshabilitado}
    />
  );
}
