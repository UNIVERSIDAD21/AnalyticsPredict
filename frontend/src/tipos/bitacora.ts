// hace parte del diseño de analisis
/**
 * bitacora.ts — Tipos para bitácora de apuestas
 */

import { LadoApuesta, Mercado, NivelConfianza } from './analisis';

export type ResultadoApuesta = 'PENDIENTE' | 'GANADA' | 'PERDIDA' | 'PUSH' | 'ANULADA';

export interface Apuesta {
  id: string;
  usuario_id: string;
  partido_id?: string | null;
  equipo_local: string;
  equipo_visitante: string;
  fecha_partido?: string | null;
  mercado: Mercado;
  lado: LadoApuesta;
  linea: number;
  cuota: number;
  stake: number;
  probabilidad_sistema?: number | null;
  confianza_sistema?: NivelConfianza | null;
  valor_esperado?: number | null;
  prediccion_media?: number | null;
  prediccion_desviacion?: number | null;
  razones?: unknown;
  resultado: ResultadoApuesta;
  puntos_reales?: number | null;
  ganancia: number;
  fecha_resolucion?: string | null;
  creado_en?: string | null;
  actualizado_en?: string | null;
}

export interface RespuestaApuesta {
  exito: boolean;
  apuesta: Apuesta;
}

export interface RespuestaListaApuestas {
  exito: boolean;
  total: number;
  pagina: number;
  total_paginas: number;
  apuestas: Apuesta[];
}

export interface RespuestaResumenApuestas {
  exito: boolean;
  resumen: Record<string, unknown>;
}

export interface PeticionCrearApuesta {
  partido_id?: string | null;
  equipo_local: string;
  equipo_visitante: string;
  fecha_partido?: string | null;
  mercado: Mercado;
  lado: LadoApuesta;
  linea: number;
  cuota: number;
  cuota_over?: number | null;
  cuota_under?: number | null;
  stake: number;
  probabilidad_sistema: number;
  confianza_sistema: NivelConfianza;
  valor_esperado?: number | null;
  prediccion_media?: number | null;
  prediccion_desviacion?: number | null;
  razones: Array<Record<string, unknown>>;

  // ════════════════════════════════════════════════════════════
  // Campos de De-Vig (P1)
  // ════════════════════════════════════════════════════════════
  devig_metodo?: string | null;
  modo_devig?: string | null;
  devig_overround?: number | null;
  devig_p_mkt_raw?: number | null;
  devig_p_mkt_fair?: number | null;
  devig_advertencias?: string[] | null;
  edge_real?: number | null;

  // ════════════════════════════════════════════════════════════
  // Campos de Score (P1)
  // ════════════════════════════════════════════════════════════
  score_total?: number | null;
  score_componentes?: Record<string, number> | null;
  score_explicacion?: string | null;
  score_penalizaciones?: string[] | null;

  // ════════════════════════════════════════════════════════════
  // Campos de Sizing/Kelly (P1)
  // ════════════════════════════════════════════════════════════
  kelly_full?: number | null;
  kelly_fraccional?: number | null;
  fraccion_kelly?: number | null;
  stake_porcentaje?: number | null;
  bankroll_momento?: number | null;
  perfil_riesgo_usado?: string | null;
  sizing_advertencias?: string[] | null;
  sizing_penalizaciones?: Record<string, number> | null;
}

export interface PeticionActualizarResultado {
  resultado: Exclude<ResultadoApuesta, 'PENDIENTE'>;
  puntos_reales?: number | null;
}

// ══════════════════════════════════════════════════════════════
// Tipos para métricas de bitácora
// ══════════════════════════════════════════════════════════════

export interface MetricaMercadoBitacora {
  mercado: Mercado;
  total: number;
  ganadas: number;
  perdidas: number;
  push: number;
  win_rate: number | null;
  stake_total: number;
  ganancia_total: number;
  roi: number | null;
  edge_promedio: number | null;
  probabilidad_promedio: number | null;
}

export interface MetricaConfianzaBitacora {
  confianza: NivelConfianza;
  total: number;
  ganadas: number;
  perdidas: number;
  win_rate: number | null;
  stake_total: number;
  ganancia_total: number;
  roi: number | null;
}

export interface MetricaTemporalBitacora {
  periodo: string;
  total: number;
  ganadas: number;
  perdidas: number;
  win_rate: number | null;
  ganancia: number;
  roi: number | null;
}

export interface ResumenGlobalBitacora {
  total: number;
  ganadas: number;
  perdidas: number;
  push: number;
  win_rate: number | null;
  stake_total: number;
  ganancia_total: number;
  roi: number | null;
  edge_promedio: number | null;
  probabilidad_promedio: number | null;
}

export interface RespuestaMetricasBitacora {
  exito: boolean;
  periodo: {
    desde: string;
    hasta: string;
  };
  resumen_global: ResumenGlobalBitacora;
  por_mercado: MetricaMercadoBitacora[];
  por_confianza: MetricaConfianzaBitacora[];
  por_mes: MetricaTemporalBitacora[];
  advertencias: string[];
}
