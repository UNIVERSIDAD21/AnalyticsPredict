/** Servidor HTTP sintético para pruebas de interfaz, no una migración del producto. */
import { AxiosError } from 'axios';
import { vi } from 'vitest';
import { clienteAPI } from '../servicios/api';
import { leerCuadernoNavegador } from '../servicios/cuadernoLocal';
import { leerFavoritosNavegador } from '../servicios/favoritosLocales';
import { olvidarCachePersonal, recibirPersonal, type EstadoPersonalPC } from '../servicios/personalCache';

export function instalarAlmacenPersonalSimulado() {
  olvidarCachePersonal();
  let current: EstadoPersonalPC | null = null;
  const get = clienteAPI.get.bind(clienteAPI), post = clienteAPI.post.bind(clienteAPI);
  const leer = () => {
    if (!current) current = { formato: 'almacen-personal-v1', existe: false, revision: 0, sha256: null, actualizadoEn: null,
      datos: { cuaderno: leerCuadernoNavegador(), favoritos: leerFavoritosNavegador(), apariencia: null } };
    return current;
  };
  vi.spyOn(clienteAPI, 'get').mockImplementation((...args) => {
    if (args[0] === '/api/personal') return Promise.resolve({ data: structuredClone(leer()) }) as ReturnType<typeof clienteAPI.get>;
    return get(...args);
  });
  vi.spyOn(clienteAPI, 'post').mockImplementation((...args) => {
    if (args[0] === '/api/personal/respaldo') return Promise.resolve({ data: { revision: leer().revision } }) as ReturnType<typeof clienteAPI.post>;
    if (args[0] !== '/api/personal') return post(...args);
    const body = args[1] as { datos: EstadoPersonalPC['datos']; revision: number };
    if (leer().revision !== body.revision) return Promise.reject(new AxiosError('conflicto', 'ERR_BAD_REQUEST', undefined, undefined, { status: 409 } as never));
    current = { ...leer(), existe: true, revision: leer().revision + 1, sha256: 'hash-' + (leer().revision + 1), datos: structuredClone(body.datos) };
    return Promise.resolve({ data: { estado: structuredClone(current), revision_guardada: current.revision } }) as ReturnType<typeof clienteAPI.post>;
  });
  return { recibir: (mutar: (e: EstadoPersonalPC) => void) => { const next = structuredClone(leer()); mutar(next); next.revision++; current = next; recibirPersonal(next); }, leer };
}
