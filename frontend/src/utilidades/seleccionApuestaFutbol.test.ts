import { describe, expect, it } from 'vitest';
import { prepararApuestaGuardableFutbol } from './seleccionApuestaFutbol';
import type { AnalisisFutbolResponse } from '../tipos/futbol';

const analisis = {
  objetivo: {
    mercado: 'GOLES_FT',
    lado: 'UNDER',
    linea: 2.5,
    probabilidadesObjetivo: { over: 0.38, under: 0.62 },
  },
  recomendaciones: [],
} as unknown as Pick<AnalisisFutbolResponse, 'objetivo' | 'recomendaciones'>;

describe('prepararApuestaGuardableFutbol', () => {
  it('permite guardar la selección del usuario cuando no existe recomendación', () => {
    const guardable = prepararApuestaGuardableFutbol(analisis, {
      mercado: 'GOLES_FT',
      lado: 'UNDER',
      linea: 2.5,
      cuotas: { over: 2.1, under: 1.84 },
      trazabilidad: { idSeleccion: 'seleccion-123' },
    });

    expect(guardable).toMatchObject({
      mercado: 'GOLES_FT',
      lado: 'UNDER',
      linea: 2.5,
      cuota: 1.84,
      probabilidad: 0.62,
      confianza: null,
      valorEsperado: null,
      trazabilidad: 'seleccion-123',
      tieneRecomendacion: false,
    });
  });

  it('conserva N/D cuando probabilidad y recomendación no están disponibles', () => {
    const sinProbabilidad = {
      ...analisis,
      objetivo: { ...analisis.objetivo, probabilidadesObjetivo: { over: null, under: null } },
    } as unknown as Pick<AnalisisFutbolResponse, 'objetivo' | 'recomendaciones'>;

    const guardable = prepararApuestaGuardableFutbol(sinProbabilidad, {
      mercado: 'GOLES_FT',
      lado: 'UNDER',
      linea: 2.5,
      cuotas: {},
      trazabilidad: { idSeleccion: 'seleccion-456' },
    });

    expect(guardable.probabilidad).toBeNull();
    expect(guardable.confianza).toBeNull();
    expect(guardable.valorEsperado).toBeNull();
    expect(guardable.cuota).toBe(0);
  });
});
