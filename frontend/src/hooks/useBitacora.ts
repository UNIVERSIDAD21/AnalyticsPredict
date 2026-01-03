/**
 * useBitacora.ts — Hook para gestionar la bitácora
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { listarApuestas, obtenerResumenApuestas } from '../servicios';
import { Apuesta } from '../tipos';

export interface FiltrosBitacora {
  resultado?: string;
  mercado?: string;
  confianza?: string;
  desde?: string;
  hasta?: string;
  busqueda?: string;
  orden?: string;
}

interface EstadoBitacora {
  apuestas: Apuesta[];
  total: number;
  pagina: number;
  totalPaginas: number;
  resumen: Record<string, unknown>;
  estado: 'idle' | 'cargando' | 'exito' | 'error';
  error?: string;
}

export function useBitacora(filtros: FiltrosBitacora, pagina: number, tamano: number) {
  const [estado, setEstado] = useState<EstadoBitacora>({
    apuestas: [],
    total: 0,
    pagina: 1,
    totalPaginas: 0,
    resumen: {},
    estado: 'idle',
  });

  const parametros = useMemo(() => ({
    ...filtros,
    pagina,
    tamano,
  }), [filtros, pagina, tamano]);

  const cargar = useCallback(async () => {
    setEstado((prev) => ({ ...prev, estado: 'cargando', error: undefined }));
    try {
      const [lista, resumen] = await Promise.all([
        listarApuestas(parametros),
        obtenerResumenApuestas(),
      ]);
      setEstado({
        apuestas: lista.apuestas,
        total: lista.total,
        pagina: lista.pagina,
        totalPaginas: lista.total_paginas,
        resumen: resumen.resumen,
        estado: 'exito',
      });
    } catch (error) {
      const mensaje = error instanceof Error ? error.message : 'Error al cargar la bitácora';
      setEstado((prev) => ({ ...prev, estado: 'error', error: mensaje }));
    }
  }, [parametros]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  return {
    ...estado,
    recargar: cargar,
  };
}
