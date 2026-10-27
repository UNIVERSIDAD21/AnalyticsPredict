import { clienteAPI } from '../api';
import type { Competicion, PartidoFutbolResumen } from '../../tipos/futbol';

export interface TemporadaFutbol { id: string; nombre: string; anio_inicio: number; finales: number }
export interface AmbitoFutbol {
  competicionId: string;
  temporadaId: string;
  modo: 'proximos' | 'historicos';
  pagina: number;
}

export async function listarCompeticiones(signal: AbortSignal): Promise<Competicion[]> {
  const { data } = await clienteAPI.get('/api/futbol/competiciones', { signal });
  return data.competiciones;
}

export async function listarTemporadas(competicion: string, signal: AbortSignal): Promise<TemporadaFutbol[]> {
  const { data } = await clienteAPI.get(`/api/futbol/competiciones/${competicion}/temporadas`, { signal });
  return data.temporadas;
}

export async function resolverPartidoCatalogo(id: string, signal: AbortSignal): Promise<{ competicionId: string; temporadaId: string; estado: string; fechaPartido: string }> {
  const { data } = await clienteAPI.get(`/api/futbol/partidos/${id}`, { signal, params: { incluir_estadisticas: false } });
  return { competicionId: data.competicion_id, temporadaId: data.temporada_id, estado: data.estado, fechaPartido: data.fecha_partido };
}

export type EstadoAgenda = 'PROXIMO' | 'POR_VERIFICAR' | 'EN_JUEGO' | 'FINALIZADO' | 'NO_DISPONIBLE';
export interface PartidoAgendaFutbol extends PartidoFutbolResumen { pais: string; estadoAgenda: EstadoAgenda; analizable: boolean }
export interface AgendaFutbol {
  fecha: string; total: number; consultadoEn: string; datosActualizadosEn: string | null; partidos: PartidoAgendaFutbol[];
}
export interface FiltrosAgenda {
  fecha: string; competicionId: string; pais: string; buscar: string; estado: string; pagina: number; guardados?: string[];
}
export async function listarAgenda(filtros: FiltrosAgenda, signal: AbortSignal): Promise<AgendaFutbol> {
  const params = new URLSearchParams({ fecha: filtros.fecha, pagina: String(filtros.pagina), tamano: '50', estado: filtros.estado });
  if (filtros.competicionId) params.set('competicion_id', filtros.competicionId);
  if (filtros.pais) params.set('pais', filtros.pais);
  if (filtros.buscar.trim()) params.set('buscar', filtros.buscar.trim());
  filtros.guardados?.forEach(id => params.append('partido_ids', id));
  const { data } = await clienteAPI.get('/api/futbol/partidos/agenda', { signal, params });
  return {
    fecha: data.fecha, total: data.total, consultadoEn: data.consultado_en, datosActualizadosEn: data.datos_actualizados_en,
    partidos: data.partidos.map((p: Record<string, unknown>) => ({
      id: String(p.id), competicion: String(p.competicion_id), competicionNombre: String(p.competicion),
      temporadaId: String(p.temporada_id), fechaPartido: String(p.fecha_partido),
      precisionFecha: p.precision_fecha === 'DIA' ? 'DIA' : 'HORA', reconstruccion: p.reconstruccion === true,
      equipoLocal: String(p.equipo_local_id), equipoLocalNombre: String(p.equipo_local),
      equipoVisitante: String(p.equipo_visitante_id), equipoVisitanteNombre: String(p.equipo_visitante),
      equipoLocalLogo: p.equipo_local_logo ? String(p.equipo_local_logo) : undefined,
      equipoVisitanteLogo: p.equipo_visitante_logo ? String(p.equipo_visitante_logo) : undefined,
      estado: p.estado as PartidoFutbolResumen['estado'], pais: String(p.pais), estadoAgenda: p.estado_agenda as EstadoAgenda, analizable: Boolean(p.analizable),
      golesLocal: p.goles_local == null ? undefined : Number(p.goles_local), golesVisitante: p.goles_visitante == null ? undefined : Number(p.goles_visitante),
    })),
  };
}

export async function listarCatalogo(ambito: AmbitoFutbol, signal: AbortSignal): Promise<{ total: number; partidos: PartidoFutbolResumen[] }> {
  const { data } = await clienteAPI.get('/api/futbol/partidos/catalogo', { signal, params: {
    competicion_id: ambito.competicionId, temporada_id: ambito.temporadaId || undefined,
    modo: ambito.modo, pagina: ambito.pagina, tamano: 50,
  } });
  return { total: data.total, partidos: data.partidos.map((p: Record<string, unknown>) => ({
    id: String(p.id), competicion: String(p.competicion_id), competicionNombre: String(p.competicion),
    temporadaId: String(p.temporada_id), fechaPartido: String(p.fecha_partido),
    equipoLocal: String(p.equipo_local_id), equipoLocalNombre: String(p.equipo_local),
    equipoVisitante: String(p.equipo_visitante_id), equipoVisitanteNombre: String(p.equipo_visitante),
    estado: p.estado as PartidoFutbolResumen['estado'],
    golesLocal: p.goles_local == null ? undefined : Number(p.goles_local),
    golesVisitante: p.goles_visitante == null ? undefined : Number(p.goles_visitante),
  })) };
}
