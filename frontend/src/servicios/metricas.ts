/**
 * metricas.ts — Servicio para métricas de calibración
 */

import { clienteAPI, extraerMensajeError } from './api';
import type {
  ParametrosMetricasCalibracion,
  ParametrosCurvaCalibracion,
  RespuestaMetricasCalibracion,
  RespuestaCurvaCalibracion,
} from '../tipos';

export async function obtenerMetricasCalibracion(
  params: ParametrosMetricasCalibracion
): Promise<RespuestaMetricasCalibracion> {
  try {
    const respuesta = await clienteAPI.get<RespuestaMetricasCalibracion>('/api/metricas/calibracion', {
      params,
    });

    if (!respuesta.data.exito) {
      throw new Error('Error al cargar métricas de calibración');
    }

    return respuesta.data;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

export async function obtenerCurvaCalibracion(
  params: ParametrosCurvaCalibracion
): Promise<RespuestaCurvaCalibracion> {
  try {
    const { mercado, ...resto } = params;
    const respuesta = await clienteAPI.get<RespuestaCurvaCalibracion>(
      `/api/metricas/calibracion/${mercado}/curva`,
      { params: resto }
    );

    if (!respuesta.data.exito) {
      throw new Error('Error al cargar curva de calibración');
    }

    return respuesta.data;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}
