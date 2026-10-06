import { afterEach, describe, expect, it, vi } from 'vitest';
import { clienteAPI } from './api';
import { listarApuestasAnalizadas, obtenerResumenApuestas } from './bitacora';
import { listarBitacoraUnificada } from './combinadas';

afterEach(() => vi.restoreAllMocks());

describe('contrato v2 de bitácora', () => {
  it('muestra registros reales del envelope v2 y pide explícitamente esa versión', async () => {
    const get = vi.spyOn(clienteAPI, 'get').mockResolvedValue({ data: {
      ok: true, data: { total: 1, pagina: 1, total_paginas: 1, registros: [{ id: 'fila-1' }] },
    } });
    const resultado = await listarBitacoraUnificada({ pagina: 1 });
    expect(resultado.registros).toHaveLength(1);
    expect(resultado.total).toBe(1);
    expect(get).toHaveBeenCalledWith('/api/bitacora/unificada', { params: { pagina: 1, version: 'v2' } });
  });

  it('no convierte un error o un contrato desconocido en una bitácora vacía', async () => {
    vi.spyOn(clienteAPI, 'get').mockResolvedValueOnce({ data: { ok: false, data: { registros: [] } } })
      .mockResolvedValueOnce({ data: { exito: true, registros: [] } });
    await expect(listarBitacoraUnificada({})).rejects.toThrow();
    await expect(listarBitacoraUnificada({})).rejects.toThrow();
  });

  it('lee resumen y analizadas con nombres y estados canónicos', async () => {
    const get = vi.spyOn(clienteAPI, 'get')
      .mockResolvedValueOnce({ data: { ok: true, data: { resumen: { por_deporte: [], por_mercado: [] } } } })
      .mockResolvedValueOnce({ data: { ok: true, data: { total: 16, items: [{ id: 1, estado: 'FINALIZADA' }] } } });
    expect((await obtenerResumenApuestas()).resumen.por_deporte).toEqual([]);
    const analizadas = await listarApuestasAnalizadas({ limite: 1 });
    expect(analizadas.total).toBe(16);
    expect(analizadas.items[0].estado).toBe('FINALIZADA');
    expect(get).toHaveBeenNthCalledWith(2, '/api/bitacora/apuestas-analizadas', {
      params: { limite: 1, version: 'v2' },
    });
  });

  it('rechaza un resumen sin listas segmentadas', async () => {
    vi.spyOn(clienteAPI, 'get').mockResolvedValue({ data: { ok: true, data: { resumen: {} } } });
    await expect(obtenerResumenApuestas()).rejects.toThrow('Contrato de resumen');
  });
});
