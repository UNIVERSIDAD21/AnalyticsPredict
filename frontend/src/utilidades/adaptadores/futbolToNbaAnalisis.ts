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
  const mercadoObjetivo = analisis.mercadoObjetivo;
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
    (!analisis.mercadoObjetivo || r.mercado === analisis.mercadoObjetivo)
    && (!analisis.ladoObjetivo || r.lado === analisis.ladoObjetivo)
    && (analisis.lineaObjetivo === undefined || Math.abs(r.linea - analisis.lineaObjetivo) < 1e-9)
  )) ?? analisis.recomendaciones?.[0];

  const mercadoMain = pickMainMarket(analisis);
  const lineaMain = analisis.lineaObjetivo ?? mercadoMain?.probabilidades?.[0]?.linea ?? recObjetivo?.linea ?? 2.5;
  const pOver = mercadoMain?.probabilidades?.find((p) => p.linea === lineaMain)?.overCalibrada
    ?? mercadoMain?.probabilidades?.[0]?.overCalibrada
    ?? recObjetivo?.probabilidad
    ?? 0.5;
  const pUnder = 1 - pOver;

  const mediaTotal = mercadoMain?.media ?? 0;
  const stdTotal = mercadoMain?.std ?? 1;
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

  const mejorApuestaDetalle = recObjetivo ? {
    mercado: recObjetivo.mercado,
    lado: recObjetivo.lado,
    linea: recObjetivo.linea,
    cuota: recObjetivo.cuota ?? recObjetivo.cuotaOver ?? recObjetivo.cuotaUnder ?? 0,
    cuota_over: recObjetivo.cuotaOver ?? null,
    cuota_under: recObjetivo.cuotaUnder ?? null,
    probabilidad_sistema: recObjetivo.probabilidad,
    edge_real: recObjetivo.edgeReal ?? null,
    valor_esperado: recObjetivo.valorEsperado ?? null,
    prediccion_media: mediaTotal,
    prediccion_desviacion: stdTotal,
    distancia_z: 0,
    p_raw: recObjetivo.pRaw ?? null,
    p_calibrada: recObjetivo.pCalibrada ?? null,
    calibrador_usado: null,
    devig_metodo: recObjetivo.devigMetodo ?? 'no_aplicado',
    devig_overround: recObjetivo.devigOverround ?? null,
    devig_p_mkt_raw: 1 / (recObjetivo.cuota ?? 2),
    devig_p_mkt_fair: recObjetivo.devigPMktFair ?? (1 / (recObjetivo.cuota ?? 2)),
    devig_advertencias: recObjetivo.advertencias ?? [],
    edge_raw: null,
    score_total: recObjetivo.score ?? 0,
    score_componentes: { ev: 0, edge_real: 0, riesgo_valor: 0, riesgo_referencia: 1, riesgo_normalizado: 0, penalizacion_riesgo: 0, penalizacion_devig: 0 },
    score_explicacion: recObjetivo.razon || 'Score calculado por backend fútbol',
    score_penalizaciones: [],
    kelly_full: recObjetivo.sizing ?? null,
    kelly_fraccional: recObjetivo.sizing ?? null,
    fraccion_kelly: recObjetivo.sizing ?? null,
    stake: null,
    stake_porcentaje: null,
    bankroll_momento: null,
    perfil_riesgo_usado: 'MEDIO',
    sizing_advertencias: [],
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
    analisis_mercado: {
      cuota: recObjetivo?.cuota ?? recObjetivo?.cuotaOver ?? recObjetivo?.cuotaUnder ?? 1.9,
      probabilidad_implicita: 1 / (recObjetivo?.cuota ?? recObjetivo?.cuotaOver ?? recObjetivo?.cuotaUnder ?? 1.9),
      edge: (recObjetivo?.probabilidad ?? 0.5) - (1 / (recObjetivo?.cuota ?? recObjetivo?.cuotaOver ?? recObjetivo?.cuotaUnder ?? 1.9)),
      valor_esperado: recObjetivo?.valorEsperado ?? 0,
      recomendacion: mapearRecomendacion(recObjetivo?.valorEsperado ?? 0),
    },
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
      mercado: analisis.mercadoObjetivo ?? 'COMPLETO',
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
    linea_analizada: lineaMain,
    mensaje_apuesta: analisis.recomendaciones?.length ? 'Tu predicción coincide con la recomendación del sistema' : 'Sin recomendación disponible',
  } as ResultadoAnalisis;
}
