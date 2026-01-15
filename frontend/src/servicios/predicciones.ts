/**
 * predicciones.ts — Servicio para historial de predicciones
 */

import { clienteAPI, extraerMensajeError } from './api';
import type { ParametrosHistorialPredicciones, RespuestaHistorialPredicciones } from '../tipos';

export async function obtenerHistorialPredicciones(
  params: ParametrosHistorialPredicciones
): Promise<RespuestaHistorialPredicciones> {
  try {
    const respuesta = await clienteAPI.get<RespuestaHistorialPredicciones>(
      '/api/predicciones/historial',
      { params }
    );

    if (!respuesta.data.exito) {
      throw new Error('Error al cargar historial de predicciones');
    }

    return respuesta.data;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}
