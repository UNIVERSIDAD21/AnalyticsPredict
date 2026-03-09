import { clienteAPI, extraerMensajeError } from './api';

export type EstadoDeuda = 'ACTIVO' | 'EN_PROCESO' | 'EN_MIGRACION' | string;

export interface ScorecardDominio {
  periodo?: string;
  score_final?: number;
  nivel?: 'A' | 'B' | 'C' | 'UNKNOWN' | string;
  criticas_activas?: number;
  drift_penalty?: number;
  partial_penalty?: number;
}

export interface EstadoSistema {
  exito: boolean;
  feature_flags: Record<string, boolean>;
  scorecard_actual: {
    NBA: ScorecardDominio | null;
    FUTBOL: ScorecardDominio | null;
  };
  alertas_criticas_activas: {
    NBA: number;
    FUTBOL: number;
  };
  version_contrato: string;
  deuda_residual_b05: {
    confidence_parcial: EstadoDeuda;
    contratos_legacy_coexistentes: EstadoDeuda;
    drift_futbol_parcial_alto: EstadoDeuda;
  };
}

export async function obtenerEstadoSistema(): Promise<EstadoSistema> {
  try {
    const { data } = await clienteAPI.get<EstadoSistema>('/api/calidad/estado-sistema');
    return data;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}
