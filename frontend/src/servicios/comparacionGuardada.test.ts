import { expect, it } from 'vitest';
import { compararMasa, validarMasa, validarTablaLineas, type MasaWnba } from './comparacionGuardada';
const d: MasaWnba = { formato: 'pmf-wnba-sobol-v1', mercado: 'COMPLETO', incluye_ot: true, simulaciones: 8,
  valores: [160, 161, 180], frecuencias: [2, 4, 2], probabilidad_tipo: 'SIN_CALIBRAR', sha256: 'sintetico' };
it('compara exactamente la masa retenida con push sin alterar su distribución', () => {
  const original = JSON.stringify(d);
  expect(compararMasa(d, 161)).toEqual({ over: .25, under: .25, push: .5 });
  expect(compararMasa(d, 161.5)).toEqual({ over: .25, under: .75, push: 0 });
  expect(compararMasa(d, 0)).toEqual({ over: 1, under: 0, push: 0 });
  expect(JSON.stringify(d)).toBe(original);
  expect(compararMasa(d, 161.25)).toBeNull();
});
it('no normaliza silenciosamente frecuencias dañadas, negativos o soportes duplicados', () => {
  expect(validarMasa({ ...d, simulaciones: 9 })).toBeNull();
  expect(validarMasa({ ...d, valores: [160, 160, 180] })).toBeNull();
  expect(validarMasa({ ...d, frecuencias: [-2, 8, 2] })).toBeNull();
  expect(validarMasa(null)).toBeNull();
});
it('conserva ausencias y rechaza tablas sin fuente ni probabilidades válidas', () => {
  const tabla = { formato: 'lineas-originales-futbol-v1', mercado: 'GOLES_FT', lineas: [{ linea: 2, over: .4, under: .6, push: null, fuente: 'RAW', calibrador: null }] };
  expect(validarTablaLineas(tabla)?.lineas[0].push).toBeNull();
  expect(validarTablaLineas({ ...tabla, lineas: [tabla.lineas[0], tabla.lineas[0]] })).toBeNull();
  expect(validarTablaLineas({ ...tabla, lineas: [{ ...tabla.lineas[0], over: Number.NaN }] })).toBeNull();
});
