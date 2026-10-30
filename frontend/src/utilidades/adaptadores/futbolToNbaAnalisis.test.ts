import { describe, it, expect } from 'vitest';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { ResultadoAnalisis } from '../../componentes/organismos/ResultadoAnalisis';
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
  it('conserva solo líneas originales y no inventa push entero ni calibrador', () => {
    const a = { ...baseAnalisis, mercadosGoles: { GOLES_FT: { ...baseAnalisis.mercadosGoles.GOLES_FT,
      probabilidades: [
        { linea: 2, overRaw: .4, underRaw: .6, overCalibrada: null, underCalibrada: null },
        { linea: 2.5, overRaw: .3, underRaw: .7, overCalibrada: .35, underCalibrada: .65, calibradorId: 'identificado-no-certificado' },
      ] } } };
    const r = adaptarAnalisisFutbolAResultadoAnalisis(a);
    expect(r.metadata.comparacion_guardada).toEqual({ formato: 'lineas-originales-futbol-v1', mercado: 'GOLES_FT', lineas: [
      { linea: 2, over: .4, under: .6, push: null, fuente: 'RAW', calibrador: null },
      { linea: 2.5, over: .35, under: .65, push: 0, fuente: 'CALIBRADA', calibrador: 'identificado-no-certificado' },
    ] });
  });
  it('conserva modo, kickoff y corte sin presentar reconstrucciones como prepartido', () => {
    const analisis = { ...baseAnalisis, modo: 'HISTORICO_RECONSTRUIDO' as const,
      fechaCorte: '2026-04-03T10:00:00Z', modeloVersion: 'heuristico-americas::1.0.0' };
    const out = adaptarAnalisisFutbolAResultadoAnalisis(analisis, contexto);
    expect(out.metadata.modo_analisis).toBe('HISTORICO_RECONSTRUIDO');
    expect(out.metadata.fecha_partido).toBe(analisis.partido.fechaPartido);
    expect(out.metadata.fecha_corte).toBe(analisis.fechaCorte);
    expect(out.metadata.consulta_exploratoria).toBe(true);
    const futuro = adaptarAnalisisFutbolAResultadoAnalisis({ ...analisis, modo: 'PREPARTIDO' }, contexto);
    expect(futuro.metadata.consulta_exploratoria).toBe(true);
    const html = renderToStaticMarkup(createElement(ResultadoAnalisis, { resultado: out }));
    expect(html).toContain('Histórico reconstruido');
    expect(html).toContain('Consulta exploratoria RAW');
    expect(html).toContain('Partido:');
    expect(html).not.toContain('PAPER/SHADOW');
    expect(html).not.toContain('Sin oportunidades de apuesta');
  });
  it('sin partidos no fabrica promedios 0–0 ni forma estable', () => {
    const r=adaptarAnalisisFutbolAResultadoAnalisis(baseAnalisis,{h2h:[],historialLocal:[],historialVisitante:[]});
    expect(r.contexto?.forma_equipo).toBeNull();expect(r.contexto?.forma_rival).toBeNull();
  });
  it('calcula la forma desde el ID exacto de cada equipo y no atribuye filas ajenas al visitante', () => {
    const local = contexto.h2h[0];
    const vuelta = { ...local, id: 'vuelta', equipoLocalId: 'eq-visita', equipoVisitanteId: 'eq-local' };
    const ajeno = { ...local, id: 'ajeno', equipoLocalId: 'otro-1', equipoVisitanteId: 'otro-2' };
    const out = adaptarAnalisisFutbolAResultadoAnalisis(baseAnalisis, {
      h2h: [local,vuelta,ajeno], historialLocal: [local,vuelta,ajeno], historialVisitante: [local,vuelta,ajeno],
    });
    expect(out.contexto?.h2h?.total_partidos).toBe(2);
    expect(out.contexto?.forma_equipo?.victorias).toBe(1);
    expect(out.contexto?.forma_equipo?.derrotas).toBe(1);
    expect(out.contexto?.forma_rival?.victorias).toBe(1);
    expect(out.contexto?.forma_rival?.derrotas).toBe(1);
  });
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

  it('propaga severidad cuando mercado objetivo está fuera de coverage', () => {
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
          penalizacionesAplicadas: ['estado_mercados_vacio', 'mercado_objetivo_fuera_estado_mercados'],
        },
      },
      recomendaciones: [],
    };

    const out = adaptarAnalisisFutbolAResultadoAnalisis(analisis as unknown as AnalisisFutbolResponse, contexto);
    expect((out.advertencias_contexto || []).join(' ')).toContain('Estado de mercados vacío');
    expect((out.advertencias_contexto || []).join(' ')).toContain('Mercado objetivo fuera del estado de mercados');
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
