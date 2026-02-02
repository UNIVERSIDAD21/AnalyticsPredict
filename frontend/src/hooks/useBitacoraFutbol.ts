/**
 * useBitacoraFutbol.ts — Hook para gestionar la bitácora de apuestas de fútbol
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import type {
  ApuestaFutbol,
  ApuestaFutbolRequest,
  FiltrosApuestas,
  ResumenApuestasFutbol,
} from '../tipos/futbol';
import {
  obtenerApuestas,
  crearApuesta as crearApuestaServicio,
  actualizarApuesta as actualizarApuestaServicio,
  cancelarApuesta as cancelarApuestaServicio,
} from '../servicios/futbol';

type EstadoPeticion = 'idle' | 'cargando' | 'exito' | 'error';

interface EstadoBitacoraFutbol {
  apuestas: ApuestaFutbol[];
  resumen: ResumenApuestasFutbol;
  estado: EstadoPeticion;
  error?: string;
}

interface RetornoUseBitacoraFutbol {
  /** Lista de apuestas */
  apuestas: ApuestaFutbol[];
  /** Resumen de apuestas */
  resumen: ResumenApuestasFutbol;
  /** Indica si está cargando */
  cargando: boolean;
  /** Mensaje de error si ocurrió */
  error: string | null;
  /** Crear una nueva apuesta */
  crearApuesta: (apuesta: ApuestaFutbolRequest) => Promise<ApuestaFutbol>;
  /** Actualizar una apuesta existente */
  actualizarApuesta: (id: string, datos: Partial<ApuestaFutbolRequest>) => Promise<ApuestaFutbol>;
  /** Cancelar una apuesta */
  cancelarApuesta: (id: string) => Promise<void>;
  /** Recargar la bitácora */
  recargar: () => void;
  /** Filtros actuales */
  filtros: FiltrosApuestas;
  /** Actualizar filtros */
  setFiltros: (filtros: FiltrosApuestas | ((prev: FiltrosApuestas) => FiltrosApuestas)) => void;
  /** Página actual */
  pagina: number;
  /** Cambiar página */
  setPagina: (pagina: number) => void;
}

const RESUMEN_INICIAL: ResumenApuestasFutbol = {
  total: 0,
  pendientes: 0,
  ganadas: 0,
  perdidas: 0,
  push: 0,
  roi: null,
  winRate: null,
  stakeTotal: 0,
  gananciaNeta: 0,
};

interface OpcionesUseBitacoraFutbol {
  /** Filtros iniciales */
  filtrosIniciales?: FiltrosApuestas;
  /** Tamaño de página */
  tamano?: number;
  /** Cargar automáticamente al montar */
  cargarAlMontar?: boolean;
}

/**
 * Hook que gestiona la bitácora de apuestas de fútbol
 */
export function useBitacoraFutbol(
  opciones: OpcionesUseBitacoraFutbol = {}
): RetornoUseBitacoraFutbol {
  const {
    filtrosIniciales = {},
    tamano = 20,
    cargarAlMontar = true,
  } = opciones;

  const [estado, setEstado] = useState<EstadoBitacoraFutbol>({
    apuestas: [],
    resumen: RESUMEN_INICIAL,
    estado: 'idle',
  });

  const [filtros, setFiltros] = useState<FiltrosApuestas>(filtrosIniciales);
  const [pagina, setPagina] = useState<number>(1);

  // Memorizar parámetros para la petición
  const parametros = useMemo<FiltrosApuestas>(() => ({
    ...filtros,
    limite: tamano,
    offset: (pagina - 1) * tamano,
  }), [filtros, pagina, tamano]);

  const cargar = useCallback(async () => {
    setEstado((prev) => ({ ...prev, estado: 'cargando', error: undefined }));

    try {
      const datos = await obtenerApuestas(parametros);
      setEstado({
        apuestas: datos.apuestas,
        resumen: datos.resumen,
        estado: 'exito',
      });
    } catch (err) {
      const mensaje = err instanceof Error ? err.message : 'Error al cargar la bitácora';
      setEstado((prev) => ({ ...prev, estado: 'error', error: mensaje }));
    }
  }, [parametros]);

  useEffect(() => {
    if (cargarAlMontar) {
      void cargar();
    }
  }, [cargar, cargarAlMontar]);

  const crearApuesta = useCallback(async (apuesta: ApuestaFutbolRequest): Promise<ApuestaFutbol> => {
    try {
      const nuevaApuesta = await crearApuestaServicio(apuesta);
      // Recargar la lista después de crear
      void cargar();
      return nuevaApuesta;
    } catch (err) {
      const mensaje = err instanceof Error ? err.message : 'Error al crear apuesta';
      throw new Error(mensaje);
    }
  }, [cargar]);

  const actualizarApuesta = useCallback(
    async (id: string, datos: Partial<ApuestaFutbolRequest>): Promise<ApuestaFutbol> => {
      try {
        const apuestaActualizada = await actualizarApuestaServicio(id, datos);
        // Actualizar en la lista local
        setEstado((prev) => ({
          ...prev,
          apuestas: prev.apuestas.map((a) =>
            a.id === id ? apuestaActualizada : a
          ),
        }));
        return apuestaActualizada;
      } catch (err) {
        const mensaje = err instanceof Error ? err.message : 'Error al actualizar apuesta';
        throw new Error(mensaje);
      }
    },
    []
  );

  const cancelarApuesta = useCallback(async (id: string): Promise<void> => {
    try {
      await cancelarApuestaServicio(id);
      // Remover de la lista local o recargar
      void cargar();
    } catch (err) {
      const mensaje = err instanceof Error ? err.message : 'Error al cancelar apuesta';
      throw new Error(mensaje);
    }
  }, [cargar]);

  return {
    apuestas: estado.apuestas,
    resumen: estado.resumen,
    cargando: estado.estado === 'cargando',
    error: estado.error ?? null,
    crearApuesta,
    actualizarApuesta,
    cancelarApuesta,
    recargar: cargar,
    filtros,
    setFiltros,
    pagina,
    setPagina,
  };
}
