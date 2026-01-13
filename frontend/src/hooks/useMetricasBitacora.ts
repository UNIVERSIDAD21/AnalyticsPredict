/**
 * useMetricasBitacora.ts — Hook para obtener métricas desde la bitácora
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { clienteAPI, extraerMensajeError } from '../servicios/api';

interface MetricaMercadoBitacora {
  mercado: string;
  total: number;
  ganadas: number;
  perdidas: number;
  push: number;
  win_rate: number | null;
  stake_total: number;
  ganancia_total: number;
  roi: number | null;
  edge_promedio: number | null;
  probabilidad_promedio: number | null;
}

interface MetricaConfianzaBitacora {
  confianza: string;
  total: number;
  ganadas: number;
  perdidas: number;
  win_rate: number | null;
  stake_total: number;
  ganancia_total: number;
  roi: number | null;
}

interface MetricaTemporalBitacora {
  periodo: string;
  total: number;
  ganadas: number;
  perdidas: number;
  win_rate: number | null;
  ganancia: number;
  roi: number | null;
}

interface RespuestaMetricasBitacora {
  exito: boolean;
  periodo: {
    desde: string | null;
    hasta: string | null;
  };
  resumen_global: {
    total: number;
    ganadas: number;
    perdidas: number;
    push: number;
    win_rate: number | null;
    stake_total: number;
    ganancia_total: number;
    roi: number | null;
    edge_promedio: number | null;
    probabilidad_promedio: number | null;
  };
  por_mercado: MetricaMercadoBitacora[];
  por_confianza: MetricaConfianzaBitacora[];
  por_mes: MetricaTemporalBitacora[];
  advertencias: string[];
}

export interface ParametrosMetricasBitacora {
  desde?: string;
  hasta?: string;
  mercado?: string;
}

interface OpcionesMetricasBitacora {
  habilitado?: boolean;
}

interface EstadoMetricasBitacora {
  datos: RespuestaMetricasBitacora | null;
  estado: 'idle' | 'cargando' | 'exito' | 'error';
  error: string | null;
}

export function useMetricasBitacora(
  params: ParametrosMetricasBitacora = {},
  opciones: OpcionesMetricasBitacora = {}
) {
  const { habilitado = true } = opciones;
  const [estado, setEstado] = useState<EstadoMetricasBitacora>({
    datos: null,
    estado: 'idle',
    error: null,
  });

  const parametros = useMemo(
    () => ({
      desde: params.desde,
      hasta: params.hasta,
      mercado: params.mercado,
    }),
    [params.desde, params.hasta, params.mercado]
  );

  const cargar = useCallback(async () => {
    if (!habilitado) {
      return;
    }
    setEstado((prev) => ({ ...prev, estado: 'cargando', error: null }));
    try {
      const respuesta = await clienteAPI.get<RespuestaMetricasBitacora>('/api/bitacora/metricas', {
        params: parametros,
      });

      if (!respuesta.data.exito) {
        throw new Error('No se pudieron obtener las métricas de la bitácora.');
      }

      setEstado({
        datos: respuesta.data,
        estado: 'exito',
        error: null,
      });
    } catch (error) {
      setEstado((prev) => ({
        ...prev,
        estado: 'error',
        error: extraerMensajeError(error),
      }));
    }
  }, [habilitado, parametros]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  return {
    datos: estado.datos,
    estado: estado.estado,
    error: estado.error,
    recargar: cargar,
  };
}
