import { expect, it } from 'vitest';
import { FILTROS_INICIALES, fechaColombiaGuardada, organizarCuaderno } from './organizacionCuaderno';
import type { EntradaCuaderno } from './cuadernoLocal';
const entradas: EntradaCuaderno[] = [
  { id: 'a', titulo: 'Bogotá — Peña', liga: 'futbol', tipo: 'resultado', guardadoEn: '2026-10-30T03:59:00Z', notas: 'Revisión táctica', etiquetas: ['Rápido'], favorito: false, snapshot: {} },
  { id: 'b', titulo: 'Boston — Atlanta', liga: 'nba', tipo: 'base', guardadoEn: '2026-10-30T05:00:00Z', notas: '', etiquetas: [], favorito: true, snapshot: {} },
];
it('busca palabras sin depender de tildes ni de su orden', () => {
  expect(organizarCuaderno(entradas, { ...FILTROS_INICIALES, buscar: 'PENA tactica bogota' }).map(e => e.id)).toEqual(['a']);
});
it('filtra por el día de guardado colombiano y combina etiqueta, liga y favoritos', () => {
  expect(fechaColombiaGuardada(entradas[0].guardadoEn)).toBe('2026-10-29');
  expect(organizarCuaderno(entradas, { ...FILTROS_INICIALES, desde: '2026-10-29', hasta: '2026-10-29', etiqueta: 'rapido', liga: 'futbol' }).map(e => e.id)).toEqual(['a']);
  expect(organizarCuaderno(entradas, { ...FILTROS_INICIALES, favorito: true }).map(e => e.id)).toEqual(['b']);
});
it('ordena sin modificar el orden de la colección original', () => {
  expect(organizarCuaderno(entradas, FILTROS_INICIALES).map(e => e.id)).toEqual(['b', 'a']);
  expect(organizarCuaderno(entradas, { ...FILTROS_INICIALES, orden: 'antiguas' }).map(e => e.id)).toEqual(['a', 'b']);
  expect(entradas.map(e => e.id)).toEqual(['a', 'b']);
});
