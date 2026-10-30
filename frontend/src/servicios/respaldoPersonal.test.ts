import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest';
import { CLAVE_CUADERNO, guardarConsulta, leerCuaderno, type EntradaCuaderno } from './cuadernoLocal';
import { cambiarFavorito, CLAVE_FAVORITOS, favoritoLiga, leerFavoritos } from './favoritosLocales';
import { CLAVE_VISUAL } from './preferenciasVisuales';
import { aplicarRestauracion, crearCopiaRecuperacion, crearRespaldo, prepararRestauracion } from './respaldoPersonal';
const entrada = (id: string): EntradaCuaderno => ({ id, titulo: `Consulta ${id}`, liga: 'wnba', tipo: 'resultado', guardadoEn: '2026-10-30T03:20:00Z',
  notas: 'Peña — Bogotá', etiquetas: ['revisar'], favorito: true, snapshot: { media: 0, probabilidad: null, version: 'original', datos: { a: 1, b: 2 } } });
const respaldo = (cuaderno: EntradaCuaderno[]) => JSON.stringify({ formato: 'analyticspredict-respaldo-personal', version: 1,
  creadoEn: '2026-10-30T12:00:00Z', datos: { cuaderno, favoritos: [favoritoLiga('wnba')], apariencia: { tema: 'claro', densidad: 'compacta', texto: 'grande' } } });
beforeEach(() => { localStorage.clear(); });
afterEach(() => { vi.restoreAllMocks(); });
describe('respaldo y restauración personal', () => {
  it('reconstruye en un navegador vacío notas, favoritos, fechas, ceros y N/D sin cambiar snapshots', () => {
    const original = entrada('original');
    localStorage.setItem(CLAVE_CUADERNO, JSON.stringify([original])); cambiarFavorito(favoritoLiga('wnba'));
    localStorage.setItem(CLAVE_VISUAL, JSON.stringify({ tema: 'claro', densidad: 'compacta', texto: 'grande' }));
    const exportado = JSON.stringify(crearRespaldo()); localStorage.clear();
    const plan = prepararRestauracion(exportado, true); aplicarRestauracion(plan);
    expect(leerCuaderno()).toEqual([original]); expect(leerFavoritos()).toEqual([favoritoLiga('wnba')]);
    expect(document.documentElement.dataset.tema).toBe('claro');
    expect(localStorage.getItem(CLAVE_VISUAL)).toContain('compacta');
  });
  it('mantiene la versión local de cada ID y reconoce duplicados aunque cambie el orden de las claves JSON', () => {
    const local = entrada('local'), conflicto = { ...local, notas: 'Otra nota', snapshot: { NO: 'reemplazar' } };
    const repetida = { ...entrada('repetida'), snapshot: { datos: { b: 2, a: 1 }, version: 'original', probabilidad: null, media: 0 } };
    localStorage.setItem(CLAVE_CUADERNO, JSON.stringify([local, entrada('repetida')]));
    const plan = prepararRestauracion(respaldo([conflicto, repetida, entrada('nueva')]));
    expect([plan.nuevas, plan.repetidas, plan.conflictos]).toEqual([1, 1, 1]);
    aplicarRestauracion(plan); expect(leerCuaderno().find(e => e.id === 'local')).toEqual(local);
    expect(leerCuaderno()).toHaveLength(3);
    expect(prepararRestauracion(respaldo([entrada('nueva')])).nuevas).toBe(0);
  });
  it('importa respaldos antiguos del cuaderno y conserva apariencia y favoritos actuales', () => {
    cambiarFavorito(favoritoLiga('nba'));
    localStorage.setItem(CLAVE_VISUAL, JSON.stringify({ tema: 'oscuro', densidad: 'comoda', texto: 'normal' }));
    aplicarRestauracion(prepararRestauracion(JSON.stringify([entrada('antigua')]), true));
    expect(leerCuaderno()[0]).toEqual(entrada('antigua')); expect(leerFavoritos()).toEqual([favoritoLiga('nba')]);
    expect(localStorage.getItem(CLAVE_VISUAL)).toContain('oscuro');
  });
  it('no cambia la apariencia sin la opción explícita de importación', () => {
    localStorage.setItem(CLAVE_VISUAL, JSON.stringify({ tema: 'oscuro', densidad: 'comoda', texto: 'normal' }));
    aplicarRestauracion(prepararRestauracion(respaldo([entrada('nueva')])));
    expect(localStorage.getItem(CLAVE_VISUAL)).toContain('oscuro');
  });
  it('rechaza una vista previa si se añadió una consulta mientras estaba abierta', () => {
    const plan = prepararRestauracion(respaldo([entrada('importada')]));
    guardarConsulta({ titulo: 'Trabajo posterior', liga: 'nba', tipo: 'base', snapshot: {} });
    expect(() => aplicarRestauracion(plan)).toThrow('cambiaron');
    expect(leerCuaderno()).toHaveLength(1); expect(leerCuaderno()[0].titulo).toBe('Trabajo posterior');
    expect(leerFavoritos()).toEqual([]);
  });
  it('revierte escrituras ya realizadas cuando otra clave se queda sin espacio', () => {
    localStorage.setItem(CLAVE_CUADERNO, JSON.stringify([entrada('previa')]));
    const plan = prepararRestauracion(respaldo([entrada('nueva')]), true);
    const guardar = Storage.prototype.setItem;
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(function (this: Storage, key: string, value: string) {
      if (key === CLAVE_FAVORITOS) throw new Error('QuotaExceededError');
      guardar.call(this, key, value);
    });
    expect(() => aplicarRestauracion(plan)).toThrow('Se recuperaron los datos anteriores');
    expect(leerCuaderno()).toEqual([entrada('previa')]); expect(localStorage.getItem(CLAVE_VISUAL)).toBeNull();
  });
  it.each(['null', '{incompleto', '{"formato":"analyticspredict-respaldo-personal","version":99}', JSON.stringify([entrada('x'), entrada('x')]),
    JSON.stringify([{ ...entrada('x'), guardadoEn: 'ayer' }]), JSON.stringify([{ ...entrada('x'), liga: 'otra' }])])('rechaza archivos inválidos sin escribir (%s)', texto => {
    localStorage.setItem(CLAVE_CUADERNO, JSON.stringify([entrada('previa')]));
    const original = localStorage.getItem(CLAVE_CUADERNO);
    expect(() => prepararRestauracion(texto)).toThrow(); expect(localStorage.getItem(CLAVE_CUADERNO)).toBe(original);
  });
  it('rechaza una mezcla que superaría la capacidad en lugar de truncar consultas', () => {
    localStorage.setItem(CLAVE_CUADERNO, JSON.stringify(Array.from({ length: 100 }, (_, i) => entrada(String(i)))));
    expect(() => prepararRestauracion(respaldo([entrada('nueva')]))).toThrow('capacidad');
    expect(leerCuaderno()).toHaveLength(100);
  });
  it('preserva datos dañados y permite exportar sus originales para recuperación', () => {
    localStorage.setItem(CLAVE_CUADERNO, '{dañado');
    expect(() => prepararRestauracion(respaldo([entrada('nueva')]))).toThrow();
    expect(() => crearRespaldo()).toThrow();
    expect(crearCopiaRecuperacion().originales[CLAVE_CUADERNO]).toBe('{dañado');
  });
  it('limita tamaño y profundidad del archivo antes de comparar snapshots', () => {
    expect(() => prepararRestauracion(' '.repeat(12_000_001))).toThrow('tamaño');
    let profundo: unknown = {}; for (let i = 0; i < 70; i++) profundo = { hijo: profundo };
    expect(() => prepararRestauracion(respaldo([{ ...entrada('x'), snapshot: profundo }]))).toThrow('profunda');
  });
});
