/**
 * metricas.ts — Tipos para métricas de calibración
 */

import type { AlertaCalibracion } from './alertas';

export type OrigenMetricas = 'API_USUARIO' | 'BACKTEST_SINTETICO' | 'BACKTEST_BATCH';

export type SerieProbabilidad = 'raw' | 'calibrada';

export type MercadoMetricas = 'Q1' | 'Q2' | 'Q3' | 'Q4' | 'COMPLETO';

export interface MetricaMercado {
  mercado: MercadoMetricas;
  n_predicciones: number;
  n_raw: number;
  n_calibradas: number;
  n_excluidas_probabilidad: number;
  serie: SerieProbabilidad;
  estado_calidad: 'VALIDO_DESCRIPTIVO' | 'NO_EVALUABLE';
  periodo: { inicio?: string; fin?: string };
  n_excluidos_push: number;
  n_excluidos_outcome_dudoso: number;
  brier_score: number | null;
  brier_score_raw: number | null;
  brier_score_calibrado: number | null;
  log_loss: number | null;
  ece: number | null;
  mce: number | null;
  mae_media: number | null;
  rmse_media: number | null;
  sesgo_media: number | null;
  calibrador_activo: string | null;
  calibrador_id: string | null;
  mejora_vs_raw: number | null;
  base_rate: number | null;
  sharpness: number | null;
  suficiente_data: boolean;
  advertencias: string[];
}

export interface RespuestaMetricasCalibracion {
  exito: boolean;
  origen: OrigenMetricas;
  periodo: {
    inicio: string;
    fin: string;
  };
  modelo_version_id: number | null;
  serie: SerieProbabilidad;
  certificacion: 'NO_CERTIFICADO';
  cache: 'SIN_CACHE';
  metricas_por_mercado: MetricaMercado[];
  alertas_activas: AlertaCalibracion[];
  timestamp_calculo: string;
}

export interface ParametrosMetricasCalibracion {
  origen: OrigenMetricas;
  mercado?: MercadoMetricas;
  desde?: string;
  hasta?: string;
  modelo_version_id?: number;
  serie?: SerieProbabilidad;
}

export interface BinCalibracion {
  rango_inicio: number;
  rango_fin: number;
  n: number;
  probabilidad_promedio: number;
  frecuencia_real: number;
  gap: number;
  gap_con_signo: number;
  suficiente_data: boolean;
  advertencia?: string | null;
}

export interface RespuestaCurvaCalibracion {
  exito: boolean;
  mercado: MercadoMetricas;
  origen: OrigenMetricas;
  tipo_bins: 'fijos' | 'cuantiles';
  n_bins: number;
  n_predicciones_total: number;
  n_excluidos_push: number;
  n_excluidos_outcome_dudoso: number;
  bins: BinCalibracion[];
  ece: number | null;
  mce: number | null;
  n_excluidas_probabilidad: number;
  serie: SerieProbabilidad;
  modelo_version_id: number | null;
  estado_calidad: 'VALIDO_DESCRIPTIVO' | 'NO_EVALUABLE';
  certificacion: 'NO_CERTIFICADO';
  cache: 'SIN_CACHE';
  bin_peor_calibrado: string | null;
  linea_perfecta: Array<{ x: number; y: number }>;
  periodo: {
    inicio: string;
    fin: string;
  };
  timestamp_calculo: string;
}

export interface ParametrosCurvaCalibracion {
  serie?: SerieProbabilidad;
  modelo_version_id?: number;
  mercado: MercadoMetricas;
  origen: OrigenMetricas;
  tipo_bins?: 'fijos' | 'cuantiles';
  n_bins?: number;
  desde?: string;
  hasta?: string;
}

export interface RespuestaRecalibracion {
  exito: boolean;
  calibrador_id: string | null;
  creado: boolean;
  mensaje: string;
  detalle: Record<string, unknown>;
}

export interface RespuestaResolverAlerta {
  exito: boolean;
  alerta_id: string | null;
  resuelta: boolean;
  mensaje: string;
}
