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
  if (!mercadoObjetivo) return null;
  return (
    analisis.mercadosGoles[mercadoObjetivo]
    || analisis.mercadosCorners[mercadoObjetivo]
    || analisis.mercadosDisparos[mercadoObjetivo]
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

function numeroNullable(valor: unknown): number | null {
  const n = typeof valor === 'number' ? valor : Number(valor);
  return Number.isFinite(n) ? n : null;
}

function buscarProbabilidadLinea(mercado: PrediccionMercadoFutbol | null, linea: number): PrediccionMercadoFutbol['probabilidades'][number] | null {
  if (!mercado) return null;
  return mercado.probabilidades.find((p) => Math.abs(p.linea - linea) < 1e-9)
    ?? mercado.probabilidades.find((p) => Math.abs(p.linea - linea) < 1e-6)
    ?? null;
}

function cuotaValida(cuota?: number | null): number | null {
  const n = numeroSeguro(cuota, NaN);
  if (!Number.isFinite(n) || n <= 1) return null;
  return n;
}

type EstadoCuotas = 'sin_cuotas' | 'cuota_unica' | 'cuotas_completas' | 'no_disponible';

function clasificarEstadoCuotas(rec: AnalisisFutbolResponse['recomendaciones'][number] | undefined): {
  estado: EstadoCuotas;
  cuotaSeleccion: number | null;
  cuotaOver: number | null;
  cuotaUnder: number | null;
} {
  if (!rec) return { estado: 'no_disponible', cuotaSeleccion: null, cuotaOver: null, cuotaUnder: null };
  const cuotaOver = cuotaValida(rec.cuotaOver);
  const cuotaUnder = cuotaValida(rec.cuotaUnder);
  const cuotaSeleccion = cuotaValida(rec.cuota) ?? (rec.lado === 'OVER' ? cuotaOver : cuotaUnder) ?? cuotaOver ?? cuotaUnder;

  const validas = [cuotaOver, cuotaUnder].filter((c) => c !== null).length;
  if (validas === 2) return { estado: 'cuotas_completas', cuotaSeleccion, cuotaOver, cuotaUnder };
  if (validas === 1 || cuotaSeleccion !== null) return { estado: 'cuota_unica', cuotaSeleccion, cuotaOver, cuotaUnder };
  return { estado: 'sin_cuotas', cuotaSeleccion: null, cuotaOver: null, cuotaUnder: null };
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

function tendenciaDesdeHistorial(partidos: PartidoFutbolEstadistico[], equipoId: string): 'MEJORANDO' | 'EMPEORANDO' | 'ESTABLE' {
  if (partidos.length < 4) return 'ESTABLE';
  const recientes = partidos.slice(0, Math.min(5, partidos.length));
  const previos = partidos.slice(recientes.length, Math.min(recientes.length * 2, partidos.length));
  if (!previos.length) return 'ESTABLE';
  const promedioReciente = promedio(recientes.map((p) => desdePerspectiva(p, equipoId).equipo));
  const promedioPrevio = promedio(previos.map((p) => desdePerspectiva(p, equipoId).equipo));
  const delta = promedioReciente - promedioPrevio;
  if (delta > 0.25) return 'MEJORANDO';
  if (delta < -0.25) return 'EMPEORANDO';
  return 'ESTABLE';
}

function diferenciaVsTemporadaDesdeHistorial(partidos: PartidoFutbolEstadistico[], equipoId: string): number {
  if (!partidos.length) return 0;
  const muestraReciente = promedio(partidos.slice(0, Math.min(5, partidos.length)).map((p) => desdePerspectiva(p, equipoId).equipo));
  const muestraTotal = promedio(partidos.map((p) => desdePerspectiva(p, equipoId).equipo));
  return muestraReciente - muestraTotal;
}

export function adaptarAnalisisFutbolAResultadoAnalisis(
  analisis: AnalisisFutbolResponse,
  contexto?: AdaptadorContextoFutbol,
): ResultadoAnalisis {
  const recObjetivo = analisis.recomendaciones.find((r) => (
    (!analisis.objetivo?.mercado || r.mercado === analisis.objetivo.mercado)
    && (!analisis.objetivo?.lado || r.lado === analisis.objetivo.lado)
    && (analisis.objetivo?.linea === undefined || Math.abs(r.linea - analisis.objetivo.linea) < 1e-9)
  )) ?? null;

  const mercadoMain = pickMainMarket(analisis);
  const lineaMain = numeroNullable(analisis.objetivo?.linea);
  const probLineaObjetivo = lineaMain !== null ? buscarProbabilidadLinea(mercadoMain, lineaMain) : null;

  const pOverBase = numeroNullable(analisis.objetivo?.probabilidadesObjetivo?.over)
    ?? numeroNullable(probLineaObjetivo?.overCalibrada)
    ?? (recObjetivo && recObjetivo.lado === 'OVER' ? numeroNullable(recObjetivo.probabilidad) : null);
  const pUnderBase = numeroNullable(analisis.objetivo?.probabilidadesObjetivo?.under)
    ?? numeroNullable(probLineaObjetivo?.underCalibrada)
    ?? (recObjetivo && recObjetivo.lado === 'UNDER' ? numeroNullable(recObjetivo.probabilidad) : null);

  const pOver = pOverBase ?? (pUnderBase !== null ? Math.max(0, Math.min(1, 1 - pUnderBase)) : null);
  const pUnder = pUnderBase ?? (pOverBase !== null ? Math.max(0, Math.min(1, 1 - pOverBase)) : null);

  const mediaTotal = numeroNullable(analisis.objetivo?.mediaObjetivo) ?? numeroNullable(mercadoMain?.media);
  const stdTotal = numeroNullable(analisis.objetivo?.desviacionObjetivo) ?? numeroNullable(mercadoMain?.std);
  const mediaTotalRender = mediaTotal ?? Number.NaN;
  const stdTotalRender = stdTotal ?? Number.NaN;
  const mediaEq = Number.isFinite(mediaTotalRender) ? mediaTotalRender * 0.48 : Number.NaN;
  const mediaRv = Number.isFinite(mediaTotalRender) ? mediaTotalRender * 0.52 : Number.NaN;
  const stdEq = Number.isFinite(stdTotalRender) ? Math.max(0.5, stdTotalRender * 0.7) : Number.NaN;
  const stdRv = Number.isFinite(stdTotalRender) ? Math.max(0.5, stdTotalRender * 0.7) : Number.NaN;

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
    media_total: mediaTotalRender,
    desviacion_total: stdTotalRender,
    rango_total: [mediaTotalRender - stdTotalRender, mediaTotalRender + stdTotalRender],
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

  const estadoCuotas = clasificarEstadoCuotas(recObjetivo ?? undefined);
  const cuotaPrincipal = estadoCuotas.cuotaSeleccion;
  const pMktRaw = cuotaPrincipal ? (1 / cuotaPrincipal) : null;
  const overroundBackend = numeroNullable(recObjetivo?.devigOverround);
  const overroundValido = overroundBackend !== null && overroundBackend > 0.9 && overroundBackend < 2.0;
  const pMktFairBackend = numeroNullable(recObjetivo?.devigPMktFair);
  const pMktFair = (estadoCuotas.estado === 'cuotas_completas' && pMktFairBackend !== null) ? pMktFairBackend : null;

  const metodoDevig: 'exacto' | 'estimado' | 'no_aplicado' = estadoCuotas.estado === 'cuotas_completas'
    ? 'exacto'
    : estadoCuotas.estado === 'cuota_unica'
      ? 'estimado'
      : 'no_aplicado';

  const edgeRealCanonico = metodoDevig === 'exacto' ? numeroNullable(recObjetivo?.edgeReal) : null;
  const edgeRawCanonico = (pMktRaw !== null && numeroNullable(recObjetivo?.pRaw) !== null)
    ? (numeroNullable(recObjetivo?.pRaw)! - pMktRaw)
    : null;

  const scoreValido = (metodoDevig === 'exacto') && Number.isFinite(recObjetivo?.score ?? NaN)
    ? Number(recObjetivo?.score)
    : null;

  const advertenciasDevig = [
    ...(recObjetivo?.advertencias ?? []),
    ...(estadoCuotas.estado === 'sin_cuotas' ? ['Sin cuotas: comparación real contra la casa no disponible.'] : []),
    ...(estadoCuotas.estado === 'cuota_unica' ? ['Cuota única: de-vig interno estimado, no comparable como mercado completo.'] : []),
    ...(estadoCuotas.estado === 'cuotas_completas' && !overroundValido ? ['Overround inválido/absurdo: de-vig marcado como no disponible.'] : []),
  ];

  const penalizacionesScore: string[] = [];
  if (estadoCuotas.estado === 'sin_cuotas') penalizacionesScore.push('SIN_DEVIG');
  if (estadoCuotas.estado === 'cuota_unica') penalizacionesScore.push('DEVIG_ESTIMADO');

  const kellyCanonico = (metodoDevig === 'exacto') ? numeroNullable(recObjetivo?.sizing) : null;

  const mejorApuestaDetalle = recObjetivo ? {
    mercado: recObjetivo.mercado,
    lado: recObjetivo.lado,
    linea: recObjetivo.linea,
    cuota: cuotaPrincipal ?? 0,
    cuota_over: estadoCuotas.cuotaOver,
    cuota_under: estadoCuotas.cuotaUnder,
    probabilidad_sistema: numeroNullable(recObjetivo.probabilidad) ?? Number.NaN,
    edge_real: edgeRealCanonico,
    valor_esperado: metodoDevig === 'exacto' ? (numeroNullable(recObjetivo.valorEsperado)) : null,
    prediccion_media: mediaTotalRender,
    prediccion_desviacion: stdTotalRender,
    distancia_z: 0,
    p_raw: numeroNullable(recObjetivo.pRaw),
    p_calibrada: numeroNullable(recObjetivo.pCalibrada),
    calibrador_usado: null,
    devig_metodo: metodoDevig,
    devig_overround: (metodoDevig === 'exacto' && overroundValido) ? overroundBackend : null,
    devig_p_mkt_raw: pMktRaw ?? Number.NaN,
    devig_p_mkt_fair: pMktFair ?? Number.NaN,
    devig_advertencias: advertenciasDevig,
    edge_raw: edgeRawCanonico,
    score_total: scoreValido,
    score_componentes: scoreValido === null
      ? null
      : {
          ev: numeroNullable(recObjetivo.valorEsperado) ?? 0,
          edge_real: edgeRealCanonico ?? 0,
          riesgo_valor: stdTotal ?? 0,
          riesgo_referencia: mediaTotal !== null && mediaTotal > 0 ? mediaTotal : 1,
          riesgo_normalizado: (stdTotal !== null && mediaTotal !== null && mediaTotal > 0) ? (stdTotal / mediaTotal) : 0,
          penalizacion_riesgo: 0,
          penalizacion_devig: penalizacionesScore.length > 0 ? -20 : 0,
        },
    score_explicacion: scoreValido === null
      ? `Score no evaluable (${estadoCuotas.estado}). Requiere cuotas completas y de-vig real válido.`
      : (recObjetivo.razon || 'Score calculado por backend fútbol'),
    score_penalizaciones: penalizacionesScore,
    kelly_full: kellyCanonico,
    kelly_fraccional: kellyCanonico,
    fraccion_kelly: kellyCanonico,
    stake: null,
    stake_porcentaje: null,
    bankroll_momento: null,
    perfil_riesgo_usado: 'MEDIO',
    sizing_advertencias: kellyCanonico === null
      ? ['Sizing no evaluable: requiere score y de-vig real con cuotas completas.']
      : [],
    sizing_penalizaciones: {
      ...(estadoCuotas.estado === 'cuota_unica' ? { devig_estimado: 0.5 } : {}),
      ...(estadoCuotas.estado === 'sin_cuotas' ? { devig_no_aplicado: 0.3 } : {}),
    },
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
    nivel_confianza: normalizarConfianza(recObjetivo?.confianza),
    factores_confianza: {
      tamano_muestra: 'MEDIO',
      volatilidad: 'MEDIA',
      frescura_datos: 'ALTA',
      puntaje_total: 0.65,
    },
    analisis_mercado: (metodoDevig === 'exacto' && cuotaPrincipal && edgeRealCanonico !== null)
      ? {
          cuota: cuotaPrincipal,
          probabilidad_implicita: 1 / cuotaPrincipal,
          edge: edgeRealCanonico,
          valor_esperado: numeroNullable(recObjetivo?.valorEsperado) ?? edgeRealCanonico,
          recomendacion: mapearRecomendacion(numeroNullable(recObjetivo?.valorEsperado) ?? edgeRealCanonico),
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
      estado_cuotas: estadoCuotas.estado,
      metodo_devig: metodoDevig,
      objetivo: analisis.objetivo,
      fuente_recomendacion: recObjetivo?.fuente ?? null,
      metadata_ensemble: recObjetivo?.metadataEnsemble ?? null,
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
        tendencia_over: promedio(h2h.map((p) => (lineaMain !== null && (p.golesLocal + p.golesVisitante) > lineaMain ? 1 : 0))),
        ultimo_enfrentamiento: h2h[0] ? {
          fecha: h2h[0].fechaPartido,
          puntos_equipo: desdePerspectiva(h2h[0], equipoAnalizadoId).equipo,
          puntos_rival: desdePerspectiva(h2h[0], equipoAnalizadoId).rival,
          total: h2h[0].golesLocal + h2h[0].golesVisitante,
          ganador_id: desdePerspectiva(h2h[0], equipoAnalizadoId).equipo > desdePerspectiva(h2h[0], equipoAnalizadoId).rival
            ? 'equipo'
            : (desdePerspectiva(h2h[0], equipoAnalizadoId).equipo < desdePerspectiva(h2h[0], equipoAnalizadoId).rival ? 'rival' : 'empate'),
        } : null,
        partidos: h2h.map((p) => ({
          fecha: p.fechaPartido,
          puntos_equipo: desdePerspectiva(p, equipoAnalizadoId).equipo,
          puntos_rival: desdePerspectiva(p, equipoAnalizadoId).rival,
          total: p.golesLocal + p.golesVisitante,
          ganador_id: desdePerspectiva(p, equipoAnalizadoId).equipo > desdePerspectiva(p, equipoAnalizadoId).rival
            ? 'equipo'
            : (desdePerspectiva(p, equipoAnalizadoId).equipo < desdePerspectiva(p, equipoAnalizadoId).rival ? 'rival' : 'empate'),
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
        diferencia_vs_temporada: diferenciaVsTemporadaDesdeHistorial(historialLocal, equipoAnalizadoId),
        tendencia: tendenciaDesdeHistorial(historialLocal, equipoAnalizadoId),
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
        diferencia_vs_temporada: diferenciaVsTemporadaDesdeHistorial(historialVisitante, rivalAnalizadoId),
        tendencia: tendenciaDesdeHistorial(historialVisitante, rivalAnalizadoId),
      },
      descanso_equipo: { dias_descanso: 3, es_back_to_back: false, ultimo_partido: null, distancia_viaje_km: null },
      descanso_rival: { dias_descanso: 3, es_back_to_back: false, ultimo_partido: null, distancia_viaje_km: null },
      stats_temporada_equipo: {},
      stats_temporada_rival: {},
    },
    prediccion_base: (mediaTotal !== null && pOver !== null && pUnder !== null)
      ? {
          media: mediaTotal,
          probabilidad_over: pOver,
          probabilidad_under: pUnder,
        }
      : null,
    prediccion_ajustada: (mediaTotal !== null && stdTotal !== null && pOver !== null && pUnder !== null)
      ? {
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
            advertencias: ['Sin ajuste contextual real para el mercado objetivo.'],
            confianza_delta: 0,
          },
          confianza_base: normalizarConfianza(recObjetivo?.confianza),
          confianza_ajustada: normalizarConfianza(recObjetivo?.confianza),
        }
      : null,
    ajustes: {
      ajustes: [],
      ajuste_total: 0,
      ajuste_total_capped: 0,
      fue_capped: false,
      advertencias: ['Sin ajuste contextual real para el mercado objetivo.'],
      confianza_delta: 0,
    },
    probabilidad_over: pOver,
    probabilidad_under: pUnder,
    linea_analizada: lineaMain !== null && lineaMain > 0 ? lineaMain : null,
    advertencias_contexto: [
      ...(mediaTotal === null || stdTotal === null ? ['Datos insuficientes: no hay media/desviación válidas para el mercado objetivo exacto.'] : []),
      ...(pOver === null || pUnder === null ? ['Datos insuficientes: no hay probabilidades válidas para la línea objetivo exacta.'] : []),
      ...(estadoCuotas.estado === 'sin_cuotas' ? ['Sin cuotas: análisis de valor/calibración/riesgo no comparable contra casa.'] : []),
      ...(estadoCuotas.estado === 'cuota_unica' ? ['Cuota única: solo fallback interno, sin comparación real completa contra casa.'] : []),
      ...(estadoCuotas.estado === 'cuotas_completas' && !overroundValido ? ['Cuotas presentes pero de-vig inválido: overround fuera de rango.'] : []),
    ],
    mensaje_apuesta: analisis.recomendaciones?.length
      ? (mediaTotal === null || stdTotal === null || pOver === null || pUnder === null
          ? 'Datos insuficientes: no se puede evaluar completamente el mercado objetivo sin degradación.'
          : 'Tu predicción coincide con la recomendación del sistema')
      : 'Sin recomendación disponible',
  } as ResultadoAnalisis;
}
