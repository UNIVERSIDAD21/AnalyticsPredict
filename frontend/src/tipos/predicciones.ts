/**
 * predicciones.ts — Tipos para historial de predicciones
 */

import type { MercadoMetricas, OrigenMetricas } from './metricas';

export type EstadoPrediccion = 'GANADA' | 'PERDIDA' | 'PUSH' | 'PENDIENTE';

export interface PrediccionHistorial {
  id: string;
  partido_id: string;
  fecha_partido: string;
  equipo_local: string;
  equipo_visitante: string;
  mercado: MercadoMetricas;
  lado: string;
  linea: number;
  probabilidad_raw: number | null;
  probabilidad_calibrada: number | null;
  probabilidad_usada: number | null;
  valor_real: number | null;
  estado: EstadoPrediccion;
  origen: OrigenMetricas;
}

export interface ResumenHistorialPredicciones {
  total: number;
  ganadas: number;
  perdidas: number;
  push: number;
  pendientes: number;
  win_rate: number | null;
}

export interface RespuestaHistorialPredicciones {
  exito: boolean;
  pagina: number;
  tamano: number;
  total: number;
  total_paginas: number;
  resumen: ResumenHistorialPredicciones;
  predicciones: PrediccionHistorial[];
}

export interface ParametrosHistorialPredicciones {
  mercado?: MercadoMetricas;
  estado?: EstadoPrediccion;
  origen?: OrigenMetricas;
  desde?: string;
  hasta?: string;
  pagina?: number;
  tamano?: number;
}
