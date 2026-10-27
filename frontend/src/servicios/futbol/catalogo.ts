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

export async function resolverPartidoCatalogo(id: string, signal: AbortSignal): Promise<{ competicionId: string; temporadaId: string; estado: string }> {
  const { data } = await clienteAPI.get(`/api/futbol/partidos/${id}`, { signal, params: { incluir_estadisticas: false } });
  return { competicionId: data.competicion_id, temporadaId: data.temporada_id, estado: data.estado };
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
