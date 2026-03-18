import { clienteAPI, extraerMensajeError } from './api';
import type { RespuestaAuth, UsuarioAuth } from '../tipos/auth';

const ACCESS_TOKEN_KEY = 'auth.accessToken';
const REFRESH_TOKEN_KEY = 'auth.refreshToken';
const USER_KEY = 'auth.user';

interface EnvelopeV2<T> {
  ok: boolean;
  data: T;
  meta?: Record<string, unknown>;
}

function esEnvelopeV2<T>(data: unknown): data is EnvelopeV2<T> {
  return !!data && typeof data === 'object' && 'data' in (data as Record<string, unknown>);
}

function normalizarAuthRespuesta(payload: unknown): RespuestaAuth {
  if (esEnvelopeV2<RespuestaAuth>(payload)) {
    return payload.data;
  }
  return payload as RespuestaAuth;
}

function normalizarMensajeRespuesta(
  payload: unknown
): { message: string; reset_token_dev?: string; user?: UsuarioAuth } {
  if (esEnvelopeV2<{ message?: string; reset_token_dev?: string; user?: UsuarioAuth }>(payload)) {
    const data = payload.data ?? {};
    return {
      message: data.message ?? '',
      reset_token_dev: data.reset_token_dev,
      user: data.user,
    };
  }

  const raw = (payload ?? {}) as { message?: string; reset_token_dev?: string; user?: UsuarioAuth };
  return {
    message: raw.message ?? '',
    reset_token_dev: raw.reset_token_dev,
    user: raw.user,
  };
}

export function obtenerAccessToken(): string | null {
  return typeof window !== 'undefined' ? window.localStorage.getItem(ACCESS_TOKEN_KEY) : null;
}

export function obtenerRefreshToken(): string | null {
  return typeof window !== 'undefined' ? window.localStorage.getItem(REFRESH_TOKEN_KEY) : null;
}

export function obtenerUsuarioAuth(): UsuarioAuth | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as UsuarioAuth;
  } catch {
    return null;
  }
}

export function guardarSesionAuth(data: { accessToken: string; refreshToken: string; user?: UsuarioAuth | null }) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(ACCESS_TOKEN_KEY, data.accessToken);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, data.refreshToken);
  if (data.user) {
    window.localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    window.localStorage.setItem('usuarioId', String(data.user.id));
  }
}

export function limpiarSesionAuth() {
  if (typeof window === 'undefined') return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
  window.localStorage.removeItem('usuarioId');
}

export async function login(email: string, password: string): Promise<RespuestaAuth> {
  try {
    const { data } = await clienteAPI.post('/api/auth/login?version=v2', { email, password });
    return normalizarAuthRespuesta(data);
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

export async function register(
  email: string,
  password: string,
  legalVersion: string,
  acceptedLegal: boolean
): Promise<RespuestaAuth> {
  try {
    const { data } = await clienteAPI.post('/api/auth/register?version=v2', {
      email,
      password,
      legal_version: legalVersion,
      accepted_legal: acceptedLegal,
    });
    return normalizarAuthRespuesta(data);
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

export async function solicitarRecuperacion(email: string): Promise<{ message: string; reset_token_dev?: string }> {
  try {
    const { data } = await clienteAPI.post('/api/auth/forgot-password?version=v2', { email });
    const normalizado = normalizarMensajeRespuesta(data);
    return { message: normalizado.message, reset_token_dev: normalizado.reset_token_dev };
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

export async function restablecerPassword(token: string, newPassword: string): Promise<{ message: string }> {
  try {
    const { data } = await clienteAPI.post('/api/auth/reset-password?version=v2', {
      token,
      new_password: newPassword,
    });
    const normalizado = normalizarMensajeRespuesta(data);
    return { message: normalizado.message };
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

export async function obtenerPerfil(accessToken: string): Promise<UsuarioAuth> {
  try {
    const { data } = await clienteAPI.get('/api/auth/me?version=v2', {
      headers: { Authorization: `Bearer ${accessToken}` },
    });

    if (esEnvelopeV2<{ user: UsuarioAuth }>(data)) {
      return data.data.user;
    }

    return (data as { user: UsuarioAuth }).user;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

export async function logout(accessToken: string): Promise<void> {
  try {
    await clienteAPI.post('/api/auth/logout?version=v2', null, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
  } catch {
    // noop
  }
}
