import { beforeEach, describe, expect, it } from 'vitest';
import { csvSnapshot, editarEntrada, guardarConsulta, leerCuaderno } from './cuadernoLocal';
import { compararLinea, compararNormalDiscreta } from './consultaLocal';
beforeEach(() => localStorage.clear());
describe('copias personales inmutables', () => {
  it('conserva originales, N/D y separación de ligas al editar notas y favoritos', () => {
    const original = { partido: 'Peña — Bogotá', probabilidad: null, metadata: { corte: '2026-01-01' } };
    const e = guardarConsulta({ titulo: 'Consulta', liga: 'wnba', snapshot: original, tipo: 'resultado' });
    original.metadata.corte = 'CAMBIO EXTERNO';
    editarEntrada(e.id, { notas: 'Revisar', etiquetas: ['dato dudoso'], favorito: true });
    const r = leerCuaderno()[0];
    expect(r.snapshot).toEqual({ partido: 'Peña — Bogotá', probabilidad: null, metadata: { corte: '2026-01-01' } });
    expect(r.liga).toBe('wnba'); expect(r.favorito).toBe(true); expect(r.guardadoEn).toBe(e.guardadoEn);
  });
  it('no sobrescribe un cuaderno corrupto ni simula que está vacío', () => {
    localStorage.setItem('analyticspredict-cuaderno-v1', '{incompleto');
    expect(() => guardarConsulta({ titulo: 'X', liga: 'nba', tipo: 'base', snapshot: {} })).toThrow();
    expect(localStorage.getItem('analyticspredict-cuaderno-v1')).toBe('{incompleto');
  });
  it('exporta null como N/D, ceros observados y protege celdas fórmula', () => {
    const csv = csvSnapshot({ ausente: null, cero: 0, nota: '=HYPERLINK("x")', texto: 'a,b' });
    expect(csv).toContain('"ausente","N/D"'); expect(csv).toContain('"cero","0"');
    expect(csv).toContain("'=HYPERLINK"); expect(csv).toContain('"texto","a,b"');
  });
});
describe('comparador sin inferencia nueva', () => {
  it('respeta la masa discreta y el caso determinista Euroliga, sin extrapolar a mezclas OT', () => {
    const entero = compararNormalDiscreta(180, 10, 180)!;
    expect(entero.over).toBeCloseTo(.48006119416, 6);
    expect(entero.under).toBeCloseTo(.48006119416, 6);
    expect(entero.push).toBeCloseTo(.03987761167, 6);
    expect(entero.over + entero.under + entero.push).toBeCloseTo(1, 12);
    expect(compararNormalDiscreta(180, 10, 180.5)?.push).toBe(0);
    expect(compararNormalDiscreta(0, 1, 0)?.push).toBeCloseTo(.3829249225, 6);
    expect(compararNormalDiscreta(180, 0, 180)).toEqual({ over: 0, under: 0, push: 1 });
    expect(compararNormalDiscreta(180, 10, 180.25)).toBeNull();
  });
  it('complementa y coincide con una CDF normal conocida sin cambiar la distribución', () => {
    expect(compararLinea(180.5, 10, 180.5)?.over).toBeCloseTo(.5, 6);
    expect(compararLinea(180.5, 10, 190.5)?.over).toBeCloseTo(.1586552539, 6);
    expect(compararLinea(180.5, 10, 170.5)?.over).toBeCloseTo(.8413447461, 6);
    expect(compararLinea(180.5, 10, 180)).toBeNull();
    expect(compararLinea(180.5, 0, 180.5)).toBeNull();
  });
});
