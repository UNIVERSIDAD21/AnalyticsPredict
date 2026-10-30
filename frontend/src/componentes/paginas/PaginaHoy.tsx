import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Encabezado } from '../organismos/Encabezado';
import { consultarAgendaBaloncesto, type AgendaBaloncesto } from '../../servicios/agendaBaloncesto';
import { listarAgenda, type AgendaFutbol } from '../../servicios/futbol/catalogo';
import { fechaColombia } from '../../utilidades/agendaFutbol';
import { extraerMensajeError } from '../../servicios/api';
import { leerCuaderno, type EntradaCuaderno } from '../../servicios/cuadernoLocal';

export function PaginaHoy() {
  const [fecha, setFecha] = useState(fechaColombia), [revision, setRevision] = useState(0), [liga, setLiga] = useState('');
  const [basket, setBasket] = useState<AgendaBaloncesto | null>(null), [futbol, setFutbol] = useState<AgendaFutbol | null>(null);
  const [errorBasket, setErrorBasket] = useState(''), [errorFutbol, setErrorFutbol] = useState(''), [cargando, setCargando] = useState(true);
  let recientes: EntradaCuaderno[] = [], errorCuaderno = '';
  try { recientes = leerCuaderno().slice(0, 5); } catch { errorCuaderno = 'Cuaderno no disponible; las copias previas no se sobrescribieron.'; }
  useEffect(() => {
    const c = new AbortController(); setCargando(true); setBasket(null); setFutbol(null); setErrorBasket(''); setErrorFutbol('');
    // Cada dominio puede fallar sin ocultar al otro; no se entrena ni ingiere.
    const b = consultarAgendaBaloncesto({ fecha, liga: liga === 'futbol' ? '' : liga, buscar: '', estado: 'todos', pagina: 1 }, c.signal)
      .then(d => { if (!c.signal.aborted) setBasket(d); }).catch(e => { if (!c.signal.aborted) setErrorBasket(extraerMensajeError(e)); });
    const f = listarAgenda({ fecha, competicionId: '', pais: '', buscar: '', estado: 'todos', pagina: 1 }, c.signal)
      .then(d => { if (!c.signal.aborted) setFutbol(d); }).catch(e => { if (!c.signal.aborted) setErrorFutbol(extraerMensajeError(e)); });
    Promise.allSettled([b, f]).then(() => { if (!c.signal.aborted) setCargando(false); });
    return () => c.abort();
  }, [fecha, revision, liga]);
  return <div className="min-h-screen"><Encabezado /><main id="contenido-principal" className="contenedor py-8 space-y-7">
    <div className="flex flex-wrap gap-5 justify-between items-start"><div><p className="text-neon-cyan text-sm">Tu escritorio de análisis</p><h1 className="text-4xl font-semibold mt-2">Hoy</h1><p className="text-texto-secundario mt-3">Elige un partido, abre su ficha y conserva la consulta que quieras revisar.</p></div><Link to="/base-local" className="boton-secundario">Consultar base local NBA</Link></div>
    <div className="flex flex-wrap gap-4 items-end"><label className="text-sm">Fecha · Colombia<input type="date" className="input-base mt-2" value={fecha} onChange={e => { if (e.target.value) setFecha(e.target.value); }} /></label><label className="text-sm">Liga<select className="input-base mt-2" value={liga} onChange={e => setLiga(e.target.value)}><option value="">Todas</option>{['nba','euroliga','wnba','futbol'].map(l => <option key={l} value={l}>{l.toUpperCase()}</option>)}</select></label><button className="boton-secundario" disabled={cargando} onClick={() => setRevision(v => v+1)}>Actualizar consulta</button></div>
    <div className="grid xl:grid-cols-[minmax(0,1fr)_300px] gap-6 items-start"><div className="space-y-6 min-w-0">
      {liga !== 'futbol' && <section className="tarjeta space-y-4" aria-label="Baloncesto de hoy"><h2 className="text-xl font-semibold">Baloncesto</h2>
        {errorBasket ? <div role="alert"><p>Partidos: N/D. {errorBasket}</p><button className="text-neon-cyan mt-2" onClick={() => setRevision(v => v+1)}>Reintentar</button></div> : !basket ? <p role="status">Cargando agenda…</p> : <><p className="text-sm text-texto-secundario">{basket.total} registrados en todas las ligas · Fuente actualizada: {basket.datos_actualizados_en ?? 'N/D'}</p>
          {!basket.partidos.length && <p>No hay partidos registrados; no acredita ausencia de encuentros.</p>}
          {basket.partidos.filter(p => !liga || p.liga === liga).map(p => <Link key={p.id} className="ficha-hoy" to={`/baloncesto?${new URLSearchParams({ liga: p.liga, fecha: p.fecha_partido, partidoId: p.id })}`}><span className="text-xs text-neon-cyan">{p.liga.toUpperCase()} · {p.inicio_utc ? new Date(p.inicio_utc).toLocaleTimeString('es-CO', { timeZone: 'America/Bogota', hour: '2-digit', minute: '2-digit' }) : 'Hora por confirmar'}</span><strong>{p.equipo_local_nombre} — {p.equipo_visitante_nombre}</strong><span className="text-sm text-texto-secundario">{p.estado} · Abrir ficha →</span></Link>)}
          <Link className="text-neon-cyan text-sm" to={`/baloncesto?fecha=${fecha}`}>Ver agenda completa y filtros</Link></>}
      </section>}
      {(!liga || liga === 'futbol') && <section className="tarjeta space-y-4" aria-label="Fútbol de hoy"><h2 className="text-xl font-semibold">Fútbol</h2>
        {errorFutbol ? <div role="alert"><p>Partidos: N/D. {errorFutbol}</p><button className="text-neon-cyan mt-2" onClick={() => setRevision(v => v+1)}>Reintentar</button></div> : !futbol ? <p role="status">Cargando agenda…</p> : <><p className="text-sm text-texto-secundario">{futbol.total} registrados · Fuente actualizada: {futbol.datosActualizadosEn ?? 'N/D'}</p>
          {!futbol.partidos.length && <p>No hay partidos registrados; no acredita ausencia de encuentros.</p>}
          {futbol.partidos.map(p => <Link className="ficha-hoy" key={p.id} to={`/futbol?${new URLSearchParams({ fecha, partidoId: p.id })}`}><span className="text-xs text-neon-cyan">{p.competicionNombre} · {p.precisionFecha === 'DIA' ? 'Hora por confirmar' : new Date(p.fechaPartido).toLocaleTimeString('es-CO', { timeZone: 'America/Bogota', hour: '2-digit', minute: '2-digit' })}</span><strong>{p.equipoLocalNombre} — {p.equipoVisitanteNombre}</strong><span className="text-sm text-texto-secundario">{p.estadoAgenda} · Abrir ficha →</span></Link>)}<Link className="text-neon-cyan text-sm" to={`/futbol?fecha=${fecha}`}>Ver agenda completa y filtros</Link></>}
      </section>}
      <p className="text-xs text-texto-secundario">Vista resumida de cada agenda; abre la agenda completa para ver todos los encuentros. Consultar no descarga fuentes ni actualiza modelos.</p>
    </div><aside className="tarjeta space-y-4"><h2 className="font-semibold">Consultas recientes</h2>{errorCuaderno && <p role="alert">{errorCuaderno}</p>}{!recientes.length && <p className="text-sm text-texto-secundario">Aún no guardaste consultas en este navegador.</p>}{recientes.map(r => <p key={r.id} className="text-sm"><Link to="/cuaderno" className="text-neon-cyan">{r.favorito ? '★ ' : ''}{r.titulo}</Link><span className="block text-texto-secundario">{r.liga.toUpperCase()} · Copia, no dato actual</span></p>)}<Link to="/cuaderno" className="text-neon-cyan text-sm block">Abrir Mi cuaderno →</Link><Link to="/laboratorio" className="text-neon-cyan text-sm block">Ver modelos y evidencia →</Link></aside></div>
  </main></div>;
}
