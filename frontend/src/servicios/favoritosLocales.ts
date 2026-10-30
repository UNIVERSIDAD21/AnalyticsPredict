import type { LigaCuaderno } from './cuadernoLocal';

export interface FavoritoLocal {
  tipo: 'liga' | 'equipo' | 'competicion'; liga: LigaCuaderno; id: string; nombre: string;
}
const CLAVE = 'analyticspredict-favoritos-v1';
export const LIGAS_PERSONALES: LigaCuaderno[] = ['nba', 'wnba', 'euroliga', 'futbol'];
export const identidadFavorito = (f: FavoritoLocal) => JSON.stringify([f.liga, f.tipo, f.id]);
export function favoritoEquipo(liga: LigaCuaderno, id: string | undefined, nombre: string): FavoritoLocal {
  // Sin ID no se inventa una equivalencia con el catálogo de la BD.
  return { liga, tipo: 'equipo', id: id ? `id:${id}` : `nombre:${nombre}`, nombre };
}
export function favoritoLiga(liga: LigaCuaderno): FavoritoLocal {
  return { liga, tipo: 'liga', id: liga, nombre: liga.toUpperCase() };
}
export function leerFavoritos(): FavoritoLocal[] {
  const raw = localStorage.getItem(CLAVE);
  if (raw === null) return [];
  let parsed: { version?: unknown; elementos?: unknown };
  try { parsed = JSON.parse(raw); } catch { throw new Error('Favoritos locales dañados. No se sobrescribieron.'); }
  const validos = parsed && parsed.version === 1 && Array.isArray(parsed.elementos) && parsed.elementos.length <= 200 &&
    parsed.elementos.every((f: FavoritoLocal) => f && ['liga', 'equipo', 'competicion'].includes(f.tipo) && LIGAS_PERSONALES.includes(f.liga) &&
      typeof f.id === 'string' && f.id.length > 0 && f.id.length <= 300 && typeof f.nombre === 'string' && f.nombre.length > 0 && f.nombre.length <= 200 &&
      (f.tipo !== 'liga' || f.id === f.liga));
  if (!validos) throw new Error('Formato de favoritos no compatible. No se sobrescribieron.');
  const elementos = parsed.elementos as FavoritoLocal[];
  if (new Set(elementos.map(identidadFavorito)).size !== elementos.length) throw new Error('Favoritos duplicados. No se sobrescribieron.');
  return elementos;
}
export function cambiarFavorito(f: FavoritoLocal) {
  const previos = leerFavoritos(), key = identidadFavorito(f);
  const siguientes = previos.some(v => identidadFavorito(v) === key) ? previos.filter(v => identidadFavorito(v) !== key) : [...previos, f];
  if (siguientes.length > 200) throw new Error('Límite de 200 favoritos. Quita alguno antes de añadir otro.');
  try { localStorage.setItem(CLAVE, JSON.stringify({ version: 1, elementos: siguientes })); }
  catch { throw new Error('No se pudieron guardar los favoritos en este navegador.'); }
  window.dispatchEvent(new Event('favoritos-actualizados'));
}
export function coincideFavoritos(favoritos: FavoritoLocal[], liga: LigaCuaderno, equipos: FavoritoLocal[], competicion?: string) {
  return favoritos.some(f => f.liga === liga && (f.tipo === 'liga' ||
    (f.tipo === 'competicion' && f.id === competicion) || equipos.some(e => identidadFavorito(e) === identidadFavorito(f))));
}
