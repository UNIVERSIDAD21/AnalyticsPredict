/**
 * combinadas.ts — Servicios para combinadas
 */

import { clienteAPI, extraerMensajeError } from './api';
import {
  PeticionCrearCombinada,
  RespuestaBitacoraUnificada,
  RespuestaCombinada,
  RespuestaListaCombinadas,
} from '../tipos';

export async function crearCombinada(payload: PeticionCrearCombinada): Promise<RespuestaCombinada> {
  const respuesta = await clienteAPI.post<RespuestaCombinada>('/api/combinadas', payload);
  if (!respuesta.data.exito) {
    throw new Error('No se pudo crear la combinada');
  }
  return respuesta.data;
}

export async function listarCombinadas(params: Record<string, string | number | undefined>): Promise<RespuestaListaCombinadas> {
  const respuesta = await clienteAPI.get<RespuestaListaCombinadas>('/api/combinadas', { params });
  if (!respuesta.data.exito) {
    throw new Error('No se pudieron obtener las combinadas');
  }
  return respuesta.data;
}

export async function obtenerCombinada(combinadaId: string): Promise<RespuestaCombinada> {
  const respuesta = await clienteAPI.get<RespuestaCombinada>(`/api/combinadas/${combinadaId}`);
  if (!respuesta.data.exito) {
    throw new Error('No se pudo obtener la combinada');
  }
  return respuesta.data;
}

export async function eliminarCombinada(combinadaId: string): Promise<void> {
  const respuesta = await clienteAPI.delete(`/api/combinadas/${combinadaId}`);
  if (!respuesta.data.exito) {
    throw new Error('No se pudo eliminar la combinada');
  }
}

export interface PeticionActualizarResultadoCombinada {
  resultado: 'GANADA' | 'PERDIDA' | 'PUSH' | 'ANULADA';
}

export async function actualizarResultadoCombinada(
  combinadaId: string,
  payload: PeticionActualizarResultadoCombinada
): Promise<RespuestaCombinada> {
  const respuesta = await clienteAPI.patch<RespuestaCombinada>(
    `/api/combinadas/${combinadaId}/resultado`,
    payload
  );
  if (!respuesta.data.exito) {
    throw new Error('No se pudo actualizar el resultado de la combinada');
  }
  return respuesta.data;
}

type EnvelopeV2<T> = {
  ok: boolean;
  data: T;
  meta?: Record<string, unknown>;
};

function esEnvelopeV2<T>(data: unknown): data is EnvelopeV2<T> {
  return !!data && typeof data === 'object' && 'data' in (data as Record<string, unknown>);
}

function normalizarBitacoraUnificada(payload: unknown): RespuestaBitacoraUnificada {
  if (esEnvelopeV2<RespuestaBitacoraUnificada>(payload)) {
    const data = payload.data;
    return {
      ...data,
      exito: true,
    } as RespuestaBitacoraUnificada;
  }
  return payload as RespuestaBitacoraUnificada;
}

export async function listarBitacoraUnificada(
  params: Record<string, string | number | undefined>
): Promise<RespuestaBitacoraUnificada> {
  try {
    const respuesta = await clienteAPI.get('/api/bitacora/unificada', { params });
    const normalizada = normalizarBitacoraUnificada(respuesta.data);
    if (!normalizada.exito) {
      throw new Error('No se pudo obtener la bitácora unificada');
    }
    return normalizada;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}
