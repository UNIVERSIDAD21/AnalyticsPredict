import { useEffect, useRef, useState } from 'react';
import { clienteAPI, extraerMensajeError } from '../../servicios/api';

interface Estado {
  estado: string;
  etapa?: string;
  terminado_en?: string;
  ejecucion_id?: string;
  cobertura_operativa?: {
    competiciones_diarias: number; competiciones_diarias_con_incidencias: number;
    competiciones_archivadas: number; consultas_agenda_pendientes: number;
    consultas_agenda_error: number; eventos_agenda_pendientes: number;
    campos_estadisticas_ausentes_ventana: number; partidos_estadisticas_pendientes_ventana: number;
  };
  agenda_multiliga?: {
    desde: string; hasta: string; operaciones: number;
    ejecucion_lotes?: { lotes?: { lote: string; turnos: number; consultas: number }[];
      turnos_consumidos?: number; limite_turnos?: number; motivo_parada?: string };
    ligas: { codigo: string; nombre: string; estado: string; consultas_observadas: number;
      consultas_pendientes: number; consultas_error: number; eventos_enumerados: number;
      horas_confirmadas: number; ultima_fecha_publicada: string | null; eventos_pendientes_cola?: number }[];
  };
  fuentes_verificadas_en?: string | null;
  cambio_guardado_en?: string | null;
  detalle?: string;
  error_actualizacion?: string;
  iniciado_en?: string;
  progreso?: { ligas_revisadas: number; ligas_total: number };
  ligas_resultado?: { codigo: string; nombre: string; deporte: string; estado: string;
    desde: string; hasta: string; finales_fuente: number; insertados: number;
    resultados_actualizados: number; estadisticas_actualizadas: number; campos_completados: number;
    campos_escritos?: number; campos_acreditados?: number; campos_no_acreditados?: number;
    ambito?: string; afecta_cobertura_diaria?: boolean;
    pendientes_cola?: { resultados: number; eventos_agenda: number; campos_estadisticas: number;
      partidos_estadisticas: number; campos_estadisticas_elegibles: number; proximo_reintento_en: string | null };
    estadisticas_ventana?: { partidos_estadisticas_pendientes: number; campos_estadisticas_ausentes: number } | null;
    incidencias: { motivo: string }[] }[];
  correccion_calidad?: { campos_escritos: number; campos_acreditados: number;
    campos_no_acreditados: number; partidos_en_cuarentena: number };
  modelos?: { nombre: string; version?: number | string; corte: string | null;
    finales_posteriores?: number; necesita_actualizacion?: boolean }[];
  actualizacion_ligas?: {
    ultimo_ciclo_agendas: { terminado_en: string; estado: string } | null;
    ultimo_ciclo_integral: { terminado_en: string; estado: string } | null;
    ultima_completa_en: string | null;
    ligas: { codigo: string; nombre: string; deporte: string; cambio_en: string | null;
      resultados_hasta: string | null; estadisticas_hasta: string | null;
      verificacion_agenda_en: string | null; estado_agenda: string;
      estadisticas: { estado: string; verificado_en?: string; detalle?: string } }[];
  } | null;
  cobertura?: { competicion: string; hasta_solicitado: string; futuros_con_hora: number; ultimo_inicio_publicado: string | null; incidencias: number }[];
}
const fecha = (v?: string | null) => v ? new Date(v).toLocaleString('es-CO', { timeZone: 'America/Bogota' }) + ' COT' : 'sin acreditar';
const corte = (v: string | null) => !v ? 'N/D' : /^\d{4}-\d{2}-\d{2}$/.test(v) ? v : fecha(v);
const estadoLegible = (v: string) => ({ COMPLETA_EN_VENTANA: 'Revisada en esta ventana',
  SIN_FINALES_EN_VENTANA: 'Sin finales en esta ventana', PARCIAL: 'Con pendientes',
  SIN_ADAPTADOR: 'Sin fuente configurada', COMPLETO: 'Revisión completada',
  PLAN_SIN_APLICAR: 'Revisión sin guardar' }[v] ?? v.replace(/_/g, ' '));
const motivoLegible = (v: string) => {
  if (v.startsWith('SIN_ADAPTADOR')) return 'Esta competición no tiene una fuente vigente configurada. Su histórico se conserva.';
  if (v === 'FINAL_LOCAL_NO_CONTRASTADO_CON_FUENTE') return 'Hay un resultado guardado que no pudo contrastarse con la fuente en esta revisión.';
  if (v === 'ESTADISTICAS_LOCALES_PENDIENTES' || v === 'ESTADISTICAS_AUSENTES') return 'Todavía faltan estadísticas publicadas o vinculadas para este partido.';
  if (v.startsWith('PRESUPUESTO_ESTADISTICAS')) return 'Este partido queda pendiente del siguiente ciclo por el límite de consultas.';
  return v;
};

export function EstadoSincronizacionAgenda() {
  const [estado, setEstado] = useState<Estado | null>(null);
  const [error, setError] = useState('');
  const [ocupado, setOcupado] = useState(false);
  const [revision, setRevision] = useState(0);
  const pendiente = useRef<{ anterior?: string; desde: number } | null>(null);
  useEffect(() => {
    const ctl = new AbortController();
    clienteAPI.get<Estado>('/api/agendas/sincronizacion', { signal: ctl.signal })
      .then(r => {
        if (ctl.signal.aborted) return;
        if (pendiente.current && r.data.iniciado_en === pendiente.current.anterior && r.data.estado !== 'EN_CURSO') {
          if (Date.now() - pendiente.current.desde < 60_000) return;
          setError('No se confirmó el inicio. Consulta el estado antes de volver a solicitar la actualización.');
        }
        pendiente.current = null;
        setEstado(r.data);
      })
      .catch(e => { if (!ctl.signal.aborted) setError(extraerMensajeError(e)); });
    return () => ctl.abort();
  }, [revision]);
  const ejecutando = estado?.estado === 'EN_CURSO' || estado?.estado === 'SOLICITADA';
  const pausada = estado?.estado === 'PAUSADA_CALIDAD';
  useEffect(() => {
    if (!ejecutando) return;
    const timer = window.setInterval(() => setRevision(n => n + 1), 3000);
    return () => window.clearInterval(timer);
  }, [ejecutando]);
  const sincronizar = async () => {
    setOcupado(true); setError('');
    try {
      pendiente.current = { anterior: estado?.iniciado_en, desde: Date.now() };
      const { data } = await clienteAPI.post<Estado>('/api/agendas/sincronizar');
      setEstado(prev => ({ ...prev, ...data }));
    } catch (e) { pendiente.current = null; setError(extraerMensajeError(e)); }
    finally { setOcupado(false); }
  };
  const actualizacion = estado?.actualizacion_ligas;
  const integral = actualizacion?.ultimo_ciclo_integral;
  const agenda = actualizacion?.ultimo_ciclo_agendas;
  const ultimo = integral && (!agenda || integral.terminado_en >= agenda.terminado_en) ? integral : agenda;
  const agendaMultiliga = estado?.agenda_multiliga;
  const cobertura = estado?.cobertura_operativa;
  const historicas = estado?.ligas_resultado?.filter(l => l.afecta_cobertura_diaria === false) ?? [];
  const diariasConPendientes = estado?.ligas_resultado?.filter(l => l.afecta_cobertura_diaria !== false && l.incidencias.length > 0).length ?? 0;
  const terminado = estado?.estado === 'COMPLETO' || estado?.estado === 'PARCIAL';
  const etapa = { AGENDA: 'Agenda', RESULTADOS: 'Resultados', ESTADISTICAS: 'Estadísticas',
    COBERTURA: 'Cobertura' }[estado?.etapa ?? ''];
  return <section aria-label="Actualización de ligas" className="min-w-0 rounded-xl border border-white/10 p-4 text-xs text-texto-secundario">
    <div className="flex flex-wrap items-center gap-3">
      <button type="button" disabled={ocupado || ejecutando || pausada} className="boton-primario disabled:opacity-40" onClick={() => void sincronizar()}>Actualizar todas las ligas</button>
      <button type="button" className="boton-secundario" onClick={() => { setError(''); setRevision(n => n + 1); }}>Consultar estado</button>
    </div>
    <p className="mt-3 break-words"><strong>Última actualización completa de todas las ligas:</strong> {fecha(actualizacion?.ultima_completa_en)}.</p>
    {ultimo && <p className="mt-1 break-words">Última revisión general: {fecha(ultimo.terminado_en)} · {ultimo.estado.replace(/_/g, ' ')}. {ultimo.estado !== 'COMPLETO' && 'Hay ligas o estadísticas pendientes; consulta el detalle.'}</p>}
    {estado?.error_actualizacion && <p role="status">{estado.error_actualizacion}</p>}
    {ejecutando && <p role="status" className="mt-2 break-words">{etapa && <strong>{etapa} · </strong>}{estado?.detalle ?? 'Solicitando actualización…'}{estado?.progreso && ` · ${estado.progreso.ligas_revisadas}/${estado.progreso.ligas_total} competiciones revisadas.`}</p>}
    {terminado && estado?.terminado_en && <p className="mt-2 break-words">
      <strong>Ejecución terminada</strong> · {fecha(estado.terminado_en)} · {estadoLegible(estado.estado)}
    </p>}
    {cobertura && <div className="mt-2 space-y-1" aria-label="Pendientes de cobertura">
      <p>Resultados y estadísticas: {cobertura.competiciones_diarias_con_incidencias} de {cobertura.competiciones_diarias} competiciones de revisión diaria con incidencias.
        {' '}{cobertura.competiciones_archivadas} torneos archivados se informan por separado.</p>
      <p>Agenda: {cobertura.consultas_agenda_pendientes} consultas pendientes, {cobertura.consultas_agenda_error} con error y {cobertura.eventos_agenda_pendientes} eventos pendientes de revisión.</p>
      <p>Estadísticas de fútbol en la ventana: {cobertura.campos_estadisticas_ausentes_ventana} campos ausentes en {cobertura.partidos_estadisticas_pendientes_ventana} partidos guardados.
        {' '}Los campos, los partidos y las consultas son contadores distintos.</p>
    </div>}
    {(estado?.estado === 'ERROR' || estado?.estado === 'INTERRUMPIDA') &&
      <p role="alert" className="mt-2 break-words">{estado.detalle ?? 'La ejecución se interrumpió. Revisa el estado antes de reintentar.'}</p>}
    {pausada && <p role="status" className="mt-2">La actualización está pausada mientras se verifica la calidad de los datos.</p>}
    {estado?.correccion_calidad && <p className="mt-2 break-words">
      Corrección estadística · {estado.correccion_calidad.campos_escritos} campos escritos en el ciclo original,
      {' '}{estado.correccion_calidad.campos_acreditados} pasaron el control de coherencia y
      {' '}{estado.correccion_calidad.campos_no_acreditados} quedaron en cuarentena en
      {' '}{estado.correccion_calidad.partidos_en_cuarentena} partidos.
    </p>}
    {error && <p role="alert" className="mt-2">{error}</p>}
    {agendaMultiliga && <details className="mt-3">
      <summary className="cursor-pointer">Agenda futura · cobertura por competición</summary>
      <p className="mt-2">Horizonte solicitado: {agendaMultiliga.desde} a {agendaMultiliga.hasta}.
        {' '}Se muestran eventos publicados en las consultas disponibles. La cobertura oficial es desconocida.</p>
      {agendaMultiliga.ejecucion_lotes?.lotes && <p className="mt-2">
        Agenda recorrida en {agendaMultiliga.ejecucion_lotes.lotes.length} lotes acotados.
        {' '}Una consulta pendiente no equivale a un partido ausente; puede haber fixtures ya guardados de ciclos anteriores.
        {agendaMultiliga.ejecucion_lotes.motivo_parada === 'LIMITE_TURNOS' && ' Se alcanzó el límite del ciclo; los pendientes se conservan para continuar.'}
        {agendaMultiliga.ejecucion_lotes.motivo_parada === 'PRESUPUESTO_HTTP' && ' Se alcanzó el límite de red del ciclo; los pendientes se conservan para continuar.'}
      </p>}
      <ul className="mt-2 space-y-2" aria-label="Cobertura de agenda">
        {agendaMultiliga.ligas.filter(liga => liga.estado !== 'SIN_ADAPTADOR').map(liga =>
          <li className="break-words" key={liga.codigo}><strong>{liga.nombre}</strong> · {estadoLegible(liga.estado)}
            <p>{liga.consultas_observadas} consultas observadas, {liga.consultas_pendientes} pendientes y {liga.consultas_error} con error.
              {' '}{liga.eventos_enumerados} eventos observados, {liga.horas_confirmadas} con hora.
              {' '}Última fecha publicada: {corte(liga.ultima_fecha_publicada)}.</p>
            {!!liga.eventos_pendientes_cola &&
              <p>Eventos pendientes de revisión de agenda: {liga.eventos_pendientes_cola}.</p>}
          </li>)}
      </ul>
      {agendaMultiliga.ligas.some(liga => liga.estado === 'SIN_ADAPTADOR') &&
        <p className="mt-2">Torneos sin fuente vigente: {agendaMultiliga.ligas.filter(liga => liga.estado === 'SIN_ADAPTADOR')
          .map(liga => liga.nombre).join(', ')}.</p>}
    </details>}
    {estado?.ligas_resultado && <details className="mt-3">
      <summary className="cursor-pointer">Resultados de la última actualización · {diariasConPendientes} competiciones con pendientes</summary>
      <p className="mt-2">Se revisan partidos finalizados y estadísticas disponibles en cada ventana. Los torneos sin fuente configurada y los campos ausentes quedan visibles. Los modelos se mantienen; actualizar datos no los reentrena.</p>
      {historicas.length > 0 && <p className="mt-2">Torneos archivados, fuera del contador diario: {historicas.map(l => l.nombre).join(', ')}. Su histórico se conserva; no acredita cobertura completa.</p>}
      {estado.modelos?.map(m => <p key={m.nombre} className="mt-2 break-words"><strong>{m.nombre} {m.version ?? ''}</strong>: corte {m.corte ?? 'N/D'}.{m.necesita_actualizacion && ` Hay ${m.finales_posteriores} finales guardados posteriores; preparar un candidato es una operación separada.`}</p>)}
      <ul className="mt-3 space-y-3" aria-label="Resultado por competición">
        {estado.ligas_resultado.map(l => <li key={`${l.deporte}:${l.codigo}`} className="border-t border-white/10 pt-2 break-words">
          <strong>{l.nombre}</strong> · {estadoLegible(l.estado)}
          <p>Ventana: {l.desde} a {l.hasta}. Finales fuente: {l.finales_fuente}. Nuevos: {l.insertados}. Resultados completados: {l.resultados_actualizados}.</p>
          <p>Campos escritos en el ciclo: {l.campos_escritos ?? l.campos_completados}. Campos que pasaron el control: {l.campos_acreditados ?? 'N/D'}. Campos rechazados: {l.campos_no_acreditados ?? 'N/D'}.</p>
          {l.estadisticas_ventana && <p>En la ventana: {l.estadisticas_ventana.campos_estadisticas_ausentes} campos ausentes en {l.estadisticas_ventana.partidos_estadisticas_pendientes} partidos guardados.</p>}
          {l.pendientes_cola && <>
            <p>Cola acumulada: {l.pendientes_cola.resultados} resultados, {l.pendientes_cola.eventos_agenda} eventos de agenda y {l.pendientes_cola.campos_estadisticas} campos estadísticos en {l.pendientes_cola.partidos_estadisticas} partidos.
              {' '}{l.pendientes_cola.campos_estadisticas_elegibles} campos habilitados para reconsulta.</p>
            {l.pendientes_cola.proximo_reintento_en && <p>Próximo reintento habilitado: {fecha(l.pendientes_cola.proximo_reintento_en)}. Requiere una actualización manual; no se ejecuta automáticamente.</p>}
          </>}
          {l.incidencias.length > 0 && <details><summary className="cursor-pointer">{l.incidencias.length} pendientes o incidencias</summary><ul>{l.incidencias.slice(0, 20).map((e, i) => <li key={i}>{motivoLegible(e.motivo)}</li>)}</ul>{l.incidencias.length > 20 && <p>El informe local conserva el detalle completo.</p>}</details>}
        </li>)}
      </ul>
    </details>}
    <details className="mt-2">
    <summary className="cursor-pointer">Fuentes y sincronización · {estado?.estado.replace(/_/g, ' ') ?? 'sin consultar'}</summary>
    <div className="mt-3 space-y-3 break-words">
      <p>Última verificación de fuentes: {fecha(estado?.fuentes_verificadas_en)}. Cambios guardados en el último ciclo: {fecha(estado?.cambio_guardado_en)}.</p>
      <p>El botón revisa agenda, resultados y estadísticas disponibles. La actualización puede tardar varios minutos.</p>
      {estado?.detalle && !ejecutando && <p>{estado.detalle}</p>}
      {actualizacion && <>
        <p>Último ciclo separado de calendarios y marcadores: {fecha(actualizacion.ultimo_ciclo_agendas?.terminado_en)}. Las fechas de partidos son cortes guardados. El resumen de actualización distingue las estadísticas recuperadas de las que siguen pendientes.</p>
        <ul className="space-y-3" aria-label="Frescura por liga">
          {actualizacion.ligas.map(liga => <li key={`${liga.deporte}:${liga.codigo}`} className="border-t border-white/10 pt-2">
            <strong>{liga.nombre}</strong>
            {agendaMultiliga
              ? <p>Agenda del actualizador multiliga · {estadoLegible(agendaMultiliga.ligas.find(row => row.codigo === liga.codigo)?.estado ?? 'N/D')}.</p>
              : <p>Agenda del ciclo separado: {fecha(liga.verificacion_agenda_en)} · {liga.estado_agenda.replace(/_/g, ' ')}.</p>}
            <p>Resultados hasta: {corte(liga.resultados_hasta)}. Estadísticas hasta: {corte(liga.estadisticas_hasta)}.</p>
            <p>Último cambio de datos: {fecha(liga.cambio_en)}. Revisión de estadísticas: {liga.estadisticas.estado.replace(/_/g, ' ')}{liga.estadisticas.verificado_en ? ` · ${fecha(liga.estadisticas.verificado_en)}` : ''}.</p>
            {liga.estadisticas.detalle && <p>{liga.estadisticas.detalle}</p>}
          </li>)}
        </ul>
      </>}
      {estado?.cobertura?.map(c => <p key={c.competicion}><strong>{c.competicion}</strong>: {c.futuros_con_hora} encuentros con hora hasta {fecha(c.ultimo_inicio_publicado)}; ventana solicitada hasta {c.hasta_solicitado}; {c.incidencias} incidencias. Publicación íntegra no acreditada.</p>)}
    </div>
    </details>
  </section>;
}
