import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { ResultadoAnalisis } from './ResultadoAnalisis';
import type { ResultadoVista } from '../../tipos/resultadoVista';
vi.mock('./TarjetaProbabilidad', () => ({ TarjetaProbabilidad: (p: { mediaTotal: number; desviacion: number; probabilidadOver: number; probabilidadUnder: number }) =>
  <p data-testid="principal">{JSON.stringify(p)}</p> }));
afterEach(cleanup);
function datos(): ResultadoVista {
  return { equipo: 'local', rival: 'visita', equipo_nombre_completo: 'Local sintético', rival_nombre_completo: 'Visita sintética',
    ubicacion: 'LOCAL', fecha_analisis: '2026-01-01T12:00:00Z', metadata: { mercado: 'COMPLETO' },
    es_en_vivo: false, cuartos_reales: {}, razones: [], nivel_confianza: null, factores_confianza: null,
    analisis_mercado: null, mejor_apuesta: null, linea_analizada: 220.5, probabilidad_over: .44, probabilidad_under: .56,
    predicciones: {}, prediccion_juego_completo: { media_equipo: 110, media_rival: 108, media_total: 218, desviacion_total: 16.9,
      probabilidad_over: .44, probabilidad_under: .56, linea_analizada: 220.5 },
    prediccion_ajustada: { media_ajustada: 230, desviacion_base: 16.9, probabilidad_over_ajustada: .72, probabilidad_under_ajustada: .28 },
  } as unknown as ResultadoVista;
}
it('la tarjeta real recibe el mismo origen de parámetros/porcentajes aunque haya un escenario', () => {
  render(<ResultadoAnalisis resultado={datos()} seleccionUsuario={{ lado: 'OVER', linea: 220.5 }} />);
  const p=JSON.parse(screen.getByTestId('principal').textContent!);
  expect(p.mediaTotal).toBe(218); expect(p.desviacion).toBe(16.9);
  expect(p.probabilidadOver).toBe(.44); expect(p.probabilidadUnder).toBe(.56);
  expect(screen.getByText('Base NBA · RAW, sin ajuste contextual adicional')).toBeInTheDocument();
});
it('una línea entera no presenta liquidación/push inventados ni habilita guardar apuesta', () => {
  render(<ResultadoAnalisis resultado={datos()} seleccionUsuario={{ lado: 'OVER', linea: 220 }} onGuardar={vi.fn()} />);
  expect(screen.queryByTestId('principal')).toBeNull();
  expect(screen.getAllByText(/evento discreto.*push N\/D/).length).toBeGreaterThan(0);
  expect(screen.queryByRole('button', { name: /Guardar.*[Aa]puesta/ })).toBeNull();
});
it('una probabilidad ausente en la línea original tampoco habilita guardar', () => {
  const r = datos();
  r.prediccion_juego_completo!.probabilidad_over = null;
  render(<ResultadoAnalisis resultado={r} seleccionUsuario={{ lado: 'OVER', linea: 220.5 }} onGuardar={vi.fn()} />);
  expect(screen.queryByTestId('principal')).toBeNull();
  expect(screen.queryByRole('button', { name: /Guardar.*[Aa]puesta/ })).toBeNull();
});
