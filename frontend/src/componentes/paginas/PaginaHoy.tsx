import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { CalendarDays, ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react';
import { Encabezado } from '../organismos/Encabezado';
import { consultarAgendaBaloncesto, type AgendaBaloncesto } from '../../servicios/agendaBaloncesto';
import { listarAgenda, type AgendaFutbol } from '../../servicios/futbol/catalogo';
import { fechaColombia, sumarDias } from '../../utilidades/agendaFutbol';
import { leerCuaderno, type EntradaCuaderno } from '../../servicios/cuadernoLocal';
import { BotonFavorito, useFavoritosLocales } from '../moleculas/FavoritosLocales';
import { coincideFavoritos, favoritoEquipo, favoritoLiga } from '../../servicios/favoritosLocales';
import { useAgendaHoy } from '../../hooks/useAgendaHoy';

const marcaBasket = (d: AgendaBaloncesto) => d.datos_actualizados_en;
const marcaFutbol = (d: AgendaFutbol) => d.datosActualizadosEn;
function recientesCuaderno() {
  try { return { recientes: leerCuaderno().slice(0, 5), error: '' }; }
  catch { return { recientes: [] as EntradaCuaderno[], error: 'Cuaderno no disponible; las copias previas no se sobrescribieron.' }; }
}
interface ControlesProps {
  nombre: string; leidos: number; total: number; favoritos: number; soloFavoritos: boolean; cargando: boolean; error: string;
  cargar: () => void; detener: () => void; actualizar: () => void;
}
function ControlesPaginas({ nombre, leidos, total, favoritos, soloFavoritos, cargando, error, cargar, detener, actualizar }: ControlesProps) {
  return <div className="border-t border-neon-cyan/15 pt-4 space-y-3">
    <p role="status" className="text-sm text-texto-secundario">{soloFavoritos ? `${favoritos} favoritos encontrados · ` : ''}{leidos} de {total} registros consultados{leidos === total ? ' · Todas las páginas recibidas.' : ' · Quedan páginas por revisar.'}</p>
    {soloFavoritos && favoritos === 0 && leidos > 0 && <p className="text-sm">No encontramos favoritos entre los registros leídos{leidos < total ? '; todavía puede haberlos en las páginas restantes.' : '.'}</p>}
    {error && <div role="alert"><p>{error} Los encuentros ya leídos se conservan.</p><button className="text-neon-cyan text-sm mt-2" type="button" onClick={actualizar}>Actualizar agenda de {nombre}</button></div>}
    <div className="flex flex-wrap gap-3 items-center">{cargando ? <><span role="status" className="text-sm">Leyendo más partidos de {nombre}…</span><button type="button" className="boton-secundario" onClick={detener}>Detener búsqueda de {nombre}</button></> : leidos < total &&
      <button type="button" className="boton-secundario" onClick={cargar}>{soloFavoritos ? 'Buscar más favoritos' : 'Cargar más partidos'} de {nombre}</button>}
      {soloFavoritos && leidos < total && <p className="text-xs text-texto-secundario">Hasta 10 páginas por búsqueda. Puedes detenerla sin perder lo leído.</p>}</div>
  </div>;
}
export function PaginaHoy() {
  const [fecha, setFecha] = useState(fechaColombia), [liga, setLiga] = useState('');
  const [revisionBasket, setRevisionBasket] = useState(0), [revisionFutbol, setRevisionFutbol] = useState(0);
  const [soloFavoritos, setSoloFavoritos] = useState(false);
  const [{ recientes, error: errorCuaderno }, setRecientes] = useState(recientesCuaderno);
  const { favoritos, error: errorFavoritos } = useFavoritosLocales();
  const cargarBasket = useCallback((pagina: number, signal: AbortSignal) => consultarAgendaBaloncesto({ fecha, liga: liga === 'futbol' ? '' : liga, buscar: '', estado: 'todos', pagina }, signal), [fecha, liga]);
  const cargarFutbol = useCallback((pagina: number, signal: AbortSignal) => listarAgenda({ fecha, competicionId: '', pais: '', buscar: '', estado: 'todos', pagina }, signal), [fecha]);
  const basket = useAgendaHoy(`${fecha}:${liga}:${revisionBasket}`, liga !== 'futbol', cargarBasket, marcaBasket);
  const futbol = useAgendaHoy(`${fecha}:${revisionFutbol}`, !liga || liga === 'futbol', cargarFutbol, marcaFutbol);
  useEffect(() => {
    const actualizar = () => setRecientes(recientesCuaderno());
    window.addEventListener('cuaderno-actualizado', actualizar); window.addEventListener('storage', actualizar);
    return () => { window.removeEventListener('cuaderno-actualizado', actualizar); window.removeEventListener('storage', actualizar); };
  }, []);
  const filtrarFavoritos = soloFavoritos && !errorFavoritos;
  const hayFavoritosBasket = favoritos.some(f => f.liga !== 'futbol' && (!liga || f.liga === liga));
  const hayFavoritosFutbol = favoritos.some(f => f.liga === 'futbol');
  const equiposBasket = (p: AgendaBaloncesto['partidos'][number]) => [favoritoEquipo(p.liga, p.equipo_local_id, p.equipo_local_nombre), favoritoEquipo(p.liga, p.equipo_visitante_id, p.equipo_visitante_nombre)];
  const equiposFutbol = (p: AgendaFutbol['partidos'][number]) => [favoritoEquipo('futbol', p.equipoLocal, p.equipoLocalNombre), favoritoEquipo('futbol', p.equipoVisitante, p.equipoVisitanteNombre)];
  const basketVisibles = basket.datos?.partidos.filter(p => (!liga || p.liga === liga) && (!filtrarFavoritos || coincideFavoritos(favoritos, p.liga, equiposBasket(p)))) ?? [];
  const futbolVisibles = futbol.datos?.partidos.filter(p => !filtrarFavoritos || coincideFavoritos(favoritos, 'futbol', equiposFutbol(p), p.competicion)) ?? [];
  const cargando = basket.cargando || futbol.cargando;
  const cambiarFavoritos = (valor: boolean) => {
    setSoloFavoritos(valor);
    if (!valor) { basket.detener(); futbol.detener(); return; }
    if (hayFavoritosBasket) void basket.cargarMas(10);
    if (hayFavoritosFutbol) void futbol.cargarMas(10);
  };
  const actualizar = () => { setRevisionBasket(v => v + 1); setRevisionFutbol(v => v + 1); };
  return <div className="min-h-screen"><Encabezado /><main id="contenido-principal" tabIndex={-1} className="contenedor py-8 space-y-7">
    <div className="flex flex-wrap gap-5 justify-between items-start"><div><p className="text-neon-cyan text-sm flex gap-2 items-center"><CalendarDays size={16} aria-hidden="true" />Tu escritorio de análisis</p><h1 className="text-4xl font-semibold mt-2">Hoy</h1><p className="text-texto-secundario mt-3">Tus partidos, tus favoritos y tus consultas recientes en un mismo lugar.</p></div><Link to="/base-local" className="boton-secundario">Consultar base local</Link></div>
    <div className="tarjeta flex flex-wrap gap-4 items-end"><div className="flex gap-2 items-center"><button type="button" className="boton-secundario p-3" aria-label="Día anterior" onClick={() => setFecha(sumarDias(fecha, -1))}><ChevronLeft size={18} aria-hidden="true" /></button><button type="button" className="boton-secundario p-3" aria-label="Día siguiente" onClick={() => setFecha(sumarDias(fecha, 1))}><ChevronRight size={18} aria-hidden="true" /></button></div>
      <label className="text-sm">Fecha · Colombia<input type="date" className="input-base mt-2" value={fecha} onChange={e => { if (e.target.value) setFecha(e.target.value); }} /></label>
      <div className="flex gap-2"><button type="button" className="boton-secundario" aria-pressed={fecha === fechaColombia()} onClick={() => setFecha(fechaColombia())}>Hoy</button><button type="button" className="boton-secundario" aria-pressed={fecha === sumarDias(fechaColombia(), 1)} onClick={() => setFecha(sumarDias(fechaColombia(), 1))}>Mañana</button></div>
      <label className="text-sm">Liga<select className="input-base mt-2" value={liga} onChange={e => setLiga(e.target.value)}><option value="">Todas</option>{['nba', 'euroliga', 'wnba', 'futbol'].map(l => <option key={l} value={l}>{l === 'futbol' ? 'Fútbol' : l.toUpperCase()}</option>)}</select></label>
      <button type="button" className="boton-secundario flex gap-2 items-center" disabled={cargando} onClick={actualizar}><RefreshCw size={16} aria-hidden="true" />Actualizar consulta</button></div>
    <div className="flex flex-wrap items-center gap-5"><label className="text-sm"><input type="checkbox" checked={soloFavoritos} disabled={Boolean(errorFavoritos) || cargando} onChange={e => cambiarFavoritos(e.target.checked)} /> Solo equipos, competiciones o ligas favoritos</label><Link className="text-neon-cyan text-sm" to="/mis-analisis">Gestionar favoritos</Link></div>
    {errorFavoritos && <p role="alert">{errorFavoritos} La agenda sigue disponible sin filtro personal.</p>}
    {filtrarFavoritos && !favoritos.length && <p className="tarjeta">Todavía no tienes equipos, competiciones o ligas favoritos. Puedes guardarlos desde las fichas o desde Mis análisis.</p>}
    <div className="grid xl:grid-cols-[minmax(0,1fr)_300px] gap-6 items-start"><div className="space-y-6 min-w-0">
      {liga !== 'futbol' && <section className="tarjeta space-y-4" aria-label="Baloncesto de hoy"><h2 className="text-xl font-semibold">Baloncesto</h2>
        {basket.error ? <div role="alert"><p>Partidos: N/D. {basket.error}</p><button type="button" className="text-neon-cyan mt-2" onClick={() => setRevisionBasket(v => v + 1)}>Reintentar baloncesto</button></div> : !basket.datos ? <p role="status">Cargando agenda…</p> : <>
          <p className="text-sm text-texto-secundario">{basket.datos.total} registrados{liga ? ` en ${liga.toUpperCase()}` : ' en todas las ligas'} · Fuente actualizada: {basket.datos.datos_actualizados_en ?? 'N/D'}</p>
          {!basket.datos.partidos.length && <p>No hay partidos registrados; no acredita ausencia de encuentros.</p>}
          {basketVisibles.map(p => <article key={p.id}><Link className="ficha-hoy" to={`/baloncesto?${new URLSearchParams({ liga: p.liga, fecha: p.fecha_partido, partidoId: p.id, paginaAgenda: String(basket.paginas.get(p.id) ?? 1), ligaAgenda: liga })}`}><span className="text-xs text-neon-cyan">{p.liga.toUpperCase()} · {p.inicio_utc ? new Date(p.inicio_utc).toLocaleTimeString('es-CO', { timeZone: 'America/Bogota', hour: '2-digit', minute: '2-digit' }) : 'Hora por confirmar'}</span><strong>{p.equipo_local_nombre} — {p.equipo_visitante_nombre}</strong><span className="text-sm text-texto-secundario">{p.estado} · Abrir ficha →</span></Link><div className="flex flex-wrap gap-x-5"><BotonFavorito favorito={favoritoLiga(p.liga)} />{equiposBasket(p).map(f => <BotonFavorito key={f.id} favorito={f} />)}</div></article>)}
          <ControlesPaginas nombre="baloncesto" leidos={basket.datos.partidos.length} total={basket.datos.total} favoritos={basketVisibles.length} soloFavoritos={filtrarFavoritos} cargando={basket.cargandoMas} error={basket.errorMas}
            cargar={() => { void basket.cargarMas(filtrarFavoritos && hayFavoritosBasket ? 10 : 1); }} detener={basket.detener} actualizar={() => setRevisionBasket(v => v + 1)} />
          <Link className="text-neon-cyan text-sm" to={`/baloncesto?fecha=${fecha}`}>Ver agenda completa y filtros</Link></>}
      </section>}
      {(!liga || liga === 'futbol') && <section className="tarjeta space-y-4" aria-label="Fútbol de hoy"><h2 className="text-xl font-semibold">Fútbol</h2>
        {futbol.error ? <div role="alert"><p>Partidos: N/D. {futbol.error}</p><button type="button" className="text-neon-cyan mt-2" onClick={() => setRevisionFutbol(v => v + 1)}>Reintentar fútbol</button></div> : !futbol.datos ? <p role="status">Cargando agenda…</p> : <>
          <p className="text-sm text-texto-secundario">{futbol.datos.total} registrados · Fuente actualizada: {futbol.datos.datosActualizadosEn ?? 'N/D'}</p>
          {!futbol.datos.partidos.length && <p>No hay partidos registrados; no acredita ausencia de encuentros.</p>}
          {futbolVisibles.map(p => <article key={p.id}><Link className="ficha-hoy" to={`/futbol?${new URLSearchParams({ fecha, partidoId: p.id })}`}><span className="text-xs text-neon-cyan">{p.competicionNombre} · {p.precisionFecha === 'DIA' ? 'Hora por confirmar' : new Date(p.fechaPartido).toLocaleTimeString('es-CO', { timeZone: 'America/Bogota', hour: '2-digit', minute: '2-digit' })}</span><strong>{p.equipoLocalNombre} — {p.equipoVisitanteNombre}</strong><span className="text-sm text-texto-secundario">{p.estadoAgenda} · Abrir ficha →</span></Link><div className="flex flex-wrap gap-x-5"><BotonFavorito favorito={{ tipo: 'competicion', liga: 'futbol', id: p.competicion, nombre: p.competicionNombre }} />{equiposFutbol(p).map(f => <BotonFavorito key={f.id} favorito={f} />)}</div></article>)}
          <ControlesPaginas nombre="fútbol" leidos={futbol.datos.partidos.length} total={futbol.datos.total} favoritos={futbolVisibles.length} soloFavoritos={filtrarFavoritos} cargando={futbol.cargandoMas} error={futbol.errorMas}
            cargar={() => { void futbol.cargarMas(filtrarFavoritos && hayFavoritosFutbol ? 10 : 1); }} detener={futbol.detener} actualizar={() => setRevisionFutbol(v => v + 1)} />
          <Link className="text-neon-cyan text-sm" to={`/futbol?fecha=${fecha}`}>Ver agenda completa y filtros</Link></>}
      </section>}
      <p className="text-xs text-texto-secundario">Se muestran registros de tu base de datos. Recorrer todas las páginas no acredita un calendario oficial completo. Consultar no descarga fuentes ni actualiza modelos.</p>
    </div><aside className="tarjeta space-y-4"><h2 className="font-semibold">Consultas recientes</h2>{errorCuaderno && <p role="alert">{errorCuaderno}</p>}{!recientes.length && !errorCuaderno && <p className="text-sm text-texto-secundario">Aún no guardaste consultas en este navegador.</p>}{recientes.map(r => <p key={r.id} className="text-sm"><Link to={`/mis-analisis?entrada=${encodeURIComponent(r.id)}`} className="text-neon-cyan">{r.favorito ? '★ ' : ''}{r.titulo}</Link><span className="block text-texto-secundario">{r.liga.toUpperCase()} · Copia, no dato actual</span></p>)}<Link to="/mis-analisis" className="text-neon-cyan text-sm block">Abrir Mis análisis →</Link><Link to="/laboratorio" className="text-neon-cyan text-sm block">Ver modelos y evidencia →</Link></aside></div>
  </main></div>;
}
