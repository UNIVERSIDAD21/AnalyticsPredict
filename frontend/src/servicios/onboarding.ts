import { clienteAPI, extraerMensajeError } from './api';
import type { ApuestaAnalizada } from '../tipos/bitacora';

export interface PerfilOnboarding {
  nombre: string;
  objetivoPrincipal: 'rentabilidad' | 'disciplina' | 'aprendizaje';
  deportePreferido: 'baloncesto' | 'futbol' | 'ambos';
  frecuencia: 'diaria' | 'semanal' | 'ocasional';
  bankrollReferencial: number | null;
}

export interface EstadoOnboarding {
  completado: boolean;
  actualizadoEn: string | null;
  perfil: PerfilOnboarding | null;
}

export interface ResumenDashboard {
  apuestasTotales: number;
  apuestasResueltas: number;
  ganadas: number;
  perdidas: number;
  push: number;
  winRate: number;
}

function claveOnboarding(usuarioId: string) {
  return `b2.onboarding.${usuarioId}`;
}

export function obtenerEstadoOnboarding(usuarioId: string): EstadoOnboarding {
  if (typeof window === 'undefined') {
    return { completado: false, actualizadoEn: null, perfil: null };
  }

  const raw = window.localStorage.getItem(claveOnboarding(usuarioId));
  if (!raw) {
    return { completado: false, actualizadoEn: null, perfil: null };
  }

  try {
    const data = JSON.parse(raw) as EstadoOnboarding;
    return {
      completado: !!data.completado,
      actualizadoEn: data.actualizadoEn ?? null,
      perfil: data.perfil ?? null,
    };
  } catch {
    return { completado: false, actualizadoEn: null, perfil: null };
  }
}

function mapearPerfilBackend(data: Record<string, unknown>): PerfilOnboarding {
  return {
    nombre: String(data.nombre ?? ''),
    objetivoPrincipal: String(data.objetivo_principal ?? 'rentabilidad') as PerfilOnboarding['objetivoPrincipal'],
    deportePreferido: String(data.deporte_preferido ?? 'ambos') as PerfilOnboarding['deportePreferido'],
    frecuencia: String(data.frecuencia ?? 'semanal') as PerfilOnboarding['frecuencia'],
    bankrollReferencial: (data.bankroll_referencial as number | null | undefined) ?? null,
  };
}

function mapearPerfilPayload(perfil: PerfilOnboarding) {
  return {
    nombre: perfil.nombre,
    objetivo_principal: perfil.objetivoPrincipal,
    deporte_preferido: perfil.deportePreferido,
    frecuencia: perfil.frecuencia,
    bankroll_referencial: perfil.bankrollReferencial,
  };
}

export async function guardarEstadoOnboarding(usuarioId: string, perfil: PerfilOnboarding): Promise<EstadoOnboarding> {
  try {
    const { data } = await clienteAPI.post('/api/onboarding/perfil', mapearPerfilPayload(perfil));
    const estado: EstadoOnboarding = {
      completado: !!data?.data?.completado,
      actualizadoEn: data?.data?.updated_at ?? null,
      perfil: data?.data?.perfil ? mapearPerfilBackend(data.data.perfil as Record<string, unknown>) : perfil,
    };

    if (typeof window !== 'undefined') {
      window.localStorage.setItem(claveOnboarding(usuarioId), JSON.stringify(estado));
    }

    return estado;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

export async function refrescarEstadoOnboarding(usuarioId: string): Promise<EstadoOnboarding> {
  try {
    const { data } = await clienteAPI.get('/api/onboarding/estado');
    const estado: EstadoOnboarding = {
      completado: !!data?.data?.completado,
      actualizadoEn: data?.data?.updated_at ?? null,
      perfil: data?.data?.perfil ? mapearPerfilBackend(data.data.perfil as Record<string, unknown>) : null,
    };

    if (typeof window !== 'undefined') {
      window.localStorage.setItem(claveOnboarding(usuarioId), JSON.stringify(estado));
    }

    return estado;
  } catch {
    return obtenerEstadoOnboarding(usuarioId);
  }
}

export async function registrarEventoOnboarding(
  eventName: 'onboarding_started' | 'onboarding_completed' | 'dashboard_viewed',
  metadata?: Record<string, unknown>
): Promise<void> {
  try {
    await clienteAPI.post('/api/onboarding/evento', {
      event_name: eventName,
      metadata,
    });
  } catch {
    // best-effort telemetry
  }
}

export async function obtenerResumenDashboard(): Promise<ResumenDashboard> {
  try {
    const { data } = await clienteAPI.get('/api/bitacora/apuestas-analizadas', {
      params: { page_size: 200 },
    });

    const items = (data?.items ?? []) as ApuestaAnalizada[];
    return calcularResumen(items);
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

function calcularResumen(items: ApuestaAnalizada[]): ResumenDashboard {
  const resueltas = items.filter((item) => item.estado?.toUpperCase() === 'RESUELTA');
  const ganadas = resueltas.filter((item) => item.resultado_outcome === 'GANADA').length;
  const perdidas = resueltas.filter((item) => item.resultado_outcome === 'PERDIDA').length;
  const push = resueltas.filter((item) => item.resultado_outcome === 'PUSH').length;

  const winRate = resueltas.length > 0 ? (ganadas / resueltas.length) * 100 : 0;

  return {
    apuestasTotales: items.length,
    apuestasResueltas: resueltas.length,
    ganadas,
    perdidas,
    push,
    winRate,
  };
}
