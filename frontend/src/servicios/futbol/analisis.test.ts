import { describe, it, expect } from 'vitest';
import { transformarObjetivoAnalisis } from './analisis';

describe('transformarObjetivoAnalisis', () => {
  it('mapea calidad_datos al contrato camelCase', () => {
    const out = transformarObjetivoAnalisis({
      estado: 'datos_insuficientes',
      mercado: 'CORNERS_LOCAL_1T',
      lado: 'OVER',
      linea: 5.5,
      unidad: 'corners',
      probabilidades_objetivo: { over: null, under: null },
      bloque_base: { estado: 'datos_insuficientes', media: null, desviacion: null, probabilidades: { over: null, under: null } },
      bloque_ajustado: { estado: 'no_disponible', media: null, desviacion: null, probabilidades: { over: null, under: null } },
      devig: { estado: 'datos_insuficientes', advertencias: [] },
      calibracion: { estado: 'datos_insuficientes' },
      score_riesgo: { estado: 'datos_insuficientes' },
      disponibilidad_datos: { reales_disponibles: [], no_disponibles: [], degradacion_controlada: [], datos_insuficientes: [] },
      calidad_datos: {
        muestras: { h2h: 3, local_home: 12, visitante_away: 10, local_global: 70, visitante_global: 65, liga: 100 },
        rango_temporal: { fecha_min: '2024-01-01T00:00:00+00:00', fecha_max: '2026-03-31T00:00:00+00:00' },
        temporadas_incluidas: ['2025-26'],
        competiciones_incluidas: ['laliga'],
        muestra_insuficiente: true,
        datos_incompletos: true,
        penalizaciones_aplicadas: ['muestra_insuficiente'],
      },
    });

    expect(out.calidadDatos.muestras.h2h).toBe(3);
    expect(out.calidadDatos.muestras.localHome).toBe(12);
    expect(out.calidadDatos.rangoTemporal.fechaMin).toContain('2024-01-01');
    expect(out.calidadDatos.muestraInsuficiente).toBe(true);
    expect(out.calidadDatos.penalizacionesAplicadas).toContain('muestra_insuficiente');
  });
});
