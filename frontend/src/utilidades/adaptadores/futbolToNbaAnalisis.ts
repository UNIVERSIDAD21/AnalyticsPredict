import type { ResultadoAnalisis, PrediccionCuarto } from '../../tipos/analisis';
import type { AnalisisFutbolResponse, PrediccionMercadoFutbol } from '../../tipos/futbol';

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

export function adaptarAnalisisFutbolAResultadoAnalisis(analisis: AnalisisFutbolResponse): ResultadoAnalisis {
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
    nivel_confianza: (analisis.recomendaciones?.[0]?.confianza as any) || 'MEDIA',
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
      recomendacion: ((analisis.recomendaciones?.[0]?.valorEsperado ?? 0) > 0 ? 'APUESTA APTA' : 'NO APOSTAR') as any,
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
    probabilidad_over: pOver,
    probabilidad_under: pUnder,
    linea_analizada: lineaMain,
    mensaje_apuesta: analisis.recomendaciones?.length ? 'Tu predicción coincide con la recomendación del sistema' : 'Sin recomendación disponible',
  } as ResultadoAnalisis;
}
