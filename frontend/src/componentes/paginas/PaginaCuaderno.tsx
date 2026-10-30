import { Component, lazy, Suspense, useEffect, useState, type ReactNode } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ArrowUpRight, BookOpen, Download, Search, SlidersHorizontal, Star, X } from 'lucide-react';
import { Encabezado } from '../organismos/Encabezado';
import { leerCuaderno, editarEntrada, quitarEntrada, descargar, LIMITE_CONSULTAS, LIMITE_CUADERNO, type EntradaCuaderno } from '../../servicios/cuadernoLocal';
import type { ConsultaLocal } from '../../servicios/consultaLocal';
import type { ResultadoVista } from '../../tipos/resultadoVista';
import type { LadoApuesta } from '../../tipos';
import type { ResultadoEuro } from '../../servicios/euroliga';
import { PanelFavoritosLocales } from '../moleculas/FavoritosLocales';
import { RespaldoPersonal } from '../moleculas/RespaldoPersonal';
import { NavegacionPersonal } from '../moleculas/NavegacionPersonal';
import { FILTROS_INICIALES, organizarCuaderno, type FiltrosCuaderno } from '../../servicios/organizacionCuaderno';
import './cuaderno.css';

const ResultadoAnalisis = lazy(() => import('../organismos/ResultadoAnalisis').then(m => ({ default: m.ResultadoAnalisis })));
const VistaBaseLocal = lazy(() => import('./PaginaBaseLocal').then(m => ({ default: m.VistaBaseLocal })));
interface CopiaResultado { resultado: ResultadoVista; advertencias?: string[]; seleccionUsuario?: { lado: LadoApuesta; linea: number } | null; fuenteEuroliga?: ResultadoEuro }
class VistaProtegida extends Component<{ children: ReactNode }, { fallo: boolean }> {
  state = { fallo: false };
  static getDerivedStateFromError() { return { fallo: true }; }
  render() { return this.state.fallo ? <p role="status">Esta copia no tiene una vista compatible. Puedes consultar su JSON original o exportarla; tus datos se conservan.</p> : this.props.children; }
}
function ResultadoGuardado({ e }: { e: EntradaCuaderno }) {
  const copia = e.snapshot as CopiaResultado | null, base = e.snapshot as ConsultaLocal | null;
  return <VistaProtegida><Suspense fallback={<p role="status">Abriendo la copia guardada…</p>}>
    {e.tipo === 'base' && (base?.formato === 'consulta-local-v1' || base?.formato === 'consulta-local-v2') ? <VistaBaseLocal r={base} /> : copia?.resultado?.predicciones ?
      <ResultadoAnalisis resultado={copia.resultado} advertencias={copia.advertencias} seleccionUsuario={copia.seleccionUsuario} fuenteEuroliga={copia.fuenteEuroliga} /> :
      <p>No hay una vista compatible para esta copia. Su contenido original se conserva abajo.</p>}
  </Suspense></VistaProtegida>;
}
function Entrada({ e, abierta, abrir }: { e: EntradaCuaderno; abierta: boolean; abrir: () => void }) {
  const [notas, setNotas] = useState(e.notas), [etiquetas, setEtiquetas] = useState(e.etiquetas.join(', '));
  const [error, setError] = useState(''), [mensaje, setMensaje] = useState(''), [verResultado, setVerResultado] = useState(false), [quitar, setQuitar] = useState(false);
  const ejecutar = (accion: () => void) => { try { accion(); setError(''); } catch (err) { setError(err instanceof Error ? err.message : 'No se pudo completar.'); } };
  const pendiente = notas !== e.notas || etiquetas !== e.etiquetas.join(', ');
  return <article className={`cuaderno-entrada tarjeta ${abierta ? 'cuaderno-entrada-abierta' : ''}`}>
    <div className="cuaderno-fila">
      <span className={`cuaderno-liga cuaderno-liga-${e.liga}`}>{e.liga === 'euroliga' ? 'EURO' : e.liga === 'futbol' ? 'FÚT' : e.liga.toUpperCase()}</span>
      <div className="cuaderno-identidad"><h2><button className="cuaderno-titulo" type="button" onClick={abrir} aria-expanded={abierta} aria-controls={`consulta-${e.id}`}>{e.titulo}</button></h2>
        <p>{new Date(e.guardadoEn).toLocaleString('es-CO', { timeZone: 'America/Bogota', dateStyle: 'medium', timeStyle: 'short' })} · {e.tipo === 'base' ? 'Base local' : 'Consulta guardada'}{pendiente ? ' · Notas sin guardar' : ''}</p>
        {e.etiquetas.length > 0 && <div className="cuaderno-etiquetas">{e.etiquetas.map((t, i) => <span key={`${t}-${i}`}>{t}</span>)}</div>}
      </div>
      <div className="cuaderno-acciones"><button type="button" className={`cuaderno-icon-button ${e.favorito ? 'cuaderno-favorito-activo' : ''}`} aria-label={`${e.favorito ? 'Quitar' : 'Marcar'} favorito: ${e.titulo}`} aria-pressed={e.favorito}
        onClick={() => ejecutar(() => editarEntrada(e.id, { notas: e.notas, etiquetas: e.etiquetas, favorito: !e.favorito }))}><Star size={19} fill={e.favorito ? 'currentColor' : 'none'} aria-hidden="true" /></button>
        <button type="button" className="cuaderno-boton" onClick={abrir} aria-expanded={abierta}>{abierta ? 'Cerrar' : 'Abrir'}<ArrowUpRight size={15} aria-hidden="true" /></button></div>
    </div>
    {error && <p className="cuaderno-error" role="alert">{error}</p>}
    {abierta && <div id={`consulta-${e.id}`} className="cuaderno-detalle">
      <p className="cuaderno-ayuda">Copia del momento en que la guardaste. Abrirla no ejecuta otra consulta ni registra una apuesta.</p>
      <div className="cuaderno-editor"><label>Mis notas<textarea className="input-base" rows={3} maxLength={5000} value={notas} onChange={ev => { setNotas(ev.target.value); setMensaje(''); }} placeholder="¿Qué observaste? ¿Qué quieres revisar después?" /></label>
        <label>Etiquetas<input className="input-base" maxLength={300} value={etiquetas} onChange={ev => { setEtiquetas(ev.target.value); setMensaje(''); }} placeholder="Por ejemplo: revisar, ritmo, seguimiento" /><span className="cuaderno-ayuda">Separadas por comas · hasta 12</span></label></div>
      <div className="cuaderno-acciones herramientas-consulta"><button type="button" className="cuaderno-boton cuaderno-boton-acento" disabled={!pendiente} onClick={() => ejecutar(() => {
        const limpias = [...new Set(etiquetas.split(',').map(t => t.trim()).filter(Boolean))].slice(0, 12);
        editarEntrada(e.id, { notas, etiquetas: limpias, favorito: e.favorito }); setEtiquetas(limpias.join(', ')); setMensaje('Notas guardadas.');
      })}>Guardar notas</button><button type="button" className="cuaderno-boton" onClick={() => ejecutar(() => descargar('consulta-cuaderno.json', JSON.stringify(e, null, 2)))}><Download size={16} aria-hidden="true" />Exportar consulta</button>
        <button type="button" className="cuaderno-enlace" onClick={() => setQuitar(!quitar)}>Quitar del cuaderno</button></div>
      {mensaje && <p role="status" className="cuaderno-exito">{mensaje}</p>}
      {quitar && <div className="cuaderno-aviso"><p>Se quitará solo esta copia. Puedes exportarla antes de continuar.</p><div className="cuaderno-acciones"><button type="button" className="cuaderno-boton" onClick={() => ejecutar(() => quitarEntrada(e.id))}>Quitar esta copia</button><button type="button" className="cuaderno-enlace" onClick={() => setQuitar(false)}>Conservarla</button></div></div>}
      <button type="button" className="cuaderno-enlace" aria-expanded={verResultado} onClick={() => setVerResultado(!verResultado)}>{verResultado ? 'Ocultar resultado original' : 'Ver resultado original'}</button>
      {verResultado && <div className="cuaderno-resultado"><ResultadoGuardado e={e} /><details><summary>JSON original completo</summary><pre>{JSON.stringify(e.snapshot, null, 2)}</pre></details></div>}
    </div>}
  </article>;
}
function cargarCuaderno() {
  try { return { entradas: leerCuaderno(), error: '' }; }
  catch (e) { return { entradas: [] as EntradaCuaderno[], error: e instanceof Error ? e.message : 'No se pudo abrir el cuaderno.' }; }
}
export function PaginaCuaderno() {
  const [{ entradas, error }, setDatos] = useState(cargarCuaderno), [filtros, setFiltros] = useState<FiltrosCuaderno>({ ...FILTROS_INICIALES });
  const [params, setParams] = useSearchParams();
  useEffect(() => {
    const actualizar = () => setDatos(cargarCuaderno());
    window.addEventListener('cuaderno-actualizado', actualizar); window.addEventListener('storage', actualizar);
    return () => { window.removeEventListener('cuaderno-actualizado', actualizar); window.removeEventListener('storage', actualizar); };
  }, []);
  const cambiar = <K extends keyof FiltrosCuaderno>(clave: K, valor: FiltrosCuaderno[K]) => setFiltros(previos => ({ ...previos, [clave]: valor }));
  const visibles = organizarCuaderno(entradas, filtros), seleccionada = params.get('entrada');
  const etiquetas = [...new Set(entradas.flatMap(e => e.etiquetas))].sort((a, b) => a.localeCompare(b, 'es'));
  const ocupacion = entradas.length ? Math.min(100, Math.ceil(Math.max(entradas.length / LIMITE_CONSULTAS, JSON.stringify(entradas).length / LIMITE_CUADERNO) * 100)) : 0;
  const filtrando = filtros.buscar || filtros.liga || filtros.favorito || filtros.etiqueta || filtros.desde || filtros.hasta;
  return <div className="min-h-screen"><Encabezado /><main id="contenido-principal" tabIndex={-1} className="contenedor cuaderno-pagina">
    <NavegacionPersonal />
    <div className="cuaderno-cabecera"><div><p className="cuaderno-kicker"><BookOpen size={16} aria-hidden="true" />ESPACIO PERSONAL</p><h1>Mis análisis</h1><p>Tu memoria de análisis. Conserva lo que observaste y vuelve a ello cuando lo necesites.</p></div><Link className="cuaderno-boton" to="/base-local">Nueva consulta local<ArrowUpRight size={17} aria-hidden="true" /></Link></div>
    <section className="cuaderno-estadisticas" aria-label="Resumen del cuaderno"><div><span>Consultas guardadas</span><strong>{error ? 'N/D' : entradas.length.toString().padStart(2, '0')}</strong></div><div><span>Consultas favoritas</span><strong>{error ? 'N/D' : entradas.filter(e => e.favorito).length.toString().padStart(2, '0')}</strong></div><div><span>Ligas en tu cuaderno</span><strong>{error ? 'N/D' : new Set(entradas.map(e => e.liga)).size.toString().padStart(2, '0')}</strong></div><div className="cuaderno-capacidad"><span>Capacidad del cuaderno</span>{error ? <strong>N/D</strong> : <><strong>{ocupacion}<small>%</small></strong><meter aria-label="Capacidad del cuaderno utilizada" min={0} max={100} value={ocupacion} /><p>{entradas.length} de {LIMITE_CONSULTAS} consultas · respalda antes de liberar espacio</p></>}</div></section>
    <RespaldoPersonal />
    <section className="tarjeta cuaderno-filtros" aria-label="Buscar y organizar consultas"><div className="cuaderno-filtros-principales"><label className="cuaderno-busqueda"><span><Search size={16} aria-hidden="true" />Buscar en mis consultas</span><input className="input-base" type="search" placeholder="Equipo, nota o etiqueta…" value={filtros.buscar} onChange={e => cambiar('buscar', e.target.value)} /></label>
      <label>Liga<select className="input-base" value={filtros.liga} onChange={e => cambiar('liga', e.target.value)}><option value="">Todas las ligas</option>{['nba', 'euroliga', 'wnba', 'futbol'].map(l => <option key={l} value={l}>{l === 'futbol' ? 'Fútbol' : l.toUpperCase()}</option>)}</select></label>
      <label>Ordenar<select className="input-base" value={filtros.orden} onChange={e => cambiar('orden', e.target.value as FiltrosCuaderno['orden'])}><option value="recientes">Más recientes</option><option value="antiguas">Más antiguas</option><option value="titulo">Por título</option><option value="favoritos">Favoritas primero</option></select></label></div>
      <div className="cuaderno-filtros-secundarios"><label className="cuaderno-checkbox"><input type="checkbox" checked={filtros.favorito} onChange={e => cambiar('favorito', e.target.checked)} />Solo consultas favoritas</label>
        <details><summary><SlidersHorizontal size={16} aria-hidden="true" />Fechas y etiquetas</summary><div className="cuaderno-filtros-avanzados"><label>Guardada desde<input className="input-base" type="date" value={filtros.desde} max={filtros.hasta || undefined} onChange={e => cambiar('desde', e.target.value)} /></label><label>Guardada hasta<input className="input-base" type="date" value={filtros.hasta} min={filtros.desde || undefined} onChange={e => cambiar('hasta', e.target.value)} /></label><label>Etiqueta<select className="input-base" value={filtros.etiqueta} onChange={e => cambiar('etiqueta', e.target.value)}><option value="">Todas las etiquetas</option>{etiquetas.map(t => <option key={t}>{t}</option>)}</select></label></div><p className="cuaderno-ayuda">Fechas de guardado en hora de Colombia.</p></details>
        {filtrando && <button type="button" className="cuaderno-enlace" onClick={() => setFiltros({ ...FILTROS_INICIALES })}><X size={15} aria-hidden="true" />Limpiar filtros</button>}</div>
    </section>
    {error ? <p role="alert" className="cuaderno-aviso cuaderno-error">{error} Tus datos originales se conservan. Puedes guardar una copia de recuperación desde el bloque de respaldo.</p> : <>
      <div className="cuaderno-lista-cabecera"><h2>Consultas{filtrando ? ' filtradas' : ''}</h2><p role="status">{visibles.length} de {entradas.length}</p></div>
      {seleccionada && !entradas.some(e => e.id === seleccionada) && <p role="status" className="cuaderno-aviso">La consulta del enlace no está en este navegador. Puedes restaurarla desde un respaldo.</p>}
      {!visibles.length && <div className="tarjeta cuaderno-vacio"><BookOpen size={36} aria-hidden="true" /><h2>{entradas.length ? 'No encontramos consultas con estos filtros' : 'Tu próxima idea empieza aquí'}</h2><p>{entradas.length ? 'Prueba con otro equipo, cambia las fechas o limpia los filtros.' : 'Guarda una consulta desde cualquier resultado. Aquí podrás añadir notas, organizarla y volver a verla.'}</p>{entradas.length ? <button type="button" className="cuaderno-boton" onClick={() => setFiltros({ ...FILTROS_INICIALES })}>Ver todas mis consultas</button> : <Link className="cuaderno-boton cuaderno-boton-acento" to="/base-local">Crear mi primera consulta<ArrowUpRight size={16} aria-hidden="true" /></Link>}</div>}
      <div className="cuaderno-lista">{visibles.map(e => <Entrada key={e.id} e={e} abierta={seleccionada === e.id} abrir={() => setParams(seleccionada === e.id ? {} : { entrada: e.id }, { replace: true })} />)}</div>
    </>}
    <details className="cuaderno-favoritos tarjeta"><summary>Mis equipos, ligas y competiciones favoritos</summary><PanelFavoritosLocales /></details>
  </main></div>;
}
