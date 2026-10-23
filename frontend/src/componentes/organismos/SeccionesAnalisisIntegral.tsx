import { useState } from 'react';
import type { AnalisisIntegral } from '../../tipos/analisisIntegral';
import { evaluarEscenario } from '../../utilidades/valorEscenario';

const num = (v: number | null | undefined, digits = 2) => typeof v === 'number' && Number.isFinite(v) ? v.toFixed(digits) : 'N/D';
const pct = (v: number | null | undefined) => typeof v === 'number' && Number.isFinite(v) ? `${(v * 100).toFixed(2)} %` : 'N/D';
type Props = { datos: AnalisisIntegral; seccion: 'ganador' | 'periodos' | 'contexto' | 'valor' | 'razones'; local: string; visitante: string; lado?: 'OVER' | 'UNDER' };

/** Mismas secciones funcionales que NBA, sin fingir que el motor sea el mismo. */
export function SeccionesAnalisisIntegral({ datos: d, seccion, local, visitante, lado }: Props) {
  const [over, setOver] = useState(d.cuotas.over?.toString() ?? '');
  const [under, setUnder] = useState(d.cuotas.under?.toString() ?? '');
  const [eleccion, setEleccion] = useState(lado ?? d.lado);
  if (seccion === 'ganador') {
    const opciones = [{ nombre: local, p: d.ganador.local }, { nombre: 'Empate', p: d.ganador.empate }, { nombre: visitante, p: d.ganador.visitante }];
    const mejor = [...opciones].filter(x => x.p !== null).sort((a,b) => b.p! - a.p!)[0];
    return <section className="tarjeta p-5 space-y-3" aria-label="Ganador del partido">
      <h3 className="text-lg font-futurista">Ganador del partido</h3>
      <p className="text-sm">Resultado más probable: <strong className="text-neon-cyan">{mejor?.nombre ?? 'N/D'}</strong> · {pct(mejor?.p)}</p>
      <div className="grid grid-cols-3 gap-2">{opciones.map(x => <div key={x.nombre} className="p-2 bg-futurista-oscuro/50 rounded min-w-0"><p className="text-xs break-words">{x.nombre}</p><strong className="text-sm">{pct(x.p)}</strong></div>)}</div>
      <p className="text-sm">Marcador esperado: {d.ganador.marcador}</p>
      <p className="text-xs text-texto-secundario">{d.ganador.definicion}</p>
    </section>;
  }
  if (seccion === 'periodos') return <section className="tarjeta p-5 space-y-3" aria-label="Proyección por periodo">
    <h3 className="text-lg font-futurista">Proyección por periodo</h3>
    <p className="text-xs text-texto-secundario">{d.nota_periodos}</p>
    <div className="overflow-x-auto"><table className="w-full text-sm text-left"><thead><tr>{['Periodo',local,visitante,`Total (${d.unidad})`,'Desviación'].map((x,i)=><th className="p-2" key={i}>{x}</th>)}</tr></thead><tbody>{d.periodos.map(p=><tr key={p.periodo} className="border-t border-neon-cyan/10"><th className="p-2">{p.periodo}{p.observado ? ' · observado' : ''}</th><td className="p-2">{num(p.local)}</td><td className="p-2">{num(p.visitante)}</td><td className="p-2">{num(p.total)}</td><td className="p-2">{num(p.desviacion)}</td></tr>)}</tbody></table></div>
  </section>;
  if (seccion === 'contexto') return <>
    <section className="tarjeta p-5 space-y-3" aria-label="Impacto de ajustes contextuales">
      <h3 className="text-lg font-futurista">Impacto de ajustes contextuales</h3>
      <p className="text-xs text-texto-secundario break-words">{d.metodo}. Mercado {d.mercado}, línea {d.linea}.</p>
      <div className="grid grid-cols-2 gap-3"><div><p className="text-xs text-texto-secundario">Base antes de ajustes trazados</p><strong>{num(d.comparacion.media_base)} {d.unidad}</strong></div><div><p className="text-xs text-texto-secundario">Proyección ajustada</p><strong className="text-neon-cyan">{num(d.comparacion.media_ajustada)} {d.unidad}</strong></div></div>
      <p className="text-sm">Impacto neto: {num(d.comparacion.media_ajustada !== null && d.comparacion.media_base !== null ? d.comparacion.media_ajustada - d.comparacion.media_base : null)} {d.unidad}</p>
      <p className="text-xs">Over: {pct(d.comparacion.probabilidades_base.over)} → {pct(d.probabilidades.over)} · Under: {pct(d.comparacion.probabilidades_base.under)} → {pct(d.probabilidades.under)}</p>
      {d.comparacion.probabilidades_base.over === null && <p className="text-xs text-texto-secundario">No se conservaron probabilidades previas a los ajustes; el impacto en media sí está trazado.</p>}
    </section>
    <section className="tarjeta p-5 space-y-3" aria-label="Ajustes aplicados"><h3 className="text-lg font-futurista">Ajustes aplicados</h3>
      {d.ajustes.length ? d.ajustes.map((x,i)=><div key={i} className="border-t border-neon-cyan/10 pt-3"><p className="text-sm font-semibold">{x.factor} · {num(x.delta)} {x.unidad}</p><p className="text-xs text-texto-secundario mt-1">{x.descripcion}</p></div>) : <p className="text-sm text-texto-secundario">Sin desplazamiento adicional de media en este mercado. La sede y el histórico forman parte del estimador base; no se cuenta dos veces su efecto.</p>}
      <p className="text-xs text-texto-secundario">No incorpora bajas, alineaciones o clima sin datos suministrados. Los ajustes heurísticos no acreditan calibración.</p>
    </section>
  </>;
  if (seccion === 'razones') return <section className="tarjeta p-5 space-y-3" aria-label="Razones del análisis"><h3 className="text-lg font-futurista">Razones del análisis</h3><ul className="space-y-2 list-disc pl-5 text-sm text-texto-secundario">{d.razones.map((r,i)=><li key={i}>{r}</li>)}</ul></section>;

  const cuotaOver = over.trim() ? Number(over) : null, cuotaUnder = under.trim() ? Number(under) : null;
  const cuota = eleccion === 'OVER' ? cuotaOver : cuotaUnder;
  const p = eleccion === 'OVER' ? d.probabilidades.over : d.probabilidades.under;
  const perdida = eleccion === 'OVER' ? d.probabilidades.under : d.probabilidades.over;
  const valor = evaluarEscenario(p, perdida, d.probabilidades.push, cuota);
  const ambas = cuotaOver !== null && cuotaUnder !== null && cuotaOver > 1 && cuotaUnder > 1 && cuotaOver <= 1000 && cuotaUnder <= 1000;
  const overround = ambas ? 1 / cuotaOver! + 1 / cuotaUnder! : null;
  const fair = overround ? (1 / cuota!) / overround : null;
  return <>
    <section className="tarjeta p-5 space-y-3" aria-label="Análisis de valor"><h3 className="text-lg font-futurista">Análisis de valor</h3>
      <p className="text-xs text-texto-secundario">Escenario RAW para {d.mercado} · línea {d.linea}. Introduce cuotas decimales del mismo mercado y convención; confírmalas de nuevo al guardar.</p>
      <div className="grid grid-cols-2 gap-3">{([{nombre:'Over',value:over,set:setOver},{nombre:'Under',value:under,set:setUnder}]).map(x=><label className="text-xs" key={x.nombre}>Cuota {x.nombre}<input aria-label={`Cuota ${x.nombre} del escenario`} type="number" min="1.01" max="1000" step="0.01" value={x.value} onChange={e=>x.set(e.target.value)} className="w-full mt-1 rounded p-2 bg-futurista-oscuro border border-neon-cyan/30" /></label>)}</div>
      <label className="text-xs block">Lado del escenario<select className="ml-2 p-2 rounded bg-futurista-oscuro" value={eleccion} onChange={e=>setEleccion(e.target.value as 'OVER'|'UNDER')}><option value="OVER">Over</option><option value="UNDER">Under</option></select></label>
      <div className="grid grid-cols-2 gap-3 text-sm"><p>Probabilidad RAW: <strong>{pct(p)}</strong></p><p>Cuota de equilibrio: <strong>{num(valor?.cuotaEquilibrio)}</strong></p><p>EV por unidad: <strong>{num(valor?.ev,4)}</strong></p><p>Margen de las cuotas: <strong>{overround === null ? 'N/D' : pct(overround-1)}</strong></p><p>Probabilidad casa sin margen: <strong>{pct(fair)}</strong></p><p>Diferencia sin margen: <strong>{valor?.probabilidadCondicional !== null && valor?.probabilidadCondicional !== undefined && fair !== null ? `${((valor.probabilidadCondicional-fair)*100).toFixed(2)} pp` : 'N/D'}</strong></p></div>
      {!valor && <p className="text-xs text-texto-secundario">Falta cuota válida o distribución completa. Puedes introducir una sola cuota para calcular EV; ambas son necesarias para quitar el margen.</p>}
      <p className="text-xs text-texto-secundario">EV = P(acierto) × (cuota − 1) − P(fallo). El push devuelve la unidad. Comparación matemática, no rendimiento acreditado.</p>
    </section>
    <section className="tarjeta p-5 space-y-3" aria-label="Decisión y riesgo"><h3 className="text-lg font-futurista">Decisión y riesgo</h3>
      <p className="text-sm">Lectura del escenario: <strong>{!valor ? 'Pendiente de cuota/distribución' : valor.ev > 0 ? 'Saldo teórico positivo' : valor.ev < 0 ? 'Saldo teórico negativo' : 'Equilibrio teórico'}</strong></p>
      <div className="grid grid-cols-2 gap-3 text-sm"><p>Probabilidad de fallo: {pct(perdida)}</p><p>Push: {pct(d.probabilidades.push)}</p><p>Volatilidad del retorno: {num(valor?.desviacionRetorno,4)}</p><p>Pérdida máxima: 1 unidad del escenario</p></div>
      <p className="text-xs text-texto-secundario">Método exploratorio sin certificación. No asigna stake, no coloca apuestas ni convierte un saldo teórico positivo en recomendación. Muestras: {Object.entries(d.muestras).map(([k,v])=>`${k} ${v}`).join(' · ')}.</p>
    </section>
  </>;
}
