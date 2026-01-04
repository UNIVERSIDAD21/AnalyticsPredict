/**
 * useEstadisticasEquipos.ts — Hook para manejar estadísticas de equipos
 */

import { useCallback, useEffect, useState } from 'react';
import { EstadoPeticion, EstadisticasEquipo, TemporadaDisponible } from '../tipos';
import { obtenerEstadisticasEquipos } from '../servicios';

interface RetornoUseEstadisticasEquipos {
  equipos: EstadisticasEquipo[];
  fechaActualizacion: string;
  estado: EstadoPeticion;
  error: string | null;
  temporadasDisponibles: TemporadaDisponible[];
  temporadaActual: string | null;
  cambiarTemporada: (temporadaId: string | null) => void;
  recargar: () => void;
}

export function useEstadisticasEquipos(): RetornoUseEstadisticasEquipos {
  const [equipos, setEquipos] = useState<EstadisticasEquipo[]>([]);
  const [fechaActualizacion, setFechaActualizacion] = useState('');
  const [estado, setEstado] = useState<EstadoPeticion>('inactivo');
  const [error, setError] = useState<string | null>(null);
  const [temporadasDisponibles, setTemporadasDisponibles] = useState<TemporadaDisponible[]>([]);
  const [temporadaActual, setTemporadaActual] = useState<string | null>(null);
  const [temporadaSeleccionada, setTemporadaSeleccionada] = useState<string | null>(null);

  const cargar = useCallback(async (temporadaId?: string | null) => {
    setEstado('cargando');
    setError(null);
    try {
      const respuesta = await obtenerEstadisticasEquipos({
        temporadaId: temporadaId || undefined,
      });
      setEquipos(respuesta.equipos);
      setFechaActualizacion(respuesta.fecha_actualizacion);
      setTemporadasDisponibles(respuesta.temporadas_disponibles || []);
      setTemporadaActual(respuesta.temporada_actual || null);
      setEstado('exito');
    } catch (err) {
      const mensaje = err instanceof Error ? err.message : 'Error al cargar estadísticas';
      setError(mensaje);
      setEstado('error');
    }
  }, []);

  useEffect(() => {
    cargar(temporadaSeleccionada);
  }, [cargar, temporadaSeleccionada]);

  const cambiarTemporada = useCallback((temporadaId: string | null) => {
    setTemporadaSeleccionada(temporadaId);
  }, []);

  return {
    equipos,
    fechaActualizacion,
    estado,
    error,
    temporadasDisponibles,
    temporadaActual,
    cambiarTemporada,
    recargar: () => cargar(temporadaSeleccionada),
  };
}
