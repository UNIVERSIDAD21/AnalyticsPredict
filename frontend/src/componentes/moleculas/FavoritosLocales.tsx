import { useEffect, useState } from 'react';
import { cambiarFavorito, favoritoLiga, identidadFavorito, leerFavoritos, LIGAS_PERSONALES, type FavoritoLocal } from '../../servicios/favoritosLocales';
import { descargar } from '../../servicios/cuadernoLocal';

export function useFavoritosLocales() {
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const actualizar = () => setRevision(v => v + 1);
    window.addEventListener('favoritos-actualizados', actualizar); window.addEventListener('storage', actualizar);
    return () => { window.removeEventListener('favoritos-actualizados', actualizar); window.removeEventListener('storage', actualizar); };
  }, []);
  let favoritos: FavoritoLocal[] = [], error = '';
  try { favoritos = leerFavoritos(); } catch (e) { error = e instanceof Error ? e.message : 'Almacenamiento local no disponible.'; }
  return { favoritos, error, revision };
}
export function BotonFavorito({ favorito }: { favorito: FavoritoLocal }) {
  const { favoritos, error } = useFavoritosLocales(), [fallo, setFallo] = useState('');
  const activo = favoritos.some(f => identidadFavorito(f) === identidadFavorito(favorito));
  return <span className="inline-flex flex-col items-start gap-1"><button type="button" className="text-xs text-neon-cyan py-2"
    aria-pressed={activo} disabled={Boolean(error)} aria-label={`${activo ? 'Quitar' : 'Guardar'} favorito ${favorito.nombre}`}
    onClick={() => { try { cambiarFavorito(favorito); setFallo(''); } catch (e) { setFallo(e instanceof Error ? e.message : 'No se pudo guardar.'); } }}>
    {activo ? '★' : '☆'} {favorito.nombre}</button>{(fallo || error) && <span role="alert" className="text-xs">{fallo || error}</span>}</span>;
}
export function PanelFavoritosLocales() {
  const { favoritos, error } = useFavoritosLocales();
  return <section className="tarjeta space-y-4" aria-label="Equipos y ligas favoritos"><h2 className="text-xl font-semibold">Equipos y ligas favoritos</h2>
    <p className="text-sm text-texto-secundario">Preferencias de este navegador, separadas de las consultas favoritas y de la Bitácora. No crean apuestas ni descargan datos.</p>
    {error ? <p role="alert">{error}</p> : <><div className="flex flex-wrap gap-5">{LIGAS_PERSONALES.map(l => <BotonFavorito key={l} favorito={favoritoLiga(l)} />)}</div>
      <p className="text-sm">Guarda equipos y competiciones desde Hoy, la ficha de fútbol o Base local NBA. En Hoy puedes filtrar la página recibida por estos favoritos.</p>
      {favoritos.filter(f => f.tipo !== 'liga').map(f => <div key={identidadFavorito(f)} className="flex flex-wrap gap-3 items-center"><span className="text-xs text-texto-secundario">{f.liga.toUpperCase()} · {f.tipo}{f.id.startsWith('nombre:') ? ' · nombre del catálogo local, sin ID de BD' : ''}</span><BotonFavorito favorito={f} /></div>)}
      <button className="text-neon-cyan text-sm" onClick={() => descargar('favoritos-analyticspredict.json', JSON.stringify({ version: 1, elementos: favoritos }, null, 2))}>Exportar favoritos JSON</button></>}
  </section>;
}
