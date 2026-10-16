import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import type { RespuestaCurvaCalibracion } from '../../tipos';
import { GraficoCurvaCalibracion } from './GraficoCurvaCalibracion';

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="grafico">{children}</div>,
  LineChart: () => <div />, CartesianGrid: () => null, Line: () => null,
  ReferenceLine: () => null, Tooltip: () => null, XAxis: () => null, YAxis: () => null,
}));
afterEach(cleanup);
const vacia: RespuestaCurvaCalibracion = {
  exito: true, mercado: 'Q1', origen: 'API_USUARIO', tipo_bins: 'fijos', n_bins: 10,
  n_predicciones_total: 0, n_excluidos_push: 0, n_excluidos_outcome_dudoso: 2,
  n_excluidas_probabilidad: 3, bins: [], ece: null, mce: null,
  serie: 'calibrada', modelo_version_id: 7, estado_calidad: 'NO_EVALUABLE',
  certificacion: 'NO_CERTIFICADO', cache: 'SIN_CACHE', bin_peor_calibrado: null,
  linea_perfecta: [], periodo: { inicio: '2026-01-01', fin: '2026-01-31' },
  timestamp_calculo: '2026-10-16T17:00:00+00:00',
};
describe('Curva con serie y muestra explícitas', () => {
  it('no dibuja una curva perfecta sin muestra ni declara calibración excelente', () => {
    render(<GraficoCurvaCalibracion datos={vacia} />);
    expect(screen.queryByTestId('grafico')).toBeNull();
    expect(screen.getByText(/Sin pares válidos para esta serie/)).toBeTruthy();
    expect(screen.getByText(/Serie calibrada.*Modelo 7/)).toBeTruthy();
    expect(screen.getByText('Sin probabilidad válida: 3')).toBeTruthy();
    expect(screen.queryByText(/excelente|Bien calibrado|Sin señales fuertes de drift/)).toBeNull();
    expect(screen.getByText('ECE: —')).toBeTruthy();
  });
  it('un ECE cero de tres partidos sigue siendo muestra pequeña', () => {
    render(<GraficoCurvaCalibracion datos={{ ...vacia, n_predicciones_total: 3, ece: 0, mce: 0,
      estado_calidad: 'VALIDO_DESCRIPTIVO', bins: [{ rango_inicio: 0, rango_fin: .1, n: 3,
        probabilidad_promedio: 0, frecuencia_real: 0, gap: 0, gap_con_signo: 0, suficiente_data: false }] }} />);
    expect(screen.getByText(/Muestra pequeña o bins insuficientes/)).toBeTruthy();
    expect(screen.queryByText(/excelente|Bien calibrado/)).toBeNull();
  });
});
