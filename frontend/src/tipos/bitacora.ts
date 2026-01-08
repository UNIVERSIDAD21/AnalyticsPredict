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
  stake: number;
  probabilidad_sistema: number;
  confianza_sistema: NivelConfianza;
  valor_esperado?: number | null;
  prediccion_media?: number | null;
  prediccion_desviacion?: number | null;
  razones: Array<Record<string, unknown>>;
}

export interface PeticionActualizarResultado {
  resultado: Exclude<ResultadoApuesta, 'PENDIENTE'>;
  puntos_reales?: number | null;
}
