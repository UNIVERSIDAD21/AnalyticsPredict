import { describe, it, expect, vi, afterEach } from 'vitest';
import axios, { AxiosError } from 'axios';
import { clienteAPI, extraerMensajeError } from './api';
import { obtenerTemporadasEquipos } from './equipos';

afterEach(() => vi.restoreAllMocks());

describe('carga de temporadas concurrente', () => {
  it('serializa todos los IDs sin corchetes y permite cancelar una selección anterior', async () => {
    const controller = new AbortController();
    const get = vi.spyOn(clienteAPI, 'get').mockResolvedValue({ data: { exito: true, temporadas: [] } });
    await obtenerTemporadasEquipos(['a', 'b'], controller.signal);
    const config = get.mock.calls[0][1]!;
    expect(config.signal).toBe(controller.signal);
    const uri = axios.getUri({ ...config, url: '/api/equipos/temporadas' });
    expect(uri).toBe('/api/equipos/temporadas?equipo_ids=a&equipo_ids=b');
  });
  it('un timeout no se presenta como un mensaje técnico ni como una conexión perdida', () => {
    const error = new AxiosError('timeout of 30000ms exceeded', 'ECONNABORTED');
    expect(extraerMensajeError(error)).toBe('El servidor tardó demasiado en responder. Intenta cargar de nuevo.');
    expect(clienteAPI.defaults.timeout).toBe(30000);
  });
});
