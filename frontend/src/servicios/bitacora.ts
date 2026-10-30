/**
 * bitacora.ts — Servicios para Seguimiento de apuestas
 */

import { clienteAPI } from './api';
import { leerDatosBitacora } from './contratoBitacora';
import {
  PeticionActualizarResultado,
  PeticionCrearApuesta,
  RespuestaApuesta,
  RespuestaListaApuestas,
  RespuestaResumenApuestas,
  RespuestaApuestasAnalizadas,
  PartidoGuardadoFutbol,
  RespuestaPartidosGuardados,
} from '../tipos';

export interface ResumenResolucionBitacora {
  resueltas: number;
  pendientes: number;
  errores: number;
  importes_no_disponibles: number;
  motivos_pendientes: Record<string, number>;
}

export async function resolverPendientesBitacora(): Promise<ResumenResolucionBitacora> {
  const respuesta = await clienteAPI.post<{ exito: boolean; resumen: ResumenResolucionBitacora }>('/api/bitacora/resolver');
  if (!respuesta.data.exito || !respuesta.data.resumen) {
    throw new Error('No se pudieron completar las apuestas pendientes');
  }
  return respuesta.data.resumen;
}

export async function crearApuesta(payload: PeticionCrearApuesta): Promise<RespuestaApuesta> {
  const respuesta = await clienteAPI.post<RespuestaApuesta>('/api/bitacora', payload);
  if (!respuesta.data.exito) {
    throw new Error('No se pudo guardar la apuesta');
  }
  return respuesta.data;
}

export async function listarApuestas(params: Record<string, string | number | undefined>): Promise<RespuestaListaApuestas> {
  const respuesta = await clienteAPI.get('/api/bitacora', { params: { ...params, version: 'v2' } });
  const data = leerDatosBitacora<Omit<RespuestaListaApuestas, 'exito'>>(respuesta.data, {
    total: 'number', pagina: 'number', total_paginas: 'number', apuestas: 'array',
  });
  return { ...data, exito: true };
}

export async function obtenerResumenApuestas(): Promise<RespuestaResumenApuestas> {
  const respuesta = await clienteAPI.get('/api/bitacora/resumen', { params: { version: 'v2' } });
  const data = leerDatosBitacora<Omit<RespuestaResumenApuestas, 'exito'>>(respuesta.data, { resumen: 'object' });
  if (!Array.isArray(data.resumen.por_deporte) || !Array.isArray(data.resumen.por_mercado)) {
    throw new Error('Contrato de resumen de seguimiento inválido');
  }
  return { ...data, exito: true };
}

export async function actualizarResultadoApuesta(
  apuestaId: string,
  payload: PeticionActualizarResultado
): Promise<RespuestaApuesta> {
  const respuesta = await clienteAPI.patch<RespuestaApuesta>(`/api/bitacora/${apuestaId}/resultado`, payload);
  if (!respuesta.data.exito) {
    throw new Error('No se pudo actualizar el resultado');
  }
  return respuesta.data;
}

export async function eliminarApuesta(apuestaId: string): Promise<void> {
  const respuesta = await clienteAPI.delete(`/api/bitacora/${apuestaId}`);
  if (!respuesta.data.exito) {
    throw new Error('No se pudo eliminar la apuesta');
  }
}


export async function listarApuestasAnalizadas(
  params: Record<string, string | number | undefined> = {}
): Promise<RespuestaApuestasAnalizadas> {
  const respuesta = await clienteAPI.get('/api/bitacora/apuestas-analizadas', { params: { ...params, version: 'v2' } });
  const data = leerDatosBitacora<Omit<RespuestaApuestasAnalizadas, 'exito'>>(respuesta.data, {
    total: 'number', items: 'array',
  });
  return { ...data, exito: true };
}

export async function listarPartidosGuardados(): Promise<RespuestaPartidosGuardados> {
  const respuesta = await clienteAPI.get('/api/bitacora/partidos-guardados', {
    params: { version: 'v2', limite: 500 },
  });
  const data = leerDatosBitacora<Omit<RespuestaPartidosGuardados, 'exito'>>(respuesta.data, {
    total: 'number', partidos: 'array',
  });
  return { ...data, exito: true };
}

export async function guardarPartidoParaRevisar(partidoId: string): Promise<PartidoGuardadoFutbol> {
  const respuesta = await clienteAPI.post('/api/bitacora/partidos-guardados?version=v2', {
    partido_id: partidoId,
  });
  const data = leerDatosBitacora<{ partido: PartidoGuardadoFutbol }>(respuesta.data, {
    partido: 'object',
  });
  return data.partido;
}

export async function archivarPartidoGuardado(partidoId: string): Promise<void> {
  await clienteAPI.post(`/api/bitacora/partidos-guardados/${partidoId}/archivar?version=v2`);
}
