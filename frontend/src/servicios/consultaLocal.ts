import { clienteAPI } from './api';
export interface IdentidadLocal {
  modelo_version: number; dataset_hash: string | null; corte_modelo: string | null;
  modelo_generado_en: string; muestra_entrenamiento: number | null; incluye_ot: false;
}
export interface ConsultaLocal {
  formato: 'consulta-local-v1'; analisis_id: string; liga: 'nba'; equipo_local: string; equipo_visitante: string;
  periodo: string; linea: number; generado_en: string; modo: 'BASE_LOCAL'; metadata: IdentidadLocal;
  distribucion: { familia: 'normal_continua'; media: number; desviacion: number; origen: string; probabilidad_tipo: 'RAW' };
  probabilidad_over: number | null; probabilidad_under: number | null; probabilidad_push: number | null;
  motivo_nd: string | null; advertencias: string[];
}
export async function catalogoLocal(signal: AbortSignal) {
  return (await clienteAPI.get<{ equipos: string[]; metadata: IdentidadLocal }>('/api/local/nba/catalogo', { signal })).data;
}
export async function consultarLocal(p: { equipo_local: string; equipo_visitante: string; periodo: string; linea: number }, signal?: AbortSignal) {
  return (await clienteAPI.post<ConsultaLocal>('/api/local/nba/consultar', p, { signal })).data;
}
/** CDF aproximada (error absoluto < 1e-6). Comparador, no nueva salida del modelo. */
export function compararLinea(media: number, sigma: number, linea: number) {
  if (![media, sigma, linea].every(Number.isFinite) || sigma <= 0 || Math.abs((linea % 1) - 0.5) > 1e-9) return null;
  const z = (linea - media) / sigma, x = Math.abs(z), t = 1 / (1 + .2316419 * x);
  const cola = Math.exp(-x * x / 2) / Math.sqrt(2 * Math.PI) * t * (.319381530 + t * (-.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))));
  const over = Math.max(0, Math.min(1, z >= 0 ? cola : 1 - cola));
  return { over, under: 1 - over };
}
