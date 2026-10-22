/** Predictor Euroliga: datos, probabilidades RAW y cortes visibles, sin picks/stakes. */
import { useEffect, useState } from 'react';
import { Encabezado } from '../organismos/Encabezado';
import { extraerMensajeError } from '../../servicios/api';
import { analizarEuroliga, cargarEuroliga, type MercadoEuro, type ResultadoEuro } from '../../servicios/euroliga';

type Datos = Awaited<ReturnType<typeof cargarEuroliga>>;
const MERCADOS: MercadoEuro[] = ['Q1', 'Q2', 'Q3', 'Q4', 'COMPLETO'];
const ETIQUETAS: Record<MercadoEuro, string> = { Q1: '1.er cuarto', Q2: '2.º cuarto', Q3: '3.er cuarto', Q4: '4.º cuarto', COMPLETO: 'Total de regulación (sin OT)' };
const input = 'w-full min-w-0 rounded-lg border border-neon-cyan/30 bg-futurista-oscuro p-3 text-texto-principal';
const pct = (n: number) => `${(100 * n).toFixed(2)} %`;
const num = (n: number) => n.toFixed(2);

function Resultado({ r }: { r: ResultadoEuro }) {
  const p = r.predicciones[r.mercado];
  return <section aria-label="Resultado Euroliga" className="tarjeta p-5 space-y-5 min-w-0">
    <div>
      <p className="text-neon-cyan text-xs uppercase">{r.modo === 'PREPARTIDO' ? 'Prepartido' : `Corte al cierre de ${r.modo.replace('CIERRE_', '')}`} · Solo regulación · RAW</p>
      <h2 className="text-xl font-bold mt-2">{r.equipo_local} — {r.equipo_visitante}</h2>
      <p>{ETIQUETAS[r.mercado]} · Línea {r.linea}</p>
      <p className="text-xs text-texto-secundario mt-2">Calculado: {new Date(r.fecha_analisis).toLocaleString()} · Datos hasta {r.corte_datos}</p>
    </div>
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      <div className="rounded-lg border border-neon-cyan/20 p-4"><p>Over {r.linea}</p><strong className="text-2xl">{pct(r.probabilidades.over)}</strong></div>
      <div className="rounded-lg border border-neon-cyan/20 p-4"><p>Under {r.linea}</p><strong className="text-2xl">{pct(r.probabilidades.under)}</strong></div>
      <div className="rounded-lg border border-neon-cyan/20 p-4"><p>Igual a la línea (push)</p><strong className="text-2xl">{pct(r.probabilidades.push)}</strong></div>
    </div>
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
  </section>;
}

export function PaginaEuroliga() {
  const [datos, setDatos] = useState<Datos | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [revision, setRevision] = useState(0);
  const [partido, setPartido] = useState('');
  const [local, setLocal] = useState('');
  const [visitante, setVisitante] = useState('');
  const [mercado, setMercado] = useState<MercadoEuro>('COMPLETO');
  const [linea, setLinea] = useState('');
  const [cuartos, setCuartos] = useState(0);
  const [parciales, setParciales] = useState<[string, string][]>([['', ''], ['', ''], ['', '']]);
  const [resultado, setResultado] = useState<ResultadoEuro | null>(null);
  const [cargando, setCargando] = useState(false);
  const [tab, setTab] = useState<'analisis' | 'historial'>('analisis');
  useEffect(() => {
    let activo = true;
    cargarEuroliga().then(d => { if (activo) { setDatos(d); setError(null); } }).catch(e => { if (activo) setError(extraerMensajeError(e)); });
    return () => { activo = false; };
  }, [revision]);

  const cambiarFixture = (id: string) => {
    setPartido(id); setResultado(null); setCuartos(0); setParciales([['', ''], ['', ''], ['', '']]);
    const p = datos?.partidos.find(x => x.id === id);
    setLocal(p?.equipo_local_nombre ?? ''); setVisitante(p?.equipo_visitante_nombre ?? '');
  };
  const enviar = async (e: React.FormEvent) => {
    e.preventDefault(); if (cargando) return;
    const scores = parciales.slice(0, cuartos).map(q => q.map(Number) as [number, number]);
    if (parciales.slice(0, cuartos).some(q => q.some(x => x.trim() === '')) || scores.some(q => q.some(x => !Number.isInteger(x) || x < 0 || x > 100))) {
      setError('Completa los marcadores de cada cuarto terminado (enteros entre 0 y 100).'); return;
    }
    setCargando(true); setError(null); setResultado(null);
    try {
      const r = await analizarEuroliga({ equipo_local: local, equipo_visitante: visitante, mercado, linea: Number(linea), partido_id: partido || undefined, parciales: scores });
      setResultado(r); setDatos(d => d ? { ...d, historial: [r, ...d.historial].slice(0, 20) } : d);
    } catch (e) { setError(extraerMensajeError(e)); } finally { setCargando(false); }
  };
  const limpiar = () => { cambiarFixture(''); setLinea(''); setError(null); };
  return <div className="min-h-screen"><Encabezado /><main className="contenedor py-6 space-y-5">
    <div className="tarjeta p-5">
      <p className="text-neon-cyan uppercase text-xs">Baloncesto · Modelo exclusivo Euroliga</p>
      <h1 className="text-2xl font-futurista mt-2">Predictor Euroliga</h1>
      <p className="mt-2 text-sm text-texto-secundario">Cuartos y total de 40 minutos, sin prórrogas. Probabilidades RAW no calibradas; eficacia no certificada. Sin picks ni recomendaciones de apuestas.</p>
      {datos && <p className="mt-2 text-sm">{datos.estado.partidos} finales · {datos.estado.equipos} equipos históricos · modelo hasta {datos.estado.corte_datos} · último final en BD: {datos.ultimoFinal ?? 'N/D'}</p>}
      <button type="button" className="text-neon-cyan mt-3 text-sm" disabled={cargando} onClick={() => setRevision(n => n + 1)}>Actualizar estado y calendario</button>
    </div>
    {error && <div role="alert" className="tarjeta border border-red-500/40 p-4">{error}</div>}
    {!datos && !error && <p role="status">Cargando Euroliga…</p>}
    {datos && <>
      <div className="flex gap-3"><button type="button" aria-pressed={tab === 'analisis'} onClick={() => setTab('analisis')} className="tarjeta p-3">Análisis</button><button type="button" aria-pressed={tab === 'historial'} onClick={() => setTab('historial')} className="tarjeta p-3">Historial Euroliga ({datos.historial.length})</button></div>
      {tab === 'analisis' ? <div className="grid lg:grid-cols-[minmax(300px,390px)_minmax(0,1fr)] gap-5 items-start">
        <form onSubmit={enviar} className="tarjeta p-5 space-y-4 min-w-0">
          <h2 className="text-lg font-semibold">Configurar análisis Euroliga</h2>
          <fieldset disabled={cargando} className="space-y-4 min-w-0">
            <label className="block">Partido Euroliga<select className={input} value={partido} onChange={e => cambiarFixture(e.target.value)}><option value="">Solo cálculo — seleccionar equipos</option>{datos.partidos.map(p => <option key={p.id} value={p.id}>{p.fecha_partido} · {p.equipo_local_nombre} — {p.equipo_visitante_nombre} · {p.tipo_partido}</option>)}</select></label>
            {!datos.partidos.length && <p>No hay fixtures Euroliga próximos en la base.</p>}
            <label className="block">Equipo local<select required className={input} value={local} disabled={Boolean(partido)} onChange={e => { setLocal(e.target.value); setResultado(null); }}><option value="">Selecciona local</option>{datos.equipos.map(x => <option key={x.id} disabled={!x.elegible || x.nombre === visitante} value={x.nombre}>{x.nombre} · n={x.muestras}</option>)}</select></label>
            <label className="block">Equipo visitante<select required className={input} value={visitante} disabled={Boolean(partido)} onChange={e => { setVisitante(e.target.value); setResultado(null); }}><option value="">Selecciona visitante</option>{datos.equipos.map(x => <option key={x.id} disabled={!x.elegible || x.nombre === local} value={x.nombre}>{x.nombre} · n={x.muestras}</option>)}</select></label>
            <label className="block">Periodo<select className={input} value={mercado} onChange={e => { setMercado(e.target.value as MercadoEuro); setResultado(null); }}>{MERCADOS.map(m => <option key={m} value={m}>{ETIQUETAS[m]}</option>)}</select></label>
            <label className="block">Línea de puntos<input required type="number" min="0.01" max="600" step="any" className={input} value={linea} onChange={e => { setLinea(e.target.value); setResultado(null); }} /></label>
            <label className="block">Modo de análisis<select className={input} value={cuartos} onChange={e => { setCuartos(Number(e.target.value)); setResultado(null); }}><option value={0}>Prepartido</option>{[1, 2, 3].map(q => <option key={q} value={q}>Condicionado al cierre de Q{q}</option>)}</select></label>
            {Array.from({ length: cuartos }, (_, i) => <div key={i} className="grid grid-cols-2 gap-2">{[0, 1].map(lado => <label key={lado} className="block text-sm">Q{i + 1} {lado === 0 ? 'local' : 'visitante'}<input required type="number" min="0" max="100" step="1" className={input} value={parciales[i][lado]} onChange={e => { setParciales(prev => prev.map((q, j) => j === i ? q.map((x, k) => k === lado ? e.target.value : x) as [string, string] : q)); setResultado(null); }} /></label>)}</div>)}
            {cuartos > 0 && <p className="text-xs text-texto-secundario">Introduce puntos de cada cuarto completo, no acumulados. No admite marcador parcial ni reloj del cuarto en curso.</p>}
            <p className="text-xs text-texto-secundario">Se conserva una captura local por ejecución. No registra apuestas ni predicciones NBA, no entrena y no modifica Neon.</p>
            <button type="submit" className="w-full rounded-lg bg-neon-cyan/20 border border-neon-cyan p-3 font-semibold">{cargando ? 'Analizando…' : 'Analizar Euroliga'}</button>
            <button type="button" className="w-full p-2 text-texto-secundario" onClick={limpiar}>Limpiar</button>
          </fieldset>
        </form>
        {resultado ? <Resultado r={resultado} /> : <section className="tarjeta p-5 space-y-4 min-w-0"><h2 className="text-lg">Listo para analizar Euroliga</h2><p>Selecciona un partido o dos equipos, el periodo y la línea. Solo se utilizan datos y parámetros Euroliga.</p><p className="text-sm text-texto-secundario">Mínimo {datos.estado.min_partidos_equipo} finales por equipo; menos de 20 genera aviso de muestra pequeña. La anotación y la incertidumbre no se toman de NBA.</p>
          <details><summary className="cursor-pointer">Evaluación temporal y límites del modelo</summary><p className="mt-3 text-sm">TRAIN {datos.estado.validacion.train_n}, CAL de dispersión {datos.estado.validacion.cal_util_n}. EVAL: {datos.estado.validacion.evaluacion.evaluados}/{datos.estado.validacion.evaluacion.partidos}; abstenciones: {datos.estado.validacion.evaluacion.abstenciones}.</p><p className="text-sm mt-2">{datos.estado.validacion.limitacion}</p><div className="overflow-x-auto"><table className="w-full text-sm mt-3"><thead><tr><th>Periodo</th><th>MAE Ridge</th><th>MAE media liga</th></tr></thead><tbody>{Object.entries(datos.estado.validacion.evaluacion.mercados).map(([m, x]) => <tr key={m}><th>{m}</th><td>{num(x.mae)}</td><td>{num(x.mae_media_liga)}</td></tr>)}</tbody></table></div></details>
          <p className="text-xs break-all">Versión: {datos.estado.version}</p>
        </section>}
      </div> : <div className="space-y-4">{datos.historial.length === 0 && <p>Aún no hay análisis Euroliga conservados.</p>}{datos.historial.map(r => <details key={r.analisis_id} className="tarjeta p-4"><summary className="cursor-pointer">{new Date(r.fecha_analisis).toLocaleString()} · {r.equipo_local} — {r.equipo_visitante} · {r.mercado} · {r.linea} · {r.modo}</summary><div className="mt-4"><Resultado r={r} /></div></details>)}</div>}
    </>}
  </main></div>;
}
