/**
 * useAnalisisFutbol.ts — Hook para manejar análisis de partidos de fútbol
 */

import { useState, useCallback } from 'react';
import type {
  AnalisisFutbolRequest,
  AnalisisFutbolResponse,
} from '../tipos/futbol';
import { analizarPartido } from '../servicios/futbol';

type EstadoPeticion = 'inactivo' | 'cargando' | 'exito' | 'error';

interface RetornoUseAnalisisFutbol {
  /** Resultado del análisis */
  analisis: AnalisisFutbolResponse | null;
  /** Indica si está cargando */
  cargando: boolean;
  /** Mensaje de error si ocurrió */
  error: string | null;
  /** Ejecutar el análisis de un partido */
  ejecutarAnalisis: (request: AnalisisFutbolRequest) => Promise<void>;
  /** Limpiar el estado del análisis */
  limpiar: () => void;
}

/**
 * Hook que gestiona el análisis de partidos de fútbol.
 * Permite analizar un partido y obtener predicciones para corners, goles y disparos.
 */
export function useAnalisisFutbol(): RetornoUseAnalisisFutbol {
  const [analisis, setAnalisis] = useState<AnalisisFutbolResponse | null>(null);
  const [estado, setEstado] = useState<EstadoPeticion>('inactivo');
  const [error, setError] = useState<string | null>(null);

  const ejecutarAnalisis = useCallback(async (request: AnalisisFutbolRequest) => {
    setEstado('cargando');
    setError(null);
    setAnalisis(null);

    try {
      const resultado = await analizarPartido(request);
      setAnalisis(resultado);
      setEstado('exito');
    } catch (err) {
      const mensaje = err instanceof Error ? err.message : 'Error al analizar partido';
      setError(mensaje);
      setEstado('error');
    }
  }, []);

  const limpiar = useCallback(() => {
    setAnalisis(null);
    setEstado('inactivo');
    setError(null);
  }, []);

  return {
    analisis,
    cargando: estado === 'cargando',
    error,
    ejecutarAnalisis,
    limpiar,
  };
}
