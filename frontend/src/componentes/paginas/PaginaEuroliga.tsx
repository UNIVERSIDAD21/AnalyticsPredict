/** Motor Euroliga dentro del mismo formulario y layout del analizador NBA. */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { FormularioAnalisis } from '../organismos/FormularioAnalisis';
import { ResultadoEuroliga } from '../organismos/ResultadoEuroliga';
import { FormularioGuardarApuesta } from '../organismos/FormularioGuardarApuesta';
import { EstadoVacio, PanelesAnalisisBaloncesto } from '../organismos/PanelesAnalisisBaloncesto';
import { MensajeError } from '../moleculas';
import { Spinner } from '../atomos';
import { extraerMensajeError } from '../../servicios/api';
import { crearApuesta } from '../../servicios/bitacora';
import { analizarEuroliga, cargarEuroliga, type PeticionEuro, type ResultadoEuro } from '../../servicios/euroliga';
import type { Equipo, LadoApuesta, PeticionCrearApuesta } from '../../tipos';
import { useToasts } from '../../contextos/Toasts';
import { adaptarResultadoEuroliga } from '../../utilidades/resultadoEuroliga';

type Datos = Awaited<ReturnType<typeof cargarEuroliga>>;
const OPCIONES = [
  { valor: 'Q1' as const, etiqueta: 'Primer Cuarto (Q1)' },
  { valor: 'Q2' as const, etiqueta: 'Segundo Cuarto (Q2)' },
  { valor: 'Q3' as const, etiqueta: 'Tercer Cuarto (Q3)' },
  { valor: 'Q4' as const, etiqueta: 'Cuarto Cuarto (Q4)' },
  { valor: 'COMPLETO' as const, etiqueta: 'Total de regulación (40 min, sin OT)' },
];
const claseTab = (activo: boolean) => `px-4 py-2 rounded-md text-sm font-semibold border ${activo ? 'bg-neon-cyan/20 border-neon-cyan text-neon-cyan' : 'border-neon-cyan/20 text-texto-secundario'}`;

export function ModuloEuroliga({ partidoAgenda = null }: { partidoAgenda?: import('../../servicios/agendaBaloncesto').PartidoAgendaBaloncesto | null }) {
  const [datos, setDatos] = useState<Datos | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [revision, setRevision] = useState(0);
  const [seleccion, setSeleccion] = useState<{ lado: LadoApuesta; linea: number } | null>(null);
  const [resultado, setResultado] = useState<ResultadoEuro | null>(null);
  const [cargando, setCargando] = useState(false);
  const [actualizando, setActualizando] = useState(true);
  const [tab, setTab] = useState<'analisis' | 'estadisticas' | 'historial'>('analisis');
  const [mostrarGuardar, setMostrarGuardar] = useState(false);
  const [guardandoApuesta, setGuardandoApuesta] = useState(false);
  const [errorGuardar, setErrorGuardar] = useState<string | null>(null);
  const { agregarToast } = useToasts();

  useEffect(() => {
    let activo = true;
    setActualizando(true);
    cargarEuroliga().then(d => { if (activo) { setDatos(d); setError(null); } })
      .catch(e => { if (activo) setError(extraerMensajeError(e)); })
      .finally(() => { if (activo) setActualizando(false); });
    return () => { activo = false; };
  }, [revision]);

  const equipos = useMemo<Equipo[]>(() => (datos?.equipos ?? []).map(x => ({
    ...x, nombre_corto: x.nombre, abreviatura: '',
  })), [datos?.equipos]);
  const invalidar = useCallback(() => { setResultado(null); setError(null); setMostrarGuardar(false); }, []);
  const actualizar = useCallback(() => { setResultado(null); setRevision(n => n + 1); }, []);

  const enviar = async (peticion: PeticionEuro, lado?: LadoApuesta) => {
    setSeleccion(lado ? { lado, linea: peticion.linea } : null);
    if (cargando) return;
    setCargando(true); setError(null); setErrorGuardar(null); setMostrarGuardar(false); setResultado(null);
    try {
      const r = await analizarEuroliga(peticion);
      setResultado(r);
      setDatos(d => d ? { ...d, historial: [r, ...d.historial].slice(0, 20) } : d);
    } catch (e) { setError(extraerMensajeError(e)); }
    finally { setCargando(false); }
  };

  const guardarApuesta = async (apuesta: PeticionCrearApuesta) => {
    setGuardandoApuesta(true);
    setErrorGuardar(null);
    try {
      await crearApuesta(apuesta);
      setMostrarGuardar(false);
      agregarToast({ titulo: 'Guardado en Seguimiento', mensaje: 'La selección Euroliga quedó registrada.', tipo: 'success' });
    } catch (e) {
      const mensaje = extraerMensajeError(e);
      setErrorGuardar(mensaje);
      agregarToast({ titulo: 'No se pudo guardar', mensaje, tipo: 'error' });
    } finally {
      setGuardandoApuesta(false);
    }
  };

  return <div aria-label="Analizador Euroliga">
    {partidoAgenda?.reconstruccion && <p role="note" className="tarjeta p-4 mb-4 text-sm text-neon-cyan">Reconstrucción histórica · datos anteriores al día del encuentro. Solo consulta; sin registrar apuestas ni predicciones.</p>}
    <div className="mb-6 tarjeta p-4 border border-neon-cyan/20 space-y-2">
      <p className="text-xs uppercase tracking-wider text-neon-cyan">Euroliga · Predictor propio</p>
      <p className="text-sm text-texto-secundario">Cuartos de 10 minutos y total de 40 minutos, sin prórroga. Probabilidades RAW no calibradas; eficacia no certificada. Sin picks ni recomendaciones de apuestas.</p>
      {datos && <p className="text-xs text-texto-secundario">{datos.estado.partidos} finales · {datos.estado.equipos} equipos históricos · modelo hasta {datos.estado.corte_datos} · último final en BD: {datos.ultimoFinal ?? 'N/D'}</p>}
      <button type="button" className="text-neon-cyan text-xs" disabled={cargando || actualizando} onClick={actualizar}>Actualizar estado y calendario</button>
    </div>
    {error && <div className="mb-6"><MensajeError titulo="Euroliga" mensaje={error} onCerrar={() => setError(null)} /></div>}
    {errorGuardar && <div className="mb-6"><MensajeError titulo="Guardado de apuesta Euroliga" mensaje={errorGuardar} onCerrar={() => setErrorGuardar(null)} /></div>}
    {!datos && actualizando && <p role="status">Cargando Euroliga…</p>}
    {!datos && error && <button type="button" className="text-neon-cyan mb-6" onClick={actualizar}>Reintentar carga de Euroliga</button>}
    {datos && <>
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <button type="button" aria-pressed={tab === 'analisis'} onClick={() => setTab('analisis')} className={claseTab(tab === 'analisis')}>Análisis</button>
        <button type="button" aria-pressed={tab === 'estadisticas'} onClick={() => setTab('estadisticas')} className={claseTab(tab === 'estadisticas')}>Estadísticas de equipos</button>
        <button type="button" aria-pressed={tab === 'historial'} onClick={() => setTab('historial')} className={claseTab(tab === 'historial')}>Historial Euroliga ({datos.historial.length})</button>
      </div>
      <div hidden={tab !== 'analisis'}><PanelesAnalisisBaloncesto formulario={
        <FormularioAnalisis deporte="EUROLIGA" equipos={equipos} partidosDisponibles={datos.partidos} partidoActual={partidoAgenda ?? undefined} ocultarSelectorPartido={Boolean(partidoAgenda)} consultaHistorica={Boolean(partidoAgenda?.reconstruccion)}
          opcionesMercado={OPCIONES} textoAyudaMercado="Q1–Q4: cuartos de 10 minutos. Total: regulación de 40 minutos, sin prórroga."
          onAnalizar={enviar} cargando={cargando || actualizando} onCambiarParametros={invalidar} onActualizarPartidos={actualizar} />
      }>
        {cargando ? <div className="tarjeta min-h-[420px] flex items-center justify-center" role="status"><Spinner texto="Analizando partido Euroliga…" tamano="lg" centrado /></div> : resultado ? <ResultadoEuroliga r={resultado} seleccionUsuario={seleccion} onGuardar={resultado.modo === 'PREPARTIDO' && seleccion ? () => { setMostrarGuardar(true); setErrorGuardar(null); } : undefined} /> : <div className="tarjeta h-full min-h-[500px]">
          <EstadoVacio />
          <details className="px-6 pb-6 text-sm text-texto-secundario">
            <summary className="cursor-pointer">Evaluación temporal y límites del modelo Euroliga</summary>
            <p className="mt-3">TRAIN {datos.estado.validacion.train_n}, CAL de dispersión {datos.estado.validacion.cal_util_n}. EVAL: {datos.estado.validacion.evaluacion.evaluados}/{datos.estado.validacion.evaluacion.partidos}; abstenciones: {datos.estado.validacion.evaluacion.abstenciones}.</p>
            <p className="mt-2">{datos.estado.validacion.limitacion}</p>
            <div className="overflow-x-auto"><table className="w-full text-sm mt-3"><thead><tr><th>Periodo</th><th>MAE Ridge</th><th>MAE media liga</th></tr></thead><tbody>{Object.entries(datos.estado.validacion.evaluacion.mercados).map(([m, x]) => <tr key={m}><th>{m}</th><td>{x.mae.toFixed(2)}</td><td>{x.mae_media_liga.toFixed(2)}</td></tr>)}</tbody></table></div>
            <p className="mt-3 break-all">Versión: {datos.estado.version}</p>
          </details>
        </div>}
      </PanelesAnalisisBaloncesto></div>
      {tab === 'estadisticas' && <section className="tarjeta p-6 space-y-4" aria-label="Muestra de equipos Euroliga">
        <h2 className="text-lg font-futurista">Equipos Euroliga · muestra del predictor</h2>
        <p className="text-sm text-texto-secundario">Finales válidos que utiliza el modelo, no partidos de la temporada actual. Mínimo {datos.estado.min_partidos_equipo} por equipo; menos de 20 indica muestra pequeña. La forma reciente y los enfrentamientos directos se muestran en el resultado del análisis.</p>
        <div className="overflow-x-auto"><table className="w-full text-sm text-left"><thead><tr><th className="p-2">Equipo</th><th className="p-2">Finales</th><th className="p-2">Soporte</th></tr></thead><tbody>{datos.equipos.map(x => <tr key={x.id} className="border-t border-neon-cyan/10"><th className="p-2">{x.nombre}</th><td className="p-2">{x.muestras}</td><td className="p-2">{!x.elegible ? 'Muestra insuficiente' : x.muestras < 20 ? 'Muestra pequeña' : 'Disponible'}</td></tr>)}</tbody></table></div>
      </section>}
      {tab === 'historial' && <div className="space-y-4">
        {!datos.historial.length && <p>Aún no hay análisis Euroliga conservados.</p>}
        {datos.historial.map(r => <details key={r.analisis_id} className="tarjeta p-4"><summary className="cursor-pointer">{new Date(r.fecha_analisis).toLocaleString()} · {r.equipo_local} — {r.equipo_visitante} · {r.mercado} · {r.linea} · {r.modo}</summary><div className="mt-4"><ResultadoEuroliga r={r} /></div></details>)}
      </div>}
    </>}
    {resultado && seleccion && resultado.modo === 'PREPARTIDO' && <FormularioGuardarApuesta
      abierto={mostrarGuardar}
      resultado={adaptarResultadoEuroliga(resultado)}
      ladoSeleccionado={seleccion.lado}
      lineaSeleccionada={seleccion.linea}
      fechaPartido={resultado.fecha_partido ?? undefined}
      partidoId={resultado.partido_id ?? undefined}
      competicionCodigo="euroleague"
      permitirCuotaManual
      guardando={guardandoApuesta}
      onCerrar={() => setMostrarGuardar(false)}
      onGuardar={guardarApuesta}
    />}
  </div>;
}
