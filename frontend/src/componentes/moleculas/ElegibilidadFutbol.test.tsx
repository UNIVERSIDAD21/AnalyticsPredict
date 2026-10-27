import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { ElegibilidadObjetivo, InventarioElegibilidad } from './ElegibilidadFutbol';
import type { ElegibilidadObjetivoFutbol, MuestraElegibilidadFutbol } from '../../tipos/futbol';

const muestra: MuestraElegibilidadFutbol = { denominador: 30, observados: 18, estimados: 0, ausentes: 11, invalidos: 1, utilizables: 18, ceros: 2, motivos: { CAMPO_NULL: 11, PERIODOS_NO_CONCILIAN: 1 }, fecha_max: '2026-10-18' };
const datos: ElegibilidadObjetivoFutbol = { politica: 'v1', mercado: 'CORNERS_1T', estado: 'MUESTRA_LIMITADA', naturaleza: 'OBSERVADO', calculable: true, muestras: { local_home: muestra }, minimos_contexto: { h2h: 5, local_home: 25, visitante_away: 25 }, bloques_insuficientes: ['local_home'], advertencias: ['Muestra limitada; se conserva el cálculo.'] };
afterEach(cleanup);

describe('Elegibilidad por objetivo', () => {
  it('muestra denominadores y exclusiones sin convertir ausencia en cero', () => {
    render(<ElegibilidadObjetivo datos={datos} />);
    expect(screen.getByText('18 / 30')).toBeTruthy();
    expect(screen.getByText(/Campo ausente \(NULL\) · 11/)).toBeTruthy();
    expect(screen.getByText(/Periodos incompatibles · 1/)).toBeTruthy();
    expect(screen.getByText(/Cero observado sí cuenta/)).toBeTruthy();
  });
  it('distingue N/D de estimaciones por tiempo', () => {
    const { rerender } = render(<ElegibilidadObjetivo datos={{ ...datos, estado: 'SIN_DATOS', calculable: false }} />);
    expect(screen.getByText(/N\/D · sin soporte/)).toBeTruthy();
    rerender(<ElegibilidadObjetivo datos={{ ...datos, estado: 'ESTIMADO', naturaleza: 'ESTIMADO', muestras: { local_home: { ...muestra, observados: 0, estimados: 18 } } }} />);
    expect(screen.getByText(/Estimación por tiempo desde FT/)).toBeTruthy();
    const fila = within(screen.getByRole('table')).getAllByRole('row')[1];
    expect(within(fila).getAllByRole('cell').map(e => e.textContent)).toEqual(['18 / 30', '0', '18', '11', '1']);
  });
  it('Estado cambia temporada sin mezclar muestras', () => {
    render(<InventarioElegibilidad datos={{ finales_validos: 30, finales_sin_ft: 1, criterio: 'Denominador explícito.', corte: '2026-10-25', mercados: { corners_1t: muestra }, por_temporada: [{ temporada_id: 't1', temporada: '2025-26', mercados: { corners_1t: { ...muestra, denominador: 10, observados: 0, ausentes: 10, invalidos: 0, utilizables: 0 } } }] }} />);
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 't1' } });
    const fila = within(screen.getByRole('table')).getAllByRole('row')[1];
    expect(within(fila).getAllByRole('cell')[0].textContent).toBe('10');
    expect(within(fila).getAllByRole('cell')[1].textContent).toBe('0');
    expect(screen.getByText(/Tiros 1T\/2T son estimados/)).toBeTruthy();
  });
});
