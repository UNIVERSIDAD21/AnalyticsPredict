/**
 * usePartidosFutbol.ts — Hook para manejar la carga de partidos de fútbol
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import type { PartidoFutbolResumen, FiltrosPartidos } from '../tipos/futbol';
import {
  obtenerPartidosHoy,
  obtenerPartidosProximos,
  obtenerPartidosRecientes,
} from '../servicios/futbol';

type EstadoPeticion = 'inactivo' | 'cargando' | 'exito' | 'error';

interface RetornoUsePartidosFutbol {
  /** Lista de partidos */
  partidos: PartidoFutbolResumen[];
  /** Indica si está cargando */
  cargando: boolean;
  /** Mensaje de error si ocurrió */
  error: string | null;
  /** Recargar los partidos */
  recargar: () => void;
  /** Filtros actuales */
  filtros: FiltrosPartidos;
  /** Actualizar filtros */
  setFiltros: (filtros: FiltrosPartidos | ((prev: FiltrosPartidos) => FiltrosPartidos)) => void;
}

interface OpcionesUsePartidosFutbol {
  /** Tipo de partidos a cargar: 'hoy', 'proximos' o 'recientes' */
  tipo?: 'hoy' | 'proximos' | 'recientes';
  /** Filtros iniciales */
  filtrosIniciales?: FiltrosPartidos;
  /** Cargar automáticamente al montar */
  cargarAlMontar?: boolean;
}

/**
 * Hook que carga y gestiona la lista de partidos de fútbol
 */
export function usePartidosFutbol(
  opciones: OpcionesUsePartidosFutbol = {}
): RetornoUsePartidosFutbol {
  const {
    tipo = 'proximos',
    filtrosIniciales = {},
    cargarAlMontar = true,
  } = opciones;

  const [partidos, setPartidos] = useState<PartidoFutbolResumen[]>([]);
  const [estado, setEstado] = useState<EstadoPeticion>('inactivo');
  const [error, setError] = useState<string | null>(null);
  const [filtros, setFiltros] = useState<FiltrosPartidos>(filtrosIniciales);

  // Memorizar filtros para evitar llamadas innecesarias
  const filtrosMemo = useMemo(() => ({
    competicion: filtros.competicion,
    dias: filtros.dias,
    estado: filtros.estado,
    equipo: filtros.equipo,
    limite: filtros.limite,
  }), [filtros.competicion, filtros.dias, filtros.estado, filtros.equipo, filtros.limite]);

  const cargarPartidos = useCallback(async () => {
    setEstado('cargando');
    setError(null);

    try {
      const servicio =
        tipo === 'hoy'
          ? obtenerPartidosHoy
          : tipo === 'proximos'
            ? obtenerPartidosProximos
            : obtenerPartidosRecientes;
      const datos = await servicio(filtrosMemo);
      setPartidos(datos);
      setEstado('exito');
    } catch (err) {
      const mensaje = err instanceof Error ? err.message : 'Error al cargar partidos';
      setError(mensaje);
      setEstado('error');
    }
  }, [tipo, filtrosMemo]);

  useEffect(() => {
    if (cargarAlMontar) {
      void cargarPartidos();
    }
  }, [cargarPartidos, cargarAlMontar]);

  return {
    partidos,
    cargando: estado === 'cargando',
    error,
    recargar: cargarPartidos,
    filtros,
    setFiltros,
  };
}
