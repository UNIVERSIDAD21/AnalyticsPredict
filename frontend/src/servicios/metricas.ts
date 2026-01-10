/**
 * metricas.ts — Servicio para métricas de calibración
 */

import { clienteAPI, extraerMensajeError } from './api';
import type {
  ParametrosMetricasCalibracion,
  ParametrosCurvaCalibracion,
  RespuestaMetricasCalibracion,
  RespuestaCurvaCalibracion,
  RespuestaRecalibracion,
  RespuestaResolverAlerta,
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

export async function recalibrarMercado(
  mercado: ParametrosCurvaCalibracion['mercado'],
  origen: ParametrosCurvaCalibracion['origen'],
  cutoff_datos: string
): Promise<RespuestaRecalibracion> {
  try {
    const respuesta = await clienteAPI.post<RespuestaRecalibracion>('/api/interno/recalibrar', {
      mercado,
      origen,
      cutoff_datos,
    });

    if (!respuesta.data.exito) {
      throw new Error('No se pudo recalibrar el mercado.');
    }

    return respuesta.data;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

export async function resolverAlertaCalibracion(
  alerta_id: string,
  nota?: string
): Promise<RespuestaResolverAlerta> {
  try {
    const respuesta = await clienteAPI.post<RespuestaResolverAlerta>(
      '/api/interno/alertas-calibracion/resolver',
      { alerta_id, nota }
    );

    if (!respuesta.data.exito) {
      throw new Error('No se pudo resolver la alerta.');
    }

    return respuesta.data;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}
