/** Controlador WNBA del recorrido NBA: mismos componentes, motor y fuentes propios. */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { FormularioAnalisis } from '../organismos/FormularioAnalisis';
import { ResultadoAnalisis } from '../organismos/ResultadoAnalisis';
import { FormularioGuardarApuesta } from '../organismos/FormularioGuardarApuesta';
import { CreadorCombinada } from '../organismos/CreadorCombinada';
import { CabeceraAnalizadorBaloncesto } from '../organismos/CabeceraAnalizadorBaloncesto';
import { TablaEstadisticasEquipos } from '../organismos/TablaEstadisticasEquipos';
import { HistorialEquipo } from '../organismos/HistorialEquipo';
import { EstadoVacio, PanelesAnalisisBaloncesto } from '../organismos/PanelesAnalisisBaloncesto';
import { MensajeError, ProgresoAnalisis } from '../moleculas';
import { Spinner } from '../atomos';
import { analizarWnba, cargarWnba, estadisticasWnba, sincronizarCalendarioWnba, type FormularioWnba, type ResultadoWnba } from '../../servicios/wnba';
import { adaptarResultadoWnba } from '../../utilidades/resultadoWnba';
import { crearApuesta } from '../../servicios/bitacora';
import { extraerMensajeError } from '../../servicios/api';
import { useToasts } from '../../contextos/Toasts';
import type { Equipo, LadoApuesta, PartidoResumen, SeleccionCombinadaInput } from '../../tipos';

export function ModuloWnba() {
  const [params,setParams] = useSearchParams();
  const [datos, setDatos] = useState<Awaited<ReturnType<typeof cargarWnba>> | null>(null);
  const [resultado, setResultado] = useState<ResultadoWnba | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);
  const [tab, setTab] = useState<'analisis' | 'estadisticas'>('analisis');
  const [fixture, setFixture] = useState<PartidoResumen | null>(null);
  const [cuartos, setCuartos] = useState(0);
  const [lado, setLado] = useState<LadoApuesta>('OVER');
  const [guardar, setGuardar] = useState(false);
  const [equipoHistorialId, setEquipoHistorialId] = useState<string | null>(null);
  const [cuota, setCuota] = useState<number>();
  const [cargandoDatos, setCargandoDatos] = useState(true);
  const generacion = useRef(0);
  const controller = useRef<AbortController | null>(null);
  const montado = useRef(false);
  const { agregarToast } = useToasts();
  const recargar = useCallback(async (signal?: AbortSignal) => {
    try {
      const d = await cargarWnba(signal);
      if (!montado.current || signal?.aborted) return;
      setDatos(d); setError(null);
    } catch (e) { if (montado.current && !signal?.aborted) setError(extraerMensajeError(e)); }
    finally { if (montado.current && !signal?.aborted) setCargandoDatos(false); }
  }, []);
  useEffect(() => {
    montado.current = true;
    const estadoGeneracion = generacion;
    const c = new AbortController();
    void recargar(c.signal);
    return () => { montado.current = false; estadoGeneracion.current++; c.abort(); controller.current?.abort(); };
  }, [recargar]);
  useEffect(() => {
    const aid = params.get('analisis');
    const anterior = datos?.historial.find(r=>r.analisis_id===aid);
    if (anterior) {
      setResultado(anterior);
      const seleccion = anterior.lado_solicitado ?? (params.get('lado') === 'UNDER' ? 'UNDER' : 'OVER');
      setLado(seleccion);setCuota(anterior.valor[seleccion.toLowerCase() as 'over'|'under'].cuota ?? undefined);
      setFixture(datos?.proximos.find(p=>p.id===anterior.partido_id)??null);
    }
  }, [datos?.historial, datos?.proximos, params]);
  useEffect(() => {
    if (resultado && window.innerWidth < 1024) {
      document.getElementById('resultado-analisis')?.scrollIntoView?.({ behavior: 'smooth', block: 'start' });
    }
  }, [resultado]);
  useEffect(() => {
    if (tab !== 'estadisticas') setEquipoHistorialId(null);
  }, [tab]);
  const invalidar = useCallback(() => {
    generacion.current++; controller.current?.abort(); setCargando(false); setResultado(null); setError(null); setGuardar(false);
    setParams(prev=>{if(!prev.has('analisis'))return prev;const n=new URLSearchParams(prev);n.delete('analisis');n.delete('lado');return n;},{replace:true});
  }, [setParams]);
  const equipos = useMemo<Equipo[]>(()=>datos?.catalogo.equipos.map(e=>({...e,nombre_corto:e.nombre,abreviatura:'WNBA'}))??[],[datos?.catalogo.equipos]);
  const vista = useMemo(()=>resultado?adaptarResultadoWnba(resultado,lado):null,[resultado,lado]);
  const valoresIniciales=useMemo(()=>resultado&&params.get('analisis')===resultado.analisis_id?{
    id:resultado.analisis_id,equipoLocal:resultado.equipo_local,equipoVisitante:resultado.equipo_visitante,
    mercado:resultado.mercado,linea:String(resultado.linea),ladoApuesta:lado,
    cuotaOver:resultado.valor.over.cuota?.toString()??'',cuotaUnder:resultado.valor.under.cuota?.toString()??'',
    temporadas:resultado.temporadas_solicitadas.map(t=>t.id),parciales:resultado.parciales??[],
  }:undefined,[resultado,params,lado]);
  const seleccionCombinada = useMemo<SeleccionCombinadaInput | null>(()=>resultado&&vista&&!vista.es_en_vivo&&cuota?{
    partido_id:resultado.partido_id,equipo_local:resultado.equipo_local,equipo_visitante:resultado.equipo_visitante,
    fecha_partido:resultado.fecha_partido?new Intl.DateTimeFormat('en-CA',{timeZone:'America/Bogota'}).format(new Date(resultado.fecha_partido)):undefined,
    mercado:resultado.mercado,lado,linea:resultado.linea,cuota,probabilidad_sistema:resultado.probabilidades[lado==='OVER'?'over':'under'],
    prediccion_media:resultado.predicciones[resultado.mercado].media_total,prediccion_desviacion:resultado.predicciones[resultado.mercado].desviacion_total,
    confianza_sistema:null,razones:[{tipo:'trazabilidad_wnba',...vista.metadata}]
  }:null,[resultado,vista,cuota,lado]);
  const enviar = async (p: FormularioWnba, l: LadoApuesta = 'OVER') => {
    invalidar(); const id=++generacion.current; const c=new AbortController(); controller.current=c;
    setCargando(true);setLado(l);setCuota(l==='OVER'?p.cuota_over:p.cuota_under);
    try {
      const r=await analizarWnba({...p,temporadas:p.temporadas??datos!.catalogo.temporadas.map(t=>t.id),
        fases:['REG'],es_prueba:params.get('prueba')==='1'},c.signal);
      if (!montado.current || id!==generacion.current) return;
      setResultado(r);
      agregarToast({titulo:'Análisis completado',mensaje:'El motor terminó y los resultados están listos.',tipo:'success'});
    } catch(e) { if(montado.current&&id===generacion.current&&!c.signal.aborted) setError(extraerMensajeError(e)); }
    finally { if(montado.current&&id===generacion.current) setCargando(false); }
  };
  const actualizar = async () => {
    invalidar(); const id=++generacion.current;const c=new AbortController();controller.current=c;setCargando(true);
    try { await sincronizarCalendarioWnba(c.signal); if(montado.current&&id===generacion.current) await recargar(c.signal); }
    catch(e) { if(montado.current&&id===generacion.current&&!c.signal.aborted) setError(extraerMensajeError(e)); }
    finally { if(montado.current&&id===generacion.current) setCargando(false); }
  };
  const cambiarTemporada = async (tid: string | null) => {
    const c=new AbortController();controller.current?.abort();controller.current=c;
    try {const e=await estadisticasWnba(tid,c.signal);if(montado.current&&!c.signal.aborted)setDatos(d=>d?{...d,estadisticas:e}:d);}
    catch(e){if(montado.current&&!c.signal.aborted)setError(extraerMensajeError(e));}
  };
  return <div aria-label="Analizador WNBA">
    <CabeceraAnalizadorBaloncesto liga="WNBA" tabActivo={tab} onTab={setTab} />
    {cargandoDatos&&<div className="flex-1 flex items-center justify-center py-20"><div className="text-center"><Spinner tamano="lg" texto="Inicializando sistema..." centrado/><p className="text-texto-terciario text-sm mt-4 font-mono">Conectando con el servidor de análisis</p></div></div>}
    {!datos&&error&&<MensajeError titulo="Error de conexión" mensaje={error} onCerrar={()=>void recargar()}/>}
    {datos&&tab==='analisis'&&<PanelesAnalisisBaloncesto formulario={<FormularioAnalisis deporte="WNBA" equipos={equipos}
      estadisticas={datos.estadisticas.equipos} partidosDisponibles={datos.proximos} partidoActual={fixture}
      onSeleccionarPartido={setFixture} onAnalizar={enviar} cargando={cargando} onCambiarParametros={invalidar}
      onCambiarModo={setCuartos} onActualizarPartidos={()=>void actualizar()}
      estadoCalendario={datos.comprobacion} valoresIniciales={valoresIniciales}/> }>
      {error&&<MensajeError titulo="Error en el análisis" mensaje={error} onCerrar={invalidar}/>}
      {cargando&&<ProgresoAnalisis/>}
      {resultado&&vista&&!cargando&&<div className="space-y-4"><ResultadoAnalisis resultado={vista}
        advertencias={[...(resultado.es_prueba ? ['ANÁLISIS DE PRUEBA: no es un pronóstico oficial ni una apuesta. En los cortes de comprobación los parciales son entradas de prueba, no marcadores reales verificados.'] : []),...resultado.advertencias,`Publicación ${resultado.publicacion_version}; datos ${resultado.dataset_sha256}; ${resultado.muestras.partidos} partidos; último dato utilizado ${resultado.ultimo_dato_utilizado}.`,
          `Regulación: ${resultado.regulacion?.media_total.toFixed(2)??'N/D'} puntos. OT: ${resultado.ot?.n??'N/D'} casos del alcance. ${resultado.politica_corte}`]}
        seleccionUsuario={{lado,linea:resultado.linea}} equipoLocalId={resultado.equipo_local_id} equipoVisitanteId={resultado.equipo_visitante_id}
        onGuardar={vista.es_en_vivo?undefined:()=>setGuardar(true)} onConfigurarBankroll={()=>window.location.assign('/configuracion')}
        onNavegarlEquipo={id=>{setEquipoHistorialId(id);setTab('estadisticas');}}/></div>}
      {!resultado&&!cargando&&!error&&<div className="tarjeta h-full min-h-[500px]"><EstadoVacio/></div>}
      {cuartos===0&&!vista?.es_en_vivo&&<div className="mt-4"><CreadorCombinada liga="wnba" seleccionActual={seleccionCombinada}/></div>}
    </PanelesAnalisisBaloncesto>}
    {datos&&tab==='estadisticas'&&<div className="space-y-4">
      <button type="button" onClick={()=>setTab('analisis')} className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-neon-cyan/30 bg-futurista-oscuro/50 text-neon-cyan hover:bg-neon-cyan/10 hover:border-neon-cyan/50 transition-all duration-200 text-sm font-medium"><ArrowLeft className="w-4 h-4"/><span>Volver a Análisis</span></button>
      <div className="space-y-6"><TablaEstadisticasEquipos equipos={datos.estadisticas.equipos} equiposCatalogo={equipos}
        fechaActualizacion={datos.estadisticas.fecha_actualizacion} temporadasDisponibles={datos.estadisticas.temporadas_disponibles}
        temporadaActual={datos.estadisticas.temporada_actual} onCambiarTemporada={tid=>void cambiarTemporada(tid)}
        onSeleccionarEquipo={setEquipoHistorialId} equipoResaltadoId={equipoHistorialId??undefined}/>
        {equipoHistorialId&&<HistorialEquipo equipoId={equipoHistorialId} liga="wnba" onCerrar={()=>setEquipoHistorialId(null)}/>}</div>
    </div>}
    {resultado&&vista&&!vista.es_en_vivo&&<FormularioGuardarApuesta abierto={guardar} resultado={vista} competicionCodigo="wnba"
      ladoSeleccionado={lado} lineaSeleccionada={resultado.linea} cuotaSeleccionada={cuota} partidoId={resultado.partido_id??undefined}
      fechaPartido={resultado.fecha_partido?new Intl.DateTimeFormat('en-CA',{timeZone:'America/Bogota'}).format(new Date(resultado.fecha_partido)):undefined}
      bloqueoGuardado={resultado.guardar_bitacora_habilitado?undefined:resultado.motivo_bitacora}
      onCerrar={()=>setGuardar(false)} onGuardar={async p=>{try{await crearApuesta(p);setGuardar(false);}catch(e){setError(extraerMensajeError(e));}}}/>}
  </div>;
}
