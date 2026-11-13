import { useState } from 'react';
import { AlertCircle, Archive, CalendarDays, ChevronDown, Database, Layers3, Search, ShieldCheck } from 'lucide-react';
import type { EstadoActualizacion } from '../../tipos/actualizacionLigas';
import { corteActualizacion as corte, fechaActualizacion as fecha, estadoActualizacionLegible as legible,
  motivoActualizacionLegible, unirLigasActualizacion, eventosPendientesActualizacion, tienePendientesActualizacion,
  type LigaActualizacion } from '../../utilidades/actualizacionLigas';

export function ResumenActualizacion({ estado }: { estado: EstadoActualizacion | null }) {
  const c = estado?.cobertura_operativa;
  return <div className="actualizacion-metricas" aria-label="Resumen de cobertura">
    <article className="actualizacion-metrica" aria-label="Incidencias diarias">
      <span><AlertCircle size={17} aria-hidden="true" /> Resultados y estadísticas</span>
      <strong>{c ? <>{c.competiciones_diarias_con_incidencias}<small> / {c.competiciones_diarias}</small></> : 'N/D'}</strong>
      <p>competiciones diarias con incidencias</p>
      <small>{c ? `${c.competiciones_archivadas} torneos archivados, aparte` : 'Esperando cobertura acreditada'}</small>
    </article>
    <article className="actualizacion-metrica" aria-label="Eventos de agenda pendientes">
      <span><CalendarDays size={17} aria-hidden="true" /> Agenda por revisar</span>
      <strong>{c?.eventos_agenda_pendientes ?? 'N/D'}</strong>
      <p>eventos en la cola acumulada</p>
      <small>{c ? `${c.consultas_agenda_pendientes} consultas pendientes · ${c.consultas_agenda_error} con error` : 'No equivale a partidos ausentes'}</small>
    </article>
    <article className="actualizacion-metrica" aria-label="Estadísticas ausentes en ventana">
      <span><Layers3 size={17} aria-hidden="true" /> Campos ausentes</span>
      <strong>{c?.campos_estadisticas_ausentes_ventana ?? 'N/D'}</strong>
      <p>{c ? `en ${c.partidos_estadisticas_pendientes_ventana} ${c.partidos_estadisticas_pendientes_ventana === 1 ? 'partido guardado' : 'partidos guardados'}` : 'Sin inventario confirmado'}</p>
      <small>Solo fútbol · ventana revisada</small>
    </article>
    <article className="actualizacion-metrica actualizacion-metrica-fecha" aria-label="Última actualización completa de todas las ligas">
      <span><ShieldCheck size={17} aria-hidden="true" /> Última completa acreditada</span>
      <strong>{estado?.actualizacion_ligas?.ultima_completa_en ? fecha(estado.actualizacion_ligas.ultima_completa_en) : 'Sin acreditar'}</strong>
      <p>Una revisión parcial no cambia esta fecha.</p>
      <small>Cobertura oficial no acreditada</small>
    </article>
  </div>;
}

function DetalleLiga({ liga }: { liga: LigaActualizacion }) {
  const r = liga.resultado, a = liga.agenda, f = liga.frescura, cola = r?.pendientes_cola;
  return <div className="actualizacion-detalle">
    <div className="actualizacion-detalle-grid">
      <div>
        <h3>Agenda publicada</h3>
        {a ? <>
          <p>{legible(a.estado)}.</p>
          <p>{a.consultas_observadas} consultas observadas · {a.consultas_pendientes} pendientes · {a.consultas_error} con error.</p>
          <p>{a.eventos_enumerados} eventos observados · {a.horas_confirmadas} con hora.</p>
          <p>Última fecha publicada: {corte(a.ultima_fecha_publicada)}.</p>
        </> : <p>Sin captura de agenda en este informe.</p>}
        <p>Eventos pendientes de revisión: {eventosPendientesActualizacion(liga) ?? 'N/D'}.</p>
      </div>
      <div>
        <h3>Resultados del ciclo</h3>
        {r ? <>
          <p>Ventana: {r.desde} a {r.hasta}.</p>
          <p>Finales fuente: {r.finales_fuente} · Nuevos: {r.insertados} · Resultados completados: {r.resultados_actualizados}.</p>
          <p>Campos escritos en el ciclo: {r.campos_escritos ?? r.campos_completados ?? 'N/D'}. Campos que pasaron el control: {r.campos_acreditados ?? 'N/D'}. Campos rechazados: {r.campos_no_acreditados ?? 'N/D'}.</p>
          <p>{legible(r.estado)}. Solo finales y campos objetivo; no certifica el histórico.</p>
        </> : <p>Sin revisión de resultados en este informe.</p>}
      </div>
      <div>
        <h3>Estadísticas: ventana y cola</h3>
        {r?.estadisticas_ventana ? <p>En la ventana: <strong>{r.estadisticas_ventana.campos_estadisticas_ausentes} campos ausentes en {r.estadisticas_ventana.partidos_estadisticas_pendientes} partidos guardados.</strong></p> : <p>Campos de fútbol en ventana: N/D; no se aplica este contador a baloncesto.</p>}
        {cola ? <>
          <p>Cola acumulada: {cola.resultados} resultados, {cola.eventos_agenda} eventos de agenda y <strong>{cola.campos_estadisticas} campos estadísticos en {cola.partidos_estadisticas} partidos.</strong></p>
          <p>{cola.campos_estadisticas_elegibles} campos habilitados para reconsulta.</p>
          {cola.proximo_reintento_en && <p className="actualizacion-reintento">Próximo reintento habilitado: {fecha(cola.proximo_reintento_en)}. Requiere una actualización manual; no se ejecuta automáticamente.</p>}
        </> : <p>Cola acumulada: N/D.</p>}
      </div>
      <div>
        <h3>Fuentes y cortes guardados</h3>
        {f ? <>
          <p>Resultados hasta: {corte(f.resultados_hasta)}.</p>
          <p>Estadísticas hasta: {corte(f.estadisticas_hasta)}.</p>
          <p>Último cambio de datos: {fecha(f.cambio_en)}.</p>
          <p>Revisión de estadísticas: {legible(f.estadisticas.estado)} · {fecha(f.estadisticas.verificado_en)}.</p>
          {f.estadisticas.detalle && <p>{f.estadisticas.detalle}</p>}
          {!a && <p>Última revisión de agenda: {fecha(f.verificacion_agenda_en)} · {legible(f.estado_agenda)}.</p>}
        </> : <p>Fechas de frescura no acreditadas en este informe.</p>}
      </div>
    </div>
    {!!r?.incidencias?.length && <div className="actualizacion-motivos">
      <h3>{r.incidencias.length} pendientes o incidencias de resultados/estadísticas</h3>
      <ul>{r.incidencias.map((incidencia, i) => <li key={i}>{motivoActualizacionLegible(incidencia.motivo)}</li>)}</ul>
    </div>}
  </div>;
}

function FilaLiga({ liga }: { liga: LigaActualizacion }) {
  const pendiente = tienePendientesActualizacion(liga), r = liga.resultado, a = liga.agenda;
  const eventos = eventosPendientesActualizacion(liga);
  const ventana = r?.estadisticas_ventana;
  return <details className={`actualizacion-fila ${pendiente ? 'actualizacion-fila-pendiente' : ''}`}>
    <summary>
      <div className="actualizacion-liga-nombre"><strong>{liga.nombre}</strong><span>{liga.deporte === 'baloncesto' ? 'Baloncesto' : liga.deporte === 'futbol' ? 'Fútbol' : 'Deporte N/D'} · {liga.archivada ? 'Archivada' : 'Revisión diaria'}</span></div>
      <div className="actualizacion-celda"><small>Agenda</small><strong>{eventos == null ? 'N/D' : `${eventos} por revisar`}</strong><span>{a ? legible(a.estado) : 'Sin revisión de agenda'}</span></div>
      <div className="actualizacion-celda"><small>Resultados</small><strong>{corte(liga.frescura?.resultados_hasta)}</strong><span>{legible(r?.estado)}</span></div>
      <div className="actualizacion-celda"><small>Estadísticas en ventana</small><strong>{ventana ? `${ventana.campos_estadisticas_ausentes} campos ausentes` : r ? legible(r.estado) : 'N/D'}</strong><span>{ventana ? `${ventana.partidos_estadisticas_pendientes} partidos guardados` : 'Campos objetivo de su liga'}</span></div>
      <div className="actualizacion-fila-estado"><span className={`actualizacion-insignia ${pendiente ? 'aviso' : ''}`}>{liga.archivada ? 'Archivada' : pendiente ? 'Con pendientes' : r?.estado === 'COMPLETA_EN_VENTANA' ? 'Revisada en ventana' : 'Ver detalle'}</span><ChevronDown aria-hidden="true" size={18} /><span className="sr-only">Ver detalle de {liga.nombre}</span></div>
    </summary>
    <DetalleLiga liga={liga} />
  </details>;
}

export function TableroActualizacionLigas({ estado }: { estado: EstadoActualizacion | null }) {
  const [filtro, setFiltro] = useState<'pendientes' | 'diarias' | 'archivadas'>('pendientes');
  const [busqueda, setBusqueda] = useState('');
  const [deporte, setDeporte] = useState('');
  const ligas = unirLigasActualizacion(estado);
  const diarias = ligas.filter(l => !l.archivada), archivadas = ligas.filter(l => l.archivada);
  const pendientes = diarias.filter(tienePendientesActualizacion);
  const grupo = filtro === 'archivadas' ? archivadas : filtro === 'pendientes' ? pendientes : diarias;
  const normalizar = (s: string) => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es');
  const visibles = grupo.filter(l => (!deporte || l.deporte === deporte) && normalizar(l.nombre).includes(normalizar(busqueda.trim())));
  const agenda = estado?.agenda_multiliga;
  return <>
    <section className="actualizacion-competiciones" aria-label="Cobertura por competición">
      <div className="actualizacion-titulo-seccion"><div><p className="actualizacion-eyebrow">Del resumen al detalle</p><h2>Competiciones</h2></div><span className="actualizacion-ayuda">Abre una fila para ver fuentes, cola y motivos.</span></div>
      <div className="actualizacion-filtros">
        <div role="group" aria-label="Ámbito de competiciones" className="actualizacion-segmentos">
          {([{ valor: 'pendientes', texto: 'Con pendientes', total: pendientes.length }, { valor: 'diarias', texto: 'Todas las diarias', total: diarias.length }, { valor: 'archivadas', texto: 'Archivadas', total: archivadas.length }] as const).map(f => <button type="button" key={f.valor} aria-pressed={filtro === f.valor} onClick={() => setFiltro(f.valor)}>{f.texto} <span>{estado ? f.total : '—'}</span></button>)}
        </div>
        <div className="actualizacion-busqueda">
          <label><span>Buscar competición</span><div><Search size={16} aria-hidden="true" /><input type="search" value={busqueda} onChange={e => setBusqueda(e.target.value)} placeholder="Nombre de la liga…" maxLength={100} /></div></label>
          <label><span>Deporte</span><select value={deporte} onChange={e => setDeporte(e.target.value)}><option value="">Todos los deportes</option><option value="baloncesto">Baloncesto</option><option value="futbol">Fútbol</option></select></label>
        </div>
      </div>
      <p className="actualizacion-nota">{filtro === 'archivadas' ? 'Torneos archivados: fuera del contador diario; el histórico se conserva.' : 'El filtro incluye pendientes de agenda, resultados o estadísticas. No equivale al contador de incidencias diarias de resultados y estadísticas.'}</p>
      {agenda && <p className="actualizacion-nota">Agenda solicitada: <strong>{agenda.desde} → {agenda.hasta}</strong> · {agenda.ejecucion_lotes?.lotes?.length ?? 'N/D'} lotes recorridos. Cobertura oficial desconocida.</p>}
      <p className="actualizacion-conteo" aria-live="polite">Mostrando {visibles.length} de {grupo.length} competiciones de este filtro.</p>
      <div className="actualizacion-lista" aria-label="Detalle por liga">
        {visibles.map(l => <FilaLiga liga={l} key={l.codigo} />)}
        {visibles.length === 0 && <div className="actualizacion-vacio"><Database size={28} aria-hidden="true" /><p>{!estado ? 'Esperando el estado guardado.' : ligas.length === 0 ? 'El informe no contiene detalle por competición. No se acredita cobertura.' : 'No hay competiciones para estos filtros.'}</p><p>Que esta lista esté vacía no demuestra una cobertura completa.</p>{(busqueda || deporte) && <button type="button" className="actualizacion-boton" onClick={() => { setBusqueda(''); setDeporte(''); }}>Limpiar búsqueda y deporte</button>}</div>}
      </div>
    </section>
    <details className="actualizacion-extra">
      <summary><Layers3 size={18} aria-hidden="true" /><strong>Modelos y cortes de entrenamiento</strong><span>Separados de la actualización de datos</span><ChevronDown size={18} aria-hidden="true" /></summary>
      <div className="actualizacion-modelos">
        {estado?.modelos?.map(m => <article key={m.nombre}><span>{m.nombre}</span><strong>{m.version ?? 'Versión N/D'}</strong><p>Corte: {corte(m.corte)}.</p><p>{m.finales_posteriores == null ? 'Finales posteriores: N/D.' : `${m.finales_posteriores} finales guardados posteriores.`}</p>{m.necesita_actualizacion && <span className="actualizacion-insignia aviso">Hay datos posteriores</span>}</article>)}
        {!estado?.modelos?.length && <p>Inventario de modelos no disponible.</p>}
      </div>
      <p className="actualizacion-nota">Actualizar datos no reentrena, activa ni certifica modelos. Preparar un candidato es una operación separada.</p>
    </details>
    <details className="actualizacion-extra">
      <summary><Archive size={18} aria-hidden="true" /><strong>Fuentes, fechas y alcance</strong><span>Qué acredita esta revisión</span><ChevronDown size={18} aria-hidden="true" /></summary>
      <div className="actualizacion-fuentes">
        <p>Última verificación de fuentes: {fecha(estado?.fuentes_verificadas_en)}.</p>
        <p>Cambios guardados en el último ciclo: {fecha(estado?.cambio_guardado_en)}.</p>
        <p>Último ciclo separado de calendarios y marcadores: {fecha(estado?.actualizacion_ligas?.ultimo_ciclo_agendas?.terminado_en)}.</p>
        {estado?.detalle && <p>{estado.detalle}</p>}
        <p>Los campos, los partidos, los eventos y las consultas son contadores distintos. La cola es acumulada; la ventana revisada no recertifica todo el histórico.</p>
        {agenda && <p>Se muestran eventos publicados en las consultas disponibles, no un calendario oficial íntegro. Una consulta pendiente no equivale a un partido ausente.</p>}
        {agenda?.ejecucion_lotes && ['LIMITE_TURNOS', 'PRESUPUESTO_HTTP'].includes(agenda.ejecucion_lotes.motivo_parada ?? '') && <p>Se alcanzó el límite del ciclo; los pendientes se conservan para continuar manualmente.</p>}
        {estado?.cobertura?.map(c => <p key={c.competicion}>{c.competicion}: {c.futuros_con_hora} encuentros con hora hasta {fecha(c.ultimo_inicio_publicado)}; horizonte {c.hasta_solicitado}; {c.incidencias} incidencias. Publicación íntegra no acreditada.</p>)}
      </div>
    </details>
  </>;
}
