/** Salida exclusiva Euroliga; no es moneyline NBA. */
import type { MercadoEuro, ResultadoEuro } from '../../servicios/euroliga';
import { TarjetaProbabilidad } from './TarjetaProbabilidad';

const MERCADOS: MercadoEuro[] = ['Q1', 'Q2', 'Q3', 'Q4', 'COMPLETO'];
const ETIQUETAS: Record<MercadoEuro, string> = { Q1: '1.er cuarto', Q2: '2.º cuarto', Q3: '3.er cuarto', Q4: '4.º cuarto', COMPLETO: 'Total de regulación (sin OT)' };
const pct = (n: number) => `${(100 * n).toFixed(2)} %`;
const num = (n: number) => n.toFixed(2);

export function ResultadoEuroliga({ r }: { r: ResultadoEuro }) {
  const p = r.predicciones[r.mercado];
  return <section aria-label="Resultado Euroliga" className="space-y-6 min-w-0 animate-entrada">
    <div className="tarjeta p-6 border-t-2 border-neon-cyan">
      <p className="text-neon-cyan text-xs uppercase">{r.modo === 'PREPARTIDO' ? 'Prepartido' : `Corte al cierre de ${r.modo.replace('CIERRE_', '')}`} · Solo regulación · RAW</p>
      <h2 className="text-xl font-bold mt-2">{r.equipo_local} — {r.equipo_visitante}</h2>
      <p>{ETIQUETAS[r.mercado]} · Línea {r.linea}</p>
      <p className="text-xs text-texto-secundario mt-2">Calculado: {new Date(r.fecha_analisis).toLocaleString()} · Datos hasta {r.corte_datos}</p>
    </div>
    <TarjetaProbabilidad linea={r.linea} probabilidadOver={r.probabilidades.over} probabilidadUnder={r.probabilidades.under}
      probabilidadPush={r.probabilidades.push} mediaTotal={p.media_total} desviacion={p.desviacion_total} decimales={2} unidadLabel="puntos" />
    <div className="tarjeta p-6 space-y-5 min-w-0">
    <p>Media total <strong>{num(p.media_total)}</strong> · Desviación <strong>{num(p.desviacion_total)}</strong> · Intervalo predictivo 80 % RAW: {p.intervalo_predictivo_80_raw.map(num).join(' – ')}</p>
    <p className="text-xs text-texto-secundario">Aproximación Normal; el 80 % es nominal, no cobertura certificada. La línea no es una cotización verificada.</p>
    <div className="overflow-x-auto"><table className="w-full text-sm text-left">
      <caption className="text-left mb-2">Proyección por periodo · cuartos de 10 minutos</caption>
      <thead><tr><th className="p-2">Periodo</th><th className="p-2">Local</th><th className="p-2">Visitante</th><th className="p-2">Total</th><th className="p-2">Desviación</th></tr></thead>
      <tbody>{MERCADOS.map(m => <tr key={m} className="border-t border-neon-cyan/10"><th className="p-2">{m}{r.predicciones[m].observado ? ' (observado)' : ''}</th>{['media_local', 'media_visitante', 'media_total', 'desviacion_total'].map(k => <td className="p-2" key={k}>{num(r.predicciones[m][k as 'media_local'])}</td>)}</tr>)}</tbody>
    </table></div>
    <div>
      <h3 className="font-semibold">Ventaja de puntos al terminar la regulación</h3>
      <p>{r.equipo_local}: {pct(r.ventaja_regulacion.local)} · {r.equipo_visitante}: {pct(r.ventaja_regulacion.visitante)}</p>
      <p className="text-xs text-texto-secundario">{r.ventaja_regulacion.definicion}</p>
    </div>
    <div className="border border-amber-500/30 rounded-lg p-3"><ul className="list-disc pl-5 text-sm space-y-2">{r.advertencias.map(a => <li key={a}>{a}</li>)}</ul></div>
    <div>
      <h3 className="font-semibold">Forma reciente e historial Euroliga</h3>
      <p className="text-xs text-texto-secundario">{r.contexto.uso}</p>
      {Object.entries(r.contexto.equipos).map(([nombre, datos]) => <details key={nombre} className="mt-3 border border-neon-cyan/20 rounded p-3">
        <summary className="cursor-pointer capitalize">{nombre} · {datos.n_historico} finales · media últimos 10: {datos.media_regulacion == null ? 'N/D' : num(datos.media_regulacion)}</summary>
        <ul className="mt-2 text-sm space-y-2">{datos.recientes.map(x => <li key={x.id}>{x.fecha} · {x.como_local ? 'Local' : 'Visitante'} vs {x.rival}: {x.puntos_regulacion}–{x.puntos_rival_regulacion} (regulación)</li>)}</ul>
      </details>)}
      <details className="mt-3 border border-neon-cyan/20 rounded p-3"><summary className="cursor-pointer">Enfrentamientos directos ({r.contexto.h2h.length}, últimos 10)</summary>
        <ul className="mt-2 text-sm space-y-2">{r.contexto.h2h.map((x, i) => <li key={i}>{x.fecha} · {x.local} {x.local_total}–{x.visitante_total} {x.visitante} (final, puede incluir OT)</li>)}</ul>
        {!r.contexto.h2h.length && <p>Sin enfrentamientos registrados antes del fixture.</p>}
      </details>
    </div>
    <div className="text-xs text-texto-secundario space-y-1 break-all">
      <p>Modelo: {r.modelo_version}</p><p>Dataset SHA-256: {r.dataset_sha256}</p><p>Análisis: {r.analisis_id}</p>
      <p>Muestras de entrenamiento: local {r.muestras.local}, visitante {r.muestras.visitante}.</p>
      <p>Temporada {r.temporada_reciente}: local {r.muestras_temporada.local}, visitante {r.muestras_temporada.visitante} finales.</p>
      <p>{r.prospectiva_acreditada_por_fecha ? 'Captura anterior a la fecha del fixture.' : 'Esta captura no acredita anterioridad al kickoff (sin fixture futuro fechado o corte live).'} No acredita calibración.</p>
    </div>
    </div>
  </section>;
}
