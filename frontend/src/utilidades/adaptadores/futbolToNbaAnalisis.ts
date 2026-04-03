import type { ResultadoAnalisis, PrediccionCuarto, NivelConfianza as NivelConfianzaNba, TipoRecomendacion } from '../../tipos/analisis';
import type { AnalisisFutbolResponse, PrediccionMercadoFutbol, NivelConfianza as NivelConfianzaFutbol, PartidoFutbolEstadistico } from '../../tipos/futbol';

interface AdaptadorContextoFutbol {
  h2h?: PartidoFutbolEstadistico[];
  historialLocal?: PartidoFutbolEstadistico[];
  historialVisitante?: PartidoFutbolEstadistico[];
}

function normalizarConfianza(confianza?: NivelConfianzaFutbol): NivelConfianzaNba {
  if (confianza === 'MUY_ALTA' || confianza === 'ALTA') return 'ALTA';
  if (confianza === 'MUY_BAJA' || confianza === 'BAJA') return 'BAJA';
  return 'MEDIA';
}

function mapearRecomendacion(valorEsperado: number): TipoRecomendacion {
  if (valorEsperado > 0.02) return 'VALOR';
  if (valorEsperado < 0) return 'EVITAR';
  return 'JUSTO';
}

function pickMainMarket(analisis: AnalisisFutbolResponse): PrediccionMercadoFutbol | null {
  const mercadoObjetivo = analisis.objetivo?.mercado;
  if (mercadoObjetivo) {
    return (
      analisis.mercadosGoles[mercadoObjetivo]
      || analisis.mercadosCorners[mercadoObjetivo]
      || analisis.mercadosDisparos[mercadoObjetivo]
      || null
    );
  }

  const rec = analisis.recomendaciones?.[0];
  if (rec) {
    return (
      analisis.mercadosGoles[rec.mercado]
      || analisis.mercadosCorners[rec.mercado]
      || analisis.mercadosDisparos[rec.mercado]
      || null
    );
  }

  return (
    Object.values(analisis.mercadosGoles)[0]
    || Object.values(analisis.mercadosCorners)[0]
    || Object.values(analisis.mercadosDisparos)[0]
    || null
  );
}

function promedio(nums: number[]): number {
  if (nums.length === 0) return 0;
  return nums.reduce((acc, n) => acc + n, 0) / nums.length;
}

function numeroSeguro(valor: unknown, fallback = 0): number {
  const n = typeof valor === 'number' ? valor : Number(valor);
  return Number.isFinite(n) ? n : fallback;
}

function cuotaValida(cuota?: number | null): number | null {
  const n = numeroSeguro(cuota, NaN);
  if (!Number.isFinite(n) || n <= 1) return null;
  return n;
}

function desdePerspectiva(partido: PartidoFutbolEstadistico, equipoId: string): { equipo: number; rival: number } {
  const esLocal = String(partido.equipoLocalId) === String(equipoId);
  if (esLocal) return { equipo: partido.golesLocal, rival: partido.golesVisitante };
  return { equipo: partido.golesVisitante, rival: partido.golesLocal };
}

function rachaDesdeHistorial(partidos: PartidoFutbolEstadistico[], equipoId: string): string {
  if (!partidos.length) return '0E';
  let tipo: 'G' | 'E' | 'P' | null = null;
  let n = 0;
  for (const partido of partidos) {
    const m = desdePerspectiva(partido, equipoId);
    const actual: 'G' | 'E' | 'P' = m.equipo > m.rival ? 'G' : (m.equipo < m.rival ? 'P' : 'E');
    if (tipo === null) {
      tipo = actual;
      n = 1;
      continue;
    }
    if (actual === tipo) n += 1;
    else break;
  }
  return `${n}${tipo}`;
}

export function adaptarAnalisisFutbolAResultadoAnalisis(
  analisis: AnalisisFutbolResponse,
  contexto?: AdaptadorContextoFutbol,
): ResultadoAnalisis {
  const recObjetivo = analisis.recomendaciones.find((r) => (
    (!analisis.objetivo?.mercado || r.mercado === analisis.objetivo.mercado)
    && (!analisis.objetivo?.lado || r.lado === analisis.objetivo.lado)
    && (analisis.objetivo?.linea === undefined || Math.abs(r.linea - analisis.objetivo.linea) < 1e-9)
  )) ?? analisis.recomendaciones?.[0];

  const mercadoMain = pickMainMarket(analisis);
  const lineaMain = numeroSeguro(analisis.objetivo?.linea ?? mercadoMain?.probabilidades?.[0]?.linea ?? recObjetivo?.linea, 0);
  const pOver = numeroSeguro(
    mercadoMain?.probabilidades?.find((p) => p.linea === lineaMain)?.overCalibrada
    ?? mercadoMain?.probabilidades?.[0]?.overCalibrada
    ?? recObjetivo?.probabilidad,
    0,
  );
  const pUnder = Math.max(0, Math.min(1, 1 - pOver));

  const mediaTotal = numeroSeguro(mercadoMain?.media, 0);
  const stdTotal = numeroSeguro(mercadoMain?.std, 0);
  const mediaEq = mediaTotal * 0.48;
  const mediaRv = mediaTotal * 0.52;
  const stdEq = Math.max(0.5, stdTotal * 0.7);
  const stdRv = Math.max(0.5, stdTotal * 0.7);

  const h2h = contexto?.h2h ?? [];
  const historialLocal = contexto?.historialLocal ?? [];
  const historialVisitante = contexto?.historialVisitante ?? [];
  const equipoAnalizadoId = String(analisis.partido.equipoLocal);
  const rivalAnalizadoId = String(analisis.partido.equipoVisitante);

  const predMain: PrediccionCuarto = {
    cuarto: 'COMPLETO',
    media_equipo: mediaEq,
    desviacion_equipo: stdEq,
    rango_equipo: [mediaEq - stdEq, mediaEq + stdEq],
    media_rival: mediaRv,
    desviacion_rival: stdRv,
    rango_rival: [mediaRv - stdRv, mediaRv + stdRv],
    media_total: mediaTotal,
    desviacion_total: stdTotal,
    rango_total: [mediaTotal - stdTotal, mediaTotal + stdTotal],
    linea_analizada: lineaMain,
    probabilidad_over: pOver,
    probabilidad_under: pUnder,
    ganador_probable: (analisis.prediccionGanador?.ganadorProbable === 'LOCAL' ? 'equipo' : 'rival'),
    probabilidad_ganador: Math.max(
      analisis.prediccionGanador?.probLocal ?? 0,
      analisis.prediccionGanador?.probVisitante ?? 0,
      analisis.prediccionGanador?.probEmpate ?? 0,
    ),
  };

  const cuotaPrincipal = cuotaValida(recObjetivo?.cuota) ?? cuotaValida(recObjetivo?.cuotaOver) ?? cuotaValida(recObjetivo?.cuotaUnder);
  const pMktRaw = cuotaPrincipal ? (1 / cuotaPrincipal) : null;
  const pMktFair = numeroSeguro(recObjetivo?.devigPMktFair, pMktRaw ?? 0);
  const scoreValido = cuotaPrincipal && Number.isFinite(recObjetivo?.score ?? NaN)
    ? Number(recObjetivo?.score)
    : null;

  const mejorApuestaDetalle = recObjetivo ? {
    mercado: recObjetivo.mercado,
    lado: recObjetivo.lado,
    linea: recObjetivo.linea,
    cuota: cuotaPrincipal ?? 0,
    cuota_over: cuotaValida(recObjetivo.cuotaOver) ?? null,
    cuota_under: cuotaValida(recObjetivo.cuotaUnder) ?? null,
    probabilidad_sistema: numeroSeguro(recObjetivo.probabilidad, 0),
    edge_real: Number.isFinite(recObjetivo.edgeReal ?? NaN) ? recObjetivo.edgeReal ?? null : null,
    valor_esperado: Number.isFinite(recObjetivo.valorEsperado ?? NaN) ? recObjetivo.valorEsperado ?? null : null,
    prediccion_media: mediaTotal,
    prediccion_desviacion: stdTotal,
    distancia_z: 0,
    p_raw: Number.isFinite(recObjetivo.pRaw ?? NaN) ? recObjetivo.pRaw ?? null : null,
    p_calibrada: Number.isFinite(recObjetivo.pCalibrada ?? NaN) ? recObjetivo.pCalibrada ?? null : null,
    calibrador_usado: null,
    devig_metodo: cuotaPrincipal ? (recObjetivo.devigMetodo ?? 'estimado') : 'no_aplicado',
    devig_overround: Number.isFinite(recObjetivo.devigOverround ?? NaN) ? recObjetivo.devigOverround ?? null : null,
    devig_p_mkt_raw: pMktRaw ?? Number.NaN,
    devig_p_mkt_fair: cuotaPrincipal ? pMktFair : Number.NaN,
    devig_advertencias: cuotaPrincipal ? (recObjetivo.advertencias ?? []) : ['Sin cuotas reales: no se puede calcular de-vig de mercado'],
    edge_raw: null,
    score_total: scoreValido ?? -1000,
    score_componentes: { ev: 0, edge_real: 0, riesgo_valor: 0, riesgo_referencia: 1, riesgo_normalizado: 0, penalizacion_riesgo: 0, penalizacion_devig: cuotaPrincipal ? 0 : -20 },
    score_explicacion: scoreValido === null
      ? 'Score no disponible: faltan datos mínimos válidos para evaluación de valor.'
      : (recObjetivo.razon || 'Score calculado por backend fútbol'),
    score_penalizaciones: cuotaPrincipal ? [] : ['SIN_DEVIG'],
    kelly_full: Number.isFinite(recObjetivo.sizing ?? NaN) ? recObjetivo.sizing ?? null : null,
    kelly_fraccional: Number.isFinite(recObjetivo.sizing ?? NaN) ? recObjetivo.sizing ?? null : null,
    fraccion_kelly: Number.isFinite(recObjetivo.sizing ?? NaN) ? recObjetivo.sizing ?? null : null,
    stake: null,
    stake_porcentaje: null,
    bankroll_momento: null,
    perfil_riesgo_usado: 'MEDIO',
    sizing_advertencias: cuotaPrincipal ? [] : ['Sin cuotas reales, sizing degradado'],
    sizing_penalizaciones: {},
    aplicaron_caps: false,
  } : null;

  return {
    equipo: analisis.partido.equipoLocalNombre,
    equipo_nombre_completo: analisis.partido.equipoLocalNombre,
    rival: analisis.partido.equipoVisitanteNombre,
    rival_nombre_completo: analisis.partido.equipoVisitanteNombre,
    ubicacion: 'LOCAL',
    fecha_analisis: analisis.timestampAnalisis,
    predicciones: { COMPLETO: predMain },
    prediccion_juego_completo: predMain,
    razones: [
      {
        factor: 'prediccion_sistema',
        direccion: 'sube',
        impacto: predMain.media_total,
        descripcion: `Sistema proyecta ${predMain.media_total.toFixed(1)} en mercado principal de fútbol.`,
      },
    ],
    nivel_confianza: normalizarConfianza(analisis.recomendaciones?.[0]?.confianza),
    factores_confianza: {
      tamano_muestra: 'MEDIO',
      volatilidad: 'MEDIA',
      frescura_datos: 'ALTA',
      puntaje_total: 0.65,
    },
    analisis_mercado: cuotaPrincipal
      ? {
          cuota: cuotaPrincipal,
          probabilidad_implicita: 1 / cuotaPrincipal,
          edge: (recObjetivo?.probabilidad ?? 0) - (1 / cuotaPrincipal),
          valor_esperado: recObjetivo?.valorEsperado ?? 0,
          recomendacion: mapearRecomendacion(recObjetivo?.valorEsperado ?? 0),
        }
      : null,
    mejor_apuesta: recObjetivo
      ? {
          cuarto: 'COMPLETO',
          mercado: recObjetivo.mercado,
          lado: recObjetivo.lado,
          linea: recObjetivo.linea,
          probabilidad: recObjetivo.probabilidad,
          media: predMain.media_total,
          desviacion: predMain.desviacion_total,
          distancia_z: 0,
        }
      : null,
    mejor_apuesta_detalle: mejorApuestaDetalle as ResultadoAnalisis['mejor_apuesta_detalle'],
    es_en_vivo: false,
    cuartos_reales: {},
    metadata: {
      deporte: 'futbol',
      mercado: analisis.objetivo?.mercado ?? 'COMPLETO',
      policy_gate: 'POLICY_GATE_FUTBOL_MERCADOS_BLOQUEADOS',
      modelo_version: analisis.modeloVersion,
    },
    contexto: {
      h2h: {
        total_partidos: h2h.length,
        victorias_equipo: h2h.filter((p) => {
          const m = desdePerspectiva(p, equipoAnalizadoId);
          return m.equipo > m.rival;
        }).length,
        victorias_rival: h2h.filter((p) => {
          const m = desdePerspectiva(p, equipoAnalizadoId);
          return m.rival > m.equipo;
        }).length,
        promedio_total: promedio(h2h.map((p) => p.golesLocal + p.golesVisitante)),
        promedio_equipo: promedio(h2h.map((p) => desdePerspectiva(p, equipoAnalizadoId).equipo)),
        promedio_rival: promedio(h2h.map((p) => desdePerspectiva(p, equipoAnalizadoId).rival)),
        tendencia_over: promedio(h2h.map((p) => ((p.golesLocal + p.golesVisitante) > lineaMain ? 1 : 0))),
        ultimo_enfrentamiento: h2h[0] ? {
          fecha: h2h[0].fechaPartido,
          puntos_equipo: desdePerspectiva(h2h[0], equipoAnalizadoId).equipo,
          puntos_rival: desdePerspectiva(h2h[0], equipoAnalizadoId).rival,
          total: h2h[0].golesLocal + h2h[0].golesVisitante,
          ganador_id: desdePerspectiva(h2h[0], equipoAnalizadoId).equipo >= desdePerspectiva(h2h[0], equipoAnalizadoId).rival ? 'equipo' : 'rival',
        } : null,
        partidos: h2h.map((p) => ({
          fecha: p.fechaPartido,
          puntos_equipo: desdePerspectiva(p, equipoAnalizadoId).equipo,
          puntos_rival: desdePerspectiva(p, equipoAnalizadoId).rival,
          total: p.golesLocal + p.golesVisitante,
          ganador_id: desdePerspectiva(p, equipoAnalizadoId).equipo >= desdePerspectiva(p, equipoAnalizadoId).rival ? 'equipo' : 'rival',
          diferencia_puntos: desdePerspectiva(p, equipoAnalizadoId).equipo - desdePerspectiva(p, equipoAnalizadoId).rival,
        })),
      },
      forma_equipo: {
        ultimos_n: historialLocal.length,
        victorias: historialLocal.filter((p) => desdePerspectiva(p, equipoAnalizadoId).equipo > desdePerspectiva(p, equipoAnalizadoId).rival).length,
        derrotas: historialLocal.filter((p) => desdePerspectiva(p, equipoAnalizadoId).equipo < desdePerspectiva(p, equipoAnalizadoId).rival).length,
        racha: rachaDesdeHistorial(historialLocal, equipoAnalizadoId),
        ppg: promedio(historialLocal.map((p) => desdePerspectiva(p, equipoAnalizadoId).equipo)),
        opp_ppg: promedio(historialLocal.map((p) => desdePerspectiva(p, equipoAnalizadoId).rival)),
        net_rating: promedio(historialLocal.map((p) => desdePerspectiva(p, equipoAnalizadoId).equipo - desdePerspectiva(p, equipoAnalizadoId).rival)),
        ppg_temporada: promedio(historialLocal.map((p) => desdePerspectiva(p, equipoAnalizadoId).equipo)),
        diferencia_vs_temporada: 0,
        tendencia: 'ESTABLE',
      },
      forma_rival: {
        ultimos_n: historialVisitante.length,
        victorias: historialVisitante.filter((p) => desdePerspectiva(p, rivalAnalizadoId).equipo > desdePerspectiva(p, rivalAnalizadoId).rival).length,
        derrotas: historialVisitante.filter((p) => desdePerspectiva(p, rivalAnalizadoId).equipo < desdePerspectiva(p, rivalAnalizadoId).rival).length,
        racha: rachaDesdeHistorial(historialVisitante, rivalAnalizadoId),
        ppg: promedio(historialVisitante.map((p) => desdePerspectiva(p, rivalAnalizadoId).equipo)),
        opp_ppg: promedio(historialVisitante.map((p) => desdePerspectiva(p, rivalAnalizadoId).rival)),
        net_rating: promedio(historialVisitante.map((p) => desdePerspectiva(p, rivalAnalizadoId).equipo - desdePerspectiva(p, rivalAnalizadoId).rival)),
        ppg_temporada: promedio(historialVisitante.map((p) => desdePerspectiva(p, rivalAnalizadoId).equipo)),
        diferencia_vs_temporada: 0,
        tendencia: 'ESTABLE',
      },
      descanso_equipo: { dias_descanso: 3, es_back_to_back: false, ultimo_partido: null, distancia_viaje_km: null },
      descanso_rival: { dias_descanso: 3, es_back_to_back: false, ultimo_partido: null, distancia_viaje_km: null },
      stats_temporada_equipo: {},
      stats_temporada_rival: {},
    },
    prediccion_base: {
      media: mediaTotal,
      probabilidad_over: pOver,
      probabilidad_under: pUnder,
    },
    prediccion_ajustada: {
      media_base: mediaTotal,
      desviacion_base: stdTotal,
      probabilidad_over_base: pOver,
      probabilidad_under_base: pUnder,
      media_ajustada: mediaTotal,
      probabilidad_over_ajustada: pOver,
      probabilidad_under_ajustada: pUnder,
      ajustes_aplicados: {
        ajustes: [],
        ajuste_total: 0,
        ajuste_total_capped: 0,
        fue_capped: false,
        advertencias: [],
        confianza_delta: 0,
      },
      confianza_base: normalizarConfianza(analisis.recomendaciones?.[0]?.confianza),
      confianza_ajustada: normalizarConfianza(analisis.recomendaciones?.[0]?.confianza),
    },
    ajustes: {
      ajustes: [],
      ajuste_total: 0,
      ajuste_total_capped: 0,
      fue_capped: false,
      advertencias: [],
      confianza_delta: 0,
    },
    probabilidad_over: pOver,
    probabilidad_under: pUnder,
    linea_analizada: lineaMain > 0 ? lineaMain : null,
    advertencias_contexto: [
      ...(mediaTotal <= 0 || stdTotal <= 0 ? ['Mercado principal sin media/desviación válidas. Verifica selección y disponibilidad de datos.'] : []),
      ...(!cuotaPrincipal ? ['Análisis sin cuotas reales: se desactiva comparación de valor contra mercado.'] : []),
    ],
    mensaje_apuesta: analisis.recomendaciones?.length
      ? (mediaTotal <= 0 || stdTotal <= 0
          ? 'Inconsistencia detectada: faltan datos válidos del mercado principal para evaluación completa.'
          : 'Tu predicción coincide con la recomendación del sistema')
      : 'Sin recomendación disponible',
  } as ResultadoAnalisis;
}
