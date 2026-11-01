/** Solo memoria de la pestaña. No migra ni modifica claves del navegador. */
import type { EntradaCuaderno } from './cuadernoLocal';
import type { FavoritoLocal } from './favoritosLocales';
import type { PreferenciasVisualesLocal } from './preferenciasVisuales';

export interface DatosPersonalesPC {
  cuaderno: EntradaCuaderno[]; favoritos: FavoritoLocal[]; apariencia: PreferenciasVisualesLocal | null;
}
export interface EstadoPersonalPC {
  formato: 'almacen-personal-v1'; existe: boolean; revision: number;
  datos: DatosPersonalesPC; sha256: string | null; actualizadoEn: string | null;
}
let actual: EstadoPersonalPC | null = null;
export function cachePersonal() { return actual; }
export function recibirPersonal(estado: EstadoPersonalPC) {
  if (actual && estado.revision < actual.revision) return;
  actual = estado;
  for (const nombre of ['personal-actualizado', 'cuaderno-actualizado', 'favoritos-actualizados']) window.dispatchEvent(new Event(nombre));
}
export function olvidarCachePersonal() { actual = null; }
