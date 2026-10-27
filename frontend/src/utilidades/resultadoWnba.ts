/** Adaptador al resultado NBA, no una segunda presentación ni un predictor NBA. */
import type { ResultadoWnba, PartidoWnbaContexto } from '../servicios/wnba';
import type { ResultadoVista, FormaVista } from '../tipos/resultadoVista';
import type { ContextoDescanso, LadoApuesta } from '../tipos';

function puntos(r: PartidoWnbaContexto, rival: boolean, mercado: string, ot: boolean) {
  if (mercado !== 'COMPLETO') return (rival ? r.cuartos_rival : r.cuartos)[Number(mercado[1])-1];
  return ot ? (rival ? r.final_rival ?? r.regulacion_rival + (r.ot_rival ?? 0) : r.final) : (rival ? r.regulacion_rival : r.regulacion);
}
function forma(r: ResultadoWnba, tid: string): FormaVista {
  const equipo = r.contexto.equipos[tid];
  const rows = equipo.recientes.slice(0,10);
  const pf = rows.map(x=>puntos(x,false,r.mercado,r.incluye_ot));
  const pc = rows.map(x=>puntos(x,true,r.mercado,r.incluye_ot));
  const resultados = pf.map((x,i)=>x>pc[i]?'V':x<pc[i]?'D':'E');
  const n = rows.length;
  const media = (x: number[])=>x.reduce((a,b)=>a+b,0)/n;
  const racha = resultados.findIndex(x=>x!==resultados[0]);
  const temporada=equipo.temporada_resumen;
  const mediaTemporada=temporada?(r.mercado==='COMPLETO'&&!r.incluye_ot?temporada.media_regulacion:temporada.medias_favor[r.mercado]):undefined;
  const diferencia=mediaTemporada===undefined?undefined:media(pf)-mediaTemporada;
  return { ...(mediaTemporada===undefined?{}:{ppg_temporada:mediaTemporada,diferencia_vs_temporada:diferencia,tendencia:diferencia!>0?'MEJORANDO' as const:diferencia!<0?'EMPEORANDO' as const:'ESTABLE' as const}),ultimos_n:n, victorias:resultados.filter(x=>x==='V').length, derrotas:resultados.filter(x=>x==='D').length,
    empates:resultados.filter(x=>x==='E').length, racha:`${resultados[0]}${racha<0?n:racha}`,
    ppg:media(pf), opp_ppg:media(pc), net_rating:media(pf)-media(pc) };
}
function descanso(r: ResultadoWnba, tid: string): ContextoDescanso | null {
  const ultimo = r.contexto.equipos[tid]?.recientes[0];
  if (!ultimo || !r.fecha_partido) return null;
  const fecha = new Intl.DateTimeFormat('en-CA',{timeZone:'America/Bogota'}).format(new Date(r.fecha_partido));
  const dias = Math.round((Date.parse(fecha)-Date.parse(ultimo.fecha))/86400000)-1;
  return { dias_descanso:Math.max(0,dias), es_back_to_back:dias===0, ultimo_partido:{fecha:ultimo.fecha,puntos_equipo:ultimo.final,puntos_rival:ultimo.final_rival??ultimo.regulacion_rival+(ultimo.ot_rival??0),ubicacion:ultimo.como_local?'LOCAL':'VISITANTE'}, distancia_viaje_km:null };
}
export function adaptarResultadoWnba(r: ResultadoWnba, lado: LadoApuesta): ResultadoVista {
  const live = Boolean(r.parciales?.length);
  const predicciones = Object.fromEntries(Object.entries(r.predicciones).map(([k,p])=>[k,{
    media_equipo:p.media_local, media_rival:p.media_visitante, media_total:p.media_total, desviacion_total:p.desviacion_total,
    probabilidad_over:k===r.mercado?r.probabilidades.over:null, probabilidad_under:k===r.mercado?r.probabilidades.under:null,
    ganador_tres_vias:p.ganador ?? (k==='COMPLETO'?r.ganador_regulacion:undefined),
    ganador_probable:(p.ganador?.local??0)>=(p.ganador?.visitante??0)?'equipo' as const:'rival' as const,
    probabilidad_ganador:p.ganador?.local,
  }]));
  const h2h = r.contexto.h2h.map(x=>{
    const local = x.local_id===r.equipo_local_id;
    const q = r.mercado==='COMPLETO' ? null : Number(r.mercado[1])-1;
    const a = q===null ? (r.incluye_ot ? x.local_total : x.y.slice(0,4).reduce((a,b)=>a+b,0)) : x.y[q];
    const b = q===null ? (r.incluye_ot ? x.visitante_total : x.y.slice(4).reduce((a,b)=>a+b,0)) : x.y[q+4];
    const pf=local?a:b,pc=local?b:a;
    return {fecha:x.fecha,puntos_equipo:pf,puntos_rival:pc,total:pf+pc,ganador_id:pf>pc?r.equipo_local_id:pf<pc?r.equipo_visitante_id:'',diferencia_puntos:Math.abs(pf-pc)};
  });
  const avg=(key:'total'|'puntos_equipo'|'puntos_rival')=>h2h.length?h2h.reduce((s,x)=>s+x[key],0)/h2h.length:0;
  const p=r.predicciones[r.mercado];
  const cuota=r.valor[lado.toLowerCase() as 'over'|'under'].cuota;
  const qover=r.valor.over.cuota,qunder=r.valor.under.cuota;
  const overround=qover&&qunder?1/qover+1/qunder:null;
  const prob=r.probabilidades[lado==='OVER'?'over':'under'];
  const fair=overround&&cuota?(1/cuota)/overround:null;
  const cond=prob!==null && r.probabilidades.push!==null && r.probabilidades.push<1 ? prob/(1-r.probabilidades.push) : null;
  const base=r.base_descompuesta;
  const delta=base&&p?p.media_total-base.prediccion.media_total:0;
  const ajustes={ ajustes:base?[{factor:'Identidad y localía Ridge WNBA',valor:delta,direccion:delta>=0?'sube' as const:'baja' as const,confianza_ajuste:null,descripcion:base.definicion,datos_soporte:{version:r.modelo_version}}]:[],ajuste_total:delta,ajuste_total_capped:delta,fue_capped:false,advertencias:['Descomposición de coeficientes ya incluidos, no ajuste añadido por segunda vez.'],confianza_delta:null };
  return {
    equipo:r.equipo_local,rival:r.equipo_visitante,equipo_nombre_completo:r.equipo_local,rival_nombre_completo:r.equipo_visitante,
    ubicacion:'LOCAL',fecha_analisis:r.fecha_analisis,predicciones,prediccion_juego_completo:predicciones.COMPLETO??null,
    prediccion_base:base?{media:base.prediccion.media_total,probabilidad_over:base.probabilidades.over,probabilidad_under:base.probabilidades.under}:undefined,
    prediccion_ajustada:base&&p&&r.probabilidades.over!==null&&r.probabilidades.under!==null?{media_base:base.prediccion.media_total,desviacion_base:p.desviacion_total,probabilidad_over_base:base.probabilidades.over,probabilidad_under_base:base.probabilidades.under,media_ajustada:p.media_total,probabilidad_over_ajustada:r.probabilidades.over,probabilidad_under_ajustada:r.probabilidades.under,ajustes_aplicados:ajustes,confianza_base:null,confianza_ajustada:null}:undefined,
    ajustes:base?ajustes:undefined,
    nivel_confianza:null,factores_confianza:null,analisis_mercado:null,mejor_apuesta:null,
    es_en_vivo:live,cuartos_reales:Object.fromEntries((r.parciales??[]).map((q,i)=>[`Q${i+1}`,q])),
    linea_analizada:r.linea,probabilidad_over:r.probabilidades.over,probabilidad_under:r.probabilidades.under,
    razones:p?[{factor:'ataque_equipo',descripcion:`Proyección propia WNBA de ${r.equipo_local} en ${r.mercado}: ${p.media_local.toFixed(2)} puntos.`,direccion:'sube',impacto:p.media_local},
      {factor:'ataque_rival',descripcion:`Proyección propia WNBA de ${r.equipo_visitante} en ${r.mercado}: ${p.media_visitante.toFixed(2)} puntos.`,direccion:'sube',impacto:p.media_visitante}]:[],
    contexto:r.contexto.equipos[r.equipo_local_id]?.recientes.length && r.contexto.equipos[r.equipo_visitante_id]?.recientes.length ? { h2h:{total_partidos:h2h.length,victorias_equipo:h2h.filter(x=>x.puntos_equipo>x.puntos_rival).length,victorias_rival:h2h.filter(x=>x.puntos_equipo<x.puntos_rival).length,promedio_total:avg('total'),promedio_equipo:avg('puntos_equipo'),promedio_rival:avg('puntos_rival'),tendencia_over:h2h.length?h2h.filter(x=>x.total>r.linea).length/h2h.length:0,ultimo_enfrentamiento:h2h[0]??null,partidos:h2h},
      forma_equipo:forma(r,r.equipo_local_id),forma_rival:forma(r,r.equipo_visitante_id),descanso_equipo:descanso(r,r.equipo_local_id),descanso_rival:descanso(r,r.equipo_visitante_id),stats_temporada_equipo:{},stats_temporada_rival:{} }:null,
    detalle_descriptivo:cuota&&!live?{mercado:r.mercado,lado,linea:r.linea,cuota,cuota_over:qover,cuota_under:qunder,probabilidad_sistema:prob,
      p_raw:prob,p_calibrada:null,calibrador_usado:null,devig_metodo:overround?'exacto':'no_aplicado',devig_overround:overround,
      devig_p_mkt_raw:1/cuota,devig_p_mkt_fair:fair,edge_raw:cond===null?null:cond-1/cuota,edge_real:fair===null||cond===null?null:cond-fair,
      devig_advertencias:overround?['Probabilidad WNBA RAW condicionada a no-push para comparar cuotas.']:['N/D sin cuota opuesta: no se inventa margen.'],
      valor_esperado:r.valor[lado.toLowerCase() as 'over'|'under'].ev_sin_calibrar,
      score_total:null,score_componentes:{ev:null,edge_real:null,riesgo_valor:p?.desviacion_total??null,riesgo_referencia:null,riesgo_normalizado:null,penalizacion_riesgo:null,penalizacion_devig:null},score_explicacion:'N/D: no hay política de score ni recomendación validada para WNBA.',score_penalizaciones:[],
      sizing_advertencias:['N/D: sin política WNBA validada de stake, Kelly o riesgo. No se reutiliza la de NBA.'],sizing_penalizaciones:null,
      aplicaron_caps:false}:undefined,
    metadata:{deporte:'baloncesto',liga:'wnba',mercado:r.mercado,modo_analisis:r.modo==='HISTORICO'?'HISTORICO_RECONSTRUIDO':live?r.modo:'PREPARTIDO',modelo_version:r.modelo_version,
      analisis_id:r.analisis_id,fixture_revision_sha256:r.fixture_revision_sha256,partido_id:r.partido_id,fecha_partido:r.fecha_partido,probabilidad_push:r.probabilidades.push,
      duracion_regulacion:40,incluye_ot:r.incluye_ot,metodo_live:r.condicionamiento?.metodo,
      mercados_no_disponibles:r.mercados_no_disponibles,politica_muestras:r.politica_muestras,
      objetivo:{trazabilidad:{estado_operativo_mercado:'NO_CERTIFICADO',motivos_estado_operativo:['WNBA · SIN_CALIBRAR',`Alcance ${r.temporadas_utilizadas.join(', ')} · ${r.fases_utilizadas.join(', ')}`,`Corte exclusivo ${r.corte_exclusivo}`,`Modelo ${r.modelo_version}`]}}},
  };
}
