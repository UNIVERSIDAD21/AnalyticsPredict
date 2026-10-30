const MERCADOS = ['Q1', 'Q2', 'Q3', 'Q4', 'COMPLETO'];
interface Medida { n: number; mae: number; brier_binario: number; cobertura_intervalo80_raw: number }
export interface InformeExperimento {
  formato: string; activado: false; refit_final: null; prospectivos: 0; limitacion: string;
  snapshot: { publicacion: string; dataset_sha256: string; corte_exclusivo: string };
  cobertura: { denominador: number; experimento: number; original: number; comunes: number };
  seleccion: { elegida: { k: number; semivida_dias: number | null } };
  tabla_comun: { experimento: Record<string, Medida>; original: Record<string, Medida>; media_liga: Record<string, Medida> };
  tabla_ampliada: { experimento: Record<string, Medida>; media_liga: Record<string, Medida> };
}
export function validarInformeExperimento(valor: unknown): InformeExperimento {
  const r = valor as InformeExperimento;
  const fallo = () => { throw new Error('Evaluación incompatible o incompleta; no se cargó como modelo.'); };
  if (!r || r.formato !== 'experimento-wnba-contraccion-v1' || r.activado !== false || r.refit_final !== null || r.prospectivos !== 0 ||
      typeof r.limitacion !== 'string' || typeof r.snapshot?.publicacion !== 'string' || !/^[a-f0-9]{64}$/.test(r.snapshot?.dataset_sha256) ||
      typeof r.snapshot?.corte_exclusivo !== 'string' || !r.cobertura || !r.seleccion?.elegida) fallo();
  const c = r.cobertura;
  if (![0, 8, 24].includes(r.seleccion.elegida.k) || ![null, 365, 730].includes(r.seleccion.elegida.semivida_dias)) fallo();
  if (![c.denominador, c.experimento, c.original, c.comunes].every(v => Number.isInteger(v) && v >= 0) ||
      c.denominador < 1 || c.experimento > c.denominador || c.original > c.denominador || c.comunes > Math.min(c.experimento, c.original)) fallo();
  const tablas = [r.tabla_comun?.experimento, r.tabla_comun?.original, r.tabla_comun?.media_liga, r.tabla_ampliada?.experimento, r.tabla_ampliada?.media_liga];
  tablas.forEach((tabla, indice) => {
    for (const mercado of MERCADOS) {
      const m = tabla?.[mercado], n = indice < 3 ? c.comunes : c.experimento;
      if (!m || m.n !== n || !Number.isFinite(m.mae) || m.mae < 0 || !Number.isFinite(m.brier_binario) || m.brier_binario < 0 || m.brier_binario > 1 ||
          !Number.isFinite(m.cobertura_intervalo80_raw) || m.cobertura_intervalo80_raw < 0 || m.cobertura_intervalo80_raw > 1) fallo();
    }
  });
  // Solo datos de presentación validados: se descartan extras, no se ejecuta código.
  const tabla = (t: Record<string, Medida>) => Object.fromEntries(MERCADOS.map(k => [k, t[k]]));
  return { ...r, tabla_comun: { experimento: tabla(r.tabla_comun.experimento), original: tabla(r.tabla_comun.original), media_liga: tabla(r.tabla_comun.media_liga) },
    tabla_ampliada: { experimento: tabla(r.tabla_ampliada.experimento), media_liga: tabla(r.tabla_ampliada.media_liga) } };
}
