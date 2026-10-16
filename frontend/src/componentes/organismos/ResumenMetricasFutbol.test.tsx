import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { ResumenMetricasFutbol } from './ResumenMetricasFutbol';
import type { EstadoModeloFutbol } from '../../tipos/futbol';

afterEach(cleanup);
const modelo: EstadoModeloFutbol = {
  tipoModelo: 'GOLES', version: '1', fechaEntrenamiento: '2026-10-16T02:00:00Z',
  mae: 0.1, rmse: null, r2: 0.99, nPartidosEntrenamiento: 100, nEquipos: 20,
  ambitoMetricas: 'AJUSTE_IN_SAMPLE_NO_VALIDACION', cargado: false,
};
describe('Estado ML fútbol sin falsa validación', () => {
  it('no califica excelente un ajuste alto y conserva N/D', () => {
    render(<ResumenMetricasFutbol metricas={{ modelos: [modelo], calibracion: [], rendimiento: [] }} />);
    expect(screen.getByText('no validado')).toBeTruthy();
    expect(screen.queryByText('excelente')).toBeNull();
    expect(screen.getByText(/Métricas de ajuste, no de validación temporal/)).toBeTruthy();
    expect(screen.getAllByText('N/D').length).toBeGreaterThan(0);
  });
  it('no crea tarjetas de modelos cuando el almacén no tiene versiones', () => {
    render(<ResumenMetricasFutbol metricas={{ modelos: [], calibracion: [], rendimiento: [] }} />);
    expect(screen.queryByText('Estado de Modelos')).toBeNull();
    expect(screen.queryByText(/Modelo cargado para análisis/)).toBeNull();
  });
});
