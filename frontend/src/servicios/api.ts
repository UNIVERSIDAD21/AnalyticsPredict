/**
 * api.ts — Cliente HTTP base para comunicación con el backend
 */

import axios, {
  AxiosError,
  AxiosHeaders,
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from 'axios';
import { ErrorAPI } from '../tipos';

// ══════════════════════════════════════════════════════════════
// CONFIGURACIÓN
// ══════════════════════════════════════════════════════════════

/**
 * URL base del backend desde variables de entorno
 */
const URL_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Tiempo máximo de espera para peticiones (ms)
 */
const TIMEOUT = 30000;

/**
 * Obtiene el ID del usuario autenticado para la bitácora
 */
function obtenerUsuarioId(): string | null {
  const idEnv = import.meta.env.VITE_USUARIO_ID as string | undefined;
  const idStorage = typeof window !== 'undefined' ? window.localStorage.getItem('usuarioId') : null;
  return idStorage || idEnv || null;
}

function obtenerAccessToken(): string | null {
  return typeof window !== 'undefined' ? window.localStorage.getItem('auth.accessToken') : null;
}

function obtenerRefreshToken(): string | null {
  return typeof window !== 'undefined' ? window.localStorage.getItem('auth.refreshToken') : null;
}

function guardarTokens(accessToken: string, refreshToken: string) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem('auth.accessToken', accessToken);
  window.localStorage.setItem('auth.refreshToken', refreshToken);
}

function limpiarTokens() {
  if (typeof window === 'undefined') return;
  window.localStorage.removeItem('auth.accessToken');
  window.localStorage.removeItem('auth.refreshToken');
  window.localStorage.removeItem('auth.user');
}

// ══════════════════════════════════════════════════════════════
// CLIENTE AXIOS
// ══════════════════════════════════════════════════════════════

/**
 * Instancia de Axios configurada para el backend
 */
export const clienteAPI: AxiosInstance = axios.create({
  baseURL: URL_BASE,
  timeout: TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// ══════════════════════════════════════════════════════════════
// INTERCEPTORES
// ══════════════════════════════════════════════════════════════

/**
 * Interceptor de respuestas exitosas
 */
type ConfigConRetry = InternalAxiosRequestConfig & { _retry?: boolean };

async function intentarRefreshToken(configOriginal?: AxiosRequestConfig): Promise<AxiosResponse | null> {
  const refreshToken = obtenerRefreshToken();
  if (!refreshToken || !configOriginal) return null;

  try {
    const respuestaRefresh = await axios.post(
      `${URL_BASE}/api/auth/refresh`,
      { refresh_token: refreshToken },
      { timeout: TIMEOUT }
    );

    const nuevoAccessToken = respuestaRefresh.data?.access_token as string | undefined;
    const nuevoRefreshToken = respuestaRefresh.data?.refresh_token as string | undefined;

    if (!nuevoAccessToken || !nuevoRefreshToken) {
      limpiarTokens();
      return null;
    }

    guardarTokens(nuevoAccessToken, nuevoRefreshToken);

    const headersPlano: Record<string, string> = {
      ...((configOriginal.headers as Record<string, string> | undefined) ?? {}),
      Authorization: `Bearer ${nuevoAccessToken}`,
    };

    return clienteAPI.request({
      ...configOriginal,
      headers: headersPlano,
    });
  } catch {
    limpiarTokens();
    return null;
  }
}

clienteAPI.interceptors.response.use(
  (respuesta: AxiosResponse) => {
    if (import.meta.env.DEV) {
      console.log(`✅ ${respuesta.config.method?.toUpperCase()} ${respuesta.config.url}`, respuesta.data);
    }
    return respuesta;
  },
  async (error: AxiosError<ErrorAPI>) => {
    if (import.meta.env.DEV) {
      console.error(`❌ Error en petición:`, error.response?.data || error.message);
    }

    const status = error.response?.status;
    const originalConfig = error.config as ConfigConRetry | undefined;
    const url = originalConfig?.url ?? '';
    const esRutaAuth = url.includes('/api/auth/login') || url.includes('/api/auth/refresh');

    if (status === 401 && originalConfig && !originalConfig._retry && !esRutaAuth) {
      originalConfig._retry = true;
      const reintento = await intentarRefreshToken(originalConfig);
      if (reintento) return reintento;
    }

    return Promise.reject(error);
  }
);

/**
 * Interceptor para adjuntar usuario ID en peticiones
 */
clienteAPI.interceptors.request.use((config) => {
  const usuarioId = obtenerUsuarioId();
  const accessToken = obtenerAccessToken();

  if (usuarioId) {
    if (config.headers instanceof AxiosHeaders) {
      config.headers.set('X-Usuario-Id', usuarioId);
    } else {
      config.headers = {
        ...((config.headers as Record<string, unknown>) ?? {}),
        'X-Usuario-Id': usuarioId,
      } as unknown as AxiosHeaders;
    }
  }

  if (accessToken) {
    if (config.headers instanceof AxiosHeaders) {
      config.headers.set('Authorization', `Bearer ${accessToken}`);
    } else {
      config.headers = {
        ...((config.headers as Record<string, unknown>) ?? {}),
        Authorization: `Bearer ${accessToken}`,
      } as unknown as AxiosHeaders;
    }
  }

  return config;
});

// ══════════════════════════════════════════════════════════════
// FUNCIONES AUXILIARES
// ══════════════════════════════════════════════════════════════

/**
 * Extrae el mensaje de error de una respuesta de la API
 */
export function extraerMensajeError(error: unknown): string {
  // Error de Axios con respuesta del servidor
  if (axios.isAxiosError(error)) {
    const data = (error.response?.data ?? {}) as Record<string, unknown>;
    const envelopeError = (data.error ?? {}) as Record<string, unknown>;

    const candidatos = [
      // Envelope custom
      envelopeError.mensaje,
      envelopeError.message,
      envelopeError.detail,
      // FastAPI estándar
      data.detail,
      // Respuestas legacy
      data.mensaje,
      data.message,
      // Fallback Axios
      error.message,
    ];

    const mensajeDetectado = candidatos.find(
      (valor) => typeof valor === 'string' && valor.trim().length > 0
    ) as string | undefined;

    if (mensajeDetectado) {
      return mensajeDetectado;
    }

    if (error.response?.status === 400) {
      return 'Solicitud inválida. Revisa equipos, línea y cuotas antes de reintentar.';
    }

    if (error.response?.status === 404) {
      return 'No se encontró el recurso solicitado. Verifica equipos, temporada o mercado.';
    }

    if (error.response?.status === 422) {
      return 'Los datos enviados no son válidos. Revisa cuotas, línea y mercado.';
    }

    if (error.response?.status === 500) {
      return 'Error interno del servidor. Intenta de nuevo más tarde.';
    }

    if (error.code === 'ECONNABORTED') {
      return 'La petición tardó demasiado. Verifica tu conexión o reintenta.';
    }

    if (error.code === 'ERR_NETWORK') {
      return 'No se pudo conectar con el servidor. Revisa tu conexión o el estado del backend.';
    }

    if (!error.response) {
      return 'No se recibió respuesta del servidor. Verifica tu conexión e intenta nuevamente.';
    }

    return 'Error desconocido en la petición.';
  }

  // Error genérico
  if (error instanceof Error) {
    return error.message;
  }

  return 'Ocurrió un error inesperado.';
}

/**
 * Verifica si el backend está disponible
 */
export async function verificarConexion(): Promise<boolean> {
  try {
    const respuesta = await clienteAPI.get('/salud');
    return respuesta.data?.estado === 'saludable' || respuesta.data?.estado === 'degradado';
  } catch {
    return false;
  }
}
