// hace parte del diseño de analisis
/**
 * useAnalisis.ts — Hook para manejar análisis de partidos
 *
 * Fase 2: Ahora incluye advertencias del backend para mostrar en UI.
 */

import { useState, useCallback } from 'react';
import { PeticionAnalisis, ResultadoAnalisis, EstadoPeticion } from '../tipos';
import { analizarPartido } from '../servicios';

interface RetornoUseAnalisis {
  /** Resultado del análisis */
  resultado: ResultadoAnalisis | null;

  /** Advertencias del backend (Fase 2) */
  advertencias: string[];

  /** Estado de la petición */
  estado: EstadoPeticion;

  /** Mensaje de error si hay */
  error: string | null;

  /** Ejecutar análisis */
  analizar: (peticion: PeticionAnalisis) => Promise<void>;

  /** Limpiar estado */
  limpiar: () => void;
}

/**
 * Hook que gestiona el análisis de partidos.
 * Fase 2: Ahora retorna advertencias del backend para mostrar en UI.
 */
export function useAnalisis(): RetornoUseAnalisis {
  const [resultado, setResultado] = useState<ResultadoAnalisis | null>(null);
  const [advertencias, setAdvertencias] = useState<string[]>([]);
  const [estado, setEstado] = useState<EstadoPeticion>('inactivo');
  const [error, setError] = useState<string | null>(null);

  const analizar = useCallback(async (peticion: PeticionAnalisis) => {
    setEstado('cargando');
    setError(null);
    setResultado(null);
    setAdvertencias([]);

    try {
      const respuesta = await analizarPartido(peticion);
      setResultado(respuesta.datos);
      setAdvertencias(respuesta.advertencias);
      setEstado('exito');
    } catch (err) {
      const mensaje = err instanceof Error ? err.message : 'Error al analizar partido';
      setError(mensaje);
      setEstado('error');
    }
  }, []);

  const limpiar = useCallback(() => {
    setResultado(null);
    setAdvertencias([]);
    setEstado('inactivo');
    setError(null);
  }, []);

  return {
    resultado,
    advertencias,
    estado,
    error,
    analizar,
    limpiar,
  };
}
