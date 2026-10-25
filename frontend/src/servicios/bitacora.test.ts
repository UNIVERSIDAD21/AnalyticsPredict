import { afterEach, describe, expect, it, vi } from 'vitest';
import { clienteAPI } from './api';
import { crearApuesta, listarApuestasAnalizadas, obtenerResumenApuestas, resolverPendientesBitacora } from './bitacora';
import { listarBitacoraUnificada } from './combinadas';
import type { PeticionCrearApuesta, RespuestaApuesta } from '../tipos';

afterEach(() => vi.restoreAllMocks());

describe('contrato v2 de bitácora', () => {
  it('completa finalizadas solo por POST explícito y conserva motivos de pendientes', async () => {
    const resumen = { resueltas: 3, pendientes: 1, errores: 0, importes_no_disponibles: 1,
      motivos_pendientes: { sin_datos_mercado: 1 } };
    const post = vi.spyOn(clienteAPI, 'post').mockResolvedValue({ data: { exito: true, resumen } });
    expect(await resolverPendientesBitacora()).toEqual(resumen);
    expect(post).toHaveBeenCalledWith('/api/bitacora/resolver');
  });

  it('no presenta un cierre fallido como completado', async () => {
    vi.spyOn(clienteAPI, 'post').mockResolvedValue({ data: { exito: false } });
    await expect(resolverPendientesBitacora()).rejects.toThrow('No se pudieron completar');
  });
  it('envía cuota manual Euroliga a la bitácora y conserva analíticas no disponibles como null', async () => {
    const payload: PeticionCrearApuesta = {
      partido_id: 'fixture-euro', competicion_codigo: 'euroleague',
      equipo_local: 'Real Madrid', equipo_visitante: 'Maccabi', fecha_partido: '2026-10-22',
      mercado: 'COMPLETO', lado: 'UNDER', linea: 170.5, cuota: 1.91, stake: 25,
      probabilidad_sistema: null, confianza_sistema: null, valor_esperado: null,
      razones: [{ tipo: 'trazabilidad_euroliga', analisis_id: 'analisis-euro' }],
    };
    const respuesta: RespuestaApuesta = {
      exito: true,
      apuesta: {
        id: 'apuesta-euro', partido_id: 'fixture-euro', competicion_id: 'competencia-euro',
        competicion_nombre: 'EuroLeague', equipo_local: 'Real Madrid', equipo_visitante: 'Maccabi',
        fecha_partido: '2026-10-22', mercado: 'COMPLETO', lado: 'UNDER', linea: 170.5,
        cuota: 1.91, stake: 25, probabilidad_sistema: null, confianza_sistema: null,
        valor_esperado: null, resultado: 'PENDIENTE', ganancia: 0,
      },
    };
    const post = vi.spyOn(clienteAPI, 'post').mockResolvedValue({ data: respuesta });

    const guardada = await crearApuesta(payload);

    expect(post).toHaveBeenCalledWith('/api/bitacora', payload);
    expect(guardada.apuesta.competicion_nombre).toBe('EuroLeague');
    expect(guardada.apuesta.cuota).toBe(1.91);
    expect(guardada.apuesta.probabilidad_sistema).toBeNull();
    expect(guardada.apuesta.confianza_sistema).toBeNull();
    expect(guardada.apuesta.valor_esperado).toBeNull();
  });

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
