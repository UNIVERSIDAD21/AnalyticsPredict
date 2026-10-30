import { clienteAPI } from './api';
export type LigaBaseLocal = 'nba' | 'euroliga' | 'wnba';
export interface EquipoBaseLocal { clave: string; nombre: string; id?: string; muestra?: number; disponible: boolean }
export interface IdentidadLocal {
  modelo_version: number | string; dataset_hash: string | null; corte_modelo: string | null;
  modelo_generado_en: string | null; muestra_entrenamiento: number | null; incluye_ot: false;
  minutos_regulacion?: number; alcance?: string; ajuste_version?: string; publicacion_dataset_hash?: string;
}
export interface ConsultaLocal {
  formato: 'consulta-local-v1' | 'consulta-local-v2'; analisis_id: string; liga: LigaBaseLocal; equipo_local: string; equipo_visitante: string;
  equipo_local_id?: string; equipo_visitante_id?: string;
  periodo: string; linea: number; generado_en: string; modo: 'BASE_LOCAL'; metadata: IdentidadLocal;
  distribucion: { familia: 'normal_continua' | 'normal_discretizada'; media: number; desviacion: number; origen: string; probabilidad_tipo: 'RAW' };
  probabilidad_over: number | null; probabilidad_under: number | null; probabilidad_push: number | null;
  motivo_nd: string | null; advertencias: string[];
}
export async function catalogoLocal(signal: AbortSignal, liga: LigaBaseLocal = 'nba') {
  return (await clienteAPI.get<{ equipos: (string | EquipoBaseLocal)[]; metadata: IdentidadLocal }>(`/api/local/${liga}/catalogo`, { signal })).data;
}
export async function consultarLocal(p: { equipo_local: string; equipo_visitante: string; periodo: string; linea: number }, signal?: AbortSignal, liga: LigaBaseLocal = 'nba') {
  return (await clienteAPI.post<ConsultaLocal>(`/api/local/${liga}/consultar`, p, { signal })).data;
}
/** CDF aproximada (error absoluto < 1e-6). Comparador, no nueva salida del modelo. */
function colaNormal(z: number) {
  const x = Math.abs(z), t = 1 / (1 + .2316419 * x);
  const cola = Math.exp(-x * x / 2) / Math.sqrt(2 * Math.PI) * t * (.319381530 + t * (-.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))));
  return Math.max(0, Math.min(1, z >= 0 ? cola : 1 - cola));
}
export function compararLinea(media: number, sigma: number, linea: number) {
  if (![media, sigma, linea].every(Number.isFinite) || sigma <= 0 || Math.abs((linea % 1) - 0.5) > 1e-9) return null;
  const over = colaNormal((linea - media) / sigma);
  return { over, under: 1 - over };
}
/** Contrato Euroliga: normal discretizada, distinta de la normal continua NBA. */
export function compararNormalDiscreta(media: number, sigma: number, linea: number) {
  if (![media, sigma, linea].every(Number.isFinite) || media < 0 || sigma < 0 || linea < 0 || linea > 600 || !Number.isInteger(2 * linea)) return null;
  if (sigma * sigma <= 1e-10) return { over: Number(media > linea), under: Number(media < linea), push: Number(media === linea) };
  const over = colaNormal((Math.floor(linea) + .5 - media) / sigma);
  const under = Number.isInteger(linea) ? 1 - colaNormal((Math.ceil(linea) - .5 - media) / sigma) : 1 - over;
  return { over, under, push: Number.isInteger(linea) ? Math.max(0, 1 - over - under) : 0 };
}
