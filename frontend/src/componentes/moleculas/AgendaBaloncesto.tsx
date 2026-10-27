import { useEffect, useRef, useState } from 'react';
import { CalendarDays, ChevronLeft, ChevronRight, RefreshCw, Search } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import { consultarAgendaBaloncesto, type AgendaBaloncesto as DatosAgenda, type PartidoAgendaBaloncesto } from '../../servicios/agendaBaloncesto';
import { extraerMensajeError } from '../../servicios/api';
import { fechaColombia, sumarDias } from '../../utilidades/agendaFutbol';

interface Props { seleccionado: PartidoAgendaBaloncesto | null; onSeleccionar: (p: PartidoAgendaBaloncesto) => void; onCambiar: () => void }
const campo = 'input-base w-full min-w-0';
export function AgendaBaloncesto({ seleccionado, onSeleccionar, onCambiar }: Props) {
  const [params, setParams] = useSearchParams();
  const fechaUrl = params.get('fecha');
  const fecha = fechaUrl && /^\d{4}-\d{2}-\d{2}$/.test(fechaUrl) && Number.isFinite(Date.parse(fechaUrl)) ? fechaUrl : fechaColombia();
  // La liga del motor no restringe la agenda. El filtro es explícito y visible.
  const [liga, setLiga] = useState('');
  const [estado, setEstado] = useState('todos');
  const [buscar, setBuscar] = useState('');
  const [busqueda, setBusqueda] = useState('');
  const [pagina, setPagina] = useState(1);
  const [revision, setRevision] = useState(0);
  const [reloj, setReloj] = useState(Date.now);
  useEffect(() => { const id = setInterval(() => setReloj(Date.now()), 15000); return () => clearInterval(id); }, []);
  const [datos, setDatos] = useState<DatosAgenda | null>(null);
  const [error, setError] = useState('');
  const [cargando, setCargando] = useState(true);
  useEffect(() => { const timer = setTimeout(() => setBusqueda(buscar.trim()), 250); return () => clearTimeout(timer); }, [buscar]);
  useEffect(() => {
    const ctl = new AbortController();
    setCargando(true); setError('');
    consultarAgendaBaloncesto({ fecha, liga, estado, buscar: busqueda, pagina }, ctl.signal)
      .then(d => { if (!ctl.signal.aborted) setDatos(d); })
      .catch(e => { if (!ctl.signal.aborted) { setDatos(null); setError(extraerMensajeError(e)); } })
      .finally(() => { if (!ctl.signal.aborted) setCargando(false); });
    return () => ctl.abort();
  }, [fecha, liga, estado, busqueda, pagina, revision]);
  const partidoUrl = params.get('partidoId');
  const ultimoEnlace = useRef<string | null>(null);
  useEffect(() => {
    if (!partidoUrl) ultimoEnlace.current = null;
    if (!cargando && partidoUrl && ultimoEnlace.current !== partidoUrl) {
      const p = datos?.partidos.find(x => x.id === partidoUrl);
      if (p) {
        ultimoEnlace.current = partidoUrl;
        if (seleccionado?.id !== partidoUrl) onSeleccionar(p);
      }
    }
  }, [cargando, datos, partidoUrl, seleccionado, onSeleccionar]);
  const cambiarFecha = (valor: string) => {
    if (!valor || valor === fecha) return;
    onCambiar(); setPagina(1);
    setParams(prev => { const p = new URLSearchParams(prev); p.set('fecha', valor); p.delete('partidoId'); return p; });
  };
  const filtrado = Boolean(liga || buscar || estado !== 'todos');
  return <section className="tarjeta p-4 sm:p-6 mb-6 space-y-5 min-w-0" aria-label="Agenda de baloncesto">
    <div className="flex flex-wrap justify-between gap-3 items-start">
      <div><p className="text-xs tracking-wider text-neon-cyan">BALONCESTO · TODAS TUS COMPETICIONES</p><h1 className="font-futurista text-2xl mt-2 flex gap-2 items-center"><CalendarDays aria-hidden="true" />Partidos</h1><p className="text-sm text-texto-secundario mt-2">{new Date(`${fecha}T12:00:00Z`).toLocaleDateString('es-CO', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', timeZone: 'America/Bogota' })} · hora de Colombia</p></div>
      <button type="button" className="text-neon-cyan text-sm flex gap-2 items-center" disabled={cargando} onClick={() => setRevision(n => n+1)}><RefreshCw className="w-4 h-4" />Actualizar agenda</button>
    </div>
    <div className="flex flex-wrap gap-2 items-center">
      {[[fechaColombia(), 'Hoy'], [sumarDias(fechaColombia(), 1), 'Mañana']].map(([f, texto]) => <button key={texto} type="button" aria-pressed={fecha === f} onClick={() => cambiarFecha(f)} className={`rounded-xl border px-4 py-2 ${fecha === f ? 'border-neon-cyan bg-neon-cyan/15 text-neon-cyan' : 'border-white/15'}`}>{texto}</button>)}
      <button type="button" aria-label="Día anterior" className="p-2" onClick={() => cambiarFecha(sumarDias(fecha,-1))}><ChevronLeft /></button>
      <label className="text-xs text-texto-secundario min-w-0">Elegir fecha<input aria-label="Fecha de los partidos" type="date" className={`${campo} mt-1`} value={fecha} onInput={e => cambiarFecha(e.currentTarget.value)} onChange={e => cambiarFecha(e.target.value)} /></label>
      <button type="button" aria-label="Día siguiente" className="p-2" onClick={() => cambiarFecha(sumarDias(fecha,1))}><ChevronRight /></button>
    </div>
    <div className="grid sm:grid-cols-[minmax(0,1fr)_180px_180px] gap-3">
      <label className="text-xs text-texto-secundario">Buscar equipo<span className="relative block mt-1"><Search aria-hidden="true" className="absolute left-3 top-3 w-4 h-4" /><input type="search" className={`${campo} pl-9`} placeholder="Buscar un equipo…" value={buscar} onChange={e => { setBuscar(e.target.value); setPagina(1); onCambiar(); }} maxLength={100} /></span></label>
      <label className="text-xs text-texto-secundario">Filtrar por liga<select className={`${campo} mt-1`} value={liga} onChange={e => { setLiga(e.target.value); setPagina(1); onCambiar(); }}><option value="">Todas las ligas</option><option value="nba">NBA</option><option value="wnba">WNBA</option><option value="euroliga">Euroliga</option></select></label>
      <label className="text-xs text-texto-secundario">Estado<select className={`${campo} mt-1`} value={estado} onChange={e => { setEstado(e.target.value); setPagina(1); onCambiar(); }}><option value="todos">Todos los estados</option><option value="pendientes">Sin resultado confirmado</option><option value="finalizados">Finalizados</option></select></label>
    </div>
    {filtrado && <button type="button" className="text-sm text-neon-cyan" onClick={() => { setLiga(''); setBuscar(''); setEstado('todos'); setPagina(1); onCambiar(); }}>Quitar filtros · ver todas las ligas</button>}
    <p role="status" className="text-xs text-texto-secundario">{cargando ? 'Cargando partidos…' : `${datos?.total ?? 0} partidos registrados · ${datos?.competiciones.length ?? 0} competiciones`}</p>
    {datos && <p className="text-xs text-texto-terciario">Consulta: {new Date(datos.consultado_en).toLocaleTimeString('es-CO', { hour:'2-digit', minute:'2-digit', timeZone:'America/Bogota' })} COT · Último cambio guardado: {datos.datos_actualizados_en ? new Date(datos.datos_actualizados_en).toLocaleString('es-CO', { timeZone:'America/Bogota' }) : 'sin acreditar'}. Consultar la BD no acredita actualización de la fuente.</p>}
    {error && <div role="alert"><p>{error}</p><button type="button" className="text-neon-cyan mt-2" onClick={() => setRevision(n => n+1)}>Reintentar carga</button></div>}
    {!error && !cargando && !datos?.partidos.length && <p className="p-6 border border-dashed border-white/15 rounded-xl text-texto-secundario">No hay partidos registrados para esta fecha y estos filtros. Una agenda vacía no acredita que no haya encuentros.</p>}
    <div className={`grid lg:grid-cols-2 gap-4 ${cargando ? 'opacity-50' : ''}`}>
      {datos?.partidos.map(original => { const reconstruccion = original.inicio_utc ? Date.parse(original.inicio_utc) <= reloj : original.fecha_partido <= fechaColombia(new Date(reloj)); const p = { ...original, reconstruccion }; return <article key={`${p.liga}-${p.id}`} className={`rounded-2xl border p-5 space-y-4 ${seleccionado?.id === p.id ? 'border-neon-cyan bg-neon-cyan/5' : 'border-white/10 bg-black/10'}`}>
        <div className="flex flex-wrap justify-between gap-2 text-sm"><strong>{p.inicio_utc ? new Date(p.inicio_utc).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', timeZone: 'America/Bogota' }) : 'Hora por confirmar'}</strong><span className="text-texto-secundario">{p.finalizado ? 'Finalizado' : p.estado === 'PROGRAMADO' && p.reconstruccion ? 'Estado por verificar' : p.estado === 'PROGRAMADO' ? 'Programado' : p.estado}</span></div>
        <p className="text-xs text-neon-cyan">{p.competicion_nombre} · {p.temporada_nombre}{p.condicional ? ' · Condicional' : ''}</p>
        <p className="font-semibold">{p.equipo_local_nombre}{p.finalizado ? ` · ${p.local_total}` : ''}</p><p className="font-semibold">{p.equipo_visitante_nombre}{p.finalizado ? ` · ${p.visitante_total}` : ''}</p>
        <button type="button" disabled={cargando || !p.analizable} aria-label={`Analizar ${p.equipo_local_nombre} vs ${p.equipo_visitante_nombre}`} className="w-full rounded-xl border border-neon-cyan/30 py-3 text-sm text-neon-cyan disabled:opacity-40" onClick={() => onSeleccionar(p)}>{seleccionado?.id === p.id ? 'Seleccionado' : p.analizable ? p.reconstruccion ? 'Analizar con corte histórico' : 'Analizar partido' : 'No disponible para análisis previo'}</button>
      </article>; })}
    </div>
    {datos && datos.total > datos.tamano && <nav aria-label="Páginas de la agenda" className="flex justify-between text-sm"><button disabled={pagina === 1 || cargando} onClick={() => setPagina(n => n-1)}>Anterior</button><span>Página {pagina} de {Math.ceil(datos.total/datos.tamano)}</span><button disabled={pagina*datos.tamano >= datos.total || cargando} onClick={() => setPagina(n => n+1)}>Siguiente</button></nav>}
    <p className="text-xs text-texto-terciario">NBA y Euroliga conservan fecha canónica sin hora: no se acredita el orden horario entre esos encuentros. Los análisis históricos usan datos de días anteriores; no son pronósticos emitidos entonces. Actualizar agenda consulta la BD, sin descargar calendarios.</p>
  </section>;
}
