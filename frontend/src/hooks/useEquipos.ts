/**
 * useEquipos.ts — Hook para manejar la carga de equipos
 */

import { useState, useEffect, useCallback } from 'react';
import { Equipo, EstadoPeticion } from '../tipos';
import { obtenerEquipos } from '../servicios';

interface RetornoUseEquipos {
  equipos: Equipo[];
  estado: EstadoPeticion;
  error: string | null;
  recargar: () => void;
}

/**
 * Hook que carga y gestiona la lista de equipos NBA
 */
export function useEquipos(): RetornoUseEquipos {
  const [equipos, setEquipos] = useState<Equipo[]>([]);
  const [estado, setEstado] = useState<EstadoPeticion>('inactivo');
  const [error, setError] = useState<string | null>(null);

  const cargarEquipos = useCallback(async () => {
    setEstado('cargando');
    setError(null);

    try {
      const datos = await obtenerEquipos();
      setEquipos(datos);
      setEstado('exito');
    } catch (err) {
      const mensaje = err instanceof Error ? err.message : 'Error al cargar equipos';
      setEquipos([]);
      setError(mensaje);
      setEstado('error');
    }
  }, []);

  useEffect(() => {
    cargarEquipos();
  }, [cargarEquipos]);

  return {
    equipos,
    estado,
    error,
    recargar: cargarEquipos,
  };
}
