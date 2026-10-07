import { afterEach, expect, it, vi } from 'vitest';
import { clienteAPI } from '../api';
import { obtenerApuestas } from './apuestas';

afterEach(() => vi.restoreAllMocks());

it('conserva N/D de ganancia y ROI en el resumen de apuestas', async () => {
  vi.spyOn(clienteAPI, 'get').mockResolvedValue({ data: {
    apuestas: [], resumen: { total: 2, ganadas: 1, perdidas: 1,
      stake_total: 20, ganancia_neta: null, roi: null, win_rate: 50 },
  } });
  const { resumen } = await obtenerApuestas();
  expect(resumen.gananciaNeta).toBeNull();
  expect(resumen.roi).toBeNull();
  expect(resumen.winRate).toBe(50);
});
