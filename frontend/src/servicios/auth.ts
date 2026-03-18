import { clienteAPI, extraerMensajeError } from './api';
import type { RespuestaAuth, UsuarioAuth } from '../tipos/auth';

const ACCESS_TOKEN_KEY = 'auth.accessToken';
const REFRESH_TOKEN_KEY = 'auth.refreshToken';
const USER_KEY = 'auth.user';

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
}

export async function login(email: string, password: string): Promise<RespuestaAuth> {
  try {
    const { data } = await clienteAPI.post<RespuestaAuth>('/api/auth/login', { email, password });
    return data;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

export async function register(email: string, password: string): Promise<RespuestaAuth> {
  try {
    const { data } = await clienteAPI.post<RespuestaAuth>('/api/auth/register', { email, password });
    return data;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

export async function solicitarRecuperacion(email: string): Promise<{ message: string; reset_token_dev?: string }> {
  try {
    const { data } = await clienteAPI.post<{ ok: boolean; message: string; reset_token_dev?: string }>(
      '/api/auth/forgot-password',
      { email }
    );
    return { message: data.message, reset_token_dev: data.reset_token_dev };
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

export async function restablecerPassword(token: string, newPassword: string): Promise<{ message: string }> {
  try {
    const { data } = await clienteAPI.post<{ ok: boolean; message: string }>('/api/auth/reset-password', {
      token,
      new_password: newPassword,
    });
    return { message: data.message };
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

export async function obtenerPerfil(accessToken: string): Promise<UsuarioAuth> {
  try {
    const { data } = await clienteAPI.get<{ ok: boolean; user: UsuarioAuth }>('/api/auth/me', {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    return data.user;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

export async function logout(accessToken: string): Promise<void> {
  try {
    await clienteAPI.post('/api/auth/logout', null, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
  } catch {
    // noop
  }
}
