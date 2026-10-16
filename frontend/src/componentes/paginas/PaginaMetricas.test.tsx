import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { MetricaMercado, ParametrosMetricasCalibracion } from '../../tipos';
import { PaginaMetricas } from './PaginaMetricas';

const servicios = vi.hoisted(() => ({ metricas: vi.fn(), curva: vi.fn(), recargar: vi.fn() }));
vi.mock('../../servicios/metricas', () => ({
  obtenerMetricasCalibracion: servicios.metricas, obtenerCurvaCalibracion: servicios.curva,
}));
vi.mock('../../hooks', () => ({ useMetricasBitacora: () => ({
  datos: null, estado: 'exito', error: null, recargar: servicios.recargar,
}) }));
vi.mock('../organismos', () => ({ Encabezado: () => null, GraficoCurvaCalibracion: () => <div>Curva</div> }));
vi.mock('../moleculas', () => ({ AlertasCalibracion: () => null, MensajeError: () => <div>Error</div> }));

function metrica(mercado: MetricaMercado['mercado'], serie: 'raw' | 'calibrada'): MetricaMercado {
  return { mercado, serie, n_predicciones: serie === 'raw' ? 3 : 1, n_raw: 3, n_calibradas: 1,
    n_excluidas_probabilidad: serie === 'raw' ? 0 : 2, n_excluidos_push: 0, n_excluidos_outcome_dudoso: 0,
    estado_calidad: 'VALIDO_DESCRIPTIVO', periodo: {}, brier_score: .3,
    brier_score_raw: .3, brier_score_calibrado: .01, log_loss: .4, ece: .1, mce: .2,
    mae_media: null, rmse_media: null, sesgo_media: null, calibrador_activo: null, calibrador_id: null,
    mejora_vs_raw: null, base_rate: .5, sharpness: .09, suficiente_data: false, advertencias: [] };
}
beforeEach(() => {
  vi.clearAllMocks();
  servicios.metricas.mockImplementation(async (params: ParametrosMetricasCalibracion) => ({
    exito: true, serie: params.serie, modelo_version_id: params.modelo_version_id ?? null,
    periodo: { inicio: '2026-01-01', fin: '2026-01-31' }, timestamp_calculo: '2026-10-16T17:00:00Z',
    metricas_por_mercado: [metrica('Q1', params.serie ?? 'raw'), metrica('COMPLETO', params.serie ?? 'raw')],
    alertas_activas: [],
  }));
  servicios.curva.mockResolvedValue({});
});
afterEach(cleanup);

describe('Filtros comunes de calibración', () => {
  it('envía serie y versión a resumen y curva y conserva n de muestras pequeñas', async () => {
    render(<PaginaMetricas />);
    await screen.findByText('3 / 1');
    expect(screen.getByText('Muestra pequeña')).toBeTruthy();
    expect(screen.getAllByText('0.300').length).toBeGreaterThan(0);
    fireEvent.change(screen.getByLabelText('Probabilidades'), { target: { value: 'calibrada' } });
    await waitFor(() => expect(servicios.metricas).toHaveBeenLastCalledWith(expect.objectContaining({ serie: 'calibrada' })));
    await waitFor(() => expect(servicios.curva).toHaveBeenLastCalledWith(expect.objectContaining({ serie: 'calibrada' })));
    fireEvent.change(screen.getByLabelText('Versión de modelo (opcional)'), { target: { value: '17' } });
    await waitFor(() => expect(servicios.metricas).toHaveBeenLastCalledWith(expect.objectContaining({ serie: 'calibrada', modelo_version_id: 17 })));
    await waitFor(() => expect(servicios.curva).toHaveBeenLastCalledWith(expect.objectContaining({ serie: 'calibrada', modelo_version_id: 17 })));
    await screen.findByText(/No certificado · Serie calibrada/);
    expect(screen.getByText(/Modelo 17/)).toBeTruthy();
  });
});
