import type { ProbabilidadLinea } from '../tipos/futbol';

/** Una p_cal sin ID trazable nunca sustituye a la raw en la interfaz. */
export function resolverProbabilidadFutbol(linea: ProbabilidadLinea): {
  over: number;
  under: number;
  fuente: 'CALIBRADA' | 'RAW';
} {
  const verificada = Boolean(linea.calibradorId && linea.overCalibrada !== null && linea.underCalibrada !== null);
  return verificada
    ? { over: linea.overCalibrada ?? linea.overRaw, under: linea.underCalibrada ?? linea.underRaw, fuente: 'CALIBRADA' }
    : { over: linea.overRaw, under: linea.underRaw, fuente: 'RAW' };
}
