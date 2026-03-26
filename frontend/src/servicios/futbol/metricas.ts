/**
 * metricas.ts — Servicios de API para métricas del sistema de fútbol
 */

import { clienteAPI, extraerMensajeError } from '../api';
import type {
  MetricasCalibracionFutbol,
  MetricasRendimientoFutbol,
  EstadoModeloFutbol,
  ResumenSistema,
  TipoMercadoFutbol,
  PuntoROITemporalFutbol,
} from '../../tipos/futbol';

// ══════════════════════════════════════════════════════════════
// TRANSFORMADORES
// ══════════════════════════════════════════════════════════════

/**
 * Transforma métricas de calibración de snake_case a camelCase
 */
function transformarMetricasCalibracion(
  data: Record<string, unknown>
): MetricasCalibracionFutbol {
  return {
    mercado: String(data.mercado || '') as TipoMercadoFutbol,
    brierScore: Number(data.brier_score || data.brierScore || 0),
    ece: Number(data.ece || 0),
    logLoss: Number(data.log_loss || data.logLoss || 0),
    nPredicciones: Number(data.n_predicciones || data.nPredicciones || 0),
    calibradorActivo: Boolean(data.calibrador_activo || data.calibradorActivo),
    metodoCalibrador: data.metodo_calibrador as string | undefined,
    mejoraBrier:
      data.mejora_brier !== undefined ? Number(data.mejora_brier) : undefined,
  };
}

/**
 * Transforma métricas de rendimiento de snake_case a camelCase
 */
function transformarMetricasRendimiento(
  data: Record<string, unknown>
): MetricasRendimientoFutbol {
  return {
    mercado: String(data.mercado || '') as TipoMercadoFutbol,
    nApuestas: Number(data.n_apuestas || data.nApuestas || 0),
    ganadas: Number(data.ganadas || 0),
    perdidas: Number(data.perdidas || 0),
    roi: Number(data.roi || 0),
    winRate: Number(data.win_rate || data.winRate || 0),
    stakeTotal: Number(data.stake_total || data.stakeTotal || 0),
    gananciaNeta: Number(data.ganancia_neta || data.gananciaNeta || 0),
  };
}

/**
 * Transforma estado del modelo de snake_case a camelCase
 */
function transformarEstadoModelo(
  data: Record<string, unknown>
): EstadoModeloFutbol {
  return {
    tipoModelo: (data.tipo_modelo || data.tipoModelo) as EstadoModeloFutbol['tipoModelo'],
    version: String(data.version || ''),
    fechaEntrenamiento: String(data.fecha_entrenamiento || data.fechaEntrenamiento || ''),
    mae: Number(data.mae || 0),
    rmse: Number(data.rmse || 0),
    r2: Number(data.r2 || 0),
    nPartidosEntrenamiento: Number(
      data.n_partidos_entrenamiento || data.nPartidosEntrenamiento || 0
    ),
    nEquipos: Number(data.n_equipos || data.nEquipos || 0),
  };
}

// ══════════════════════════════════════════════════════════════
// SERVICIOS
// ══════════════════════════════════════════════════════════════

/**
 * Obtiene las métricas de calibración
 */
export async function obtenerMetricasCalibracion(
  mercado?: string
): Promise<MetricasCalibracionFutbol[]> {
  try {
    const params: Record<string, string> = {};
    if (mercado) {
      params.mercado = mercado;
    }

    const respuesta = await clienteAPI.get('/api/futbol/metricas/calibracion', {
      params,
    });
    const datos = respuesta.data?.metricas || respuesta.data || [];

    return Array.isArray(datos)
      ? datos.map((m) =>
          transformarMetricasCalibracion(m as Record<string, unknown>)
        )
      : [];
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Obtiene las métricas de rendimiento
 */
export async function obtenerMetricasRendimiento(
  mercado?: string
): Promise<MetricasRendimientoFutbol[]> {
  try {
    const params: Record<string, string> = {};
    if (mercado) {
      params.mercado = mercado;
    }

    const respuesta = await clienteAPI.get('/api/futbol/metricas/rendimiento', {
      params,
    });
    const datos = respuesta.data?.metricas || respuesta.data || [];

    return Array.isArray(datos)
      ? datos.map((m) =>
          transformarMetricasRendimiento(m as Record<string, unknown>)
        )
      : [];
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Obtiene el estado de los modelos
 */
export async function obtenerEstadoModelos(): Promise<EstadoModeloFutbol[]> {
  try {
    const respuesta = await clienteAPI.get('/api/futbol/metricas/modelos');
    const datos = respuesta.data?.modelos || respuesta.data || [];

    return Array.isArray(datos)
      ? datos.map((m) =>
          transformarEstadoModelo(m as Record<string, unknown>)
        )
      : [];
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

/**
 * Obtiene el resumen completo del sistema
 */
export async function obtenerResumenSistema(): Promise<ResumenSistema> {
  try {
    const respuesta = await clienteAPI.get('/api/futbol/metricas/resumen');
    const data = respuesta.data;

    const modelos = data.modelos || [];
    const calibradores = data.calibradores || [];
    const rendimiento = data.rendimiento || [];

    return {
      modelos: Array.isArray(modelos)
        ? modelos.map((m) =>
            transformarEstadoModelo(m as Record<string, unknown>)
          )
        : [],
      calibradores: Array.isArray(calibradores)
        ? calibradores.map((c) =>
            transformarMetricasCalibracion(c as Record<string, unknown>)
          )
        : [],
      rendimiento: Array.isArray(rendimiento)
        ? rendimiento.map((r) =>
            transformarMetricasRendimiento(r as Record<string, unknown>)
          )
        : [],
      ultimaActualizacion: String(
        data.ultima_actualizacion || data.ultimaActualizacion || new Date().toISOString()
      ),
      estadoGeneral: (data.estado_general || data.estadoGeneral || 'saludable') as ResumenSistema['estadoGeneral'],
    };
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}


export interface ResumenCalidad1x2Futbol {
  total: number;
  finalizadas: number;
  ganadas: number;
  perdidas: number;
  push: number;
  hitRateSinPush: number;
}

const CACHE_KEY_RESUMEN_1X2 = 'futbol.metricas.resumenCalidad1x2';
const CACHE_TTL_MS = 5 * 60 * 1000;

function leerCacheResumen1x2(): ResumenCalidad1x2Futbol | null {
  if (typeof window === 'undefined') return null;
  const raw = window.sessionStorage.getItem(CACHE_KEY_RESUMEN_1X2);
  if (!raw) return null;

  try {
    const parsed = JSON.parse(raw) as { ts: number; data: ResumenCalidad1x2Futbol };
    if (!parsed?.ts || Date.now() - parsed.ts > CACHE_TTL_MS) return null;
    return parsed.data;
  } catch {
    return null;
  }
}

function guardarCacheResumen1x2(data: ResumenCalidad1x2Futbol): void {
  if (typeof window === 'undefined') return;
  window.sessionStorage.setItem(
    CACHE_KEY_RESUMEN_1X2,
    JSON.stringify({ ts: Date.now(), data })
  );
}

export async function obtenerResumenCalidad1x2(forceRefresh = false): Promise<ResumenCalidad1x2Futbol> {
  try {
    if (!forceRefresh) {
      const cached = leerCacheResumen1x2();
      if (cached) return cached;
    }

    const respuesta = await clienteAPI.get('/api/futbol/metricas/resumen-calidad-1x2');
    const r = respuesta.data?.resumen || {};
    const parsed: ResumenCalidad1x2Futbol = {
      total: Number(r.total || 0),
      finalizadas: Number(r.finalizadas || 0),
      ganadas: Number(r.ganadas || 0),
      perdidas: Number(r.perdidas || 0),
      push: Number(r.push || 0),
      hitRateSinPush: Number(r.hit_rate_sin_push || 0),
    };
    guardarCacheResumen1x2(parsed);
    return parsed;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

export async function obtenerRoiTemporal(
  dias = 30
): Promise<PuntoROITemporalFutbol[]> {
  try {
    const respuesta = await clienteAPI.get('/api/futbol/metricas/roi-temporal', {
      params: { dias },
    });
    const serie = respuesta.data?.serie || [];
    if (!Array.isArray(serie)) return [];

    return serie.map((p) => ({
      fecha: String(p.fecha || ''),
      roi: Number(p.roi || 0),
      stakeAcumulado: Number(p.stake_acumulado || 0),
      gananciaAcumulada: Number(p.ganancia_acumulada || 0),
    }));
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}
