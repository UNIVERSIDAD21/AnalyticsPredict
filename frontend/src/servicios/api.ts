/**
 * api.ts — Cliente HTTP base para comunicación con el backend
 */

import axios, {
  AxiosError,
  AxiosInstance,
  AxiosResponse,
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
    return respuesta;
  },
  async (error: AxiosError<ErrorAPI>) => {
    if (import.meta.env.DEV) {
      console.error(`❌ Error en petición:`, error.response?.data || error.message);
    }

    return Promise.reject(error);
  }
);

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
