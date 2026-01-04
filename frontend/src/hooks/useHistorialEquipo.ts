/**
 * useHistorialEquipo.ts — Hook para historial de partidos de un equipo
 */

import { useCallback, useEffect, useState } from 'react';
import {
  FiltrosDisponiblesHistorial,
  InfoEquipoHistorial,
  PartidoHistorial,
  PartidoHistorialAPI,
  Equipo,
} from '../tipos';
import { obtenerEquipos, obtenerHistorialEquipo } from '../servicios';

export interface FiltrosHistorial {
  temporadaId?: string;
  comoLocal?: boolean;
  oponenteId?: string;
}

interface UseHistorialEquipoReturn {
  partidos: PartidoHistorial[];
  equipo: InfoEquipoHistorial | null;
  cargando: boolean;
  error: string | null;
  filtrosDisponibles: FiltrosDisponiblesHistorial;
  aplicarFiltros: (filtros: FiltrosHistorial) => void;
}

interface ResumenEquipoOponente {
  nombre: string;
  abreviatura: string;
}

const mapearPartido = (partido: PartidoHistorialAPI): PartidoHistorial => ({
  id: partido.id,
  fecha: partido.fecha,
  temporada: partido.temporada,
  equipoLocal: partido.equipo_local,
  localAbr: partido.local_abr,
  equipoVisitante: partido.equipo_visitante,
  visitanteAbr: partido.visitante_abr,
  ubicacionEquipo: partido.ubicacion_equipo,
  puntosEquipo: partido.puntos_equipo,
  puntosRival: partido.puntos_rival,
  resultado: partido.resultado,
});

const obtenerClaveFecha = (fecha: string): number => {
  const [anio, mes, dia] = fecha.split('T')[0].split('-').map(Number);
  if (!anio || !mes || !dia) {
    return 0;
  }
  return anio * 10000 + mes * 100 + dia;
};

const ordenarPorFechaDesc = (partidos: PartidoHistorial[]): PartidoHistorial[] =>
  [...partidos].sort((a, b) => obtenerClaveFecha(b.fecha) - obtenerClaveFecha(a.fecha));

const construirMapaOponentes = (equipos: Equipo[]): Map<string, ResumenEquipoOponente> => {
  const mapa = new Map<string, ResumenEquipoOponente>();
  equipos.forEach((equipo) => {
    mapa.set(equipo.id, {
      nombre: equipo.nombre,
      abreviatura: equipo.abreviatura,
    });
  });
  return mapa;
};

export function useHistorialEquipo(equipoId: string): UseHistorialEquipoReturn {
  const [partidos, setPartidos] = useState<PartidoHistorial[]>([]);
  const [partidosBase, setPartidosBase] = useState<PartidoHistorial[]>([]);
  const [equipo, setEquipo] = useState<InfoEquipoHistorial | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filtrosDisponibles, setFiltrosDisponibles] = useState<FiltrosDisponiblesHistorial>({
    temporadas: [],
  });
  const [filtros, setFiltros] = useState<FiltrosHistorial>({});
  const [mapaOponentes, setMapaOponentes] = useState<Map<string, ResumenEquipoOponente>>(
    new Map()
  );

  const aplicarFiltros = useCallback((nuevosFiltros: FiltrosHistorial) => {
    setFiltros(nuevosFiltros);
  }, []);

  const cargarHistorial = useCallback(async () => {
    if (!equipoId) {
      return;
    }
    setCargando(true);
    setError(null);
    try {
      const respuesta = await obtenerHistorialEquipo(equipoId, {
        temporadaId: filtros.temporadaId,
        comoLocal: filtros.comoLocal,
        orden: 'desc',
      });
      const partidosMapeados = ordenarPorFechaDesc(respuesta.partidos.map(mapearPartido));
      setPartidosBase(partidosMapeados);
      setEquipo(respuesta.equipo);
      setFiltrosDisponibles(respuesta.filtros_disponibles);
      setCargando(false);
    } catch (err) {
      const mensaje = err instanceof Error ? err.message : 'No se pudo cargar el historial';
      setError(mensaje);
      setCargando(false);
    }
  }, [equipoId, filtros.temporadaId, filtros.comoLocal]);

  useEffect(() => {
    cargarHistorial();
  }, [cargarHistorial]);

  useEffect(() => {
    let activo = true;
    const cargarEquipos = async () => {
      try {
        const equipos = await obtenerEquipos();
        if (!activo) {
          return;
        }
        setMapaOponentes(construirMapaOponentes(equipos));
      } catch {
        if (activo) {
          setMapaOponentes(new Map());
        }
      }
    };
    cargarEquipos();
    return () => {
      activo = false;
    };
  }, []);

  useEffect(() => {
    const oponenteId = filtros.oponenteId;
    if (!oponenteId) {
      setPartidos(partidosBase);
      return;
    }
    const datosOponente = mapaOponentes.get(oponenteId);
    if (!datosOponente) {
      setPartidos(partidosBase);
      return;
    }
    const nombre = datosOponente.nombre.toLowerCase();
    const abreviatura = datosOponente.abreviatura.toLowerCase();
    const filtrados = partidosBase.filter((partido) => {
      const local = partido.equipoLocal.toLowerCase();
      const visitante = partido.equipoVisitante.toLowerCase();
      return (
        local === nombre ||
        visitante === nombre ||
        partido.localAbr.toLowerCase() === abreviatura ||
        partido.visitanteAbr.toLowerCase() === abreviatura
      );
    });
    setPartidos(filtrados);
  }, [filtros.oponenteId, partidosBase, mapaOponentes]);

  return {
    partidos,
    equipo,
    cargando,
    error,
    filtrosDisponibles,
    aplicarFiltros,
  };
}
