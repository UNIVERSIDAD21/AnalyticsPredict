import { expect, it } from 'vitest';
import type { ResultadoVista } from '../tipos/resultadoVista';
import { salidaPrincipalNba } from './salidaPrincipalNba';
const resultado = () => ({
  metadata: { mercado: 'COMPLETO' }, es_en_vivo: false, linea_analizada: 220.5,
  predicciones: {}, prediccion_juego_completo: { media_total: 218, desviacion_total: 16.9, linea_analizada: 220.5, probabilidad_over: .44, probabilidad_under: .56 },
  probabilidad_over: .44, probabilidad_under: .56,
  prediccion_ajustada: { media_ajustada: 230, desviacion_base: 16.9, probabilidad_over_ajustada: .72, probabilidad_under_ajustada: .28 },
  mejor_apuesta_detalle: { prediccion_media: 999, prediccion_desviacion: 99, p_calibrada: .99 },
}) as unknown as ResultadoVista;
it('usa parámetros y probabilidades de una sola distribución, no candidatos/contexto', () => {
  const r = resultado(), antes = JSON.stringify(r);
  const p = salidaPrincipalNba(r, 'COMPLETO', 220.5);
  expect(p).toMatchObject({ media: 218, desviacion: 16.9, over: .44, under: .56, push: 0, motivo: null });
  expect(p.origen).toContain('Base NBA'); expect(JSON.stringify(r)).toBe(antes);
});
it('no transfiere una probabilidad a otra línea ni inventa masa discreta para enteras', () => {
  const r = resultado();
  expect(salidaPrincipalNba(r, 'COMPLETO', 230.5)).toMatchObject({ over: null, under: null });
  const entero = salidaPrincipalNba(r, 'COMPLETO', 220);
  expect(entero).toMatchObject({ media: 218, desviacion: 16.9, over: null, under: null, push: null });
  expect(salidaPrincipalNba(r, 'Q3', 55.5)).toMatchObject({ media: null, over: null, under: null });
});
it('identifica corte y no completa un lado ausente ni un porcentaje inválido', () => {
  const r = resultado(); r.es_en_vivo = true; r.prediccion_juego_completo!.probabilidad_under = null;
  expect(salidaPrincipalNba(r, 'COMPLETO', 220.5)).toMatchObject({ over: .44, under: null });
  expect(salidaPrincipalNba(r, 'COMPLETO', 220.5).origen).toContain('heurística de cierre');
  r.prediccion_juego_completo!.probabilidad_over = 2;
  expect(salidaPrincipalNba(r, 'COMPLETO', 220.5).over).toBeNull();
});
