/**
 * useBitacora.ts — Hook para gestionar la bitácora
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { listarBitacoraUnificada, obtenerResumenApuestas } from '../servicios';
import { RegistroBitacoraUnificada } from '../tipos';

export interface FiltrosBitacora {
  resultado?: string;
  deporte?: string;
  mercado?: string;
  confianza?: string;
  desde?: string;
  hasta?: string;
  busqueda?: string;
  orden?: string;
  tipo_apuesta?: string;
}

interface EstadoBitacora {
  apuestas: RegistroBitacoraUnificada[];
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
        listarBitacoraUnificada(parametros),
        obtenerResumenApuestas(),
      ]);
      setEstado({
        apuestas: lista.registros,
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
