/**
 * analisis.ts — Servicios de API para análisis de partidos de fútbol
 */

import { clienteAPI, extraerMensajeError } from '../api';
import type {
  AnalisisFutbolRequest,
  AnalisisFutbolResponse,
  PartidoFutbolResumen,
  PrediccionMercadoFutbol,
  RecomendacionApuesta,
  ProbabilidadLinea,
  TipoMercadoFutbol,
  NivelConfianza,
  ObjetivoAnalisisFutbol,
} from '../../tipos/futbol';

// ══════════════════════════════════════════════════════════════
// TRANSFORMADORES
// ══════════════════════════════════════════════════════════════

function numeroDesde(data: Record<string, unknown>, ...keys: string[]): number | null {
  for (const key of keys) {
    if (data[key] !== undefined && data[key] !== null) {
      const n = Number(data[key]);
      if (Number.isFinite(n)) return n;
    }
  }
  return null;
}

/**
 * Transforma un partido resumen de snake_case a camelCase
 */
function transformarPartidoResumen(
  data: Record<string, unknown>
): PartidoFutbolResumen {
  return {
    id: String(data.id || ''),
    competicion: String(data.competicion || ''),
    competicionNombre: String(data.competicion_nombre || data.competicion || ''),
    fechaPartido: String(data.fecha_partido || ''),
    equipoLocal: String(data.equipo_local || ''),
    equipoLocalNombre: String(data.equipo_local_nombre || data.equipo_local || ''),
    equipoLocalLogo: data.equipo_local_logo as string | undefined,
    equipoVisitante: String(data.equipo_visitante || ''),
    equipoVisitanteNombre: String(data.equipo_visitante_nombre || data.equipo_visitante || ''),
    equipoVisitanteLogo: data.equipo_visitante_logo as string | undefined,
    estado: (data.estado as PartidoFutbolResumen['estado']) || 'PROGRAMADO',
    jornada: data.jornada ? Number(data.jornada) : undefined,
    golesLocal: data.goles_local !== undefined ? Number(data.goles_local) : undefined,
    golesVisitante:
      data.goles_visitante !== undefined ? Number(data.goles_visitante) : undefined,
  };
}

/**
 * Transforma una probabilidad de línea de snake_case a camelCase
 */
function transformarProbabilidadLinea(
  data: Record<string, unknown>
): ProbabilidadLinea {
  const razones = Array.isArray(data.razones) ? (data.razones as ProbabilidadLinea['razones']) : undefined;
  return {
    linea: numeroDesde(data, 'linea') ?? 0,
    overRaw: numeroDesde(data, 'over_raw', 'over') ?? Number.NaN,
    overCalibrada: numeroDesde(data, 'over_calibrada', 'over') ?? Number.NaN,
    underRaw: numeroDesde(data, 'under_raw', 'under') ?? Number.NaN,
    underCalibrada: numeroDesde(data, 'under_calibrada', 'under') ?? Number.NaN,
    razones,
  };
}

/**
 * Transforma una predicción de mercado de snake_case a camelCase
 */
function transformarPrediccionMercado(
  data: Record<string, unknown>
): PrediccionMercadoFutbol {
  const probabilidades = data.probabilidades;
  let probabilidadesArray = Array.isArray(probabilidades)
    ? probabilidades.map((p) =>
        transformarProbabilidadLinea(p as Record<string, unknown>)
      )
    : [];

  if (
    probabilidadesArray.length === 0 &&
    data.lineas &&
    typeof data.lineas === 'object'
  ) {
    probabilidadesArray = Object.entries(
      data.lineas as Record<string, unknown>
    ).map(([linea, payload]) =>
      transformarProbabilidadLinea({
        linea,
        ...(payload as Record<string, unknown>),
      })
    );
  }

  return {
    mercado: String(data.mercado || '') as TipoMercadoFutbol,
    media: numeroDesde(data, 'media') ?? Number.NaN,
    std: numeroDesde(data, 'std', 'desviacion') ?? Number.NaN,
    probabilidades: probabilidadesArray,
    confianza: (data.confianza as NivelConfianza) || 'MEDIA',
  };
}

/**
 * Transforma una recomendación de apuesta de snake_case a camelCase
 */
function transformarRecomendacion(
  data: Record<string, unknown>
): RecomendacionApuesta {
  return {
    mercado: String(data.mercado || '') as TipoMercadoFutbol,
    lado: (data.lado as 'OVER' | 'UNDER') || 'OVER',
    linea: Number(data.linea || 0),
    probabilidad: numeroDesde(data, 'probabilidad', 'p_calibrada', 'p_raw') ?? Number.NaN,
    confianza: (data.confianza as NivelConfianza) || 'MEDIA',
    valorEsperado: data.valor_esperado !== undefined ? Number(data.valor_esperado) : undefined,
    razon: String(data.razon || ''),
    pRaw: data.p_raw !== undefined ? Number(data.p_raw) : undefined,
    pCalibrada: data.p_calibrada !== undefined ? Number(data.p_calibrada) : undefined,
    edgeReal: data.edge_real !== undefined ? Number(data.edge_real) : undefined,
    score: data.score !== undefined ? Number(data.score) : undefined,
    sizing: data.sizing !== undefined ? Number(data.sizing) : undefined,
    cuota: data.cuota !== undefined ? Number(data.cuota) : undefined,
    cuotaOver: data.cuota_over !== undefined ? Number(data.cuota_over) : undefined,
    cuotaUnder: data.cuota_under !== undefined ? Number(data.cuota_under) : undefined,
    devigMetodo: data.devig_metodo !== undefined ? String(data.devig_metodo) : undefined,
    devigOverround: data.devig_overround !== undefined ? Number(data.devig_overround) : undefined,
    devigPMktFair: data.devig_p_mkt_fair !== undefined ? Number(data.devig_p_mkt_fair) : undefined,
    advertencias: Array.isArray(data.advertencias) ? data.advertencias as string[] : undefined,
    fuente: data.fuente !== undefined ? String(data.fuente) : undefined,
    metadataEnsemble: (data.metadata_ensemble && typeof data.metadata_ensemble === 'object')
      ? data.metadata_ensemble as Record<string, unknown>
      : undefined,
  };
}

/**
 * Transforma mercados agrupados de snake_case a camelCase
 */
function transformarMercadosAgrupados(
  data: Record<string, unknown>
): Record<string, PrediccionMercadoFutbol> {
  const resultado: Record<string, PrediccionMercadoFutbol> = {};

  Object.entries(data).forEach(([key, value]) => {
    if (value && typeof value === 'object') {
      resultado[key] = transformarPrediccionMercado(value as Record<string, unknown>);
    }
  });

  return resultado;
}

function transformarObjetivoAnalisis(
  data: Record<string, unknown>
): ObjetivoAnalisisFutbol {
  const bloqueBase = (data.bloque_base || {}) as Record<string, unknown>;
  const bloqueAjustado = (data.bloque_ajustado || {}) as Record<string, unknown>;
  const devig = (data.devig || {}) as Record<string, unknown>;
  const calibracion = (data.calibracion || {}) as Record<string, unknown>;
  const scoreRiesgo = (data.score_riesgo || {}) as Record<string, unknown>;
  const disponibilidad = (data.disponibilidad_datos || {}) as Record<string, unknown>;

  return {
    estado: (data.estado as ObjetivoAnalisisFutbol['estado']) || 'datos_insuficientes',
    mercado: String(data.mercado || '') as TipoMercadoFutbol,
    lado: (data.lado as 'OVER' | 'UNDER') || 'OVER',
    linea: Number(data.linea || 0),
    unidad: String(data.unidad || 'unidades'),
    mediaObjetivo: data.media_objetivo !== undefined ? Number(data.media_objetivo) : null,
    desviacionObjetivo: data.desviacion_objetivo !== undefined ? Number(data.desviacion_objetivo) : null,
    probabilidadesObjetivo: {
      over: data.probabilidades_objetivo && typeof data.probabilidades_objetivo === 'object'
        ? numeroDesde((data.probabilidades_objetivo as Record<string, unknown>), 'over')
        : null,
      under: data.probabilidades_objetivo && typeof data.probabilidades_objetivo === 'object'
        ? numeroDesde((data.probabilidades_objetivo as Record<string, unknown>), 'under')
        : null,
    },
    bloqueBase: {
      estado: (bloqueBase.estado as ObjetivoAnalisisFutbol['estado']) || 'datos_insuficientes',
      media: bloqueBase.media !== undefined ? Number(bloqueBase.media) : null,
      desviacion: bloqueBase.desviacion !== undefined ? Number(bloqueBase.desviacion) : null,
      probabilidades: {
        over: bloqueBase.probabilidades && typeof bloqueBase.probabilidades === 'object'
          ? numeroDesde((bloqueBase.probabilidades as Record<string, unknown>), 'over')
          : null,
        under: bloqueBase.probabilidades && typeof bloqueBase.probabilidades === 'object'
          ? numeroDesde((bloqueBase.probabilidades as Record<string, unknown>), 'under')
          : null,
      },
    },
    bloqueAjustado: {
      estado: (bloqueAjustado.estado as ObjetivoAnalisisFutbol['estado']) || 'no_disponible',
      media: bloqueAjustado.media !== undefined ? Number(bloqueAjustado.media) : null,
      desviacion: bloqueAjustado.desviacion !== undefined ? Number(bloqueAjustado.desviacion) : null,
      probabilidades: {
        over: bloqueAjustado.probabilidades && typeof bloqueAjustado.probabilidades === 'object'
          ? numeroDesde((bloqueAjustado.probabilidades as Record<string, unknown>), 'over')
          : null,
        under: bloqueAjustado.probabilidades && typeof bloqueAjustado.probabilidades === 'object'
          ? numeroDesde((bloqueAjustado.probabilidades as Record<string, unknown>), 'under')
          : null,
      },
    },
    devig: {
      estado: (devig.estado as ObjetivoAnalisisFutbol['estado']) || 'no_disponible',
      metodo: devig.metodo !== undefined ? String(devig.metodo) : null,
      overround: devig.overround !== undefined ? Number(devig.overround) : null,
      pMktFair: devig.p_mkt_fair !== undefined ? Number(devig.p_mkt_fair) : null,
      advertencias: Array.isArray(devig.advertencias) ? devig.advertencias as string[] : [],
    },
    calibracion: {
      estado: (calibracion.estado as ObjetivoAnalisisFutbol['estado']) || 'no_disponible',
      pRaw: calibracion.p_raw !== undefined ? Number(calibracion.p_raw) : null,
      pCalibrada: calibracion.p_calibrada !== undefined ? Number(calibracion.p_calibrada) : null,
      calibradorId: calibracion.calibrador_id !== undefined ? String(calibracion.calibrador_id) : null,
    },
    scoreRiesgo: {
      estado: (scoreRiesgo.estado as ObjetivoAnalisisFutbol['estado']) || 'no_disponible',
      score: scoreRiesgo.score !== undefined ? Number(scoreRiesgo.score) : null,
      sizing: scoreRiesgo.sizing !== undefined ? Number(scoreRiesgo.sizing) : null,
      edgeReal: scoreRiesgo.edge_real !== undefined ? Number(scoreRiesgo.edge_real) : null,
      valorEsperado: scoreRiesgo.valor_esperado !== undefined ? Number(scoreRiesgo.valor_esperado) : null,
      confianza: scoreRiesgo.confianza !== undefined ? String(scoreRiesgo.confianza) : null,
    },
    disponibilidadDatos: {
      realesDisponibles: Array.isArray(disponibilidad.reales_disponibles) ? disponibilidad.reales_disponibles as string[] : [],
      noDisponibles: Array.isArray(disponibilidad.no_disponibles) ? disponibilidad.no_disponibles as string[] : [],
      degradacionControlada: Array.isArray(disponibilidad.degradacion_controlada) ? disponibilidad.degradacion_controlada as string[] : [],
      datosInsuficientes: Array.isArray(disponibilidad.datos_insuficientes) ? disponibilidad.datos_insuficientes as string[] : [],
    },
    trazabilidad: (data.trazabilidad && typeof data.trazabilidad === 'object')
      ? data.trazabilidad as Record<string, unknown>
      : {},
  };
}

// ══════════════════════════════════════════════════════════════
// SERVICIOS
// ══════════════════════════════════════════════════════════════

/**
 * Analiza un partido de fútbol
 */
export async function analizarPartido(
  request: AnalisisFutbolRequest
): Promise<AnalisisFutbolResponse> {
  try {
    // Preparar el cuerpo de la petición en snake_case
    const body: Record<string, unknown> = {
      partido_id: request.partidoId,
    };

    if (request.lineasCorners) {
      body.lineas_corners = request.lineasCorners;
    }
    if (request.lineasGoles) {
      body.lineas_goles = request.lineasGoles;
    }
    if (request.lineasDisparos) {
      body.lineas_disparos = request.lineasDisparos;
    }
    if (request.h2hLimite !== undefined) {
      body.h2h_limite = request.h2hLimite;
    }
    if (request.mercadoObjetivo) {
      body.mercado_objetivo = request.mercadoObjetivo;
    }
    if (request.ladoObjetivo) {
      body.lado_objetivo = request.ladoObjetivo;
    }
    if (request.lineaObjetivo !== undefined) {
      body.linea_objetivo = request.lineaObjetivo;
    }
    if (request.cuotasPorLinea) {
      body.cuotas_por_linea = request.cuotasPorLinea;
    }

    const respuesta = await clienteAPI.post('/api/futbol/analizar', body);
    const data = respuesta.data;

    // Transformar la respuesta a camelCase
    const mercadosCorners = data.mercados_corners || data.mercadosCorners || {};
    const mercadosGoles = data.mercados_goles || data.mercadosGoles || {};
    const mercadosDisparos = data.mercados_disparos || data.mercadosDisparos || {};
    const recomendaciones = data.recomendaciones || [];

    const pg = data.prediccion_ganador || data.prediccionGanador;

    return {
      exito: Boolean(data.exito ?? true),
      partido: transformarPartidoResumen(data.partido || {}),
      timestampAnalisis: String(data.timestamp_analisis || data.timestampAnalisis || new Date().toISOString()),
      objetivo: transformarObjetivoAnalisis((data.objetivo || {}) as Record<string, unknown>),
      mercadosCorners: transformarMercadosAgrupados(mercadosCorners),
      mercadosGoles: transformarMercadosAgrupados(mercadosGoles),
      mercadosDisparos: transformarMercadosAgrupados(mercadosDisparos),
      recomendaciones: Array.isArray(recomendaciones)
        ? recomendaciones.map((r) =>
            transformarRecomendacion(r as Record<string, unknown>)
          )
        : [],
      modeloVersion: String(data.modelo_version || data.modeloVersion || '1.0.0'),
      calibradoresActivos: Number(data.calibradores_activos || data.calibradoresActivos || 0),
      prediccionGanador: pg && typeof pg === 'object'
        ? {
            probLocal: Number((pg as Record<string, unknown>).prob_local ?? (pg as Record<string, unknown>).probLocal ?? 0),
            probEmpate: Number((pg as Record<string, unknown>).prob_empate ?? (pg as Record<string, unknown>).probEmpate ?? 0),
            probVisitante: Number((pg as Record<string, unknown>).prob_visitante ?? (pg as Record<string, unknown>).probVisitante ?? 0),
            ganadorProbable: String((pg as Record<string, unknown>).ganador_probable ?? (pg as Record<string, unknown>).ganadorProbable ?? 'LOCAL') as 'LOCAL' | 'EMPATE' | 'VISITANTE',
            marcadorProbable: String((pg as Record<string, unknown>).marcador_probable ?? (pg as Record<string, unknown>).marcadorProbable ?? ''),
            razones: Array.isArray((pg as Record<string, unknown>).razones)
              ? ((pg as Record<string, unknown>).razones as string[])
              : [],
          }
        : undefined,
    };
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}
