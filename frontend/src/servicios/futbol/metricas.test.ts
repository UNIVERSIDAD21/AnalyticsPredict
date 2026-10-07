import { afterEach, describe, expect, it, vi } from 'vitest';
import { clienteAPI } from '../api';
import { obtenerMetricasRendimiento, obtenerRoiTemporal } from './metricas';

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
      { fecha: '2026-10-06', roi: null, stake_acumulado: 0, ganancia_acumulada: null },
    ] } });
    expect((await obtenerRoiTemporal())[0]).toMatchObject({ roi: null, gananciaAcumulada: null });
  });
});
