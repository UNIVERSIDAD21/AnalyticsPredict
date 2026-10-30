import { expect, it } from 'vitest';
import { validarInformeExperimento } from './informeExperimento';
function informe() {
  const tabla = Object.fromEntries(['Q1', 'Q2', 'Q3', 'Q4', 'COMPLETO'].map(k => [k, { n: 10, mae: 2, brier_binario: .25, cobertura_intervalo80_raw: .7 }]));
  return { formato: 'experimento-wnba-contraccion-v1', activado: false, refit_final: null, prospectivos: 0, limitacion: 'Sintético para validar contratos, no eficacia.',
    snapshot: { publicacion: 'sintetico', dataset_sha256: 'a'.repeat(64), corte_exclusivo: '2025-01-01' }, cobertura: { denominador: 10, experimento: 10, original: 10, comunes: 10 },
    seleccion: { elegida: { k: 0, semivida_dias: 730 } }, tabla_comun: { experimento: tabla, original: tabla, media_liga: tabla, delta_original_ic95: {} },
    tabla_ampliada: { experimento: tabla, media_liga: tabla, por_soporte: {} } };
}
it('separa tablas comunes y ampliadas y admite diagnósticos extra del informe real', () => {
  const r = validarInformeExperimento(informe());
  expect(Object.keys(r.tabla_comun)).toEqual(['experimento', 'original', 'media_liga']);
  expect(Object.keys(r.tabla_ampliada)).toEqual(['experimento', 'media_liga']);
});
it('rechaza denominadores inconsistentes y no interpreta un modelo activo como experimento', () => {
  const r = informe(); r.cobertura.comunes = 11;
  expect(() => validarInformeExperimento(r)).toThrow('incompatible');
  expect(() => validarInformeExperimento({ ...informe(), activado: true })).toThrow();
  const sinOriginal = informe(); sinOriginal.tabla_comun.original = {};
  expect(() => validarInformeExperimento(sinOriginal)).toThrow();
  expect(() => validarInformeExperimento(null)).toThrow();
});
