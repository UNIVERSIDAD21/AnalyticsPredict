import { clienteAPI, extraerMensajeError } from './api';

export interface SaludBackend {
  estado: string;
  timestamp: string;
  servicios: {
    api: string;
    modelo: string;
    equipos_en_modelo: number;
  };
}

export interface ObservabilidadHTTPResumen {
  exito: boolean;
  http: {
    requests_total: number;
    errors_5xx: number;
    error_rate: number;
    latency_p95_ms: number | null;
    samples: number;
  };
  uptime: {
    inicio: string;
    segundos: number;
  };
  umbrales: {
    latency_p95_ms: number;
    error_rate: number;
  };
  alertas: string[];
  timestamp: string;
}

export async function obtenerSaludBackend(): Promise<SaludBackend> {
  try {
    const { data } = await clienteAPI.get<SaludBackend>('/salud');
    return data;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

export async function obtenerObservabilidadHTTP(params?: {
  umbral_p95_ms?: number;
  umbral_error_rate?: number;
}): Promise<ObservabilidadHTTPResumen> {
  try {
    const { data } = await clienteAPI.get<ObservabilidadHTTPResumen>('/api/interno/observabilidad-http', {
      params,
    });
    return data;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}
