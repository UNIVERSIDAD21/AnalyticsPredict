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

export function guardarEstadoOnboarding(usuarioId: string, perfil: PerfilOnboarding): EstadoOnboarding {
  const estado: EstadoOnboarding = {
    completado: true,
    actualizadoEn: new Date().toISOString(),
    perfil,
  };

  if (typeof window !== 'undefined') {
    window.localStorage.setItem(claveOnboarding(usuarioId), JSON.stringify(estado));
  }

  return estado;
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
