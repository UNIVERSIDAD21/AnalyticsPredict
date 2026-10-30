export interface MasaWnba {
  formato: 'pmf-wnba-sobol-v1'; mercado: string; incluye_ot: boolean;
  simulaciones: number; valores: number[]; frecuencias: number[]; sha256: string;
  probabilidad_tipo: 'SIN_CALIBRAR';
}
export interface LineaConservada {
  linea: number; over: number | null; under: number | null; push: number | null;
  fuente: 'RAW' | 'CALIBRADA'; calibrador: string | null;
}
export interface TablaLineas {
  formato: 'lineas-originales-futbol-v1'; mercado: string; lineas: LineaConservada[];
}
export function validarMasa(valor: unknown): MasaWnba | null {
  const d = valor as MasaWnba;
  if (!d || d.formato !== 'pmf-wnba-sobol-v1' || typeof d.mercado !== 'string' || typeof d.incluye_ot !== 'boolean' || d.probabilidad_tipo !== 'SIN_CALIBRAR' ||
      !Number.isSafeInteger(d.simulaciones) || d.simulaciones <= 0 || d.simulaciones > 10_000_000 ||
      !Array.isArray(d.valores) || !Array.isArray(d.frecuencias) || !d.valores.length || d.valores.length > 2000 || d.valores.length !== d.frecuencias.length ||
      !d.valores.every((v, i) => Number.isSafeInteger(v) && v >= 0 && (i === 0 || v > d.valores[i - 1])) ||
      !d.frecuencias.every(v => Number.isSafeInteger(v) && v > 0) || d.frecuencias.reduce((s, n) => s + n, 0) !== d.simulaciones) return null;
  return d;
}
export function compararMasa(valor: unknown, linea: number) {
  const d = validarMasa(valor);
  if (!d || !Number.isFinite(linea) || linea < 0 || linea > 600 || !Number.isInteger(2 * linea)) return null;
  let over = 0, under = 0, push = 0;
  d.valores.forEach((v, i) => { if (v > linea) over += d.frecuencias[i]; else if (v < linea) under += d.frecuencias[i]; else push += d.frecuencias[i]; });
  return { over: over / d.simulaciones, under: under / d.simulaciones, push: push / d.simulaciones };
}
export function validarTablaLineas(valor: unknown): TablaLineas | null {
  const d = valor as TablaLineas;
  const prob = (v: unknown) => v === null || (typeof v === 'number' && Number.isFinite(v) && v >= 0 && v <= 1);
  if (!d || d.formato !== 'lineas-originales-futbol-v1' || typeof d.mercado !== 'string' || !Array.isArray(d.lineas) || d.lineas.length > 200 ||
      !d.lineas.every(l => l && Number.isFinite(l.linea) && l.linea >= 0 && prob(l.over) && prob(l.under) && prob(l.push) &&
        ['RAW', 'CALIBRADA'].includes(l.fuente) && (l.calibrador === null || typeof l.calibrador === 'string') &&
        (l.fuente !== 'CALIBRADA' || (typeof l.calibrador === 'string' && l.calibrador.length > 0))) ||
      new Set(d.lineas.map(l => l.linea)).size !== d.lineas.length) return null;
  return d;
}
