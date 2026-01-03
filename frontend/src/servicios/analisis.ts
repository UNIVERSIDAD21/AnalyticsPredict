/**
 * analisis.ts — Servicio para análisis de partidos
 */

import { clienteAPI, extraerMensajeError } from './api';
import {
  PeticionAnalisis,
  PeticionAnalisisEnVivo,
  RespuestaAnalisis,
  ResultadoAnalisis,
} from '../tipos';

// ══════════════════════════════════════════════════════════════
// FUNCIONES
// ══════════════════════════════════════════════════════════════

/**
 * Analiza un partido (pre-partido)
 */
export async function analizarPartido(
  peticion: PeticionAnalisis
): Promise<ResultadoAnalisis> {
  try {
    const respuesta = await clienteAPI.post<RespuestaAnalisis>(
      '/api/analizar',
      peticion
    );

    if (!respuesta.data.exito) {
      throw new Error('Error al analizar partido');
    }

    return respuesta.data.datos;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Analiza un partido en vivo (con marcadores reales)
 */
export async function analizarPartidoEnVivo(
  peticion: PeticionAnalisisEnVivo
): Promise<ResultadoAnalisis> {
  try {
    const respuesta = await clienteAPI.post<RespuestaAnalisis>(
      '/api/analizar-en-vivo',
      peticion
    );

    if (!respuesta.data.exito) {
      throw new Error('Error al analizar partido en vivo');
    }

    return respuesta.data.datos;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Valida los datos antes de enviar
 */
export function validarPeticionAnalisis(peticion: Partial<PeticionAnalisis>): string[] {
  const errores: string[] = [];

  if (!peticion.equipo_local?.trim()) {
    errores.push('Debes seleccionar el equipo local');
  }

  if (!peticion.equipo_visitante?.trim()) {
    errores.push('Debes seleccionar el equipo visitante');
  }

  if (peticion.equipo_local?.toLowerCase() === peticion.equipo_visitante?.toLowerCase()) {
    errores.push('El equipo local y visitante no pueden ser el mismo');
  }

  if (!peticion.mercado) {
    errores.push('Debes seleccionar un mercado');
  }

  if (peticion.linea === undefined || peticion.linea === null) {
    errores.push('Debes ingresar una línea');
  } else if (peticion.linea <= 0) {
    errores.push('La línea debe ser mayor a 0');
  } else if (peticion.linea > 300) {
    errores.push('La línea parece demasiado alta');
  }

  if (peticion.cuota !== undefined && peticion.cuota !== null) {
    if (peticion.cuota <= 1) {
      errores.push('La cuota debe ser mayor a 1.00');
    } else if (peticion.cuota > 100) {
      errores.push('La cuota parece demasiado alta');
    }
  }

  return errores;
}
