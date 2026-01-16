/**
 * useCombinadas.ts — Hook para gestionar combinadas
 */

import { useCallback, useState } from 'react';
import { crearCombinada } from '../servicios';
import { PeticionCrearCombinada, RespuestaCombinada } from '../tipos';

interface EstadoCombinada {
  estado: 'idle' | 'cargando' | 'exito' | 'error';
  error?: string;
  combinada?: RespuestaCombinada;
}

export function useCombinadas() {
  const [estado, setEstado] = useState<EstadoCombinada>({ estado: 'idle' });

  const crear = useCallback(async (payload: PeticionCrearCombinada) => {
    setEstado({ estado: 'cargando' });
    try {
      const respuesta = await crearCombinada(payload);
      setEstado({ estado: 'exito', combinada: respuesta });
      return respuesta;
    } catch (error) {
      const mensaje = error instanceof Error ? error.message : 'Error al crear combinada';
      setEstado({ estado: 'error', error: mensaje });
      throw error;
    }
  }, []);

  const limpiar = useCallback(() => {
    setEstado({ estado: 'idle' });
  }, []);

  return {
    ...estado,
    crear,
    limpiar,
  };
}
