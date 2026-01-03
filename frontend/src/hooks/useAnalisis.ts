/**
 * useAnalisis.ts — Hook para manejar análisis de partidos
 */

import { useState, useCallback } from 'react';
import { PeticionAnalisis, ResultadoAnalisis, EstadoPeticion } from '../tipos';
import { analizarPartido } from '../servicios';

interface RetornoUseAnalisis {
  resultado: ResultadoAnalisis | null;
  estado: EstadoPeticion;
  error: string | null;
  analizar: (peticion: PeticionAnalisis) => Promise<void>;
  limpiar: () => void;
}

/**
 * Hook que gestiona el análisis de partidos
 */
export function useAnalisis(): RetornoUseAnalisis {
  const [resultado, setResultado] = useState<ResultadoAnalisis | null>(null);
  const [estado, setEstado] = useState<EstadoPeticion>('inactivo');
  const [error, setError] = useState<string | null>(null);

  const analizar = useCallback(async (peticion: PeticionAnalisis) => {
    setEstado('cargando');
    setError(null);
    setResultado(null);

    try {
      const datos = await analizarPartido(peticion);
      setResultado(datos);
      setEstado('exito');
    } catch (err) {
      const mensaje = err instanceof Error ? err.message : 'Error al analizar partido';
      setError(mensaje);
      setEstado('error');
    }
  }, []);

  const limpiar = useCallback(() => {
    setResultado(null);
    setEstado('inactivo');
    setError(null);
  }, []);

  return {
    resultado,
    estado,
    error,
    analizar,
    limpiar,
  };
}
