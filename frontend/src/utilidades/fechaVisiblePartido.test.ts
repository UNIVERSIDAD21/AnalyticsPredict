import { expect, it } from 'vitest';
import { fechaVisiblePartido } from './agendaFutbol';
it('preserva el día nominal sin convertirlo en un kickoff COT', () => {
  const p = { fechaPartido: '2026-10-30T00:00:00Z', precisionFecha: 'DIA' as const, fechaFuente: '2026-10-30' };
  const texto = fechaVisiblePartido(p);
  expect(texto).toContain('30'); expect(texto).toContain('Día nominal de fuente'); expect(texto).toContain('Hora por confirmar');
  expect(texto).not.toContain('COT'); expect(texto).not.toMatch(/\d:\d/);
  expect(fechaVisiblePartido({ ...p, fechaFuente: null })).toBe('Fecha nominal N/D · Hora por confirmar');
  expect(fechaVisiblePartido({ ...p, fechaFuente: '2026-02-30' })).toBe('Fecha nominal N/D · Hora por confirmar');
});
it('con hora acreditada convierte UTC a Colombia, sin inventar fechas inválidas', () => {
  expect(fechaVisiblePartido({ fechaPartido: '2026-10-30T02:00:00Z', precisionFecha: 'HORA' })).toContain('29');
  expect(fechaVisiblePartido({ fechaPartido: 'no-es-fecha' })).toBe('Fecha y hora N/D');
});
