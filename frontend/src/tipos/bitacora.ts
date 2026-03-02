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


export interface ApuestaAnalizada {
  id: number;
  deporte: 'baloncesto' | 'futbol' | string;
  partido_id: string;
  mercado?: string | null;
  lado?: string | null;
  linea?: number | null;
  probabilidad_sistema?: number | null;
  confianza?: string | null;
  estado: string;
  resultado_outcome?: 'GANADA' | 'PERDIDA' | 'PUSH' | null;
  valor_real?: number | null;
  resultado_resumen?: string | null;
  creado_en?: string | null;
  actualizado_en?: string | null;
}

export interface RespuestaApuestasAnalizadas {
  exito: boolean;
  total: number;
  items: ApuestaAnalizada[];
}
