import { afterEach, describe, expect, it, vi } from 'vitest';
import { clienteAPI } from '../api';
import { obtenerMetricasRendimiento, obtenerRoiTemporal, obtenerEstadoModelos } from './metricas';

afterEach(() => vi.restoreAllMocks());

describe('ROI fútbol: porcentaje de API, razón de UI y N/D', () => {
  it('convierte 10 % a razón 0.10 y conserva importes faltantes', async () => {
    vi.spyOn(clienteAPI, 'get').mockResolvedValue({ data: { metricas: [
      { mercado: 'GOLES_FT', n_apuestas: 2, roi: 10, win_rate: 0.5, stake_total: 20, ganancia_neta: 2 },
      { mercado: 'CORNERS_FT', n_apuestas: 1, roi: null, win_rate: null, stake_total: 10, ganancia_neta: null },
    ] } });
    const datos = await obtenerMetricasRendimiento();
    expect(datos[0].roi).toBe(0.1);
    expect(datos[1].roi).toBeNull();
    expect(datos[1].gananciaNeta).toBeNull();
    expect(datos[1].winRate).toBeNull();
  });

  it('no convierte el ROI temporal sin muestra en cero', async () => {
    vi.spyOn(clienteAPI, 'get').mockResolvedValue({ data: { serie: [
      { fecha: '2026-10-06', roi: null, stake_acumulado: null, ganancia_acumulada: null },
    ] } });
    expect((await obtenerRoiTemporal())[0]).toMatchObject({ roi: null, stakeAcumulado: null, gananciaAcumulada: null });
  });

  it('no inventa modelos y conserva N/D y ámbito del ajuste', async () => {
    const get = vi.spyOn(clienteAPI, 'get').mockResolvedValueOnce({ data: { modelos: [] } })
      .mockResolvedValueOnce({ data: { modelos: [{ tipo_modelo: 'goles', version: 1, mae: null, rmse: null, r2: 0,
        ambito_metricas: 'AJUSTE_IN_SAMPLE_NO_VALIDACION', cargado: false }] } });
    expect(await obtenerEstadoModelos()).toEqual([]);
    const [modelo] = await obtenerEstadoModelos();
    expect(modelo).toMatchObject({ mae: null, rmse: null, r2: 0, ambitoMetricas: 'AJUSTE_IN_SAMPLE_NO_VALIDACION', cargado: false });
    expect(get).toHaveBeenCalledTimes(2);
  });
});

it('conserva stake agregado N/D sin sustituirlo por cero', async () => {
  vi.spyOn(clienteAPI, 'get').mockResolvedValue({ data: { metricas: [
    { mercado: 'GOLES_FT', n_apuestas: 2, roi: null, win_rate: 0.5, stake_total: null, ganancia_neta: null },
  ] } });
  expect((await obtenerMetricasRendimiento())[0]).toMatchObject({
    stakeTotal: null, gananciaNeta: null, roi: null, nApuestas: 2, winRate: 0.5,
  });
});
