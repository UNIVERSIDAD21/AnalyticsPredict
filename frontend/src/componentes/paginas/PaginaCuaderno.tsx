import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Encabezado } from '../organismos/Encabezado';
import { ResultadoAnalisis } from '../organismos/ResultadoAnalisis';
import { VistaBaseLocal } from './PaginaBaseLocal';
import { leerCuaderno, editarEntrada, quitarEntrada, descargar, type EntradaCuaderno } from '../../servicios/cuadernoLocal';
import type { ConsultaLocal } from '../../servicios/consultaLocal';
import type { ResultadoVista } from '../../tipos/resultadoVista';
import type { LadoApuesta } from '../../tipos';
import type { ResultadoEuro } from '../../servicios/euroliga';
import { PanelFavoritosLocales } from '../moleculas/FavoritosLocales';

interface CopiaResultado { resultado: ResultadoVista; advertencias?: string[]; seleccionUsuario?: { lado: LadoApuesta; linea: number } | null; fuenteEuroliga?: ResultadoEuro }
function Entrada({ e, cambiar }: { e: EntradaCuaderno; cambiar: () => void }) {
  const [notas, setNotas] = useState(e.notas), [etiquetas, setEtiquetas] = useState(e.etiquetas.join(', ')), [error, setError] = useState('');
  const guardar = (favorito = e.favorito) => {
    try { editarEntrada(e.id, { notas, etiquetas: etiquetas.split(',').map(t => t.trim()).filter(Boolean), favorito }); cambiar(); setError(''); }
    catch (err) { setError(err instanceof Error ? err.message : 'No se pudo guardar.'); }
  };
  const copia = e.snapshot as CopiaResultado | null;
  const base = e.snapshot as ConsultaLocal | null;
  return <article className="tarjeta space-y-4 cuaderno-entrada">
    <div className="flex flex-wrap justify-between gap-3"><h2 className="font-semibold text-lg">{e.titulo}</h2><button aria-pressed={e.favorito} onClick={() => guardar(!e.favorito)}>{e.favorito ? '★ Favorito' : '☆ Favorito'}</button></div>
    <p className="text-sm text-texto-secundario">{e.liga.toUpperCase()} · Copia guardada {new Date(e.guardadoEn).toLocaleString('es-CO')} · No acredita actualidad ni registra una apuesta.</p>
    <div className="herramientas-consulta space-y-3">
      <label className="block text-sm">Notas<textarea className="input-base mt-2" rows={3} maxLength={5000} value={notas} onChange={ev => setNotas(ev.target.value)} /></label>
      <label className="block text-sm">Etiquetas separadas por comas<input className="input-base mt-2" maxLength={300} value={etiquetas} onChange={ev => setEtiquetas(ev.target.value)} /></label>
      <div className="flex flex-wrap gap-4 text-sm"><button className="text-neon-cyan" onClick={() => guardar()}>Guardar notas</button><button onClick={() => descargar('copia-cuaderno.json', JSON.stringify(e, null, 2))}>Exportar copia</button><button onClick={() => { if (window.confirm('¿Quitar esta copia del navegador? Exporta primero si quieres conservarla.')) { try { quitarEntrada(e.id); cambiar(); } catch (err) { setError(String(err)); } } }}>Quitar copia</button></div>
    </div>
    {error && <p role="alert">{error}</p>}
    <details><summary className="text-neon-cyan cursor-pointer">Reabrir resultado original · sin nueva consulta</summary><div className="mt-4 min-w-0">
      {e.tipo === 'base' && base?.formato === 'consulta-local-v1' ? <VistaBaseLocal r={base} /> : copia?.resultado?.predicciones ? <ResultadoAnalisis {...copia} /> : <p>No hay una vista compatible. La copia original se conserva abajo.</p>}
      <details className="mt-4"><summary>JSON original completo</summary><pre className="text-xs whitespace-pre-wrap break-all mt-3">{JSON.stringify(e.snapshot, null, 2)}</pre></details>
    </div></details>
  </article>;
}
export function PaginaCuaderno() {
  const [revision, setRevision] = useState(0), [buscar, setBuscar] = useState(''), [favoritos, setFavoritos] = useState(false), [liga, setLiga] = useState('');
  let entradas: EntradaCuaderno[] = [], error = '';
  try { entradas = leerCuaderno(); } catch (e) { error = e instanceof Error ? e.message : 'No se pudo abrir el cuaderno.'; }
  const visibles = entradas.filter(e => (!liga || e.liga === liga) && (!favoritos || e.favorito) && `${e.titulo} ${e.notas} ${e.etiquetas.join(' ')}`.toLocaleLowerCase().includes(buscar.toLocaleLowerCase()));
  return <div className="min-h-screen"><Encabezado /><main id="contenido-principal" tabIndex={-1} className="contenedor py-8 space-y-6" data-revision={revision}>
    <div><h1 className="text-3xl font-semibold">Mi cuaderno</h1><p className="mt-3 text-texto-secundario">Consultas, notas y etiquetas de todas las ligas. Se guardan solo en este navegador: exporta una copia para respaldarlas.</p></div>
    <PanelFavoritosLocales />
    <div className="flex flex-wrap gap-4 herramientas-consulta"><label>Buscar<input className="input-base mt-2" type="search" value={buscar} onChange={e => setBuscar(e.target.value)} /></label><label>Liga<select className="input-base mt-2" value={liga} onChange={e => setLiga(e.target.value)}><option value="">Todas</option>{['nba','euroliga','wnba','futbol'].map(l => <option key={l} value={l}>{l.toUpperCase()}</option>)}</select></label><label className="self-end pb-3"><input type="checkbox" checked={favoritos} onChange={e => setFavoritos(e.target.checked)} /> Solo favoritos</label><button onClick={() => descargar('cuaderno-analyticspredict.json', JSON.stringify(entradas, null, 2))}>Respaldar cuaderno JSON</button></div>
    {error ? <p role="alert">{error} No se sobrescribieron las entradas.</p> : <><p role="status" className="text-sm text-texto-secundario">{visibles.length} copias visibles de {entradas.length}</p>{!visibles.length && <p className="tarjeta">No hay copias para estos filtros. Puedes guardar una consulta desde el resultado o desde <Link className="text-neon-cyan" to="/base-local">Base local NBA</Link>.</p>}{visibles.map(e => <Entrada key={e.id} e={e} cambiar={() => setRevision(v => v+1)} />)}</>}
  </main></div>;
}
