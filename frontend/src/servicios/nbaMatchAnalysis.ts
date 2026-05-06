import axios from 'axios';
import { clienteAPI, extraerMensajeError } from './api';

export type NbaMarket = 'FULL_GAME_TOTAL' | 'Q1_TOTAL' | 'HOME_TEAM_TOTAL' | 'AWAY_TEAM_TOTAL';
export type NbaSourceType = 'REAL_MARKET' | 'DERIVED_FROM_TOTAL_SPREAD' | 'TECHNICAL_ESTIMATE' | 'MANUAL_INPUT';

export interface NbaMarketInput {
  market: NbaMarket;
  line: number;
  over_odds: number | null;
  under_odds: number | null;
  source: string;
  source_type: NbaSourceType;
  source_url?: string | null;
  notes?: string | null;
}

export interface NbaMatchAnalysisRequest {
  home: string;
  away: string;
  date: string;
  markets: NbaMarketInput[];
}

export interface NbaStructuredWarning {
  code: string;
  severity: string;
  message: string;
  scope: string;
  market?: string;
  team?: string;
  details?: Record<string, unknown>;
}

export interface NbaMarketEvaluation {
  market: string;
  input?: NbaMarketInput;
  source?: string;
  source_type?: NbaSourceType;
  source_url?: string | null;
  notes?: string | null;
  evaluable?: boolean;
  promedio_combinado?: number;
  mediana_combinada?: number;
  diferencia_contra_linea?: number;
  volatilidad?: number;
  clasificacion_tecnica?: string;
  clasificacion?: string;
  porcentaje_cumplimiento_over?: Record<string, number>;
  porcentaje_cumplimiento_under?: Record<string, number>;
  resumen_muestras?: Record<string, unknown>;
  advertencias?: Array<NbaStructuredWarning | string>;
}

export interface NbaDataQualityBucket {
  valid?: unknown[];
  excluded?: unknown[];
  excluded_count?: number;
  valid_count?: number;
  reason_counts?: Record<string, number>;
  [key: string]: unknown;
}

export interface NbaMatchAnalysisResponse {
  ok: boolean;
  metadata: Record<string, unknown>;
  teams: {
    fecha?: string;
    fecha_maxima_disponible_bd?: string;
    equipo_local?: { abreviatura?: string; nombre?: string };
    equipo_visitante?: { abreviatura?: string; nombre?: string };
    [key: string]: unknown;
  };
  samples: {
    calidad_datos?: Record<string, NbaDataQualityBucket>;
    [key: string]: unknown;
  };
  combined_metrics: Record<string, unknown>;
  market_evaluations: NbaMarketEvaluation[];
  data_quality: Record<string, NbaDataQualityBucket>;
  warnings: NbaStructuredWarning[];
  external_summary: string;
  generated_files: unknown;
  policy: {
    no_picks: boolean;
    no_stake: boolean;
    no_betting_recommendations: boolean;
  };
}

export class NbaMatchAnalysisError extends Error {
  status?: number;
  details?: unknown;

  constructor(message: string, status?: number, details?: unknown) {
    super(message);
    this.name = 'NbaMatchAnalysisError';
    this.status = status;
    this.details = details;
  }
}

function formatearDetalle422(detail: unknown): string | null {
  if (typeof detail === 'string') return detail;
  if (!Array.isArray(detail)) return null;

  return detail
    .map((item) => {
      if (!item || typeof item !== 'object') return null;
      const registro = item as { loc?: Array<string | number>; msg?: string };
      const campo = Array.isArray(registro.loc) ? registro.loc.join('.') : 'campo';
      return `${campo}: ${registro.msg ?? 'valor inválido'}`;
    })
    .filter(Boolean)
    .join(' | ');
}

export async function generarAnalisisNba(
  payload: NbaMatchAnalysisRequest
): Promise<NbaMatchAnalysisResponse> {
  try {
    const respuesta = await clienteAPI.post<NbaMatchAnalysisResponse>('/api/nba/match-analysis', payload);
    return respuesta.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status;
      const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
      const detalle422 = status === 422 ? formatearDetalle422(detail) : null;
      const mensajeBase =
        status === 401 || status === 403
          ? 'No tienes autorización para usar esta herramienta interna.'
          : status === 422
            ? 'El backend rechazó el request por validación.'
            : extraerMensajeError(error);

      throw new NbaMatchAnalysisError(
        detalle422 ? `${mensajeBase} ${detalle422}` : mensajeBase,
        status,
        error.response?.data
      );
    }

    throw new NbaMatchAnalysisError(extraerMensajeError(error));
  }
}
