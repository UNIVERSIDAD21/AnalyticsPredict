/** Contrato exclusivo Euroliga; jamás llama a /api/analizar ni entrena al consultar. */
import { clienteAPI } from './api';
import type { PartidoResumen } from '../tipos';

export type MercadoEuro = 'Q1' | 'Q2' | 'Q3' | 'Q4' | 'COMPLETO';
export interface EvaluacionEuro {
  partidos: number; evaluados: number; abstenciones: number; cobertura: number | null;
  mercados: Record<string, { mae: number; mae_media_liga: number; brier_raw: number; n: number }>;
}
export interface EstadoEuro {
  version: string; corte_datos: string; fit_completed_at: string; partidos: number; equipos: number;
  dataset_sha256: string; min_partidos_equipo: number;
  validacion: { train_n: number; cal_util_n: number; evaluacion: EvaluacionEuro; limitacion: string };
}
export interface EquipoEuro { id: string; nombre: string; muestras: number; elegible: boolean }
export interface PeticionEuro {
  equipo_local: string; equipo_visitante: string; mercado: MercadoEuro; linea: number;
  partido_id?: string; parciales: [number, number][];
}
export interface PrediccionEuro {
  media_local: number; media_visitante: number; media_total: number; desviacion_total: number;
  intervalo_predictivo_80_raw: [number, number]; observado: boolean;
}
export interface ResultadoEuro {
  analisis_id: string; partido_id: string | null; fecha_partido: string | null;
  modelo_version: string; dataset_sha256: string; fecha_analisis: string; corte_datos: string;
  equipo_local: string; equipo_visitante: string; mercado: MercadoEuro; linea: number; modo: string;
  muestras: { local: number; visitante: number }; predicciones: Record<MercadoEuro, PrediccionEuro>;
  muestras_temporada: { local: number; visitante: number }; temporada_reciente: string;
  probabilidades: { over: number; under: number; push: number };
  ventaja_regulacion: { local: number; visitante: number; definicion: string };
  advertencias: string[]; prospectiva_acreditada_por_fecha: boolean;
  contexto: { uso: string; equipos: Record<string, { n_historico: number; media_regulacion: number | null;
    recientes: { id: string; fecha: string; rival: string; como_local: boolean; puntos_regulacion: number; puntos_rival_regulacion: number }[] }>;
    h2h: { fecha: string; local: string; visitante: string; local_total: number; visitante_total: number }[] };
}

export async function cargarEuroliga() {
  const [estado, equipos, partidos, historial] = await Promise.all([
    clienteAPI.get<EstadoEuro>('/api/euroliga/estado'),
    clienteAPI.get<{ equipos: EquipoEuro[] }>('/api/euroliga/equipos'),
    clienteAPI.get<{ partidos: PartidoResumen[]; ultimo_final_bd: string | null }>('/api/euroliga/partidos'),
    clienteAPI.get<{ analisis: ResultadoEuro[] }>('/api/euroliga/historial'),
  ]);
  return { estado: estado.data, equipos: equipos.data.equipos, partidos: partidos.data.partidos,
    ultimoFinal: partidos.data.ultimo_final_bd, historial: historial.data.analisis };
}
export async function analizarEuroliga(peticion: PeticionEuro): Promise<ResultadoEuro> {
  return (await clienteAPI.post<{ resultado: ResultadoEuro }>('/api/euroliga/analizar', peticion)).data.resultado;
}
