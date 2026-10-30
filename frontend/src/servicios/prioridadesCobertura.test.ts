import { expect, it } from 'vitest';
import { priorizarCobertura } from './prioridadesCobertura';
import { favoritoEquipo, favoritoLiga } from './favoritosLocales';
import type { EntradaCuaderno } from './cuadernoLocal';
it('ordena por preferencias explícitas antes que copias sin inferir equivalencias entre ligas', () => {
  const copias = Array.from({ length: 5 }, () => ({ liga: 'nba' } as EntradaCuaderno));
  const r = priorizarCobertura([favoritoLiga('euroliga'), favoritoEquipo('wnba','42','Igual nombre')], copias);
  expect(r.map(x => x.liga)).toEqual(['euroliga','wnba','nba','futbol']);
  expect(r.find(x => x.liga === 'nba')!.entidades).toBe(0);
  expect(r.find(x => x.liga === 'nba')!.copias).toBe(5);
  expect(copias).toHaveLength(5);
});
it('sin preferencias conserva el orden declarado y no inventa prioridad observada', () => {
  expect(priorizarCobertura([], []).map(x => x.liga)).toEqual(['nba','wnba','euroliga','futbol']);
  expect(priorizarCobertura([], []).every(x => x.copias === 0 && !x.favorita && x.entidades === 0)).toBe(true);
});
