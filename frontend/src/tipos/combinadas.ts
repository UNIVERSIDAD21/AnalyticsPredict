/**
 * combinadas.ts — Tipos para apuestas combinadas
 */

import { NivelConfianza } from './analisis';
import { ResultadoApuesta } from './bitacora';

export type ResultadoCombinada = 'PENDIENTE' | 'GANADA' | 'PERDIDA' | 'PUSH';

export interface SeleccionCombinadaInput {
  partido_id?: string | null;
  equipo_local: string;
  equipo_visitante: string;
  fecha_partido?: string | null;
  mercado: 'Q1' | 'Q2' | 'Q3' | 'Q4' | 'COMPLETO';
  lado: 'OVER' | 'UNDER';
  linea: number;
  cuota: number;
  cuota_over?: number | null;
  cuota_under?: number | null;
  probabilidad_sistema: number;
  prediccion_media?: number | null;
  prediccion_desviacion?: number | null;
  confianza_sistema?: NivelConfianza | null;
  valor_esperado_individual?: number | null;
  razones?: Array<Record<string, unknown>> | null;
}

export interface SeleccionCombinada extends SeleccionCombinadaInput {
  id: string;
  combinada_id: string;
  grupo_correlacion?: number | null;
  factor_ajuste_correlacion?: number | null;
  resultado?: ResultadoApuesta | null;
  puntos_reales?: number | null;
  fecha_resolucion?: string | null;
  orden: number;
}

export interface Combinada {
  id: string;
  usuario_id: string;
  stake: number;
  cuota_total: number;
  n_selecciones: number;
  probabilidad_independiente: number;
  factor_correlacion: number;
  probabilidad_ajustada: number;
  cuota_justa_sistema?: number | null;
  edge_combinada?: number | null;
  valor_esperado?: number | null;
  confianza_sistema?: NivelConfianza | null;
  tiene_mismo_partido: boolean;
  n_partidos_unicos: number;
  advertencias?: string[] | null;
  correlaciones_detectadas?: Array<Record<string, unknown>> | null;
  resultado: ResultadoCombinada;
  ganancia: number;
  selecciones_ganadas: number;
  selecciones_perdidas: number;
  selecciones_push: number;
  selecciones_pendientes: number;
  fecha_resolucion?: string | null;
  notas?: string | null;
  etiquetas?: string[] | null;
  creado_en?: string | null;
  actualizado_en?: string | null;
  selecciones?: SeleccionCombinada[];
}

export interface PeticionCrearCombinada {
  stake: number;
  cuota_total: number;
  selecciones: SeleccionCombinadaInput[];
  notas?: string | null;
  etiquetas?: string[] | null;
}

export interface RespuestaCombinada {
  exito: boolean;
  combinada: Combinada;
}

export interface RespuestaListaCombinadas {
  exito: boolean;
  total: number;
  pagina: number;
  total_paginas: number;
  combinadas: Combinada[];
}

export type TipoApuesta = 'SIMPLE' | 'COMBINADA';

export interface RegistroBitacoraUnificada {
  id: string;
  tipo_apuesta: TipoApuesta;
  resultado: ResultadoApuesta | ResultadoCombinada;
  stake: number;
  ganancia: number;
  cuota?: number | null;
  cuota_total?: number | null;
  n_selecciones?: number | null;
  selecciones_ganadas?: number | null;
  selecciones_perdidas?: number | null;
  selecciones_push?: number | null;
  selecciones_pendientes?: number | null;
  tiene_mismo_partido?: boolean | null;
  factor_correlacion?: number | null;
  advertencias?: string[] | null;
  equipo_local?: string | null;
  equipo_visitante?: string | null;
  fecha_partido?: string | null;
  mercado?: string | null;
  lado?: string | null;
  linea?: number | null;
  probabilidad_sistema?: number | null;
  confianza_sistema?: NivelConfianza | null;
  valor_esperado?: number | null;
  creado_en?: string | null;
  actualizado_en?: string | null;
  selecciones?: SeleccionCombinada[] | null;
}

export interface RespuestaBitacoraUnificada {
  exito: boolean;
  total: number;
  pagina: number;
  total_paginas: number;
  registros: RegistroBitacoraUnificada[];
}
