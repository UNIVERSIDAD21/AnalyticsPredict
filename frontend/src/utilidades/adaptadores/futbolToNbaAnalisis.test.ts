import { describe, it, expect } from 'vitest';
import { adaptarAnalisisFutbolAResultadoAnalisis } from './futbolToNbaAnalisis';
import type { AnalisisFutbolResponse, PartidoFutbolEstadistico } from '../../tipos/futbol';

const baseAnalisis = {
  exito: true,
  partido: {
    id: 'p1',
    competicion: 'c1',
    competicionNombre: 'Liga X',
    fechaPartido: '2026-04-03T10:00:00Z',
    equipoLocal: 'eq-local',
    equipoLocalNombre: 'Local',
    equipoVisitante: 'eq-visita',
    equipoVisitanteNombre: 'Visitante',
    estado: 'PROGRAMADO',
  },
  timestampAnalisis: '2026-04-03T10:00:00Z',
  objetivo: {
    estado: 'disponible',
    mercado: 'GOLES_FT',
    lado: 'OVER',
    linea: 2.5,
    unidad: 'goles',
    mediaObjetivo: 2.8,
    desviacionObjetivo: 0.9,
    probabilidadesObjetivo: { over: 0.6, under: 0.4 },
  },
  mercadosGoles: { GOLES_FT: { mercado: 'GOLES_FT', media: 2.8, std: 0.9, probabilidades: [{ linea: 2.5, overCalibrada: 0.6, underCalibrada: 0.4 }] } },
  mercadosCorners: {},
  mercadosDisparos: {},
  recomendaciones: [{ mercado: 'GOLES_FT', lado: 'OVER', linea: 2.5, probabilidad: 0.6, confianza: 'MEDIA' }],
  modeloVersion: 'v1',
} as unknown as AnalisisFutbolResponse;

const contexto: { h2h: PartidoFutbolEstadistico[]; historialLocal: PartidoFutbolEstadistico[]; historialVisitante: PartidoFutbolEstadistico[] } = {
  h2h: [
    {
      id: 'h2h-1',
      fechaPartido: '2026-03-01T10:00:00Z',
      equipoLocalId: 'eq-local',
      equipoVisitanteId: 'eq-visita',
      equipoLocalNombre: 'Local',
      equipoVisitanteNombre: 'Visitante',
      golesLocal: 1,
      golesVisitante: 2,
      cornersLocal: 7,
      cornersVisitante: 4,
      cornersLocal1t: 3,
      cornersVisitante1t: 1,
      disparosLocal: 12,
      disparosVisitante: 9,
      disparosArcoLocal: 5,
      disparosArcoVisitante: 3,
    },
  ],
  historialLocal: [],
  historialVisitante: [],
};

describe('futbolToNbaAnalisis market-aware contexto', () => {
  it('usa corners del mercado objetivo y no mezcla con goles', () => {
    const analisis = {
      ...baseAnalisis,
      objetivo: { ...baseAnalisis.objetivo, mercado: 'CORNERS_1T', linea: 3.5 },
      mercadosGoles: {},
      mercadosCorners: {
        CORNERS_1T: { mercado: 'CORNERS_1T', media: 4.2, std: 1.0, probabilidades: [{ linea: 3.5, overCalibrada: 0.61, underCalibrada: 0.39 }] },
      },
      recomendaciones: [{ mercado: 'CORNERS_1T', lado: 'OVER', linea: 3.5, probabilidad: 0.61, confianza: 'MEDIA' }],
    };

    const out = adaptarAnalisisFutbolAResultadoAnalisis(analisis as unknown as AnalisisFutbolResponse, contexto);
    expect(out.contexto?.h2h?.promedio_total).toBe(4); // 3+1 corners 1T
  });

  it('usa disparos a puerta para mercado DISPAROS_ARCO_FT', () => {
    const analisis = {
      ...baseAnalisis,
      objetivo: { ...baseAnalisis.objetivo, mercado: 'DISPAROS_ARCO_FT', linea: 7.5 },
      mercadosGoles: {},
      mercadosDisparos: {
        DISPAROS_ARCO_FT: { mercado: 'DISPAROS_ARCO_FT', media: 8.2, std: 1.1, probabilidades: [{ linea: 7.5, overCalibrada: 0.58, underCalibrada: 0.42 }] },
      },
      recomendaciones: [{ mercado: 'DISPAROS_ARCO_FT', lado: 'OVER', linea: 7.5, probabilidad: 0.58, confianza: 'MEDIA' }],
    };

    const out = adaptarAnalisisFutbolAResultadoAnalisis(analisis as unknown as AnalisisFutbolResponse, contexto);
    expect(out.contexto?.h2h?.promedio_total).toBe(8); // 5+3 disparos arco
  });

  it('sin recomendación del mercado objetivo no emite mensaje de coincidencia', () => {
    const analisis = {
      ...baseAnalisis,
      objetivo: { ...baseAnalisis.objetivo, mercado: 'CORNERS_LOCAL_1T', linea: 5.0 },
      recomendaciones: [],
    };

    const out = adaptarAnalisisFutbolAResultadoAnalisis(analisis as unknown as AnalisisFutbolResponse, contexto);
    expect(out.mensaje_apuesta).toBe('Sin recomendación disponible');
  });

  it('alinea total H2H al tamaño de muestra canónica cuando backend la reporta', () => {
    const analisis = {
      ...baseAnalisis,
      objetivo: {
        ...baseAnalisis.objetivo,
        calidadDatos: {
          muestras: { h2h: 1, localHome: 0, visitanteAway: 0, localGlobal: 0, visitanteGlobal: 0, liga: 0 },
          rangoTemporal: { fechaMin: null, fechaMax: null },
          temporadasIncluidas: [],
          competicionesIncluidas: [],
          muestraInsuficiente: true,
          datosIncompletos: true,
          penalizacionesAplicadas: [],
        },
      },
    };

    const ctx = {
      ...contexto,
      h2h: [...contexto.h2h, { ...contexto.h2h[0], id: 'h2h-2' }],
    };

    const out = adaptarAnalisisFutbolAResultadoAnalisis(analisis as unknown as AnalisisFutbolResponse, ctx);
    expect(out.contexto?.h2h?.total_partidos).toBe(1);
    expect(out.contexto?.h2h?.partidos?.length).toBe(1);
  });
});
