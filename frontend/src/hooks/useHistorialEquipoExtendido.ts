/**
 * useHistorialEquipoExtendido.ts — Hook para historial de partidos con filtros avanzados
 *
 * Proporciona datos de historial filtrados por cantidad, ubicación y mercado,
 * calculando estadísticas OVER/UNDER en tiempo real según la línea ingresada.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  PartidoHistorial,
  PartidoHistorialAPI,
  PartidoConMercado,
  ConfiguracionHistorial,
  EstadisticasOverUnder,
  TendenciaHistorial,
  RachaActual,
} from '../tipos';
import type { Mercado } from '../tipos/analisis';
import { obtenerHistorialEquipo } from '../servicios';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface UseHistorialEquipoExtendidoReturn {
  /** Partidos transformados con datos del mercado seleccionado */
  partidos: PartidoConMercado[];
  /** Estadísticas agregadas OVER/UNDER */
  estadisticas: EstadisticasOverUnder | null;
  /** Estado de carga */
  cargando: boolean;
  /** Mensaje de error si ocurrió */
  error: string | null;
  /** Forzar recarga de datos */
  recargar: () => void;
}

// ══════════════════════════════════════════════════════════════
// FUNCIONES AUXILIARES
// ══════════════════════════════════════════════════════════════

/**
 * Mapea un partido de la API al formato interno
 */
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

/**
 * Obtiene el total de puntos según el mercado seleccionado
 */
function obtenerTotalParaMercado(partido: PartidoHistorial, mercado: Mercado): number {
  if (mercado === 'COMPLETO') {
    return (partido.puntosEquipo.total || 0) + (partido.puntosRival.total || 0);
  }
  const key = mercado.toLowerCase() as 'q1' | 'q2' | 'q3' | 'q4';
  return (partido.puntosEquipo[key] || 0) + (partido.puntosRival[key] || 0);
}

/**
 * Obtiene el resultado formateado según el mercado
 */
function obtenerResultadoParaMercado(partido: PartidoHistorial, mercado: Mercado): string {
  if (mercado === 'COMPLETO') {
    return `${partido.puntosEquipo.total || 0}-${partido.puntosRival.total || 0}`;
  }
  const key = mercado.toLowerCase() as 'q1' | 'q2' | 'q3' | 'q4';
  return `${partido.puntosEquipo[key] || 0}-${partido.puntosRival[key] || 0}`;
}

/**
 * Calcula la racha actual de OVER/UNDER consecutivos
 */
function calcularRachaActual(partidos: PartidoConMercado[]): RachaActual {
  if (partidos.length === 0) {
    return { tipo: 'MIXTA', cantidad: 0 };
  }

  const primerPartido = partidos[0];
  const tipoRacha = primerPartido.esOver ? 'OVER' : 'UNDER';
  let cantidad = 1;

  for (let i = 1; i < partidos.length; i++) {
    const esOver = partidos[i].esOver;
    if ((tipoRacha === 'OVER' && esOver) || (tipoRacha === 'UNDER' && !esOver)) {
      cantidad++;
    } else {
      break;
    }
  }

  return { tipo: tipoRacha, cantidad };
}

/**
 * Calcula la tendencia comparando últimos 5 vs anteriores 5
 */
function calcularTendencia(
  ultimos5Promedio: number,
  anteriores5Promedio: number
): TendenciaHistorial {
  const diferencia = ultimos5Promedio - anteriores5Promedio;
  const umbral = 3; // Diferencia mínima para considerar tendencia

  if (diferencia > umbral) return 'SUBIENDO';
  if (diferencia < -umbral) return 'BAJANDO';
  return 'ESTABLE';
}

/**
 * Calcula las estadísticas OVER/UNDER a partir de los partidos
 */
function calcularEstadisticasOverUnder(
  partidos: PartidoConMercado[],
  linea: number
): EstadisticasOverUnder {
  const totalPartidos = partidos.length;

  if (totalPartidos === 0) {
    return {
      totalPartidos: 0,
      partidosOver: 0,
      partidosUnder: 0,
      porcentajeOver: 0,
      promedioTotal: 0,
      promedioVsLinea: 0,
      rachaActual: { tipo: 'MIXTA', cantidad: 0 },
      tendencia: 'ESTABLE',
      ultimos5Promedio: 0,
      anteriores5Promedio: 0,
    };
  }

  // Contar OVER/UNDER
  const partidosOver = partidos.filter((p) => p.esOver).length;
  const partidosUnder = totalPartidos - partidosOver;
  const porcentajeOver = (partidosOver / totalPartidos) * 100;

  // Calcular promedios
  const sumaTotal = partidos.reduce((acc, p) => acc + p.totalMercado, 0);
  const promedioTotal = sumaTotal / totalPartidos;
  const promedioVsLinea = promedioTotal - linea;

  // Calcular racha actual
  const rachaActual = calcularRachaActual(partidos);

  // Calcular tendencia (últimos 5 vs anteriores 5)
  const ultimos5 = partidos.slice(0, Math.min(5, totalPartidos));
  const anteriores5 = partidos.slice(5, Math.min(10, totalPartidos));

  const ultimos5Promedio =
    ultimos5.length > 0
      ? ultimos5.reduce((acc, p) => acc + p.totalMercado, 0) / ultimos5.length
      : 0;

  const anteriores5Promedio =
    anteriores5.length > 0
      ? anteriores5.reduce((acc, p) => acc + p.totalMercado, 0) / anteriores5.length
      : ultimos5Promedio; // Si no hay suficientes, usar el mismo valor

  const tendencia = calcularTendencia(ultimos5Promedio, anteriores5Promedio);

  return {
    totalPartidos,
    partidosOver,
    partidosUnder,
    porcentajeOver,
    promedioTotal,
    promedioVsLinea,
    rachaActual,
    tendencia,
    ultimos5Promedio,
    anteriores5Promedio,
  };
}

// ══════════════════════════════════════════════════════════════
// HOOK PRINCIPAL
// ══════════════════════════════════════════════════════════════

/**
 * Hook para obtener historial de partidos con filtros avanzados
 * y cálculos de estadísticas OVER/UNDER
 */
export function useHistorialEquipoExtendido(
  equipoId: string,
  config: ConfiguracionHistorial
): UseHistorialEquipoExtendidoReturn {
  const [partidosBase, setPartidosBase] = useState<PartidoHistorial[]>([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Cargar historial cuando cambian los filtros de servidor
  const cargarHistorial = useCallback(async () => {
    if (!equipoId) {
      setPartidosBase([]);
      return;
    }

    setCargando(true);
    setError(null);

    try {
      // Determinar filtro de ubicación para la API
      const comoLocal =
        config.ubicacion === 'TODOS' ? undefined : config.ubicacion === 'LOCAL';

      const respuesta = await obtenerHistorialEquipo(equipoId, {
        limite: config.cantidad,
        comoLocal,
        orden: 'desc',
      });

      const partidosMapeados = respuesta.partidos.map(mapearPartido);
      setPartidosBase(partidosMapeados);
    } catch (err) {
      const mensaje = err instanceof Error ? err.message : 'Error al cargar historial';
      setError(mensaje);
      setPartidosBase([]);
    } finally {
      setCargando(false);
    }
  }, [equipoId, config.cantidad, config.ubicacion]);

  // Efecto para cargar datos
  useEffect(() => {
    cargarHistorial();
  }, [cargarHistorial]);

  // Transformar partidos con datos del mercado seleccionado
  const partidosConMercado = useMemo<PartidoConMercado[]>(() => {
    return partidosBase.map((partido) => {
      const totalMercado = obtenerTotalParaMercado(partido, config.mercado);
      const resultadoMercado = obtenerResultadoParaMercado(partido, config.mercado);
      const esOver = totalMercado > config.linea;
      const margenVsLinea = totalMercado - config.linea;

      return {
        ...partido,
        totalMercado,
        resultadoMercado,
        esOver,
        margenVsLinea,
      };
    });
  }, [partidosBase, config.mercado, config.linea]);

  // Calcular estadísticas derivadas
  const estadisticas = useMemo<EstadisticasOverUnder | null>(() => {
    if (partidosConMercado.length === 0) return null;
    return calcularEstadisticasOverUnder(partidosConMercado, config.linea);
  }, [partidosConMercado, config.linea]);

  return {
    partidos: partidosConMercado,
    estadisticas,
    cargando,
    error,
    recargar: cargarHistorial,
  };
}
