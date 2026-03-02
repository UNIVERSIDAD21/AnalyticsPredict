/**
 * api.ts — Cliente HTTP base para comunicación con el backend
 */

import axios, { AxiosError, AxiosHeaders, AxiosInstance, AxiosResponse } from 'axios';
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
clienteAPI.interceptors.response.use(
  (respuesta: AxiosResponse) => {
    // Log en desarrollo
    if (import.meta.env.DEV) {
      console.log(`✅ ${respuesta.config.method?.toUpperCase()} ${respuesta.config.url}`, respuesta.data);
    }
    return respuesta;
  },
  (error: AxiosError<ErrorAPI>) => {
    // Log en desarrollo
    if (import.meta.env.DEV) {
      console.error(`❌ Error en petición:`, error.response?.data || error.message);
    }
    return Promise.reject(error);
  }
);

/**
 * Interceptor para adjuntar usuario ID en peticiones
 */
clienteAPI.interceptors.request.use((config) => {
  const usuarioId = obtenerUsuarioId();
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
    const respuesta = error.response?.data as ErrorAPI | undefined;

    if (respuesta?.error?.mensaje) {
      return respuesta.error.mensaje;
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

    return error.message || 'Error desconocido en la petición.';
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
