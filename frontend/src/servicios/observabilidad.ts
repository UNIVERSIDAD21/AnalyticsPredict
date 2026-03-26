import { clienteAPI, extraerMensajeError } from './api';

const CACHE_TTL_MS = 60 * 1000;
const KEY_SALUD = 'observabilidad.salud';
const KEY_HTTP = 'observabilidad.http';

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

function leerCache<T>(key: string): T | null {
  if (typeof window === 'undefined') return null;
  const raw = window.sessionStorage.getItem(key);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as { ts: number; data: T };
    if (!parsed?.ts || Date.now() - parsed.ts > CACHE_TTL_MS) return null;
    return parsed.data;
  } catch {
    return null;
  }
}

function guardarCache<T>(key: string, data: T): void {
  if (typeof window === 'undefined') return;
  window.sessionStorage.setItem(key, JSON.stringify({ ts: Date.now(), data }));
}

export async function obtenerSaludBackend(forceRefresh = false): Promise<SaludBackend> {
  try {
    if (!forceRefresh) {
      const cached = leerCache<SaludBackend>(KEY_SALUD);
      if (cached) return cached;
    }

    const { data } = await clienteAPI.get<SaludBackend>('/salud');
    guardarCache(KEY_SALUD, data);
    return data;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

export async function obtenerObservabilidadHTTP(
  params?: {
    umbral_p95_ms?: number;
    umbral_error_rate?: number;
  },
  forceRefresh = false
): Promise<ObservabilidadHTTPResumen> {
  try {
    if (!forceRefresh) {
      const cached = leerCache<ObservabilidadHTTPResumen>(KEY_HTTP);
      if (cached) return cached;
    }

    const { data } = await clienteAPI.get<ObservabilidadHTTPResumen>('/api/interno/observabilidad-http', {
      params,
    });
    guardarCache(KEY_HTTP, data);
    return data;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}
