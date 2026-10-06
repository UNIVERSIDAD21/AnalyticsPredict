import { describe, expect, it } from 'vitest';
import type { ProbabilidadLinea } from '../tipos/futbol';
import { resolverProbabilidadFutbol } from './probabilidadFutbol';

const base: ProbabilidadLinea = {
  linea: 2.5, overRaw: 0.2, underRaw: 0.8,
  overCalibrada: 0.7, underCalibrada: 0.3,
};

describe('probabilidad fútbol con procedencia', () => {
  it('rechaza el nombre calibrated si no hay ID', () => {
    expect(resolverProbabilidadFutbol(base)).toEqual({ over: 0.2, under: 0.8, fuente: 'RAW' });
  });

  it('usa la transformación cuando hay ID y ambas probabilidades', () => {
    expect(resolverProbabilidadFutbol({ ...base, calibradorId: 'cal-1' })).toEqual({ over: 0.7, under: 0.3, fuente: 'CALIBRADA' });
  });

  it('conserva raw ante calibración incompleta', () => {
    expect(resolverProbabilidadFutbol({ ...base, calibradorId: 'cal-1', underCalibrada: null })).toEqual({ over: 0.2, under: 0.8, fuente: 'RAW' });
  });
});
