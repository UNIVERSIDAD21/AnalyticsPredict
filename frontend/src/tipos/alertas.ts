/**
 * alertas.ts — Tipos para alertas de calibración
 */

import type { MercadoMetricas, OrigenMetricas } from './metricas';

export type SeveridadAlerta = 'INFO' | 'WARNING' | 'CRITICAL';

export interface AlertaCalibracion {
  id: string;
  timestamp_deteccion: string;
  periodo_inicio: string | null;
  periodo_fin: string | null;
  mercado: MercadoMetricas;
  origen: OrigenMetricas;
  tipo_alerta: string;
  severidad: SeveridadAlerta;
  metrica_afectada: string;
  valor_actual: number | null;
  valor_umbral: number | null;
  valor_baseline: number | null;
  mensaje?: string | null;
  detalles_json?: Record<string, unknown> | null;
  resuelta: boolean;
}
