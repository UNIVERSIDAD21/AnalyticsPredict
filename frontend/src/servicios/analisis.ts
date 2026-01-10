// hace parte del diseño de analisis
/**
 * analisis.ts — Servicio para análisis de partidos
 */

import { clienteAPI, extraerMensajeError } from './api';
import {
  PeticionAnalisis,
  PeticionAnalisisEnVivo,
  RespuestaAnalisis,
  ResultadoAnalisis,
  ConfiguracionUsuario,
} from '../tipos';

// ══════════════════════════════════════════════════════════════
// TIPOS DE RESPUESTA EXTENDIDA
// ══════════════════════════════════════════════════════════════

/**
 * Respuesta extendida que incluye datos y advertencias del backend.
 * Las advertencias NO deben perderse en el flujo de UI.
 */
export interface RespuestaAnalisisExtendida {
  datos: ResultadoAnalisis;
  advertencias: string[];
}

// ══════════════════════════════════════════════════════════════
// FUNCIONES
// ══════════════════════════════════════════════════════════════

/**
 * Analiza un partido (pre-partido).
 * Retorna tanto los datos como las advertencias del backend.
 */
export async function analizarPartido(
  peticion: PeticionAnalisis,
  configuracion?: ConfiguracionUsuario
): Promise<RespuestaAnalisisExtendida> {
  try {
    const respuesta = await clienteAPI.post<RespuestaAnalisis>(
      '/api/analizar',
      construirPeticionConConfiguracion(peticion, configuracion)
    );

    if (!respuesta.data.exito) {
      throw new Error('Error al analizar partido');
    }

    return {
      datos: respuesta.data.datos,
      advertencias: respuesta.data.advertencias ?? [],
    };
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Analiza un partido en vivo (con marcadores reales).
 * Retorna tanto los datos como las advertencias del backend.
 */
export async function analizarPartidoEnVivo(
  peticion: PeticionAnalisisEnVivo
): Promise<RespuestaAnalisisExtendida> {
  try {
    const respuesta = await clienteAPI.post<RespuestaAnalisis>(
      '/api/analizar-en-vivo',
      peticion
    );

    if (!respuesta.data.exito) {
      throw new Error('Error al analizar partido en vivo');
    }

    return {
      datos: respuesta.data.datos,
      advertencias: respuesta.data.advertencias ?? [],
    };
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

function construirPeticionConConfiguracion(
  peticion: PeticionAnalisis,
  configuracion?: ConfiguracionUsuario
): PeticionAnalisis {
  if (!configuracion) {
    return peticion;
  }

  const payload: PeticionAnalisis = { ...peticion };

  if (configuracion.bankroll !== null && configuracion.bankroll > 0) {
    payload.bankroll = configuracion.bankroll;
  }

  if (configuracion.perfilRiesgo) {
    payload.perfil_riesgo = configuracion.perfilRiesgo;
  }

  const tieneCuotas =
    payload.cuota_over !== undefined ||
    payload.cuota_under !== undefined ||
    payload.cuota !== undefined;

  if (!payload.modo_devig && configuracion.modoDevig && tieneCuotas) {
    payload.modo_devig = configuracion.modoDevig;
  }

  return payload;
}

/**
 * Valida los datos antes de enviar.
 *
 * Soporta cuotas duales (over/under) y modo_devig.
 * Valida coherencia entre lado seleccionado y cuotas ingresadas.
 */
export function validarPeticionAnalisis(peticion: Partial<PeticionAnalisis>): string[] {
  const errores: string[] = [];

  // ═══════════════════════════════════════════════════════════
  // Validaciones de equipos
  // ═══════════════════════════════════════════════════════════

  if (!peticion.equipo_local?.trim()) {
    errores.push('Debes seleccionar el equipo local');
  }

  if (!peticion.equipo_visitante?.trim()) {
    errores.push('Debes seleccionar el equipo visitante');
  }

  if (peticion.equipo_local?.toLowerCase() === peticion.equipo_visitante?.toLowerCase()) {
    errores.push('El equipo local y visitante no pueden ser el mismo');
  }

  // ═══════════════════════════════════════════════════════════
  // Validaciones de mercado y línea
  // ═══════════════════════════════════════════════════════════

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

  // ═══════════════════════════════════════════════════════════
  // Validaciones de cuotas (legacy y duales)
  // ═══════════════════════════════════════════════════════════

  // Cuota legacy (deprecada pero aún soportada)
  if (peticion.cuota !== undefined && peticion.cuota !== null) {
    if (peticion.cuota <= 1) {
      errores.push('La cuota debe ser mayor a 1.00');
    } else if (peticion.cuota > 100) {
      errores.push('La cuota parece demasiado alta');
    }
  }

  // Cuotas duales
  const tieneOver = peticion.cuota_over !== undefined && peticion.cuota_over !== null;
  const tieneUnder = peticion.cuota_under !== undefined && peticion.cuota_under !== null;

  if (tieneOver) {
    if (peticion.cuota_over! <= 1) {
      errores.push('La cuota OVER debe ser mayor a 1.00');
    } else if (peticion.cuota_over! > 100) {
      errores.push('La cuota OVER parece demasiado alta');
    }
  }

  if (tieneUnder) {
    if (peticion.cuota_under! <= 1) {
      errores.push('La cuota UNDER debe ser mayor a 1.00');
    } else if (peticion.cuota_under! > 100) {
      errores.push('La cuota UNDER parece demasiado alta');
    }
  }

  // ═══════════════════════════════════════════════════════════
  // Validación de coherencia lado/cuotas
  // Si hay cuotas, debe haber al menos la cuota del lado seleccionado
  // ═══════════════════════════════════════════════════════════

  if ((tieneOver || tieneUnder) && peticion.lado) {
    const soloLadoOpuesto =
      (peticion.lado === 'OVER' && tieneUnder && !tieneOver) ||
      (peticion.lado === 'UNDER' && tieneOver && !tieneUnder);

    if (soloLadoOpuesto) {
      errores.push(
        `Ingresaste cuota del lado contrario. Completa la cuota ${peticion.lado} o cambia el lado de apuesta.`
      );
    }
  }

  // ═══════════════════════════════════════════════════════════
  // Validaciones de temporadas
  // ═══════════════════════════════════════════════════════════

  if (peticion.temporadas && peticion.temporadas.length === 0) {
    errores.push('Debes seleccionar al menos una temporada para el análisis');
  }

  return errores;
}
