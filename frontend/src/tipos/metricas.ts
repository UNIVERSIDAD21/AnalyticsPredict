/**
 * metricas.ts — Tipos para métricas de calibración
 */

export type OrigenMetricas = 'API_USUARIO' | 'BACKTEST_SINTETICO' | 'BACKTEST_BATCH';

export type MercadoMetricas = 'Q1' | 'Q2' | 'Q3' | 'Q4' | 'COMPLETO';

export interface MetricaMercado {
  mercado: MercadoMetricas;
  n_predicciones: number;
  n_excluidos_push: number;
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
  metricas_por_mercado: MetricaMercado[];
  alertas_activas: Record<string, unknown>[];
  timestamp_calculo: string;
}

export interface ParametrosMetricasCalibracion {
  origen: OrigenMetricas;
  mercado?: MercadoMetricas;
  desde?: string;
  hasta?: string;
  modelo_version_id?: number;
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
  bins: BinCalibracion[];
  ece: number;
  mce: number;
  bin_peor_calibrado: string | null;
  linea_perfecta: Array<{ x: number; y: number }>;
  periodo: {
    inicio: string;
    fin: string;
  };
  timestamp_calculo: string;
}

export interface ParametrosCurvaCalibracion {
  mercado: MercadoMetricas;
  origen: OrigenMetricas;
  tipo_bins?: 'fijos' | 'cuantiles';
  n_bins?: number;
  desde?: string;
  hasta?: string;
}
