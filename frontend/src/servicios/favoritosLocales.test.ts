import { beforeEach, expect, it, vi } from 'vitest';
import { cambiarFavorito, coincideFavoritos, favoritoEquipo, favoritoLiga, leerFavoritos } from './favoritosLocales';
beforeEach(() => { localStorage.clear(); vi.restoreAllMocks(); });
it('separa identidades entre ligas y no equipara nombres locales con IDs de BD', () => {
  const nba = favoritoEquipo('nba', '42', 'Boston'), wnba = favoritoEquipo('wnba', '42', 'Boston');
  cambiarFavorito(nba); cambiarFavorito(wnba); cambiarFavorito(favoritoEquipo('nba', undefined, 'Boston'));
  cambiarFavorito(nba);
  expect(leerFavoritos()).toHaveLength(2);
  expect(coincideFavoritos(leerFavoritos(), 'nba', [nba])).toBe(false);
  expect(coincideFavoritos(leerFavoritos(), 'wnba', [wnba])).toBe(true);
  cambiarFavorito(favoritoLiga('nba'));
  expect(coincideFavoritos(leerFavoritos(), 'nba', [nba])).toBe(true);
  expect(coincideFavoritos(leerFavoritos(), 'euroliga', [])).toBe(false);
});
it('no reemplaza favoritos corruptos o de versión futura', () => {
  for (const raw of ['{incompleto', '{"version":2,"elementos":[]}', 'null']) {
    localStorage.setItem('analyticspredict-favoritos-v1', raw);
    expect(() => cambiarFavorito(favoritoLiga('futbol'))).toThrow();
    expect(localStorage.getItem('analyticspredict-favoritos-v1')).toBe(raw);
  }
});
it('conserva preferencias previas si se agota el almacenamiento', () => {
  cambiarFavorito(favoritoLiga('nba'));
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('QuotaExceededError'); });
  expect(() => cambiarFavorito(favoritoLiga('futbol'))).toThrow('No se pudieron guardar');
  expect(leerFavoritos()).toEqual([favoritoLiga('nba')]);
});
