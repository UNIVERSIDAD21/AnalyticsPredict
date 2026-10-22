/** Adaptación visual sin atribuir a Euroliga confianza, moneyline o métricas NBA. */
import type { ResultadoEuro } from '../servicios/euroliga';
import type { ResultadoVista, FormaVista, H2HVista } from '../tipos/resultadoVista';

export function adaptarResultadoEuroliga(r: ResultadoEuro): ResultadoVista {
  const predicciones = Object.fromEntries(Object.entries(r.predicciones).map(([m, p]) => [m, {
    media_equipo: p.media_local, media_rival: p.media_visitante, media_total: p.media_total, desviacion_total: p.desviacion_total,
    probabilidad_over: m === r.mercado ? r.probabilidades.over : null,
    probabilidad_under: m === r.mercado ? r.probabilidades.under : null,
    ...(m === 'COMPLETO' ? { ganador_probable: r.ventaja_regulacion.local >= 0.5 ? 'equipo' : 'rival', probabilidad_ganador: r.ventaja_regulacion.local } : {}),
  }]));
  return { equipo: r.equipo_local, rival: r.equipo_visitante, equipo_nombre_completo: r.equipo_local, rival_nombre_completo: r.equipo_visitante,
    ubicacion: 'LOCAL', fecha_analisis: r.fecha_analisis, predicciones, prediccion_juego_completo: predicciones.COMPLETO,
    razones: [], nivel_confianza: null, factores_confianza: null, analisis_mercado: null, mejor_apuesta: null,
    es_en_vivo: r.modo !== 'PREPARTIDO', cuartos_reales: Object.fromEntries(Object.entries(r.predicciones).filter(([m,p]) => m !== 'COMPLETO' && p.observado).map(([m,p]) => [m,[p.media_local,p.media_visitante]])),
    metadata: { deporte: 'baloncesto', liga: 'euroliga', mercado: r.mercado, modo_analisis: r.modo },
    linea_analizada: r.linea, probabilidad_over: r.probabilidades.over, probabilidad_under: r.probabilidades.under };
}

export function formaEuroliga(datos: ResultadoEuro['contexto']['equipos'][string] | undefined): FormaVista | null {
  const recientes = [...(datos?.recientes ?? [])].sort((a,b) => b.fecha.localeCompare(a.fecha));
  if (!recientes.length) return null;
  const resultados = recientes.map(x => x.puntos_regulacion > x.puntos_rival_regulacion ? 'V' : x.puntos_regulacion < x.puntos_rival_regulacion ? 'D' : 'E');
  const media = (campo: 'puntos_regulacion' | 'puntos_rival_regulacion') => recientes.reduce((sum,x) => sum+x[campo],0)/recientes.length;
  return { ultimos_n: recientes.length, victorias: resultados.filter(x=>x==='V').length, derrotas: resultados.filter(x=>x==='D').length,
    empates: resultados.filter(x=>x==='E').length, racha: `${resultados[0]}${resultados.findIndex(x=>x!==resultados[0]) < 0 ? resultados.length : resultados.findIndex(x=>x!==resultados[0])}`,
    ppg: media('puntos_regulacion'), opp_ppg: media('puntos_rival_regulacion'), net_rating: media('puntos_regulacion')-media('puntos_rival_regulacion') };
}

export function h2hEuroliga(r: ResultadoEuro): H2HVista {
  const partidos = r.contexto.h2h.map(x => {
    const local = x.local.toLocaleLowerCase() === r.equipo_local.toLocaleLowerCase();
    const pf = local ? x.local_total : x.visitante_total, pc = local ? x.visitante_total : x.local_total;
    return { fecha:x.fecha, puntos_equipo:pf, puntos_rival:pc,total:pf+pc,ganador_id:pf>pc?r.equipo_local:pf<pc?r.equipo_visitante:'', diferencia_puntos:Math.abs(pf-pc) };
  });
  const media = (campo: 'total'|'puntos_equipo'|'puntos_rival') => partidos.length ? partidos.reduce((s,x)=>s+x[campo],0)/partidos.length : 0;
  return { total_partidos:partidos.length, victorias_equipo:partidos.filter(x=>x.puntos_equipo>x.puntos_rival).length, victorias_rival:partidos.filter(x=>x.puntos_equipo<x.puntos_rival).length,
    promedio_total:media('total'),promedio_equipo:media('puntos_equipo'),promedio_rival:media('puntos_rival'),ultimo_enfrentamiento:partidos[0]??null,partidos };
}

export function formaEquipoEuroliga(r: ResultadoEuro, nombre: string): FormaVista | null {
  return formaEuroliga(Object.entries(r.contexto.equipos).find(([k]) => k.toLocaleLowerCase() === nombre.toLocaleLowerCase())?.[1]);
}
