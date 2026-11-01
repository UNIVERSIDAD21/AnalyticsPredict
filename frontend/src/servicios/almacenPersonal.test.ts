import { AxiosError } from 'axios';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { clienteAPI } from './api';
import { conservarPersonal, editarEntradaDuradera, guardarConsultaDuradera, importarNavegador, prepararImportacionNavegador } from './almacenPersonal';
import { olvidarCachePersonal, type EstadoPersonalPC } from './personalCache';
import { CLAVE_CUADERNO, type EntradaCuaderno } from './cuadernoLocal';

vi.mock('./api', () => ({ clienteAPI: { get: vi.fn(), post: vi.fn() }, extraerMensajeError: () => 'No se confirmó el guardado' }));
const entrada = (id = 'legado', notas = ''): EntradaCuaderno => ({ id, titulo: 'Peña — Bogotá', liga: 'nba', guardadoEn: '2026-10-21T01:02:03.123Z', tipo: 'resultado', snapshot: { probabilidad: 0.6281749820031, cero: 0, ausente: null }, notas, etiquetas: [], favorito: false });
let server: EstadoPersonalPC;
beforeEach(() => {
  vi.resetAllMocks(); localStorage.clear(); olvidarCachePersonal();
  server = { formato: 'almacen-personal-v1', existe: false, revision: 0, sha256: null, actualizadoEn: null, datos: { cuaderno: [], favoritos: [], apariencia: null } };
  vi.mocked(clienteAPI.get).mockImplementation(async () => ({ data: structuredClone(server) }));
  vi.mocked(clienteAPI.post).mockImplementation(async (url, payload) => {
    if (String(url).endsWith('/respaldo')) return { data: { revision: server.revision } };
    const body = payload as { revision: number; datos: EstadoPersonalPC['datos'] };
    if (body.revision !== server.revision) throw new AxiosError('conflicto', 'ERR_BAD_REQUEST', undefined, undefined, { status: 409 } as never);
    server = { ...server, existe: true, revision: server.revision + 1, sha256: 'sha-' + (server.revision + 1), datos: structuredClone(body.datos) };
    return { data: { estado: structuredClone(server), revision_guardada: server.revision } };
  });
});
afterEach(() => { olvidarCachePersonal(); localStorage.clear(); });

it('guarda en el PC, relee y conserva NULL/ceros/probabilidad sin escribir localStorage', async () => {
  const original = entrada();
  const e = await guardarConsultaDuradera(original);
  expect(e.snapshot).toEqual(original.snapshot);
  expect(server.datos.cuaderno[0]).toEqual(e);
  expect(clienteAPI.post).toHaveBeenCalledTimes(1);
  expect(clienteAPI.get).toHaveBeenCalledTimes(2);
  expect(localStorage.length).toBe(0);
});
it('un resultado incierto se confirma leyendo sin repetir el POST', async () => {
  vi.mocked(clienteAPI.post).mockImplementationOnce(async (_url, payload) => {
    server = { ...server, existe: true, revision: 1, sha256: 'sha-1', datos: structuredClone((payload as { datos: EstadoPersonalPC['datos'] }).datos) };
    throw new AxiosError('timeout', 'ECONNABORTED');
  });
  const e = await guardarConsultaDuradera(entrada());
  expect(server.datos.cuaderno[0].id).toBe(e.id);
  expect(clienteAPI.post).toHaveBeenCalledTimes(1);
});
it('no anuncia éxito si la lectura de confirmación no coincide', async () => {
  vi.mocked(clienteAPI.post).mockResolvedValueOnce({ data: { estado: { ...server, revision: 1, sha256: 'nueva' } } });
  await expect(conservarPersonal(server.datos, 0)).rejects.toThrow(/cambió/);
  expect(localStorage.length).toBe(0);
});
it('rechaza editar una nota obsoleta sin pisar la de otra pestaña', async () => {
  server.datos.cuaderno = [entrada('a', 'La otra pestaña')]; server.revision = 2;
  await expect(editarEntradaDuradera(entrada('a', 'Anterior'), { notas: 'Mi borrador', etiquetas: [], favorito: false })).rejects.toThrow(/otra pestaña/);
  expect(clienteAPI.post).not.toHaveBeenCalled();
  expect(server.datos.cuaderno[0].notas).toBe('La otra pestaña');
});
it('preview sin POST y mezcla conservadora con backup; conserva literalmente los originales', async () => {
  const original = JSON.stringify([entrada('mismo', 'Navegador'), entrada('nueva')]);
  localStorage.setItem(CLAVE_CUADERNO, original);
  server.existe = true; server.revision = 3; server.datos.cuaderno = [entrada('mismo', 'PC')];
  const plan = await prepararImportacionNavegador();
  expect(plan.nuevas).toBe(1); expect(plan.conflictos).toBe(1);
  expect(clienteAPI.post).not.toHaveBeenCalled();
  await importarNavegador(plan);
  expect(server.datos.cuaderno.find(e => e.id === 'mismo')?.notas).toBe('PC');
  expect(server.datos.cuaderno.find(e => e.id === 'nueva')?.snapshot).toEqual(entrada().snapshot);
  expect(localStorage.getItem(CLAVE_CUADERNO)).toBe(original);
  expect(clienteAPI.post).toHaveBeenCalledTimes(2); // Respaldo anterior y commit, sin POST deportivo.
});
it('no importa si el navegador cambió después de la vista previa', async () => {
  localStorage.setItem(CLAVE_CUADERNO, JSON.stringify([entrada()]));
  const plan = await prepararImportacionNavegador();
  localStorage.setItem(CLAVE_CUADERNO, '[]');
  await expect(importarNavegador(plan)).rejects.toThrow(/cambiaron/);
  expect(clienteAPI.post).not.toHaveBeenCalled();
});
it('un409 no se reintenta ni guarda un fallback en el navegador', async () => {
  vi.mocked(clienteAPI.post).mockRejectedValueOnce(new AxiosError('conflicto', 'ERR_BAD_REQUEST', undefined, undefined, { status: 409 } as never));
  await expect(guardarConsultaDuradera(entrada())).rejects.toThrow(/otra pestaña/);
  expect(clienteAPI.post).toHaveBeenCalledTimes(1); expect(localStorage.length).toBe(0);
});
