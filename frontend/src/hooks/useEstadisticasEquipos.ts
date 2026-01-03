/**
 * useEstadisticasEquipos.ts — Hook para manejar estadísticas de equipos
 */

import { useCallback, useEffect, useState } from 'react';
import { EstadoPeticion, EstadisticasEquipo } from '../tipos';
import { obtenerEstadisticasEquipos } from '../servicios';

interface RetornoUseEstadisticasEquipos {
  equipos: EstadisticasEquipo[];
  fechaActualizacion: string;
  estado: EstadoPeticion;
  error: string | null;
  recargar: () => void;
}

export function useEstadisticasEquipos(): RetornoUseEstadisticasEquipos {
  const [equipos, setEquipos] = useState<EstadisticasEquipo[]>([]);
  const [fechaActualizacion, setFechaActualizacion] = useState('');
  const [estado, setEstado] = useState<EstadoPeticion>('inactivo');
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    setEstado('cargando');
    setError(null);
    try {
      const respuesta = await obtenerEstadisticasEquipos();
      setEquipos(respuesta.equipos);
      setFechaActualizacion(respuesta.fecha_actualizacion);
      setEstado('exito');
    } catch (err) {
      const mensaje = err instanceof Error ? err.message : 'Error al cargar estadísticas';
      setError(mensaje);
      setEstado('error');
    }
  }, []);

  useEffect(() => {
    cargar();
  }, [cargar]);

  return {
    equipos,
    fechaActualizacion,
    estado,
    error,
    recargar: cargar,
  };
}
