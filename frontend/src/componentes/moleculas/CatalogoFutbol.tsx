import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, CalendarDays, RefreshCw, Search, SlidersHorizontal, Star } from 'lucide-react';
import type { Competicion, PartidoFutbolResumen } from '../../tipos/futbol';
import { listarAgenda, listarCompeticiones, resolverPartidoCatalogo, type AgendaFutbol, type FiltrosAgenda, type PartidoAgendaFutbol } from '../../servicios/futbol/catalogo';
import { fechaColombia, puedeAnalizarPartido, sumarDias } from '../../utilidades/agendaFutbol';

interface Props {
  revision: number; onInicio: () => void; onCargando: (valor: boolean) => void; onError: (valor: string | null) => void;
  onDatos: (partidos: PartidoFutbolResumen[]) => void; onSeleccionar: (partido: PartidoFutbolResumen) => void;
  seleccionadoId: string; guardadosIds: Set<string>;
}
const campo = 'w-full min-w-0 rounded-xl border border-neon-cyan/20 bg-futurista-negro/70 px-3 py-2.5 text-sm text-texto-principal focus:border-neon-cyan focus:outline-none focus:ring-1 focus:ring-neon-cyan';
const hora = (valor: string) => new Intl.DateTimeFormat('es-CO', { timeZone: 'America/Bogota', hour: '2-digit', minute: '2-digit' }).format(new Date(valor));
function Escudo({ nombre, url }: { nombre: string; url?: string }) {
  const [fallo, setFallo] = useState(false);
  return <span aria-hidden="true" className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-white/10 bg-white/5 text-[10px] font-bold text-texto-secundario">
    {url && !fallo ? <img src={url} alt="" className="h-7 w-7 object-contain" loading="lazy" onError={() => setFallo(true)} /> : nombre.slice(0, 3).toUpperCase()}
  </span>;
}
function estadoVisible(p: PartidoAgendaFutbol, ahora: number) {
  if (p.estado === 'PROGRAMADO' && Date.parse(p.fechaPartido) <= ahora) return 'Estado por verificar';
  return ({ PROXIMO: 'Próximo', POR_VERIFICAR: 'Estado por verificar', EN_JUEGO: 'En juego', FINALIZADO: 'Finalizado', NO_DISPONIBLE: p.estado.toLowerCase().replace(/_/g, ' ') })[p.estadoAgenda];
}
export function CatalogoFutbol({ revision, onInicio, onCargando, onError, onDatos, onSeleccionar, seleccionadoId, guardadosIds }: Props) {
  const [ahora, setAhora] = useState(Date.now());
  const hoy = fechaColombia(new Date(ahora));
  const [filtros, setFiltros] = useState<FiltrosAgenda>(() => {
    const q = new URLSearchParams(window.location.search), fecha = q.get('fecha') || '';
    return { fecha: /^\d{4}-\d{2}-\d{2}$/.test(fecha) && Number.isFinite(Date.parse(fecha)) ? fecha : fechaColombia(), competicionId: q.get('competicionId') || '', pais: '', buscar: '', estado: 'todos', pagina: 1 };
  });
  const [textoBuscar, setTextoBuscar] = useState('');
  const [soloGuardados, setSoloGuardados] = useState(false);
  const [competiciones, setCompeticiones] = useState<Competicion[]>([]);
  const [errorFiltros, setErrorFiltros] = useState(false);
  const [agenda, setAgenda] = useState<AgendaFutbol | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [recarga, setRecarga] = useState(0);
  const [inicializado, setInicializado] = useState(() => !new URLSearchParams(window.location.search).has('partidoId'));
  const ultimaConsulta = useRef('');
  const idsGuardados = useMemo(() => [...guardadosIds].sort(), [guardadosIds]);
  const paises = useMemo(() => [...new Set(competiciones.map(c => c.pais))].sort(), [competiciones]);
  useEffect(() => { const id = window.setInterval(() => setAhora(Date.now()), 15000); return () => window.clearInterval(id); }, []);
  useEffect(() => {
    const ctl = new AbortController();
    listarCompeticiones(ctl.signal).then(data => { if (!ctl.signal.aborted) { setCompeticiones(data); setErrorFiltros(false); } })
      .catch(() => { if (!ctl.signal.aborted) setErrorFiltros(true); });
    return () => ctl.abort();
  }, [recarga]);
  useEffect(() => {
    const pid = new URLSearchParams(window.location.search).get('partidoId');
    if (!pid) return;
    const ctl = new AbortController();
    resolverPartidoCatalogo(pid, ctl.signal).then(p => {
      if (!ctl.signal.aborted) setFiltros(f => ({ ...f, fecha: fechaColombia(new Date(p.fechaPartido)), competicionId: '' }));
    }).catch(() => { /* El contenedor informa si el enlace no está disponible. */ })
      .finally(() => { if (!ctl.signal.aborted) setInicializado(true); });
    return () => ctl.abort();
  }, []);
  useEffect(() => {
    const id = window.setTimeout(() => setFiltros(f => f.buscar === textoBuscar ? f : { ...f, buscar: textoBuscar, pagina: 1 }), 250);
    return () => window.clearTimeout(id);
  }, [textoBuscar]);
  useEffect(() => {
    if (!inicializado) return;
    const ctl = new AbortController(), clave = JSON.stringify([filtros, soloGuardados]);
    if (ultimaConsulta.current !== clave) { onInicio(); ultimaConsulta.current = clave; }
    setCargando(true); onCargando(true); setError(''); onError(null);
    const consulta = soloGuardados && !idsGuardados.length
      ? Promise.resolve({ fecha: filtros.fecha, total: 0, consultadoEn: new Date().toISOString(), datosActualizadosEn: null, partidos: [] })
      : listarAgenda({ ...filtros, guardados: soloGuardados ? idsGuardados : undefined }, ctl.signal);
    consulta.then(data => { if (!ctl.signal.aborted) { setAgenda(data); onDatos(data.partidos); } })
      .catch(err => { if (!ctl.signal.aborted) { const msg = err instanceof Error ? err.message : 'No se pudo cargar la agenda'; setError(msg); onError(msg); } })
      .finally(() => { if (!ctl.signal.aborted) { setCargando(false); onCargando(false); } });
    return () => ctl.abort();
  }, [filtros, soloGuardados, idsGuardados, revision, recarga, inicializado, onInicio, onCargando, onError, onDatos]);
  const cambiar = (cambios: Partial<FiltrosAgenda>) => {
    const nuevos = { ...filtros, ...cambios, pagina: cambios.pagina ?? 1 }; setFiltros(nuevos);
    const url = new URL(window.location.href);
    ['partidoId', 'modo', 'temporadaId'].forEach(k => url.searchParams.delete(k)); url.searchParams.set('fecha', nuevos.fecha);
    if (nuevos.competicionId) url.searchParams.set('competicionId', nuevos.competicionId); else url.searchParams.delete('competicionId');
    window.history.replaceState({}, '', url);
  };
  const elegir = (p: PartidoAgendaFutbol) => {
    if (!puedeAnalizarPartido(p)) return;
    onSeleccionar(p); const url = new URL(window.location.href); url.searchParams.set('partidoId', p.id); window.history.replaceState({}, '', url);
    window.requestAnimationFrame(() => document.getElementById('configuracion-futbol')?.scrollIntoView({ behavior: 'smooth', block: 'start' }));
  };
  const filtrado = Boolean(filtros.competicionId || filtros.pais || filtros.estado !== 'todos' || soloGuardados);
  const fechaLarga = new Intl.DateTimeFormat('es-CO', { timeZone: 'America/Bogota', weekday: 'long', day: 'numeric', month: 'long' }).format(new Date(`${filtros.fecha}T12:00:00Z`));
  return <section id="agenda-futbol" aria-label="Agenda de partidos" className="tarjeta min-w-0 space-y-5 !p-4 sm:!p-6">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div><p className="text-xs font-semibold uppercase tracking-[0.2em] text-neon-cyan">Fútbol · Todas tus competiciones</p><h1 className="mt-1 flex items-center gap-2 text-2xl font-semibold text-texto-principal"><CalendarDays className="h-6 w-6 text-neon-cyan" />Partidos</h1><p className="mt-1 text-sm capitalize text-texto-secundario">{fechaLarga}<span className="normal-case"> · hora de Colombia</span></p></div>
      <button type="button" disabled={cargando} onClick={() => setRecarga(n => n + 1)} className="flex items-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-xs text-texto-secundario hover:border-neon-cyan/50 disabled:opacity-50"><RefreshCw className={`h-3.5 w-3.5 ${cargando ? 'animate-spin' : ''}`} />Actualizar agenda</button>
    </div>
    <div className="flex flex-wrap items-center gap-2">
      {[{ texto: 'Hoy', fecha: hoy }, { texto: 'Mañana', fecha: sumarDias(hoy, 1) }].map(d => <button key={d.texto} type="button" aria-pressed={filtros.fecha === d.fecha} onClick={() => cambiar({ fecha: d.fecha })} className={`rounded-xl border px-6 py-2.5 text-sm font-semibold ${filtros.fecha === d.fecha ? 'border-neon-cyan bg-neon-cyan/15 text-neon-cyan' : 'border-white/10 text-texto-secundario hover:border-neon-cyan/40'}`}>{d.texto}</button>)}
      <div className="flex min-w-0 items-center gap-1">
        <button type="button" aria-label="Día anterior" onClick={() => cambiar({ fecha: sumarDias(filtros.fecha, -1) })} className="rounded-lg border border-white/10 p-2 text-texto-secundario hover:text-neon-cyan"><ArrowLeft className="h-4 w-4" /></button>
        <label className="flex min-w-0 flex-wrap items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-xs text-texto-secundario"><CalendarDays className="h-4 w-4" />Elegir fecha<input aria-label="Fecha de los partidos" type="date" value={filtros.fecha} onInput={e => { if (e.currentTarget.value && e.currentTarget.value !== filtros.fecha) cambiar({ fecha: e.currentTarget.value }); }} onChange={e => { if (e.target.value && e.target.value !== filtros.fecha) cambiar({ fecha: e.target.value }); }} className="min-w-0 bg-transparent py-0.5 text-sm text-texto-principal [color-scheme:dark]" /></label>
        <button type="button" aria-label="Día siguiente" onClick={() => cambiar({ fecha: sumarDias(filtros.fecha, 1) })} className="rounded-lg border border-white/10 p-2 text-texto-secundario hover:text-neon-cyan"><ArrowRight className="h-4 w-4" /></button>
      </div>
    </div>
    <div className="flex flex-wrap items-start gap-3">
      <label className="relative min-w-[180px] flex-1"><span className="sr-only">Buscar equipo</span><Search className="absolute left-3 top-3 h-4 w-4 text-texto-terciario" /><input type="search" maxLength={100} placeholder="Buscar un equipo…" value={textoBuscar} onChange={e => setTextoBuscar(e.target.value)} className={`${campo} !pl-9`} /></label>
      <details className="w-full sm:w-auto"><summary className="flex cursor-pointer list-none items-center justify-center gap-2 rounded-xl border border-white/10 px-4 py-2.5 text-sm text-texto-secundario"><SlidersHorizontal className="h-4 w-4" />Filtrar{filtrado ? ' · activos' : ''}</summary>
        <div className="mt-3 grid gap-3 rounded-xl border border-white/10 bg-futurista-negro/40 p-4 sm:min-w-[340px]">
          <label className="text-xs text-texto-secundario">País<select aria-label="Filtrar por país" value={filtros.pais} className={`${campo} mt-1`} onChange={e => cambiar({ pais: e.target.value, competicionId: '' })}><option value="">Todos los países</option>{paises.map(p => <option key={p}>{p}</option>)}</select></label>
          <label className="text-xs text-texto-secundario">Competición<select aria-label="Filtrar por competición" value={filtros.competicionId} className={`${campo} mt-1`} onChange={e => cambiar({ competicionId: e.target.value })}><option value="">Todas las competiciones</option>{competiciones.filter(c => !filtros.pais || c.pais === filtros.pais).map(c => <option key={c.id} value={c.id}>{c.nombre} · {c.pais}</option>)}</select></label>
          <label className="text-xs text-texto-secundario">Estado<select aria-label="Filtrar por estado" value={filtros.estado} className={`${campo} mt-1`} onChange={e => cambiar({ estado: e.target.value })}><option value="todos">Todos los estados</option><option value="proximos">Próximos</option><option value="en_juego">En juego</option><option value="finalizados">Finalizados</option><option value="pendientes">Estado por verificar</option></select></label>
          <label className="flex items-center gap-2 text-sm text-texto-secundario"><input type="checkbox" checked={soloGuardados} onChange={e => { setSoloGuardados(e.target.checked); cambiar({}); }} /><Star className="h-4 w-4" />Solo mis partidos guardados</label>
          {filtrado && <button type="button" className="text-left text-xs text-neon-cyan" onClick={() => { setSoloGuardados(false); cambiar({ pais: '', competicionId: '', estado: 'todos' }); }}>Quitar filtros</button>}
          {errorFiltros && <p className="text-xs text-neon-amarillo">No se pudieron cargar los filtros de competición. Actualiza para reintentar.</p>}
        </div>
      </details>
    </div>
    <div aria-live="polite" className="flex flex-wrap justify-between gap-2 text-xs text-texto-secundario"><span>{cargando ? 'Cargando partidos…' : `${agenda?.total ?? 0} partidos registrados`}</span>{agenda && <span>Consulta: {hora(agenda.consultadoEn)} COT · {agenda.datosActualizadosEn ? `último cambio guardado ${new Date(agenda.datosActualizadosEn).toLocaleString('es-CO', { timeZone: 'America/Bogota', dateStyle: 'short', timeStyle: 'short' })}` : 'sin fecha de actualización acreditada'}</span>}</div>
    {error && <div role="alert" className="rounded-xl border border-neon-amarillo/30 p-4 text-sm text-neon-amarillo">No se pudo actualizar la agenda. {error}<button type="button" onClick={() => setRecarga(n => n + 1)} className="ml-2 underline">Reintentar</button></div>}
    {!cargando && !error && agenda?.partidos.length === 0 && <div className="rounded-xl border border-dashed border-white/15 px-5 py-9 text-center"><CalendarDays className="mx-auto mb-3 h-8 w-8 text-texto-terciario" /><p className="text-texto-principal">No hay partidos registrados para esta fecha y estos filtros.</p><p className="mt-2 text-sm text-texto-secundario">Prueba Mañana, elige otra fecha o quita los filtros.</p></div>}
    <div aria-busy={cargando} className={`grid gap-3 md:grid-cols-2 xl:grid-cols-3 ${cargando || error ? 'pointer-events-none opacity-45' : ''}`}>
      {agenda?.partidos.map(p => {
        const permitido = p.analizable && puedeAnalizarPartido(p, ahora), seleccionado = seleccionadoId === p.id;
        return <article key={p.id} className={`min-w-0 rounded-2xl border p-4 transition-colors ${seleccionado ? 'border-neon-cyan bg-neon-cyan/5' : 'border-white/10 bg-futurista-negro/30 hover:border-neon-cyan/40'}`}>
          <div className="mb-3 flex items-center justify-between gap-2"><time dateTime={p.fechaPartido} className="text-sm font-semibold text-texto-principal">{hora(p.fechaPartido)}</time><span className={`rounded-full px-2 py-1 text-[11px] ${estadoVisible(p, ahora) === 'Estado por verificar' ? 'bg-neon-amarillo/10 text-neon-amarillo' : p.estadoAgenda === 'EN_JUEGO' ? 'bg-neon-verde/10 text-neon-verde' : 'bg-white/5 text-texto-secundario'}`}>{estadoVisible(p, ahora)}</span></div>
          <p className="mb-3 truncate text-xs text-texto-secundario" title={`${p.competicionNombre} · ${p.pais}`}>{p.competicionNombre} · {p.pais}</p>
          {[{ nombre: p.equipoLocalNombre, logo: p.equipoLocalLogo, goles: p.golesLocal }, { nombre: p.equipoVisitanteNombre, logo: p.equipoVisitanteLogo, goles: p.golesVisitante }].map((e, i) => <div key={i} className="mb-2 flex min-w-0 items-center gap-2.5"><Escudo nombre={e.nombre} url={e.logo} /><span className="min-w-0 flex-1 break-words text-sm font-medium text-texto-principal">{e.nombre}</span>{e.goles != null && <span className="text-lg font-semibold text-texto-principal">{e.goles}</span>}</div>)}
          <button type="button" aria-label={`${p.estado === 'FINALIZADO' ? 'Ver histórico' : 'Analizar'} ${p.equipoLocalNombre} vs ${p.equipoVisitanteNombre}`} disabled={!permitido || cargando || Boolean(error)} onClick={() => elegir(p)} className="mt-3 w-full rounded-xl border border-neon-cyan/30 bg-neon-cyan/10 px-3 py-2 text-sm font-semibold text-neon-cyan hover:bg-neon-cyan/20 disabled:border-white/10 disabled:bg-white/5 disabled:text-texto-terciario">{seleccionado ? 'Seleccionado' : permitido ? p.estado === 'FINALIZADO' ? 'Ver resultado / Histórico' : 'Analizar partido' : p.estadoAgenda === 'EN_JUEGO' ? 'Prepartido cerrado' : 'No disponible para prepartido'}</button>
        </article>;
      })}
    </div>
    {agenda && agenda.total > 50 && <nav aria-label="Páginas de la agenda" className="flex items-center justify-center gap-4 text-sm"><button type="button" aria-label="Página anterior" disabled={filtros.pagina <= 1 || cargando} onClick={() => cambiar({ pagina: filtros.pagina - 1 })} className="rounded-lg border border-white/10 p-2 disabled:opacity-30"><ArrowLeft className="h-4 w-4" /></button><span className="text-texto-secundario">{filtros.pagina} / {Math.ceil(agenda.total / 50)}</span><button type="button" aria-label="Página siguiente" disabled={filtros.pagina * 50 >= agenda.total || cargando} onClick={() => cambiar({ pagina: filtros.pagina + 1 })} className="rounded-lg border border-white/10 p-2 disabled:opacity-30"><ArrowRight className="h-4 w-4" /></button></nav>}
    <p className="text-[11px] leading-relaxed text-texto-terciario">Mostramos los partidos registrados; una agenda vacía no acredita ausencia de encuentros. Los horarios vencidos requieren verificar el estado. Actualizar esta vista consulta los datos guardados, sin descargar nuevos calendarios.</p>
  </section>;
}
