import { useEffect, useRef, useState } from 'react';
import { Encabezado } from '../organismos/Encabezado';
import { HerramientasConsulta } from '../moleculas/HerramientasConsulta';
import { catalogoLocal, consultarLocal, compararLinea, compararNormalDiscreta, type ConsultaLocal, type LigaBaseLocal } from '../../servicios/consultaLocal';
import { extraerMensajeError } from '../../servicios/api';
import { BotonFavorito } from '../moleculas/FavoritosLocales';
import { favoritoEquipo, favoritoLiga } from '../../servicios/favoritosLocales';

const prob = (p: number | null) => p == null ? 'N/D' : `${(p * 100).toFixed(2)}%`;
const nombresLiga = { nba: 'NBA', euroliga: 'Euroliga', wnba: 'WNBA' };
export function VistaBaseLocal({ r }: { r: ConsultaLocal }) {
  const [linea, setLinea] = useState(String(r.linea));
  const discreta = r.distribucion.familia === 'normal_discretizada';
  const comparar = discreta ? compararNormalDiscreta : compararLinea;
  const comparacion = linea.trim() ? comparar(r.distribucion.media, r.distribucion.desviacion, Number(linea)) : null;
  return <article className="tarjeta space-y-5 min-w-0" aria-label="Consulta base local">
    <p className="text-neon-cyan text-sm">{nombresLiga[r.liga]} · Base local · {r.periodo} · {r.liga === 'nba' ? 48 : 40} min sin OT · RAW</p>
    <h2 className="text-xl font-semibold">{r.equipo_local} — {r.equipo_visitante}</h2>
    <div className="flex flex-wrap gap-5"><BotonFavorito favorito={favoritoLiga(r.liga)} />{[{ nombre: r.equipo_local, id: r.equipo_local_id }, { nombre: r.equipo_visitante, id: r.equipo_visitante_id }].map(({ nombre, id }) => <BotonFavorito key={nombre} favorito={favoritoEquipo(r.liga, id, nombre)} />)}</div>
    <p className="text-texto-secundario">Consulta: {new Date(r.generado_en).toLocaleString('es-CO', { timeZone: 'America/Bogota' })} COT. No se verifica el estado actual del encuentro.</p>
    <div className="grid sm:grid-cols-3 gap-4">
      <div><p className="text-sm text-texto-secundario">Media / desviación</p><strong>{r.distribucion.media.toFixed(2)} / {r.distribucion.desviacion.toFixed(2)} pts</strong></div>
      <div><p className="text-sm text-texto-secundario">Over {r.linea}</p><strong className="text-2xl">{prob(r.probabilidad_over)}</strong></div>
      <div><p className="text-sm text-texto-secundario">Under {r.linea}</p><strong className="text-2xl">{prob(r.probabilidad_under)}</strong></div>
    </div>
    {discreta && <p className="text-sm">Push {r.linea}: <strong>{prob(r.probabilidad_push)}</strong> · Normal discretizada de regulación</p>}
    {r.motivo_nd && <p role="note">{r.motivo_nd}</p>}
    <p className="text-sm break-words">Modelo {r.metadata.modelo_version} · Corte: {r.metadata.corte_modelo ?? 'N/D'} · Muestra de ajuste: {r.metadata.muestra_entrenamiento ?? 'N/D'}</p>
    <details><summary>Fuente y límites del resultado</summary><div className="space-y-2 pt-3 text-sm text-texto-secundario">
      <p>Modelo generado: {r.metadata.modelo_generado_en ?? 'N/D'}</p><p className="break-all">Dataset del ajuste: {r.metadata.dataset_hash ?? 'N/D'}</p>
      {r.metadata.alcance && <p>Alcance: {r.metadata.alcance}</p>}
      {r.metadata.ajuste_version && <p className="break-all">Ajuste: {r.metadata.ajuste_version}</p>}
      {r.advertencias.map(a => <p key={a}>{a}</p>)}
    </div></details>
    <details><summary>Comparar otra línea · misma distribución</summary><div className="pt-3 space-y-3 text-sm">
      <label className="block">{discreta ? 'Línea entera o terminada en .5' : 'Línea terminada en .5'}<input className="input-base max-w-48 block mt-2" type="number" step={discreta ? '0.5' : '1'} min="0.5" max={discreta ? '600' : '999.5'} value={linea} onChange={e => setLinea(e.target.value)} /></label>
      <p>{comparacion ? `Over ≈ ${prob(comparacion.over)} · Under ≈ ${prob(comparacion.under)}${'push' in comparacion ? ` · Push ≈ ${prob(comparacion.push as number)}` : ''}` : discreta ? 'N/D: usa una línea entera o terminada en .5 entre 0.5 y 600.' : 'N/D: usa una línea terminada en .5; no hay masa de push acreditada.'}</p>
      <p className="text-texto-secundario">Aproximación matemática sobre los parámetros originales, no una nueva consulta ni probabilidad calibrada. No vuelve a ajustar ni llamar a la API.</p>
    </div></details>
    <HerramientasConsulta titulo={`${r.equipo_local} — ${r.equipo_visitante} · ${r.periodo} · ${r.linea}`} liga={r.liga} snapshot={r} tipo="base" />
  </article>;
}

export function PaginaBaseLocal() {
  const [liga, setLiga] = useState<LigaBaseLocal>('nba');
  const [catalogo, setCatalogo] = useState<Awaited<ReturnType<typeof catalogoLocal>> | null>(null);
  const [equipoLocal, setLocal] = useState(''), [visitante, setVisitante] = useState('');
  const [periodo, setPeriodo] = useState('TOTAL'), [linea, setLinea] = useState('220.5');
  const [r, setR] = useState<ConsultaLocal | null>(null), [error, setError] = useState('');
  const [cargando, setCargando] = useState(false), [cargaCatalogo, setCargaCatalogo] = useState(true), [revision, setRevision] = useState(0);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => {
    const c = new AbortController(); setCargaCatalogo(true); setCatalogo(null); setError('');
    catalogoLocal(c.signal, liga).then(d => { if (!c.signal.aborted) setCatalogo(d); }).catch(e => { if (!c.signal.aborted) setError(extraerMensajeError(e)); }).finally(() => { if (!c.signal.aborted) setCargaCatalogo(false); });
    return () => { c.abort(); controller.current?.abort(); };
  }, [revision, liga]);
  const invalidar = () => { setR(null); controller.current?.abort(); setCargando(false); };
  const equipos = (catalogo?.equipos ?? []).map(e => typeof e === 'string' ? { clave: e, nombre: e, disponible: true } : e);
  const enviar = async (event: React.FormEvent) => {
    event.preventDefault(); if (cargando) return;
    const c = new AbortController(); controller.current?.abort(); controller.current = c;
    setCargando(true); setError(''); setR(null);
    try { const dato = await consultarLocal({ equipo_local: equipoLocal, equipo_visitante: visitante, periodo, linea: Number(linea) }, c.signal, liga); if (!c.signal.aborted) setR(dato); }
    catch (e) { if (!c.signal.aborted) setError(extraerMensajeError(e)); }
    finally { if (!c.signal.aborted) setCargando(false); }
  };
  return <div className="min-h-screen"><Encabezado /><main id="contenido-principal" tabIndex={-1} className="contenedor py-8 space-y-6">
    <div><p className="text-neon-cyan text-sm">Consulta sin base de datos</p><h1 className="text-3xl font-semibold mt-2">Base local · {nombresLiga[liga]}</h1><p className="text-texto-secundario mt-3">Artefacto publicado, sin contexto reciente ni verificación del fixture. Puedes guardar la copia en Mis análisis.</p></div>
    <label className="block text-sm max-w-sm">Liga<select className="input-base mt-2" value={liga} onChange={e => { invalidar(); setLocal(''); setVisitante(''); setPeriodo('TOTAL'); setLinea(e.target.value === 'nba' ? '220.5' : '160.5'); setLiga(e.target.value as LigaBaseLocal); }}>{Object.entries(nombresLiga).map(([id, nombre]) => <option key={id} value={id}>{nombre}</option>)}</select></label>
    {error && <div role="alert" className="tarjeta"><p>{error}</p>{!catalogo && <button type="button" className="mt-3 text-neon-cyan" onClick={() => setRevision(v => v+1)}>Reintentar catálogo local</button>}</div>}
    {cargaCatalogo && <p role="status">Cargando artefacto local…</p>}
    {catalogo && <><p className="text-sm text-texto-secundario">Modelo {catalogo.metadata.modelo_version} · Corte {catalogo.metadata.corte_modelo ?? 'N/D'} · Datos actuales del encuentro: N/D</p>
      <div className="grid xl:grid-cols-[340px_minmax(0,1fr)] gap-6 items-start"><form onSubmit={enviar} className="tarjeta space-y-4">
        <h2 className="font-semibold">Configurar consulta</h2>
        <label className="block text-sm">Local<select aria-label="Local" className="input-base mt-2" required value={equipoLocal} onChange={e => { invalidar(); setLocal(e.target.value); }}><option value="">Selecciona equipo</option>{equipos.map(e => <option key={e.clave} value={e.clave} disabled={!e.disponible}>{e.nombre}{!e.disponible ? ' · muestra insuficiente' : ''}</option>)}</select></label>
        <label className="block text-sm">Visitante<select aria-label="Visitante" className="input-base mt-2" required value={visitante} onChange={e => { invalidar(); setVisitante(e.target.value); }}><option value="">Selecciona equipo</option>{equipos.map(e => <option key={e.clave} value={e.clave} disabled={!e.disponible || e.clave === equipoLocal}>{e.nombre}{!e.disponible ? ' · muestra insuficiente' : ''}</option>)}</select></label>
        <label className="block text-sm">Periodo<select aria-label="Periodo" className="input-base mt-2" value={periodo} onChange={e => { invalidar(); setPeriodo(e.target.value); }}>{['TOTAL', 'Q1', 'Q2', 'Q3', 'Q4'].map(p => <option key={p}>{p}</option>)}</select></label>
        <label className="block text-sm">Línea de puntos<input className="input-base mt-2" type="number" step="0.5" min="0.5" max={liga === 'nba' ? '999.5' : '600'} required value={linea} onChange={e => { invalidar(); setLinea(e.target.value); }} /></label>
        <button className="boton-primario w-full" type="submit" disabled={cargando || !equipoLocal || !visitante || equipoLocal === visitante}>{cargando ? 'Consultando…' : 'Consultar artefacto'}</button>
      </form><div>{r ? <VistaBaseLocal key={r.analisis_id} r={r} /> : <p role="status" className="tarjeta text-texto-secundario">{cargando ? 'Calculando una única consulta…' : 'Configura la consulta para ver la distribución RAW. No se han calculado resultados para estos parámetros.'}</p>}</div></div></>}
  </main></div>;
}
