import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest';

beforeEach(() => { vi.resetModules(); window.sessionStorage.clear(); });
afterEach(() => vi.restoreAllMocks());

describe('configuración de fútbol por identidad de partido', () => {
  it('aísla cuotas, selecciones y temporadas, y no almacena resultados analíticos', async () => {
    const p = await import('./configuracionAnalisisFutbol');
    p.recordarConfiguracionFutbol('mls', { categoria: 'GOLES', temporadas: ['mls-2025'], formulario: {
      mercado: 'Q2', linea: '1.5', ladoApuesta: 'UNDER', cuotaOver: '', cuotaUnder: '1.91' } });
    p.recordarConfiguracionFutbol('arg', { categoria: 'CORNERS' });
    expect(p.leerConfiguracionFutbol('mls')).toMatchObject({ categoria: 'GOLES', temporadas: ['mls-2025'], formulario: { cuotaUnder: '1.91' } });
    expect(p.leerConfiguracionFutbol('arg').formulario).toBeUndefined();
    vi.resetModules();
    const otraCarga = await import('./configuracionAnalisisFutbol');
    expect(otraCarga.leerConfiguracionFutbol('mls').formulario?.linea).toBe('1.5');
    expect(window.sessionStorage.getItem('ap:futbol:configuraciones:v1')).not.toContain('probabilidad');
  });
  it('conserva en memoria una actualización cuando se bloquea escribir pero no leer', async () => {
    const p = await import('./configuracionAnalisisFutbol');
    p.recordarConfiguracionFutbol('mls', { categoria: 'CORNERS' });
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('Cuota agotada'); });
    p.recordarConfiguracionFutbol('mls', { categoria: 'GOLES' });
    expect(p.leerConfiguracionFutbol('mls').categoria).toBe('GOLES');
  });
  it('limpia explícitamente solo el partido elegido y limita el inventario a 50 borradores', async () => {
    const p = await import('./configuracionAnalisisFutbol');
    for (let i = 0; i < 55; i++) p.recordarConfiguracionFutbol(`p${i}`, { categoria: 'GOLES' });
    expect(JSON.parse(window.sessionStorage.getItem('ap:futbol:configuraciones:v1')!)).toHaveLength(50);
    p.olvidarConfiguracionFutbol('p54');
    expect(p.leerConfiguracionFutbol('p54').categoria).toBe('CORNERS');
    expect(p.leerConfiguracionFutbol('p53').categoria).toBe('GOLES');
  });
  it('tolera un inventario corrupto sin romper el formulario', async () => {
    const p = await import('./configuracionAnalisisFutbol');
    window.sessionStorage.setItem('ap:futbol:configuraciones:v1', '{no es json');
    expect(p.leerConfiguracionFutbol('mls')).toMatchObject({ categoria: 'CORNERS', temporadas: [] });
    p.recordarConfiguracionFutbol('mls', { categoria: 'GOLES' });
    expect(p.leerConfiguracionFutbol('mls').categoria).toBe('GOLES');
  });
});
