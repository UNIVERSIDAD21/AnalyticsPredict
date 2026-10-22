import { afterEach, expect, it, vi } from 'vitest';
import { clienteAPI } from './api';
import { obtenerPartidosProximos } from './partidos';

afterEach(() => vi.restoreAllMocks());

it('solicita el horizonte y el límite configurados para cargar todos los próximos partidos', async () => {
  const get = vi.spyOn(clienteAPI, 'get').mockResolvedValue({
    data: { exito: true, partidos: [], total: 0 },
  });

  await obtenerPartidosProximos(30, 500);

  expect(get).toHaveBeenCalledWith('/api/partidos/proximos', {
    params: { dias: 30, limite: 500 },
  });
});

it('limita los parámetros a los rangos aceptados por la API', async () => {
  const get = vi.spyOn(clienteAPI, 'get').mockResolvedValue({
    data: { exito: true, partidos: [], total: 0 },
  });

  await obtenerPartidosProximos(90, 999);

  expect(get).toHaveBeenCalledWith('/api/partidos/proximos', {
    params: { dias: 30, limite: 500 },
  });
});

it('permite aislar el selector NBA sin cambiar el calendario general', async () => {
  const get = vi.spyOn(clienteAPI, 'get').mockResolvedValue({ data: { exito: true, partidos: [], total: 0 } });
  await obtenerPartidosProximos(7, 500, 'nba');
  expect(get).toHaveBeenCalledWith('/api/partidos/proximos', { params: { dias: 7, limite: 500, competicion: 'nba' } });
});
