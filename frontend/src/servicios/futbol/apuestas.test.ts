import { afterEach, expect, it, vi } from 'vitest';
import { clienteAPI } from '../api';
import { crearApuesta, obtenerApuestas } from './apuestas';

afterEach(() => vi.restoreAllMocks());

it('conserva N/D de ganancia y ROI en el resumen de apuestas', async () => {
  vi.spyOn(clienteAPI, 'get').mockResolvedValue({ data: {
    apuestas: [], resumen: { total: 2, ganadas: 1, perdidas: 1,
      stake_total: null, ganancia_neta: null, roi: null, win_rate: 50 },
  } });
  const { resumen } = await obtenerApuestas();
  expect(resumen.gananciaNeta).toBeNull();
  expect(resumen.roi).toBeNull();
  expect(resumen.stakeTotal).toBeNull();
  expect(resumen.winRate).toBe(50);
});

it('envía la selección a fútbol y conserva N/D en campos analíticos no disponibles', async () => {
  const post = vi.spyOn(clienteAPI, 'post').mockResolvedValue({ data: {
    id: 'apuesta-1', partido_id: 'partido-1', mercado: 'GOLES_FT', lado: 'UNDER',
    linea: 2.5, cuota: 0, stake: 10, estado: 'PENDIENTE', probabilidad_sistema: null,
    confianza: null, valor_esperado: null, ganancia_potencial: 0,
    fecha_creacion: '2026-10-22T12:00:00Z',
  } });

  const apuesta = await crearApuesta({
    partidoId: 'partido-1', mercado: 'GOLES_FT', lado: 'UNDER', linea: 2.5,
    cuota: 0, stake: 10, probabilidadSistema: null, confianzaSistema: null, valorEsperado: null,
  });

  expect(post).toHaveBeenCalledWith('/api/futbol/apuestas', expect.objectContaining({
    partido_id: 'partido-1', mercado: 'GOLES_FT', lado: 'UNDER', linea: 2.5,
    cuota: 0, stake: 10, probabilidad_sistema: null, confianza_sistema: null, valor_esperado: null,
  }));
  expect(apuesta.probabilidadSistema).toBeNull();
  expect(apuesta.confianza).toBeNull();
  expect(apuesta.valorEsperado).toBeNull();
});
