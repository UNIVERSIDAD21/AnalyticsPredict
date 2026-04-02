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

export function adaptarAnalisisFutbolAResultadoAnalisis(
  analisis: AnalisisFutbolResponse,
  contexto?: AdaptadorContextoFutbol,
): ResultadoAnalisis {
  const mercadoMain = pickMainMarket(analisis);
  const lineaMain = mercadoMain?.probabilidades?.[0]?.linea ?? analisis.recomendaciones?.[0]?.linea ?? 2.5;
  const pOver = mercadoMain?.probabilidades?.find((p) => p.linea === lineaMain)?.overCalibrada
    ?? mercadoMain?.probabilidades?.[0]?.overCalibrada
    ?? analisis.recomendaciones?.[0]?.probabilidad
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
      cuota: 1.9,
      probabilidad_implicita: 1 / 1.9,
      edge: (analisis.recomendaciones?.[0]?.probabilidad ?? 0.5) - (1 / 1.9),
      valor_esperado: analisis.recomendaciones?.[0]?.valorEsperado ?? 0,
      recomendacion: mapearRecomendacion(analisis.recomendaciones?.[0]?.valorEsperado ?? 0),
    },
    mejor_apuesta: analisis.recomendaciones?.[0]
      ? {
          cuarto: 'COMPLETO',
          mercado: analisis.recomendaciones[0].mercado,
          lado: analisis.recomendaciones[0].lado,
          linea: analisis.recomendaciones[0].linea,
          probabilidad: analisis.recomendaciones[0].probabilidad,
          media: predMain.media_total,
          desviacion: predMain.desviacion_total,
          distancia_z: 0,
        }
      : null,
    es_en_vivo: false,
    cuartos_reales: {},
    metadata: {
      deporte: 'futbol',
      mercado: 'COMPLETO',
      policy_gate: 'POLICY_GATE_FUTBOL_MERCADOS_BLOQUEADOS',
      modelo_version: analisis.modeloVersion,
    },
    contexto: {
      h2h: {
        total_partidos: h2h.length,
        victorias_equipo: h2h.filter((p) => p.golesLocal > p.golesVisitante).length,
        victorias_rival: h2h.filter((p) => p.golesVisitante > p.golesLocal).length,
        promedio_total: promedio(h2h.map((p) => p.golesLocal + p.golesVisitante)),
        promedio_equipo: promedio(h2h.map((p) => p.golesLocal)),
        promedio_rival: promedio(h2h.map((p) => p.golesVisitante)),
        tendencia_over: promedio(h2h.map((p) => ((p.golesLocal + p.golesVisitante) > lineaMain ? 1 : 0))),
        ultimo_enfrentamiento: h2h[0] ? {
          fecha: h2h[0].fechaPartido,
          puntos_equipo: h2h[0].golesLocal,
          puntos_rival: h2h[0].golesVisitante,
          total: h2h[0].golesLocal + h2h[0].golesVisitante,
          ganador_id: h2h[0].golesLocal >= h2h[0].golesVisitante ? 'equipo' : 'rival',
        } : null,
        partidos: h2h.map((p) => ({
          fecha: p.fechaPartido,
          puntos_equipo: p.golesLocal,
          puntos_rival: p.golesVisitante,
          total: p.golesLocal + p.golesVisitante,
          ganador_id: p.golesLocal >= p.golesVisitante ? 'equipo' : 'rival',
          diferencia_puntos: p.golesLocal - p.golesVisitante,
        })),
      },
      forma_equipo: {
        ultimos_n: historialLocal.length,
        victorias: historialLocal.filter((p) => p.golesLocal > p.golesVisitante).length,
        derrotas: historialLocal.filter((p) => p.golesLocal < p.golesVisitante).length,
        racha: 'N/A',
        ppg: promedio(historialLocal.map((p) => p.golesLocal)),
        opp_ppg: promedio(historialLocal.map((p) => p.golesVisitante)),
        net_rating: promedio(historialLocal.map((p) => p.golesLocal - p.golesVisitante)),
        ppg_temporada: promedio(historialLocal.map((p) => p.golesLocal)),
        diferencia_vs_temporada: 0,
        tendencia: 'ESTABLE',
      },
      forma_rival: {
        ultimos_n: historialVisitante.length,
        victorias: historialVisitante.filter((p) => p.golesVisitante > p.golesLocal).length,
        derrotas: historialVisitante.filter((p) => p.golesVisitante < p.golesLocal).length,
        racha: 'N/A',
        ppg: promedio(historialVisitante.map((p) => p.golesVisitante)),
        opp_ppg: promedio(historialVisitante.map((p) => p.golesLocal)),
        net_rating: promedio(historialVisitante.map((p) => p.golesVisitante - p.golesLocal)),
        ppg_temporada: promedio(historialVisitante.map((p) => p.golesVisitante)),
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
