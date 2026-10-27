import { clienteAPI } from './api';
import type { PartidoResumen } from '../tipos';
import type { LigaBaloncesto } from '../utilidades/ligasBaloncesto';

export interface PartidoAgendaBaloncesto extends PartidoResumen {
  liga: LigaBaloncesto;
  competicion_nombre: string;
  inicio_utc: string | null;
  analizable: boolean;
  reconstruccion: boolean;
}
export interface AgendaBaloncesto {
  fecha: string; total: number; pagina: number; tamano: number;
  consultado_en: string; datos_actualizados_en: string | null;
  competiciones: string[]; partidos: PartidoAgendaBaloncesto[];
}
export async function consultarAgendaBaloncesto(params: { fecha: string; liga: string; buscar: string; estado: string; pagina: number }, signal?: AbortSignal) {
  const { data } = await clienteAPI.get<AgendaBaloncesto>('/api/partidos/agenda', { params, signal });
  return data;
}
