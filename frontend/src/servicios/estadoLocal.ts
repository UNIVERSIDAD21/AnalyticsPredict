import { clienteAPI } from './api';
import type { IdentidadLocal, LigaBaseLocal } from './consultaLocal';

export interface EstadoLocal {
  formato: 'diagnostico-local-v1'; observado_en: string; modo: 'BASE_LOCAL' | 'CON_BD_CONFIGURADA';
  bd: { deshabilitada: boolean; conexion_comprobada: false; estado: string };
  modelos: Record<LigaBaseLocal, Partial<IdentidadLocal> & { disponible: boolean; equipos_disponibles?: number; motivo?: string }>;
  limites: string[];
}
export async function leerEstadoLocal(signal?: AbortSignal) {
  const d = (await clienteAPI.get<EstadoLocal>('/api/local/estado', { signal })).data;
  if (d?.formato !== 'diagnostico-local-v1' || typeof d.bd?.deshabilitada !== 'boolean') throw new Error('Diagnóstico local incompatible.');
  return d;
}
