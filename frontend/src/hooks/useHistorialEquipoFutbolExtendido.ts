/**
 * Hook de historial detallado para fútbol (sin dependencia NBA)
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import type { CantidadPartidos, FiltroUbicacion, PartidoConMercado, EstadisticasOverUnder } from '../tipos';
import type { TipoMercadoFutbol, PartidoFutbolEstadistico } from '../tipos/futbol';
import { obtenerPartidosEquipoDetalle } from '../servicios/futbol';

interface ConfigHistorialFutbol {
  cantidad: CantidadPartidos;
  ubicacion: FiltroUbicacion;
  mercado: TipoMercadoFutbol;
  linea: number;
}

interface Retorno {
  partidos: PartidoConMercado[];
  estadisticas: EstadisticasOverUnder | null;
  cargando: boolean;
  error: string | null;
  recargar: () => void;
}

type MercadoParseado = {
  categoria: 'GOLES' | 'CORNERS' | 'DISPAROS' | 'DISPAROS_ARCO';
  periodo: '1T' | '2T' | 'FT';
  alcance: 'TOTAL' | 'LOCAL' | 'VISITANTE';
};

function parsearMercado(mercado: TipoMercadoFutbol): MercadoParseado {
  const m = mercado.toUpperCase();
  const periodo: '1T' | '2T' | 'FT' = m.endsWith('_1T') ? '1T' : (m.endsWith('_2T') ? '2T' : 'FT');
  const alcance: 'TOTAL' | 'LOCAL' | 'VISITANTE' = m.includes('_LOCAL_') ? 'LOCAL' : (m.includes('_VISITANTE_') ? 'VISITANTE' : 'TOTAL');
  const categoria: MercadoParseado['categoria'] = m.startsWith('GOLES')
    ? 'GOLES'
    : m.startsWith('CORNERS')
      ? 'CORNERS'
      : m.includes('ARCO')
        ? 'DISPAROS_ARCO'
        : 'DISPAROS';
  return { categoria, periodo, alcance };
}

function valorPorLado(partido: PartidoFutbolEstadistico, categoria: MercadoParseado['categoria'], lado: 'LOCAL' | 'VISITANTE', periodo: '1T' | '2T' | 'FT'): number {
  if (categoria === 'GOLES') return lado === 'LOCAL' ? partido.golesLocal : partido.golesVisitante;
  if (categoria === 'CORNERS') {
    if (periodo === '1T') return lado === 'LOCAL' ? (partido.cornersLocal1t ?? 0) : (partido.cornersVisitante1t ?? 0);
    if (periodo === '2T') return lado === 'LOCAL' ? (partido.cornersLocal2t ?? 0) : (partido.cornersVisitante2t ?? 0);
    return lado === 'LOCAL' ? partido.cornersLocal : partido.cornersVisitante;
  }
  if (categoria === 'DISPAROS_ARCO') return lado === 'LOCAL' ? partido.disparosArcoLocal : partido.disparosArcoVisitante;
  return lado === 'LOCAL' ? partido.disparosLocal : partido.disparosVisitante;
}

function totalMercado(partido: PartidoFutbolEstadistico, mercado: MercadoParseado): number {
  if (mercado.alcance === 'LOCAL' || mercado.alcance === 'VISITANTE') {
    return valorPorLado(partido, mercado.categoria, mercado.alcance, mercado.periodo);
  }
  const local = valorPorLado(partido, mercado.categoria, 'LOCAL', mercado.periodo);
  const visitante = valorPorLado(partido, mercado.categoria, 'VISITANTE', mercado.periodo);
  return local + visitante;
}

function calcularStats(partidos: PartidoConMercado[], linea: number): EstadisticasOverUnder {
  const totalPartidos = partidos.length;
  if (!totalPartidos) {
    return {
      totalPartidos: 0, partidosOver: 0, partidosUnder: 0, porcentajeOver: 0,
      promedioTotal: 0, promedioVsLinea: 0,
      rachaActual: { tipo: 'MIXTA', cantidad: 0 }, tendencia: 'ESTABLE', ultimos5Promedio: 0, anteriores5Promedio: 0,
    };
  }
  const partidosOver = partidos.filter((p) => p.esOver).length;
  const partidosUnder = totalPartidos - partidosOver;
  const promedioTotal = partidos.reduce((a, p) => a + p.totalMercado, 0) / totalPartidos;
  const promedioVsLinea = promedioTotal - linea;
  const primerEsOver = partidos[0].esOver;
  let racha = 1;
  for (let i = 1; i < partidos.length; i += 1) {
    if (partidos[i].esOver === primerEsOver) racha += 1;
    else break;
  }
  const ultimos5 = partidos.slice(0, Math.min(5, totalPartidos));
  const anteriores5 = partidos.slice(5, Math.min(10, totalPartidos));
  const ultimos5Promedio = ultimos5.length ? ultimos5.reduce((a, p) => a + p.totalMercado, 0) / ultimos5.length : 0;
  const anteriores5Promedio = anteriores5.length ? anteriores5.reduce((a, p) => a + p.totalMercado, 0) / anteriores5.length : ultimos5Promedio;
  const delta = ultimos5Promedio - anteriores5Promedio;
  const tendencia = delta > 0.5 ? 'SUBIENDO' : (delta < -0.5 ? 'BAJANDO' : 'ESTABLE');

  return {
    totalPartidos,
    partidosOver,
    partidosUnder,
    porcentajeOver: (partidosOver / totalPartidos) * 100,
    promedioTotal,
    promedioVsLinea,
    rachaActual: { tipo: primerEsOver ? 'OVER' : 'UNDER', cantidad: racha },
    tendencia,
    ultimos5Promedio,
    anteriores5Promedio,
  };
}

export function useHistorialEquipoFutbolExtendido(equipoId: string, config: ConfigHistorialFutbol): Retorno {
  const [base, setBase] = useState<PartidoFutbolEstadistico[]>([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const recargar = useCallback(async () => {
    if (!equipoId) return;
    setCargando(true);
    setError(null);
    try {
      const ubicacion = config.ubicacion === 'TODOS' ? 'todos' : (config.ubicacion === 'LOCAL' ? 'local' : 'visitante');
      const data = await obtenerPartidosEquipoDetalle(equipoId, config.cantidad, ubicacion);
      setBase(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error al cargar historial de fútbol');
      setBase([]);
    } finally {
      setCargando(false);
    }
  }, [equipoId, config.cantidad, config.ubicacion]);

  useEffect(() => { void recargar(); }, [recargar]);

  const partidos = useMemo<PartidoConMercado[]>(() => {
    const m = parsearMercado(config.mercado);
    return base.map((p) => {
      const esLocal = String(p.equipoLocalId) === String(equipoId);
      const equipo = esLocal ? 'LOCAL' : 'VISITANTE';
      const marcadorEquipo = esLocal ? p.golesLocal : p.golesVisitante;
      const marcadorRival = esLocal ? p.golesVisitante : p.golesLocal;
      const total = totalMercado(p, m);
      return {
        id: p.id,
        fecha: p.fechaPartido,
        temporada: null,
        equipoLocal: p.equipoLocalNombre,
        localAbr: p.equipoLocalNombre.slice(0, 3).toUpperCase(),
        equipoVisitante: p.equipoVisitanteNombre,
        visitanteAbr: p.equipoVisitanteNombre.slice(0, 3).toUpperCase(),
        ubicacionEquipo: equipo,
        puntosEquipo: { q1: 0, q2: 0, q3: 0, q4: 0, ot: 0, total: marcadorEquipo },
        puntosRival: { q1: 0, q2: 0, q3: 0, q4: 0, ot: 0, total: marcadorRival },
        resultado: marcadorEquipo > marcadorRival ? 'VICTORIA' : 'DERROTA',
        totalMercado: total,
        resultadoMercado: `${marcadorEquipo}-${marcadorRival}`,
        esOver: total > config.linea,
        margenVsLinea: total - config.linea,
      };
    });
  }, [base, config.linea, config.mercado, equipoId]);

  const estadisticas = useMemo(() => (partidos.length ? calcularStats(partidos, config.linea) : null), [partidos, config.linea]);

  return { partidos, estadisticas, cargando, error, recargar };
}
